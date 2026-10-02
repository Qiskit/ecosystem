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

"""Repository-level requirements section.

What a repository's requirements file says about Qiskit, for a repository that
declares no packaging manifest at all. There the file is not a second opinion on
something a manifest said: it is the only place the project states which Qiskit it
runs against.

This is deliberately *not* a distribution. `[python.<name>]` is keyed by a name read
from a manifest and means "you can `pip install` this from the repository", which is
false for a repository with no manifest. So this section is one table per member, with
no name to key it by, and it says nothing about installability.

Where a manifest *does* exist, the manifest is the declaration and a requirements file
alongside it is ambiguous — across the members measured it is usually a pinned CI
environment (`qiskit==2.5.2`) rather than an install requirement. `update_json` reads
nothing in that case, which is what keeps those pins out of the ecosystem data.
"""

from .serializable import JsonSerializable
from .error_handling import EcosystemError
from .github_contents import GitHubContentsMixin
from .qiskit_requirement import QiskitRequirementMixin, find_requires_qiskit, UNSET
from .python import MANIFESTS, REQUIREMENTS, parse_requirements


class RequirementsData(GitHubContentsMixin, QiskitRequirementMixin, JsonSerializable):
    """The Qiskit requirement a repository declares in its requirements file."""

    dict_keys = [
        "file",
        "requires_qiskit",
        "compatible_with_qiskit_v1",
        "compatible_with_qiskit_v2",
        "highest_supported_qiskit_release_date",
        "highest_supported_qiskit_version",
    ]

    def __init__(
        self,
        file: str = None,
        owner: str = None,
        repo: str = None,
        **kwargs,
    ):
        """
        Args:
            file: Name of the requirements file the values were read from.
            owner: GitHub owner, needed to fetch. Not serialized: it lives in the
                member's `[github]` section.
            repo: GitHub repository name. Not serialized, as above.
        """
        self.file = file
        self.owner = owner
        self.repo = repo
        self._kwargs = kwargs or {}
        self._requirements = None
        self._all_qiskit_versions = None
        self._requires_qiskit = UNSET

    def __repr__(self):
        return str(self.to_dict())

    def to_dict(self, keys=None) -> dict:
        return super().to_dict(keys=keys or RequirementsData.dict_keys)

    @classmethod
    def from_github(cls, github_data):
        """Builds an (unfetched) section from a member's `[github]` section."""
        return cls(owner=github_data.owner, repo=github_data.repo)

    @property
    def package_name(self):
        """There is no distribution here, so there is no name for one.

        `find_requires_qiskit` and the mixin name what they are reading in their
        warnings, and this is the honest answer for a repository-level section.
        """
        return None

    def update_json(self):
        """Fetches the requirements file from the default branch, if it is the only
        thing the repository declares its dependencies in.

        A repository with a packaging manifest is read by `PythonData` instead, and
        this section stays empty: see the module docstring for why a requirements
        file next to a manifest is not a declaration.
        """
        if not self.owner or not self.repo:
            raise EcosystemError(
                "RequirementsData needs owner and repo to fetch; "
                "build it with RequirementsData.from_github()"
            )
        self._requirements = None
        self.file = None
        present = self._request_listing()
        if set(MANIFESTS) & present or REQUIREMENTS not in present:
            return
        fetched = self._request_file(
            REQUIREMENTS, lambda text: {"requirements": parse_requirements(text)}
        )
        self._requirements = (fetched or {}).get("requirements")
        self._requires_qiskit = UNSET
        if self._requirements is not None:
            self.file = REQUIREMENTS

    @property
    def fetched(self):
        """True once `update_json` has read a requirements file."""
        return self._requirements is not None

    @property
    def requires_qiskit(self):
        """String with the specifier for the "qiskit" dependency.

        None when the requirements file does not mention qiskit, which is what makes
        the section not worth storing.
        """
        if not self.fetched:
            return self._kwargs.get("requires_qiskit")
        if self._requires_qiskit is not UNSET:
            # The compat properties read this repeatedly, and a miss logs a warning
            return self._requires_qiskit
        self._requires_qiskit = find_requires_qiskit(
            self._requirements, f"{self.owner}/{self.repo}"
        )
        return self._requires_qiskit
