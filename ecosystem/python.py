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

"""Python source-tree package section.

The metadata a Python project declares in its own repository, for projects that
are installable with `pip install git+<repo>` but have no release in a registry.
This is a sibling of `PyPIData`, not a parent or a child of it: a PyPI section
describes an immutable published artifact, while this one describes whatever the
default branch says today.

Values come from the three manifests `pip` would feed to setuptools, in the
precedence order setuptools itself documents:

    pyproject.toml `[project]`  >  setup.cfg `[metadata]`/`[options]`  >  setup.py

Dependencies have one rung below those: a `requirements.txt` next to the manifests.
It is read only when no manifest declares any dependency, which is exactly the
`install_requires=parse("requirements.txt")` pattern — there the file is not a
second opinion, it is the value the manifest pointed at. It is deliberately not a
manifest itself (see `REQUIREMENTS`).

`setup.py` is *parsed*, never executed: this code runs over ~200 third-party
submissions in CI, so `exec` is not on the table. Keyword arguments that are not
literals cannot be read statically; they are reported in `deferred` rather than
guessed at.
"""

from ast import parse as ast_parse, walk as ast_walk, Call, Name, Attribute
from ast import literal_eval
from configparser import ConfigParser, Error as ConfigParserError
from io import StringIO
import tomllib

from packaging.utils import canonicalize_name

from .license import License
from .serializable import JsonSerializable
from .error_handling import EcosystemError, logger
from .github_contents import GitHubContentsMixin
from .qiskit_requirement import QiskitRequirementMixin, find_requires_qiskit, UNSET

#: Sentinel for "not computed yet", so that a cached None is not recomputed.

#: Manifests that can carry packaging metadata, in precedence order.
MANIFESTS = ("pyproject.toml", "setup.cfg", "setup.py")

#: Fallback dependency list. Deliberately *not* a manifest: it declares no
#: distribution name, so it can never create a section, only fill in the
#: dependencies of one that a manifest already named.
REQUIREMENTS = "requirements.txt"


def parse_requirements(text: str) -> list:
    """Requirement lines of a requirements.txt, options and comments dropped.

    Only the requirement grammar is handled here, because `Requirement` does the
    rest downstream: markers, extras and direct URLs need no special case. Lines
    starting with a dash are pip options (`-r`, `-c`, `-e`, `--index-url`) and are
    skipped — including `-r`, so an included file is not followed. Every member
    measured declares its qiskit constraint in the file itself.
    """
    requirements = []
    for line in text.replace("\\\n", " ").splitlines():
        line = line.split("#")[0].strip()
        if not line:
            continue
        if line.startswith("-"):
            logger.debug("skipping the pip option %r in a requirements file", line)
            continue
        # a joined continuation leaves double spaces behind
        requirements.append(" ".join(line.split()))
    return requirements


def parse_setup_cfg(text: str) -> dict:
    """Parses a setup.cfg into a plain dict of sections."""
    parser = ConfigParser()
    try:
        parser.read_file(StringIO(text))
    except ConfigParserError as err:
        logger.warning("setup.cfg is not parseable: %s", err)
        return {}
    return {section: dict(parser[section]) for section in parser.sections()}


def parse_setup_py(text: str) -> dict:
    """Statically reads the `setup()` call of a setup.py.

    Returns `{"literals": {...}, "deferred": [...]}`, where `deferred` holds the
    keyword arguments whose value is computed at build time (a variable, a
    function call, an f-string) and so cannot be known without running the file.
    Never executes the module.
    """
    result = {"literals": {}, "deferred": []}
    try:
        tree = ast_parse(text)
    except SyntaxError as err:
        logger.warning("setup.py is not parseable: %s", err)
        return result

    for node in ast_walk(tree):
        if not isinstance(node, Call):
            continue
        func = node.func
        is_setup = (isinstance(func, Name) and func.id == "setup") or (
            isinstance(func, Attribute) and func.attr == "setup"
        )
        if not is_setup:
            continue
        for keyword in node.keywords:
            if keyword.arg is None:  # **kwargs
                continue
            try:
                result["literals"][keyword.arg] = literal_eval(keyword.value)
            except (ValueError, SyntaxError):
                result["deferred"].append(keyword.arg)
        return result  # first setup() call wins
    return result


class PythonData(
    GitHubContentsMixin, QiskitRequirementMixin, JsonSerializable
):  # pylint: disable=too-many-public-methods
    """
    The packaging metadata a Python project declares in its own source tree.

    Most of the public surface is one small read-only property per metadata field,
    which is what takes it past the method limit.
    """

    dict_keys = [
        "package_name",
        "version",
        "license",
        "description",
        "requires_python",
        "requires_qiskit",
        "compatible_with_qiskit_v1",
        "compatible_with_qiskit_v2",
        "highest_supported_qiskit_release_date",
        "highest_supported_qiskit_version",
        "build_backend",
        "path",
        "source",
        "deferred",
    ]

    def __init__(
        self,
        package_name: str = None,
        owner: str = None,
        repo: str = None,
        path: str = None,
        **kwargs,
    ):
        """
        Args:
            package_name: Distribution name, when already known (round-tripping a
                stored section). Otherwise it is discovered by `update_json`.
            owner: GitHub owner, needed to fetch. Not serialized: it lives in the
                member's `[github]` section.
            repo: GitHub repository name. Not serialized, as above.
            path: Directory holding the manifests, when they are not at the repo
                root. Serialized, because it cannot be discovered.
        """
        self._given_package_name = package_name
        self.owner = owner
        self.repo = repo
        self.path = path
        self._kwargs = kwargs or {}
        self._pyproject = None
        self._setup_cfg = None
        self._setup_py = None
        self._requirements = None
        self._all_qiskit_versions = None
        self._requires_qiskit = UNSET

    def __repr__(self):
        return str(self.to_dict())

    def to_dict(self, keys=None) -> dict:
        return super().to_dict(keys=keys or PythonData.dict_keys)

    @classmethod
    def from_github(cls, github_data, path: str = None):
        """Builds an (unfetched) section from a member's `[github]` section."""
        return cls(owner=github_data.owner, repo=github_data.repo, path=path)

    @classmethod
    def from_url(cls, manifest_url):
        """Builds an (unfetched) section from the URL of a packaging manifest, like
        - https://github.com/<owner>/<repo>/blob/<ref>/pyproject.toml
        - https://github.com/<owner>/<repo>/blob/<ref>/<path>/setup.cfg

        This is how a distribution that is not on a registry gets submitted: the URL
        says which repository, and which directory in it, holds the manifests. It is
        the only way to declare `path`, which cannot be discovered.

        Returns None for any other URL, GitHub ones included, so that a link to a
        repository or a release stays in `packages` for something else to claim. The
        `<ref>` is dropped: manifests are read from the default branch.
        """
        if "github.com" not in (manifest_url.hostname or ""):
            return None

        parts = [part for part in manifest_url.path.split("/") if part]
        if len(parts) < 5 or parts[2] != "blob":
            return None

        if parts[-1] not in MANIFESTS:
            raise EcosystemError(
                f"{manifest_url} does not point at one of " f"{', '.join(MANIFESTS)}"
            )

        return cls(owner=parts[0], repo=parts[1], path="/".join(parts[4:-1]) or None)

    @property
    def key(self):
        """The `[python.<key>]` key this section belongs under.

        The distribution name, once it is known. A section built from a URL does not
        know it yet: it is declared inside the repository, not in the URL. The
        repository name stands in until `update_json` reads a manifest, and
        `Member.update_python` re-keys the section then.

        The stand-in carries `path`, because a monorepo can declare several
        distributions and they would otherwise share one key and overwrite each
        other before any of them is fetched.
        """
        if self.package_name:
            return self.package_name
        if not self.repo:
            return None
        stem = f"{self.repo}-{self.path}" if self.path else self.repo
        return canonicalize_name(stem.replace("/", "-"))

    # ---------------------------------------------------------------- fetching

    def update_json(self):
        """
        Fetches the packaging manifests from the default branch of
        `github.com/{self.owner}/{self.repo}`:
          - pyproject.toml
          - setup.cfg
          - setup.py
          - requirements.txt, for the dependencies alone
        """
        if not self.owner or not self.repo:
            raise EcosystemError(
                "PythonData needs owner and repo to fetch; "
                "build it with PythonData.from_github()"
            )
        present = self._request_listing()
        parsers = {
            "pyproject.toml": tomllib.loads,
            "setup.cfg": parse_setup_cfg,
            "setup.py": parse_setup_py,
        }
        fetched = {
            filename: self._request_file(filename, parsers[filename])
            for filename in MANIFESTS
            if filename in present
        }
        self._pyproject = fetched.get("pyproject.toml")
        self._setup_cfg = fetched.get("setup.cfg")
        self._setup_py = fetched.get("setup.py")
        # wrapped in a dict like the listing is, because `request_json` adds its
        # own metadata keys to whatever the parser returns
        requirements = (
            self._request_file(
                REQUIREMENTS, lambda text: {"requirements": parse_requirements(text)}
            )
            if REQUIREMENTS in present
            else None
        )
        self._requirements = (requirements or {}).get("requirements")
        self._requires_qiskit = UNSET

    @property
    def fetched(self):
        """True once `update_json` has found at least one manifest."""
        return any((self._pyproject, self._setup_cfg, self._setup_py))

    # ------------------------------------------------------ raw manifest views

    @property
    def project(self) -> dict:
        """pyproject.toml `[project]`, the authoritative source when present."""
        return (self._pyproject or {}).get("project") or {}

    @property
    def metadata(self) -> dict:
        """setup.cfg `[metadata]`."""
        return (self._setup_cfg or {}).get("metadata") or {}

    @property
    def options(self) -> dict:
        """setup.cfg `[options]`, which is where its dependencies live."""
        return (self._setup_cfg or {}).get("options") or {}

    @property
    def setup_kwargs(self) -> dict:
        """The literal keyword arguments of the `setup()` call."""
        return (self._setup_py or {}).get("literals") or {}

    def _declared(self, project_key, cfg_key=None, setup_key=None):
        """First value declared across the manifests, in precedence order.

        Falls back to the stored value, so a section loaded from a toml file
        keeps working with no network.
        """
        cfg_key = cfg_key or project_key
        setup_key = setup_key or cfg_key
        for source in (
            self.project.get(project_key),
            self.metadata.get(cfg_key),
            self.options.get(cfg_key),
            self.setup_kwargs.get(setup_key),
        ):
            if source:
                return source
        return None

    # ----------------------------------------------------------------- fields

    @property
    def package_name(self):
        """Distribution name, as `pip` would record it."""
        name = (
            self._declared("name")
            or self._given_package_name
            or self._kwargs.get("package_name")
        )
        if not name:
            return None
        try:
            return canonicalize_name(name, validate=True)
        except Exception:  # pylint: disable=broad-except
            logger.warning("%r is not a valid distribution name", name)
            return None

    @property
    def version(self):
        """Declared version. None when the backend computes it at build time."""
        if "version" in self.dynamic:
            return None
        declared = self._declared("version")
        if isinstance(declared, str):
            return declared
        return self._kwargs.get("version")

    @property
    def description(self):
        """One-line summary."""
        return self._declared("description") or self._kwargs.get("description")

    @property
    def requires_python(self):
        """The `python_requires` specifier."""
        return self._declared("requires-python", "python_requires") or self._kwargs.get(
            "requires_python"
        )

    @property
    def build_backend(self):
        """PEP 517 build backend. None when the project declares no build system.

        Absence is meaningful: `pip` then falls back to a synthesized setuptools
        backend, which is the legacy path.
        """
        declared = (self._pyproject or {}).get("build-system", {}).get("build-backend")
        return declared or self._kwargs.get("build_backend")

    @property
    def dynamic(self) -> list:
        """Fields pyproject.toml hands back to the build backend (PEP 621)."""
        return self.project.get("dynamic") or []

    @property
    def deferred(self) -> list:
        """Fields that are declared somewhere but not statically readable.

        The union of PEP 621 `dynamic` and the non-literal `setup()` keyword
        arguments. A checker needs this to tell "no license declared" (a
        finding) from "license computed at build time" (not a finding).
        """
        if not self.fetched:
            return self._kwargs.get("deferred") or []
        deferred = list(self.dynamic) + ((self._setup_py or {}).get("deferred") or [])
        return sorted(set(deferred))

    @property
    def source(self) -> list:
        """Which manifests the values above came from."""
        if not self.fetched:
            return self._kwargs.get("source") or []
        found = {
            "pyproject.toml": self._pyproject,
            "setup.cfg": self._setup_cfg,
            "setup.py": self._setup_py,
        }
        names = [name for name in MANIFESTS if found[name]]
        if self._declared_dependencies()[1] == REQUIREMENTS:
            names.append(REQUIREMENTS)
        return names

    @property
    def license(self):
        """Declared license, normalized to an SPDX id where possible.

        `[project].license` has two incompatible shapes: a PEP 639 SPDX string,
        or the older table with `text` or `file`. A `file` reference names a
        file rather than a license, so it is not a license name and is skipped.
        """
        declared = self.project.get("license")
        if isinstance(declared, dict):
            declared = declared.get("text")
        if not declared:
            declared = self.metadata.get("license") or self.setup_kwargs.get("license")
        if declared and isinstance(declared, str):
            return License(declared)

        for classifier in self._classifiers():
            if classifier.startswith("License :: "):
                parts = [part.strip() for part in classifier.split("::")]
                if len(parts) == 3:
                    # Same trove vocabulary PyPI serves, so normalize it the same way.
                    return License(parts[2], "pypi")

        stored = self._kwargs.get("license")
        if stored:
            return stored if isinstance(stored, License) else License(str(stored))
        return None

    def _classifiers(self) -> list:
        """Trove classifiers, wherever they are declared."""
        declared = self.project.get("classifiers") or self.setup_kwargs.get(
            "classifiers"
        )
        if declared:
            return declared
        # setup.cfg keeps them as an indented multi-line string
        return [
            line.strip()
            for line in (self.metadata.get("classifiers") or "").splitlines()
            if line.strip()
        ]

    @property
    def dependencies(self) -> list:
        """Declared runtime dependencies as PEP 508 strings."""
        return self._declared_dependencies()[0]

    def _declared_dependencies(self):
        """The dependencies, and the name of the file they were declared in.

        The file matters to `source`: a requirements.txt read because the manifest
        deferred its dependencies has to be reported, or the section claims a
        `setup.py` declared something it only pointed at.
        """
        # setup.cfg keeps install_requires as an indented multi-line string
        from_cfg = [
            line.strip()
            for line in (self.options.get("install_requires") or "").splitlines()
            if line.strip()
        ]
        for declared, filename in (
            (self.project.get("dependencies"), "pyproject.toml"),
            (self.setup_kwargs.get("install_requires"), "setup.py"),
            (from_cfg, "setup.cfg"),
            (self._requirements, REQUIREMENTS),
        ):
            if declared:
                return list(declared), filename
        return [], None

    @property
    def requires_qiskit(self):
        """String with the specifier for the "qiskit" dependency.

        None when the project does not depend on Qiskit, and when it defers its
        dependencies to the build backend without a requirements.txt to fall back
        on — `deferred` tells those apart.
        """
        if not self.fetched:
            return self._kwargs.get("requires_qiskit")
        if self._requires_qiskit is not UNSET:
            # The compat properties read this repeatedly, and a miss logs a warning
            return self._requires_qiskit
        self._requires_qiskit = find_requires_qiskit(
            self.dependencies, self.package_name
        )
        return self._requires_qiskit
