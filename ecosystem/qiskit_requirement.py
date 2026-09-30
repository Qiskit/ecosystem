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

"""Qiskit requirement resolution, shared by every kind of package section.

Everything here is derived from a single PEP 440 specifier (`requires_qiskit`)
plus the table of Qiskit releases, so it does not care whether that specifier
came from PyPI, from a source tree or from a Julia registry. Mix it into a
package data class that provides `requires_qiskit`, `_kwargs` and
`package_name`.
"""

from functools import cached_property
from os import path
import json

from packaging.specifiers import SpecifierSet
from packaging.version import Version

from jsonpath import findall

from .serializable import parse_date
from .error_handling import EcosystemError, logger
from .request import request_json


class QiskitRequirementMixin:
    """Resolves a `requires_qiskit` specifier against the Qiskit release history."""

    # Subclasses normally set this in __init__; the default keeps the mixin usable
    # for classes that never fetch.
    _all_qiskit_versions = None

    def all_qiskit_versions(self, force_update=False):
        """Returns a dictionary with all the Qiskit releases,
        with version numbers as key and extra data"""
        dir_path = path.dirname(path.realpath(__file__))
        all_qiskit_versions_json = path.join(dir_path, "all_qiskit_versions.json")
        if force_update:
            qiskit_json = request_json("pypi.org/pypi/qiskit/json")
            str_versions = findall("$.releases.~", qiskit_json)
            self._all_qiskit_versions = {}
            for str_version in str_versions:
                str_dates = findall(
                    f'$.releases["{str_version}"].*.upload_time_iso_8601', qiskit_json
                )
                if not str_dates:
                    raise EcosystemError(f"Qiskit {str_version} has no release?")
                last_date = max(parse_date(d) for d in str_dates)
                self._all_qiskit_versions[str_version] = {"upload_at": last_date}
            with open(all_qiskit_versions_json, "w") as json_file:
                json.dump(self._all_qiskit_versions, json_file, indent=4, default=str)

        if self._all_qiskit_versions is None:
            try:
                with open(all_qiskit_versions_json) as data_file:
                    versions_dates_dict = json.load(data_file)
            except FileNotFoundError:
                logger.warning(
                    "%s not found. Getting it back fom PyPI.", all_qiskit_versions_json
                )
                return self.all_qiskit_versions(force_update=True)
            self._all_qiskit_versions = {
                k: {"upload_at": parse_date(v["upload_at"])}
                for k, v in versions_dates_dict.items()
            }
        return self._all_qiskit_versions

    def compatible_with_qiskit(self, major: int):
        """Boolean if the package is compatible with any Qiskit of the v<major> series"""
        if self.requires_qiskit is None:
            return self._kwargs.get(f"compatible_with_qiskit_v{major}")
        qiskit_specifier = SpecifierSet(self.requires_qiskit)
        return not (SpecifierSet(f"=={major}.*") & qiskit_specifier).is_unsatisfiable()

    @property
    def compatible_with_qiskit_v1(self):
        """Boolean if the package is compatible with any Qiskit of the v1 series"""
        return self.compatible_with_qiskit(major=1)

    @property
    def compatible_with_qiskit_v2(self):
        """Boolean if the package is compatible with any Qiskit of the v2 series"""
        return self.compatible_with_qiskit(major=2)

    @property
    def highest_supported_qiskit_version(self):
        """Returns the highest supported Qiskit version"""
        if self.requires_qiskit is None:
            return None
        return self.highest_supported_qiskit_version_and_release_date[0]

    @property
    def highest_supported_qiskit_release_date(self):
        """Returns when was released the highest supported Qiskit version"""
        if self.requires_qiskit is None:
            return None
        return parse_date(self.highest_supported_qiskit_version_and_release_date[1])

    @cached_property
    def highest_supported_qiskit_version_and_release_date(self):
        """Returns the highest supported Qiskit version and when it was released"""
        if self.requires_qiskit is None:
            return None
        if (
            self._all_qiskit_versions is None
            and "highest_supported_qiskit_release_date" in self._kwargs
            and "highest_supported_qiskit_version" in self._kwargs
        ):
            return (
                self._kwargs["highest_supported_qiskit_version"],
                self._kwargs["highest_supported_qiskit_release_date"],
            )

        qiskit_specifier = SpecifierSet(self.requires_qiskit)
        all_qiskit_versions = sorted(
            self.all_qiskit_versions().items(),
            key=lambda x: Version(x[0]),
            reverse=True,
        )
        for qiskit_version, version_data in all_qiskit_versions:
            if qiskit_specifier.contains(qiskit_version):
                return qiskit_version, version_data["upload_at"]
        return None
