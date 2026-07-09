# This code is part of Qiskit.
#
# (C) Copyright IBM 2023.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at https://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Julia section."""

from functools import reduce
from urllib.parse import ParseResult
from datetime import datetime
from io import BytesIO


import tomllib

from jsonpath import findall

from .license import License
from .serializable import JsonSerializable
from .error_handling import EcosystemError
from .request import request_json, URL, parse_juliapackages, find_first_in_csv_gz


class JuliaData(JsonSerializable):
    """
    The Julia data related to a project
    """

    dict_keys = [
        "package_name",
        "registry",
        "version",
        "license",
        "owner",
        "homepage",
        "release_date",
        "juliahub_url",
        "general_registry_url",
        "uuid",
        "estimated_unique_users",
        "monthly_downloads",
        "total_downloads",
    ]
    aliases = {}
    json_types = {
        "homepage": lambda x: x or None,
        "release_date": lambda x: datetime.strptime(x, "%b %Y").date(),
        "license": lambda x: License(x) if x else None,
    }
    reduce = {}

    def __init__(
        self,
        package_name: str = None,
        registry: str = "General",
        juliapackages_url: str = None,
        **kwargs,
    ):
        self.package_name = package_name
        self.registry = registry or "General"
        self._kwargs = kwargs or {}
        self._juliahub_url = None

        self.juliapackages_url = juliapackages_url
        self.general_registry_url = None

        self._juliahub_json = None
        self._juliapackages_json = None
        self._package_requests_json = None
        self._juliapkgstats_json = None

    def __repr__(self):
        return str(self.to_dict())

    def to_dict(self, keys=None) -> dict:
        return super().to_dict(keys=keys or JuliaData.dict_keys)

    @classmethod
    def from_url(cls, julia_project_url: ParseResult):
        """
        Builds a JuliaSection from an URL (ParseResult) that looks like:
        - https://juliahub.com/ui/Packages/<registry>/<package_name>
        Return None if none of these are passed
        """
        url_path_parts = [
            i.strip() for i in julia_project_url.path.split("/") if i.strip()
        ]
        registry, package_name = None, None
        if "juliahub.com" in julia_project_url.hostname:
            if (
                len(url_path_parts) == 4
                and url_path_parts[0] == "ui"
                and url_path_parts[1] == "Packages"
            ):
                registry, package_name = url_path_parts[2:]
            else:
                raise EcosystemError(
                    f"invalid JuliaHub url: {julia_project_url.geturl()}"
                )
        elif "juliapackages.com" in julia_project_url.hostname:
            if len(url_path_parts) == 2 and url_path_parts[0] == "p":
                return JuliaData(juliapackages_url=julia_project_url.geturl())
            raise EcosystemError(
                f"invalid juliapackages.com url: {julia_project_url.geturl()}"
            )
        if package_name is None:
            return None
        return JuliaData(package_name=package_name, registry=registry)

    def update_json(self):
        """
        Fetches remote json data from:
         - juliahub.com/docs/<registry>/<package_name>/stable/pkg.json
         - juliapackages.com/p/<package_name> (_juliapackages_json)
         - juliapkgstats.com/api/v2/monthly_downloads/<package_name> (_juliapkgstats_json)
         - juliapkgstats.com/api/v2/total_downloads/<package_name> (_juliapkgstats_json)
        """
        if self.package_name is None and self.juliapackages_url is not None:
            self._juliapackages_json = request_json(
                self.juliapackages_url, parser=parse_juliapackages
            )
            self.package_name = self._juliapackages_json["package_name"]
            self.registry = "General"
        try:
            self._juliahub_json = request_json(
                f"juliahub.com/docs/{self.registry}/{self.package_name}/stable/pkg.json"
            )
            self._juliahub_url = URL(
                f"https://juliahub.com/ui/Packages/{self.registry}/{self.package_name}"
            )
        except EcosystemError:
            self._juliahub_url = None
            if "juliahub_url" in self._kwargs:
                del self._kwargs["juliahub_url"]
        if self.uuid:
            # see https://discourse.julialang.org/t/announcing-package-download-stats/69073
            url = (
                "https://julialang-logs.s3.amazonaws.com/public_outputs/"
                "current/package_requests.csv.gz"
            )
            self._package_requests_json = request_json(
                url,
                parser=find_first_in_csv_gz(
                    {
                        "package_uuid": self.uuid,
                        "statuses": ["200", "302", "301"],
                        "client_type": "user",
                    }
                ),
                content_handler=BytesIO,
            )
        self.get_general_registry_url()
        try:
            total_downloads = request_json(
                f"https://juliapkgstats.com/api/v2/total_downloads/{self.package_name}/"
            )
            monthly_downloads = request_json(
                f"https://juliapkgstats.com/api/v2/monthly_downloads/{self.package_name}/"
            )
            self._juliapkgstats_json = {}
            # Non-existing packages return 0-download values, so filtering them
            if (
                "total_requests" in total_downloads
                and total_downloads["total_requests"] > 0
            ):
                self._juliapkgstats_json["total_downloads"] = total_downloads[
                    "total_requests"
                ]
            if (
                "total_requests" in monthly_downloads
                and monthly_downloads["total_requests"] > 0
            ):
                self._juliapkgstats_json["monthly_downloads"] = monthly_downloads[
                    "total_requests"
                ]
        except EcosystemError:
            self._juliapkgstats_json = {}

    def __getattr__(self, item):
        if self._juliahub_json:
            if item in JuliaData.aliases:
                item = JuliaData.aliases[item]

            json_elements = findall(item, self._juliahub_json)
            if item in JuliaData.json_types:
                json_elements = [JuliaData.json_types[item](e) for e in json_elements]

            if len(json_elements) == 1:
                return json_elements[0]

            if len(json_elements) >= 2:
                return reduce(JuliaData.reduce[item], json_elements)

            raise AttributeError(
                f"'{type(self).__name__}' object has no " f"attribute '{item}'"
            )

        if item in self._kwargs:
            return self._kwargs[item]

        if item in self.dict_keys:
            return None

        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{item}'"
        )

    @property
    def juliahub_json(self):
        """if the JSON was not fetch from juliahub.com, return empty dict"""
        return self._juliahub_json or {}

    def get_general_registry_url(self):
        """updates general_registry_url if exists and returns 2xx. Otherwise, nothing"""
        if self.registry == "General":
            registry = request_json(
                "https://raw.githubusercontent.com/JuliaRegistries/"
                "General/refs/heads/master/Registry.toml",
                parser=tomllib.loads,
            )
        else:
            return None
        for pkg in registry["packages"].values():
            if pkg["name"] == self.package_name:
                dirname = pkg["path"]
                break
        else:
            return None
        url = f"https://github.com/JuliaRegistries/General/tree/master/{dirname}"
        try:
            empty = request_json(url, parser=lambda x: {})
            if empty == {}:
                self.general_registry_url = URL(url)
        except EcosystemError:
            self.general_registry_url = None

    @property
    def estimated_unique_users(self):
        """unique IPs requesting users"""
        if self._package_requests_json is None:
            return self._kwargs.get("estimated_unique_users")
        return int(self._package_requests_json.get("request_addrs"))

    @property
    def monthly_downloads(self):
        """User monthly downloads as reported by https://juliapkgstats.com/api"""
        if self._juliapkgstats_json is None:
            ret = self._kwargs.get("monthly_downloads")
        else:
            ret = self._juliapkgstats_json.get("monthly_downloads")
        return int(ret) if ret else None

    @property
    def total_downloads(self):
        """User total downloads as reported by https://juliapkgstats.com/api"""
        if self._juliapkgstats_json is None:
            ret = self._kwargs.get("total_downloads")
        else:
            ret = self._juliapkgstats_json.get("total_downloads")
        return int(ret) if ret else None

    @property
    def juliahub_url(self):
        """Package URL in https://juliahub.com/ui/Packages/"""
        return self._juliahub_url or self._kwargs.get("juliahub_url")
