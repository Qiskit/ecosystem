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

"""Crates a repository declares in a `Cargo.toml` without publishing them.

The Rust counterpart of `[python.<name>]`: `[crates.<name>]` is what crates.io says about
a published crate, and this is what the source tree says about one nobody can download.
`Qiskit/Qiskit-rs` is the case it is for, with `qiskit` and the `qiskit-sys` bindings to
`libqiskit` declared and neither published.

A crate like that is not unusable, it is just not installable from a registry: a project
depends on it with a git dependency, which is also why it can never itself be published
(crates.io rejects a crate with one).

Two kinds of `Cargo.toml` are deliberately left out, both measured across the corpus:

- **A pyo3 extension module**, which is `crate-type = ["cdylib"]` and depends on `pyo3`.
  That is the compiled core of the project's *Python* package (`ffsim`,
  `pauli_prop_accelerate`, `_internal-r` and `qiskit_addon_dice_solver_accelerate` are all
  this shape, as is `qiskit-pyext` in Qiskit itself), so the thing to install is the
  distribution `[pypi.*]`/`[python.*]` already describes. A crate that also builds an
  `rlib` or a `staticlib` stays in: something can depend on it as a crate.
- **A crate the project publishes**, which `[crates.<name>]` describes already, the way
  `update_python` leaves a published distribution to `[pypi.<name>]`.

Workspace members are read when `[workspace] members` names them outright. A glob
(`members = ["crates/*"]`) is not expanded, so the two members whose root manifest declares
no package at all get no section for now.
"""

import tomllib

from .serializable import JsonSerializable
from .license import License
from .error_handling import EcosystemError
from .github_contents import GitHubContentsMixin

#: The manifest, which is the one filename Cargo accepts
MANIFEST = "Cargo.toml"

#: What a crate builds when its manifest says nothing: a Rust library
DEFAULT_CRATE_TYPE = ["rlib"]


class CargoData(GitHubContentsMixin, JsonSerializable):
    """One crate a repository declares, as its `Cargo.toml` declares it."""

    dict_keys = [
        "package_name",
        "version",
        "license",
        "description",
        "rust_version",
        "edition",
        "crate_type",
        "path",
    ]

    def __init__(
        self,
        package_name: str = None,
        owner: str = None,
        repo: str = None,
        path: str = None,
        workspace: dict = None,
        **kwargs,
    ):
        """
        Args:
            package_name: Crate name, when already known (round-tripping a stored
                section). Otherwise it is read from the manifest.
            owner: GitHub owner, needed to fetch. Not serialized: it lives in the
                member's `[github]` section.
            repo: GitHub repository name. Not serialized, as above.
            path: Directory holding the manifest, for a workspace member. Serialized,
                because it cannot be discovered from the crate name.
            workspace: The parsed root manifest, which is what the fields a crate
                inherits with `field.workspace = true` are resolved against. Not
                serialized: it is somebody else's manifest.
        """
        self._given_package_name = package_name
        self.owner = owner
        self.repo = repo
        self.path = path
        self._workspace = workspace
        self._kwargs = kwargs or {}
        self._manifest = None

    def __repr__(self):
        return str(self.to_dict())

    def to_dict(self, keys=None) -> dict:
        return super().to_dict(keys=keys or CargoData.dict_keys)

    @classmethod
    def from_dict(cls, dictionary: dict):
        """A stored section, with the license as the class that knows its equivalences"""
        if dictionary.get("license") is not None:
            dictionary["license"] = License(dictionary["license"], where="cargo")
        return cls(**dictionary)

    @classmethod
    def from_github(cls, github_data):
        """Builds a probe from a member's `[github]` section, to call `candidates` on"""
        return cls(owner=github_data.owner, repo=github_data.repo)

    def candidates(self):
        """The crates the repository declares, as sections that have not been read yet.

        One request, the root manifest. A repository without one declares no crate, and a
        workspace root that declares no package of its own contributes only its members.
        """
        root = self._request_manifest()
        if root is None:
            return []
        sections = []
        if (root.get("package") or {}).get("name"):
            sections.append(self._member(path=None, workspace=root))
        for member in (root.get("workspace") or {}).get("members") or []:
            # a glob would need a listing per pattern, and the two repositories that use
            # one declare no package at the root either, so there is nothing to anchor
            if any(wildcard in member for wildcard in "*?["):
                continue
            sections.append(self._member(path=member, workspace=root))
        return sections

    def _member(self, path, workspace):
        """One crate of this repository, sharing the workspace the fields resolve against"""
        return type(self)(
            owner=self.owner, repo=self.repo, path=path, workspace=workspace
        )

    def _request_manifest(self):
        """The parsed `Cargo.toml` of this crate's directory, or None if there is none.

        Listing the directory first costs one request but keeps a repository without a
        manifest from logging a failed fetch, which is what `GitHubContentsMixin` is for.
        """
        if MANIFEST not in self._request_listing():
            return None
        fetched = self._request_file(
            MANIFEST, lambda text: {"manifest": tomllib.loads(text)}
        )
        return (fetched or {}).get("manifest")

    def update_json(self):
        """Fetches this crate's manifest from the default branch"""
        if not self.owner or not self.repo:
            raise EcosystemError(
                "CargoData needs owner and repo to fetch; "
                "build it with CargoData.from_github()"
            )
        self._manifest = self._request_manifest()
        if self._workspace is None:
            self._workspace = self._manifest

    @property
    def fetched(self):
        """True once `update_json` has read the manifest"""
        return self._manifest is not None

    def _declared(self, field):
        """A `[package]` field, resolved through the workspace when it is inherited.

        `edition.workspace = true` means "whatever `[workspace.package]` says", which is
        how `Qiskit/Qiskit-rs` writes every field its two crates share.
        """
        value = ((self._manifest or {}).get("package") or {}).get(field)
        if isinstance(value, dict):
            if not value.get("workspace"):
                return None
            value = (
                ((self._workspace or {}).get("workspace") or {})
                .get("package", {})
                .get(field)
            )
        return value

    @property
    def package_name(self):
        """The crate name, which is what the section is keyed by"""
        return (
            self._declared("name")
            or self._given_package_name
            or self._kwargs.get("package_name")
        )

    @property
    def version(self):
        """The version the manifest declares, which no registry has to agree with"""
        return self._declared("version") or self._kwargs.get("version")

    @property
    def description(self):
        """What the crate says it is"""
        return self._declared("description") or self._kwargs.get("description")

    @property
    def license(self):
        """Crate license, as the SPDX expression the manifest declares"""
        declared = self._declared("license")
        if declared:
            return License(declared, "cargo")
        stored = self._kwargs.get("license")
        if stored is None or isinstance(stored, License):
            return stored
        return License(stored, "cargo")

    @property
    def rust_version(self):
        """The oldest Rust the crate supports, when it declares one"""
        return self._declared("rust-version") or self._kwargs.get("rust_version")

    @property
    def edition(self):
        """The Rust edition the crate is written in"""
        return self._declared("edition") or self._kwargs.get("edition")

    @property
    def crate_type(self):
        """What the crate builds. A manifest that says nothing builds a Rust library."""
        if not self._manifest:
            return self._kwargs.get("crate_type")
        declared = (self._manifest.get("lib") or {}).get("crate-type")
        return list(declared) if declared else list(DEFAULT_CRATE_TYPE)

    @property
    def dependencies(self):
        """The crate names the manifest depends on, which is what pyo3 is spotted in"""
        return list((self._manifest or {}).get("dependencies") or {})

    @property
    def is_python_extension(self):
        """Whether this manifest is a Python extension module rather than a crate.

        `cdylib` and nothing else means the only artifact is a shared library that Python
        loads, and a `pyo3` dependency is what makes it a Python one. Either alone is not
        enough: a crate can offer a `cdylib` for C beside its `rlib`, and a crate can use
        `pyo3` to expose bindings while still being a library in its own right.
        """
        return self.crate_type == ["cdylib"] and "pyo3" in self.dependencies

    @property
    def manifest_path(self):
        """Where the manifest sits in the repository, for a link to it"""
        directory = f"{self.path.strip('/')}/" if self.path else ""
        return f"{directory}{MANIFEST}"
