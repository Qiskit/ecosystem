# This code is part of Qiskit.
#
# (C) Copyright IBM 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at https://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""crates.io section.

What a project publishes to the Rust registry, in the shape `[pypi.<name>]` uses, minus
everything about Qiskit: nothing a crate can depend on is published there. Qiskit's own
crates (`qiskit-accelerate`, `qiskit-circuit`, `qiskit-cext` and the rest of
`Qiskit/qiskit/crates/*`) are workspace-internal and do not exist on crates.io, and a crate
with a git dependency cannot be published at all, so a published crate reaches Qiskit only
through the C API, through pyo3, or not at all. There is no `requires_qiskit` to record and
no compatibility to check.
"""

from re import match

from jsonpath import findall

from .license import License
from .serializable import JsonSerializable, parse_date
from .error_handling import EcosystemError
from .request import request_json

# crates.io answers 403 to a request without a User-Agent, and `request_json` sends one for
# api.github.com only
HEADERS = {
    "Accept": "application/json",
    "User-Agent": "github.com/Qiskit/ecosystem/",
}


class CratesData(JsonSerializable):
    """
    The crates.io data related to a project
    """

    dict_keys = [
        "package_name",
        "version",
        "last_release_date",
        "license",
        "description",
        "url",
        "maintainers",
        "rust_version",
        "edition",
        "total_downloads",
        "last_90_days_downloads",
    ]
    aliases = {
        "version": "crate.max_stable_version",
        "description": "crate.description",
        "total_downloads": "crate.downloads",
        "last_90_days_downloads": "crate.recent_downloads",
    }

    def __init__(self, package_name: str, **kwargs):
        self.package_name = package_name
        self._kwargs = kwargs or {}
        self._crates_json = None
        self._owners_json = None

    def __repr__(self):
        return str(self.to_dict())

    def to_dict(self, keys=None) -> dict:
        return super().to_dict(keys=keys or CratesData.dict_keys)

    @classmethod
    def from_dict(cls, dictionary: dict):
        """A stored section, with the license as the class that knows its equivalences.

        `cls(**dictionary)` rather than `super().from_dict`, which is the same call: it
        says what comes back, so a caller reading a field off it type-checks.
        """
        if dictionary.get("license") is not None:
            dictionary["license"] = License(dictionary["license"], where="crates")
        return cls(**dictionary)

    @classmethod
    def from_url(cls, crates_project_url):
        """
        Builds a CratesData from an URL that looks like
        'https://crates.io/crates/<package_name>'.
        Returns None if the given URL is not a crates.io url
        """
        if "crates.io" not in crates_project_url.hostname:
            return None

        path_parts = [
            part
            for part in crates_project_url.path.split("/")
            if match(r"^[A-Za-z0-9_.-]+$", part)
        ]
        if len(path_parts) == 2 and path_parts[0] == "crates":
            return CratesData(package_name=path_parts[1])

        raise EcosystemError(f"invalid crates.io url: {crates_project_url}")

    def update_json(self):
        """
        Fetches remote jsons data from:
          - https://crates.io/api/v1/crates/{self.package_name}
          - https://crates.io/api/v1/crates/{self.package_name}/owners
        """
        self._crates_json = self.request_crates()
        self._owners_json = self.request_owners()

    def request_crates(self):
        """Fetches https://crates.io/api/v1/crates/{self.package_name}"""
        try:
            return request_json(
                f"https://crates.io/api/v1/crates/{self.package_name}", headers=HEADERS
            )
        except EcosystemError:
            return None

    def request_owners(self):
        """Fetches https://crates.io/api/v1/crates/{self.package_name}/owners.

        A separate request because the crate payload does not carry who publishes it.
        """
        try:
            return request_json(
                f"https://crates.io/api/v1/crates/{self.package_name}/owners",
                headers=HEADERS,
            )
        except EcosystemError:
            return None

    def __getattr__(self, item):
        """A field of the fetched payload, or the stored value, or nothing.

        The stored value stays the fallback after a fetch, so a payload that turns out not
        to carry a field leaves the section with what it had rather than emptying it.
        """
        if self._crates_json:
            found = findall(CratesData.aliases.get(item, item), self._crates_json)
            if len(found) == 1:
                return found[0]
        if item in self._kwargs:
            return self._kwargs[item]
        if item in self.dict_keys:
            return None
        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{item}'"
        )

    @property
    def crates_json(self):
        """if the JSON was not fetched from crates.io, return an empty dict"""
        return self._crates_json or {}

    @property
    def released_version(self):
        """The payload of the release `version` names, out of the versions it carries.

        Everything a release declares for itself lives here rather than in the crate: the
        license, the edition and the Rust version a crate asks for are what the latest
        release asks for, not what the crate has always asked for.
        """
        for version in self.crates_json.get("versions", []):
            if version.get("num") == self.version:
                return version
        return {}

    @property
    def url(self):
        """The crate page on crates.io, which is a function of the name"""
        if "url" in self._kwargs:
            return self._kwargs["url"]
        return f"https://crates.io/crates/{self.package_name}"

    @property
    def last_release_date(self):
        """Date of the last release in crates.io"""
        created_at = self.released_version.get("created_at")
        if created_at:
            return parse_date(created_at)
        return self._kwargs.get("last_release_date")

    @property
    def license(self):
        """Crate license, as the SPDX expression the release declares"""
        crates_license = self.released_version.get("license")
        if crates_license:
            return License(crates_license, "crates")
        if "license" in self._kwargs:
            if isinstance(self._kwargs["license"], License):
                return self._kwargs["license"]
            return License(self._kwargs["license"], "crates")
        return None

    @property
    def rust_version(self):
        """The oldest Rust the release supports, when it declares one"""
        return self.released_version.get("rust_version") or self._kwargs.get(
            "rust_version"
        )

    @property
    def edition(self):
        """The Rust edition the release is written in"""
        return self.released_version.get("edition") or self._kwargs.get("edition")

    @property
    def maintainers(self):
        """Who can publish the crate, as the URLs crates.io gives for them.

        Both users and teams are owners, and a team is as much the answer to "who
        publishes this" as a person is, so neither is filtered out.
        """
        maintainers = [
            owner["url"]
            for owner in (self._owners_json or {}).get("users", [])
            if owner.get("url")
        ]
        return maintainers or self._kwargs.get("maintainers")
