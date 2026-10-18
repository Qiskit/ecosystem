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
package data class that provides `_kwargs`, plus either its own `requires_qiskit`
or the `fetched` and `dependencies` the default one reads.
"""

from os import path
import json

from packaging.requirements import Requirement, InvalidRequirement
from packaging.specifiers import SpecifierSet
from packaging.utils import canonicalize_name
from packaging.version import Version

from jsonpath import findall

from .serializable import JsonSerializable, parse_date
from .error_handling import EcosystemError, logger
from .request import request_json


def find_requires_qiskit(dependencies, declared_by=None):
    """The specifier of the "qiskit" requirement among `dependencies`, or None.

    `dependencies` is a list of PEP 508 strings, wherever they were declared: a
    manifest, a requirements file or a registry. `declared_by` only names what is
    being read, for the warnings.

    A bare `qiskit` with no specifier is reported as `">=0"`, because "depends on
    qiskit without saying which" is a different thing from "does not depend on
    qiskit", and only the specifier form survives into the stored section.
    """
    for requirement_str in dependencies:
        try:
            requirement = Requirement(requirement_str)
        except InvalidRequirement:
            logger.warning(
                "%s declares an unparseable requirement: %r",
                declared_by,
                requirement_str,
            )
            continue
        if canonicalize_name(requirement.name) != "qiskit":
            continue
        if len(requirement.specifier):
            return str(requirement.specifier)
        logger.warning(
            '%s depends on qiskit but with empty specifier. Forcing one, ">=0"',
            declared_by,
        )
        return ">=0"
    return None


class QiskitRequirementMixin:
    """Resolves a `requires_qiskit` specifier against the Qiskit release history."""

    # Subclasses normally set this in __init__; the default keeps the mixin usable
    # for classes that never fetch.
    _all_qiskit_versions = None

    def _memo(self, name, resolve):
        """`resolve()` once per value per fetch state.

        Keyed on `fetched`, which is the point: `ci.py` serializes a member after every
        updater and serializing reads these properties, so a `cached_property` filled in
        while the section was still unfetched outlived the fetch and the stored value was
        written back unchanged (a `requires_qiskit` whose ceiling had moved never resolved
        again). Re-resolving on the transition is what fixes that.

        The memoization itself is only about the warnings: `find_requires_qiskit` logs for
        an empty or unparseable specifier, and `to_dict` reads the specifier through four
        compat fields, so without it one bare `qiskit` is reported four times. It buys no
        measurable time — a stored section answers from `_kwargs` without touching the
        release table, which is every section outside an update run.
        """
        memo = self.__dict__.setdefault("_qiskit_memo", {})
        fetched = self.fetched
        if name not in memo or memo[name][0] != fetched:
            memo[name] = (fetched, resolve())
        return memo[name][1]

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

    @property
    def declared_by(self):
        """What the warnings name, for a subclass that has a distribution to name."""
        return self.package_name

    @property
    def requires_qiskit(self):
        """String with the specifier for the "qiskit" dependency, or None.

        Memoized so that a miss warns once per object rather than once per read; every
        property below reads it. `PyPIData` overrides it; `PythonData.deferred` tells its
        "no qiskit" from its "could not tell".
        """

        def resolve():
            if not self.fetched:
                return self._kwargs.get("requires_qiskit")
            return find_requires_qiskit(self.dependencies, self.declared_by)

        return self._memo("requires_qiskit", resolve)

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
        resolved = self.highest_supported_qiskit_version_and_release_date
        # None when nothing is required, and also when no release satisfies what is:
        # `>=99` is a specifier the release history cannot answer yet
        return resolved[0] if resolved else None

    @property
    def highest_supported_qiskit_release_date(self):
        """Returns when was released the highest supported Qiskit version"""
        resolved = self.highest_supported_qiskit_version_and_release_date
        return parse_date(resolved[1]) if resolved else None

    @property
    def highest_supported_qiskit_version_and_release_date(self):
        """Returns the highest supported Qiskit version and when it was released"""
        return self._memo("highest_supported", self._resolve_highest_supported)

    def _resolve_highest_supported(self):
        """The resolution itself, split out so the property stays one line."""
        if self.requires_qiskit is None:
            return None
        # Nothing was read, so there is nothing to resolve against: a stored section answers
        # from what the member file says, which is what makes it readable with no network.
        # Keyed on `fetched` rather than on whether the release table happens to be loaded:
        # that only ever became true in `update_pypi`, which force-updates the table, so the
        # other updaters re-read a repository and still handed back the stored version.
        if (
            not self.fetched
            and "highest_supported_qiskit_release_date" in self._kwargs
            and "highest_supported_qiskit_version" in self._kwargs
        ):
            return (
                self._kwargs["highest_supported_qiskit_version"],
                self._kwargs["highest_supported_qiskit_release_date"],
            )

        qiskit_specifier = SpecifierSet(self.requires_qiskit)
        prereleases = bool(qiskit_specifier.prereleases)
        all_qiskit_versions = sorted(
            self.all_qiskit_versions().items(),
            key=lambda x: Version(x[0]),
            reverse=True,
        )
        for qiskit_version, version_data in all_qiskit_versions:
            if not prereleases and Version(qiskit_version).is_prerelease:
                continue
            if qiskit_specifier.contains(qiskit_version, prereleases=prereleases):
                return qiskit_version, version_data["upload_at"]
        return None


class QiskitRequirement(QiskitRequirementMixin, JsonSerializable):
    """One qiskit requirement a release declares, and the condition it is under.

    A release can ask for qiskit several times: behind an extra (`pip install
    pkg[qiskit]`), under an environment marker, or through another dependency. Each of
    those is its own requirement with its own resolved compatibility, which is why the
    four derived fields live here rather than on the distribution: a specifier that only
    applies on Python 3.14 resolves differently from the one that applies below it.

    The shape `[[requirements]]` has, for the same reason: a specifier plus what the
    mixin derives from it, with no name of its own to be keyed by.
    """

    dict_keys = [
        "specifier",
        "extra",
        "environment",
        "via",
        "compatible_with_qiskit_v1",
        "compatible_with_qiskit_v2",
        "highest_supported_qiskit_release_date",
        "highest_supported_qiskit_version",
    ]

    def __init__(
        self,
        specifier: str = None,
        extra: str = None,
        environment: str = None,
        via: str = None,
        **kwargs,
    ):
        """
        Args:
            specifier: the PEP 440 specifier, `>=0` for a bare `qiskit`.
            extra: the extra that has to be requested for this to apply. None means a
                plain install gets it.
            environment: the rest of the PEP 508 marker, once the `extra ==` part is
                taken out. None means it always applies.
            via: the dependency this is reached through, as the release declares it.
                None means the release requires qiskit itself.
        """
        self.specifier = specifier
        self.extra = extra
        self.environment = environment
        self.via = via
        self._kwargs = kwargs or {}
        self._all_qiskit_versions = None

    def __repr__(self):
        return str(self.to_dict())

    def to_dict(self, keys=None) -> dict:
        return super().to_dict(keys=keys or QiskitRequirement.dict_keys)

    @property
    def requires_qiskit(self):
        """What the mixin resolves, which here is the specifier itself"""
        return self.specifier

    @property
    def fetched(self):
        """Always true: the specifier is the requirement, so there is nothing to fetch.

        What the mixin asks with this is whether a stored value is all it has to go on,
        and here it never is.
        """
        return True

    @property
    def declared_by(self):
        """What the warnings name"""
        return f"qiskit{self.specifier}" + (
            f" (extra {self.extra})" if self.extra else ""
        )

    @property
    def conditional(self):
        """True when something has to be true beyond installing the release.

        An extra has to be requested, an environment has to match, or another dependency
        is what brings qiskit in. A requirement with none of those is what a plain
        `pip install` creates.
        """
        return bool(self.extra or self.environment or self.via)
