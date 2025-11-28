"""Julia section."""

from functools import reduce
from urllib.parse import ParseResult
from datetime import datetime
from io import BytesIO


import tomllib

from jsonpath import findall


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
    ]
    aliases = {}
    json_types = {
        "homepage": lambda x: x or None,
        "release_date": lambda x: datetime.strptime(x, "%b %Y").date(),
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

        self.juliapackages_url = juliapackages_url
        self.juliahub_url = None
        self.general_registry_url = None

        self._juliahub_json = None
        self._juliapackages_json = None
        self._package_requests_json = None

    def __repr__(self):
        return str(self.to_dict())

    def to_dict(self) -> dict:
        dictionary = {}
        for key in JuliaData.dict_keys:
            value = getattr(self, key, None)
            if value is not None:
                dictionary[key] = value
        return dictionary

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
         - juliapackages.com/p/<package_name>
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
            self.get_juliahub_url()
        except EcosystemError:
            pass
        if self.uuid:
            # see https://discourse.julialang.org/t/announcing-package-download-stats/69073
            url = (
                "https://julialang-logs.s3.amazonaws.com/public_outputs/"
                "current/package_requests.csv.gz"
            )
            self._package_requests_json = request_json(
                url,
                parser=find_first_in_csv_gz(
                    {"package_uuid": self.uuid, "status": "200", "client_type": "user"}
                ),
                content_handler=BytesIO,
            )
        self.get_general_registry_url()

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

        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{item}'"
        )

    @property
    def juliahub_json(self):
        """if the JSON was not fetch from juliahub.com, return empty dict"""
        return self._juliahub_json or {}

    def get_juliahub_url(self):
        """updates juliahub_url if exists and returns 2xx. Otherwise, nothing"""
        url = f"https://juliahub.com/ui/Packages/{self.registry}/{self.package_name}"
        try:
            empty = request_json(url, parser=lambda x: {})
            if empty == {}:
                self.juliahub_url = URL(url)
        except EcosystemError:
            self.juliahub_url = None

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
        return self._package_requests_json.get("request_addrs")
