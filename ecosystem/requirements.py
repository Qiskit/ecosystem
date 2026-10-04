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

Every file that names qiskit gets a section, and `[R01]`/`[R02]` read all of them: a
qiskit requirement the repository asks for is one somebody ends up installing, whichever
file it is in. `Qiskit/qiskit-cpp` asks for `qiskit>=2.1.0` in `requirements.txt` and a
bare `qiskit` above its black/ruff/pylint pins in `requirements-dev.txt`, and both are
uncapped, so `[R02]` has something to say about either. The check ups name the file they
read, so a maintainer knows which one to edit.
"""

from fnmatch import fnmatchcase
from pathlib import PurePath

from .serializable import JsonSerializable
from .error_handling import EcosystemError
from .github_contents import GitHubContentsMixin
from .qiskit_requirement import QiskitRequirementMixin
from .python import MANIFESTS, parse_requirements

#: Filenames that count as a requirements file, as a `fnmatch` pattern matched against
#: the lowercased name. Deliberately not applied to `PythonData`, whose requirements
#: fallback stands in for what a manifest pointed at and so has the conventional name.
REQUIREMENTS_PATTERN = "*requirements*.txt"


class RequirementsData(GitHubContentsMixin, QiskitRequirementMixin, JsonSerializable):
    """The Qiskit requirement one requirements file of a repository declares."""

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
            file: Name of the requirements file this section reads. A section without
                one is a probe, good only for `candidates`.
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

    def __repr__(self):
        return str(self.to_dict())

    def to_dict(self, keys=None) -> dict:
        return super().to_dict(keys=keys or RequirementsData.dict_keys)

    @classmethod
    def from_github(cls, github_data):
        """Builds a probe from a member's `[github]` section, to call `candidates` on."""
        return cls(owner=github_data.owner, repo=github_data.repo)

    @classmethod
    def from_url(cls, requirements_url):
        """Builds an (unfetched) section from the URL of a requirements file, like
        - https://github.com/<owner>/<repo>/blob/<ref>/requirements.txt
        - https://github.com/<owner>/<repo>/blob/<ref>/docs/requirements.txt

        This is how a file outside the repository root gets recorded: `candidates` lists the
        root only, so a `docs/requirements.txt` is never discovered, and whether such a file
        is what the project declares is a judgement a person makes rather than a rule.

        The path may be a pattern (`versions/*/requirements.txt`), which
        `Member.update_requirements` expands against the repository on every run. The `<ref>`
        is dropped: files are read from the default branch.

        Returns None for any other URL, so that a link to a registry stays for something
        else to claim.
        """
        if "github.com" not in (requirements_url.hostname or ""):
            return None

        parts = [part for part in requirements_url.path.split("/") if part]
        if len(parts) < 5 or parts[2] != "blob":
            return None

        path = "/".join(parts[4:])
        if not fnmatchcase(parts[-1].lower(), REQUIREMENTS_PATTERN):
            return None

        return cls(file=path, owner=parts[0], repo=parts[1])

    @property
    def is_pattern(self):
        """Whether `file` is a pattern standing for the files it matches, not a file."""
        return any(wildcard in (self.file or "") for wildcard in "*?[")

    def matches(self):
        """The files of the repository this pattern stands for, as unfetched sections.

        `PurePath.full_match` rather than `fnmatch`: there `*` crosses `/`, so
        `*requirements*.txt` would also claim `binder/jupyter-requirements-security.txt`.
        Here a pattern matches what it looks like it matches, and `**/` is how you ask for
        any depth.
        """
        return [
            type(self)(file=path, owner=self.owner, repo=self.repo)
            for path in sorted(self._request_tree())
            if PurePath(path).full_match(self.file)
        ]

    @property
    def dependencies(self):
        """The requirement lines read from the file, for the mixin to find qiskit in."""
        return self._requirements or []

    @property
    def declared_by(self):
        """What the mixin names in its warnings: no distribution here, so the repo."""
        return f"{self.owner}/{self.repo}"

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

    @property
    def fetched(self):
        """True once `update_json` has read the requirements file."""
        return self._requirements is not None
