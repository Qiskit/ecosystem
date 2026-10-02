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

"""Repository-level requirements sections.

What a repository's requirements files say about Qiskit, for a repository that declares
no packaging manifest at all. There a requirements file is not a second opinion on
something a manifest said: it is the only place the project states which Qiskit it runs
against.

This is deliberately *not* a distribution. `[python.<name>]` is keyed by a name read
from a manifest and means "you can `pip install` this from the repository", which is
false for a repository with no manifest. So these sections have no name to be keyed by,
and they say nothing about installability.

Where a manifest *does* exist, the manifest is the declaration and a requirements file
alongside it is ambiguous — across the members measured it is usually a pinned CI
environment (`qiskit==2.5.2`) rather than an install requirement. `candidates` reads
nothing in that case, which is what keeps those pins out of the ecosystem data.

A repository may declare several, so this is an array of tables:

    [[requirements]]
    file = "requirements.txt"
    ...

`REQUIREMENTS_PATTERN` is what counts as one. It is wider than the single
`requirements.txt` that `PythonData` falls back on, because without a manifest there is
no reason the file has to carry the conventional name: of the members measured,
`Qiskit/benchpress` declares its Qiskit only in `requirements-qiskit.txt` (one of eight
such files, the rest for other SDKs) and `quantumcat` only in `requirements-review.txt`.

Breadth has a cost, and `primary` is what pays it. A file that names qiskit is worth
recording whatever it is for, but a dev or lint file is not a statement about what the
project runs against: `Qiskit/qiskit-cpp` asks for `qiskit>=2.1.0` in
`requirements.txt` and a bare `qiskit` above its black/ruff/pylint pins in
`requirements-dev.txt`. Reading the bare one as a declaration would mean the project
allows an unreleased Qiskit 3, and `[R02]` would say so. So every file that names
qiskit is stored, and exactly one is judged: see `primary_of`.
"""

from fnmatch import fnmatchcase

from .serializable import JsonSerializable
from .error_handling import EcosystemError
from .github_contents import GitHubContentsMixin
from .qiskit_requirement import QiskitRequirementMixin, find_requires_qiskit, UNSET
from .python import MANIFESTS, REQUIREMENTS, parse_requirements

#: Filenames that count as a requirements file, as a `fnmatch` pattern matched against
#: the lowercased name. Deliberately not applied to `PythonData`, whose requirements
#: fallback stands in for what a manifest pointed at and so has the conventional name.
REQUIREMENTS_PATTERN = "*requirements*.txt"


def primary_of(sections):
    """The one section the check ups judge, out of a member's list.

    `requirements.txt` wins when the repository has one, because that is the file the
    convention reserves for what the project itself needs; anything else is there for a
    purpose the filename alone does not reveal. With no such file there is nothing to
    prefer, so the first one is taken — the list is sorted by name, so the choice is at
    least stable. `mark_primary` records the answer in the toml, and this reads it back,
    falling back to the same rule for a section written by hand.

    Returns None for a member with no sections at all.
    """
    if not sections:
        return None
    for section in sections:
        if section.primary:
            return section
    by_name = {section.file: section for section in sections}
    return by_name.get(REQUIREMENTS) or sections[0]


def mark_primary(sections):
    """Records which section `primary_of` chose, when there is a choice to record.

    Left off a lone section: there is nothing for it to be primary *among*, and the
    check ups read it either way.
    """
    for section in sections:
        section.primary = None
    if len(sections) > 1:
        primary_of(sections).primary = True


class RequirementsData(GitHubContentsMixin, QiskitRequirementMixin, JsonSerializable):
    """The Qiskit requirement one requirements file of a repository declares."""

    dict_keys = [
        "file",
        "primary",
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
        primary: bool = None,
        **kwargs,
    ):
        """
        Args:
            file: Name of the requirements file this section reads. A section without
                one is a probe, good only for `candidates`.
            owner: GitHub owner, needed to fetch. Not serialized: it lives in the
                member's `[github]` section.
            repo: GitHub repository name. Not serialized, as above.
            primary: True on the section the check ups judge, when a member has more
                than one. Set by `mark_primary`, not by hand.
        """
        self.file = file
        self.owner = owner
        self.repo = repo
        self.primary = primary
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
        """Builds a probe from a member's `[github]` section, to call `candidates` on."""
        return cls(owner=github_data.owner, repo=github_data.repo)

    @property
    def package_name(self):
        """There is no distribution here, so there is no name for one.

        `find_requires_qiskit` and the mixin name what they are reading in their
        warnings, and this is the honest answer for a repository-level section.
        """
        return None

    def candidates(self):
        """The requirements files of the repository, as unfetched sections.

        Empty for a repository with a packaging manifest, which is read by `PythonData`
        instead: see the module docstring for why a requirements file next to a
        manifest is not a declaration. Empty, too, when the repository has no
        requirements file at all.

        One request, the directory listing, which `PythonData.update_json` makes for
        every member anyway — so over a full run this is served from the cache.
        Subdirectories are not searched: the listing reports files only, and every
        requirements file measured across the corpus sits beside the manifests.
        """
        present = self._request_listing()
        if set(MANIFESTS) & present:
            return []
        return [
            type(self)(file=name, owner=self.owner, repo=self.repo)
            for name in sorted(present)
            if fnmatchcase(name.lower(), REQUIREMENTS_PATTERN)
        ]

    def update_json(self):
        """Fetches this section's requirements file from the default branch."""
        if not self.owner or not self.repo:
            raise EcosystemError(
                "RequirementsData needs owner and repo to fetch; "
                "build it with RequirementsData.from_github()"
            )
        if not self.file:
            raise EcosystemError(
                "RequirementsData needs a file to fetch; "
                "build it with RequirementsData.candidates()"
            )
        fetched = self._request_file(
            self.file, lambda text: {"requirements": parse_requirements(text)}
        )
        self._requirements = (fetched or {}).get("requirements")
        self._requires_qiskit = UNSET

    @property
    def fetched(self):
        """True once `update_json` has read the requirements file."""
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
