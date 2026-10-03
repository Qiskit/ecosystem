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

"""Tests for ecosystem/cargo.py, and for the pages built from the section"""

from unittest import TestCase
from unittest.mock import patch

from ecosystem.cargo import CargoData
from ecosystem.crates import CratesData
from ecosystem.docs.cargo_page import CargoPage
from ecosystem.docs.project_page import ProjectPage
from ecosystem.error_handling import EcosystemError
from ecosystem.github import GitHubData
from ecosystem.member import Member

OWNER = "banana-org"
REPO = "banana-rs"

# the shape of `Qiskit/Qiskit-rs`: a crate at the root, a workspace member beside it, and
# every shared field inherited from `[workspace.package]`
ROOT = """
[package]
name = "banana"
version = "0.0.0"
edition.workspace = true
rust-version.workspace = true
license.workspace = true
description = "Rust bindings to libbanana"

[workspace]
members = ["banana-sys"]

[workspace.package]
edition = "2024"
rust-version = "1.85"
license = "Apache-2.0"

[dependencies]
banana-sys = { path = "banana-sys", version = "2.5.1" }
"""

MEMBER = """
[package]
name = "banana-sys"
version = "2.5.1"
edition.workspace = true
license.workspace = true
description = "Raw bindings to libbanana"
"""

# a pyo3 extension module: the compiled core of the project's Python package
EXTENSION = """
[package]
name = "banana_accelerate"
version = "0.1.0"

[lib]
crate-type = ["cdylib"]

[dependencies]
pyo3 = "0.22"
numpy = "0.22"
"""

# a workspace root with no crate of its own, and only a glob to find them by
GLOB_ONLY = """
[workspace]
members = ["crates/*"]
"""


def fake_repository(**manifests):
    """Stands in for the two requests `GitHubContentsMixin` makes.

    `manifests` maps a directory (`""` for the root) to the Cargo.toml it holds; a
    directory that is not there answers with a listing that has no manifest in it.
    """

    def request(url, **kwargs):
        directory = url.split("/contents/")[1]
        if directory.endswith("Cargo.toml"):
            text = manifests[directory[: -len("Cargo.toml")]]
            return kwargs["parser"](text)
        contents = manifests.get(directory)
        entries = [{"name": "Cargo.toml", "type": "file"}] if contents else []
        return {"entries": entries}

    return request


class CargoTestCase(TestCase):
    """A repository read the way `update_cargo` reads one"""

    @staticmethod
    def member(**kwargs):
        """A member whose repository declares its crates in Cargo manifests"""
        return Member(
            name="Banana rs",
            url=f"https://github.com/{OWNER}/{REPO}",
            uuid="banana00-0000-0000-0000-000000000000",
            maturity="experimental",
            github=GitHubData(owner=OWNER, repo=REPO),
            **kwargs,
        )

    def sections(self, member=None, **manifests):
        """The sections such a repository gives such a member"""
        member = member or self.member()
        with patch(
            "ecosystem.github_contents.request_json",
            side_effect=fake_repository(**manifests),
        ):
            member.update_cargo()
        return member.cargo


class TestWhichManifestsGetASection(CargoTestCase):
    """The scope rule, which is the whole of the design"""

    def test_the_root_crate_and_its_workspace_members(self):
        """`Qiskit/Qiskit-rs` declares one of each, and both are crates"""
        sections = self.sections(**{"": ROOT, "banana-sys/": MEMBER})
        self.assertEqual(["banana", "banana-sys"], sorted(sections))
        self.assertEqual("banana-sys", sections["banana-sys"].path)
        self.assertIsNone(sections["banana"].path)

    def test_a_pyo3_extension_module_is_not_a_crate(self):
        """It is the Python package's compiled core, and that is already described"""
        self.assertEqual({}, self.sections(**{"": EXTENSION}))

    def test_a_crate_that_also_builds_an_rlib_stays(self):
        """Something can depend on it as a crate, pyo3 bindings or not"""
        manifest = EXTENSION.replace(
            'crate-type = ["cdylib"]', 'crate-type = ["cdylib", "rlib"]'
        )
        self.assertEqual(["banana_accelerate"], list(self.sections(**{"": manifest})))

    def test_a_published_crate_is_left_to_the_registry_section(self):
        """`[crates.*]` says more about it than a manifest can"""
        member = self.member(crates={"banana": CratesData(package_name="banana")})
        sections = self.sections(member, **{"": ROOT, "banana-sys/": MEMBER})
        self.assertEqual(["banana-sys"], list(sections))

    def test_a_workspace_with_only_a_glob_yields_nothing(self):
        """Expanding it would need a listing per pattern, which is a later step"""
        self.assertEqual({}, self.sections(**{"": GLOB_ONLY}))

    def test_a_repository_with_no_manifest_declares_no_crate(self):
        """Which is most members"""
        self.assertEqual({}, self.sections())

    def test_a_section_that_is_gone_from_the_manifests_is_dropped(self):
        """The manifests are the source of truth, so a stale section says nothing"""
        member = self.member(cargo={"banana": CargoData(package_name="banana")})
        self.assertEqual({}, self.sections(member))

    def test_a_member_without_a_github_section_is_skipped(self):
        """There is nothing to read without a repository to read it from"""
        member = Member(name="Banana rs", url=f"https://github.com/{OWNER}/{REPO}")
        member.update_cargo()
        self.assertEqual({}, member.cargo)


class TestWhatTheSectionSays(CargoTestCase):
    """The fields, and the workspace inheritance they come through"""

    def section(self, name="banana"):
        """One section of such a repository"""
        return self.sections(**{"": ROOT, "banana-sys/": MEMBER})[name]

    def test_the_fields_the_manifest_declares(self):
        """Including the `crate_type` the scope rule turns on"""
        self.assertEqual(
            {
                "package_name": "banana",
                "version": "0.0.0",
                "license": "Apache-2.0",
                "description": "Rust bindings to libbanana",
                "rust_version": "1.85",
                "edition": "2024",
                "crate_type": ["rlib"],
            },
            self.section().to_dict(),
        )

    def test_an_inherited_field_is_resolved_against_the_workspace(self):
        """`license.workspace = true` in a member crate means the root's license"""
        member = self.section("banana-sys")
        self.assertEqual("Apache-2.0", str(member.license))
        self.assertEqual("2024", member.edition)

    def test_a_field_the_workspace_does_not_declare_either_is_nothing(self):
        """An inherited field is not a promise that anybody declared it"""
        root = ROOT.replace('rust-version = "1.85"\n', "")
        self.assertIsNone(self.sections(**{"": root})["banana"].rust_version)

    def test_the_manifest_path_is_where_the_crate_was_read(self):
        """Which is what the page and the table link"""
        self.assertEqual("Cargo.toml", self.section().manifest_path)
        self.assertEqual(
            "banana-sys/Cargo.toml", self.section("banana-sys").manifest_path
        )

    def test_a_crate_with_no_lib_table_builds_a_library(self):
        """Which is what Cargo does with a manifest that says nothing"""
        self.assertEqual(["rlib"], self.section().crate_type)

    def test_fetching_needs_owner_and_repo(self):
        """A stored section is readable, but it cannot be refreshed on its own"""
        with self.assertRaises(EcosystemError):
            CargoData(package_name="banana").update_json()


class TestTheStoredSection(CargoTestCase):
    """What a member file carries, read back without the network"""

    @staticmethod
    def stored(**section):
        """A CargoData as `from_dict` builds one out of a member file"""
        return CargoData.from_dict({"package_name": "banana"} | section)

    def test_stored_values_are_returned_unfetched(self):
        """Reading a member file must not reach GitHub"""
        crate = self.stored(
            version="0.0.0",
            license="Apache-2.0",
            crate_type=["rlib"],
            path="banana-sys",
        )
        self.assertEqual("0.0.0", crate.version)
        self.assertEqual("Apache-2.0", str(crate.license))
        self.assertEqual(["rlib"], crate.crate_type)
        self.assertEqual("banana-sys/Cargo.toml", crate.manifest_path)

    def test_what_is_not_stored_reads_as_nothing(self):
        """Most manifests declare no MSRV, which is not an error"""
        self.assertIsNone(self.stored().rust_version)
        self.assertIsNone(self.stored().edition)
        self.assertIsNone(self.stored().license)
        self.assertIsNone(self.stored().description)

    def test_a_license_given_as_a_string_is_wrapped(self):
        """A section built in code, rather than read back through `from_dict`"""
        self.assertEqual(
            "MIT", str(CargoData(package_name="banana", license="MIT").license)
        )

    def test_an_inherited_field_nobody_declared_is_nothing(self):
        """`version = { workspace = false }` is not an inheritance, so it says nothing"""
        crate = CargoData(package_name="banana")
        crate._manifest = {  # pylint: disable=protected-access
            "package": {"name": "banana", "version": {"workspace": False}}
        }
        self.assertIsNone(crate.version)

    def test_the_section_prints_as_what_it_stores(self):
        """`repr` is what the update log shows for it"""
        self.assertIn("banana", repr(self.stored(version="0.0.0")))

    def test_a_crate_fetched_on_its_own_is_its_own_workspace(self):
        """`update_json` outside `candidates` has no root manifest to resolve against"""
        crate = CargoData(package_name="banana", owner=OWNER, repo=REPO)
        with patch(
            "ecosystem.github_contents.request_json",
            side_effect=fake_repository(**{"": ROOT}),
        ):
            crate.update_json()
        self.assertEqual("2024", crate.edition)

    def test_the_sections_round_trip_through_from_dict(self):
        """A member file is read back into the same sections it was written from"""
        member = self.member()
        self.sections(member, **{"": ROOT, "banana-sys/": MEMBER})
        read_back = Member.from_dict(member.to_dict())
        self.assertEqual(
            {name: crate.to_dict() for name, crate in member.cargo.items()},
            {name: crate.to_dict() for name, crate in read_back.cargo.items()},
        )


class TestTheCargoPage(CargoTestCase):
    """The page about one declared crate, and the row on the project page"""

    def setUp(self):
        super().setUp()
        self.project = self.member()
        self.sections(self.project, **{"": ROOT, "banana-sys/": MEMBER})

    def page(self, name="banana-sys"):
        """The page about that crate"""
        return CargoPage(
            self.project.cargo[name], self.project, f"cargo-source/{name}.md"
        )

    def test_without_a_repository_there_is_no_dependency_line(self):
        """Owner and repo live in `[github]`; without it there is no URL to guess"""
        crate = self.project.cargo["banana-sys"]
        page = CargoPage(crate, Member(name="Banana rs", url="x"), "cargo-source/x.md")
        self.assertIsNone(page.card.manifest_url)
        lines = "\n".join(page.description() + page.cargo_card())
        self.assertNotIn("cargo add", lines)
        self.assertIn("**Declared in** `banana-sys/Cargo.toml`", lines)

    def test_the_page_says_it_is_not_published(self):
        """The whole point of the section, so it is stated and not implied"""
        self.assertIn(
            "Not published to crates.io", "\n".join(self.page().description())
        )

    def test_the_manifest_link_includes_the_subdirectory(self):
        """A workspace member is not at the repository root"""
        self.assertEqual(
            f"https://github.com/{OWNER}/{REPO}/blob/HEAD/banana-sys/Cargo.toml",
            self.page().card.manifest_url,
        )

    def test_the_dependency_command_is_a_block_with_a_copy_button(self):
        """A fenced block is the only thing the theme puts a copy button on"""
        self.assertIn(
            "```bash\ncargo add --git "
            f"https://github.com/{OWNER}/{REPO} banana-sys\n```",
            "\n".join(self.page().description()),
        )

    def test_the_page_holds_the_dependency_line_and_both_cards(self):
        """A git dependency is the only way to reach a crate like this"""
        lines = "\n".join(self.page().generate_all_lines())
        self.assertIn("# banana-sys ", lines)
        self.assertIn(
            f"cargo add --git https://github.com/{OWNER}/{REPO} banana-sys", lines
        )
        self.assertIn("**Project** [Banana rs](../p/", lines)

    def test_the_card_names_the_rust_the_crate_needs(self):
        """The root crate declares one; its workspace member inherits only some fields"""
        lines = "\n".join(self.page("banana").generate_all_lines())
        self.assertIn("**Requires Rust** 1.85", lines)
        self.assertIn("**Edition** 2024", lines)

    def test_the_card_says_what_the_crate_builds(self):
        """`rlib` is what makes it a crate rather than an extension module"""
        self.assertIn("**Builds** `rlib`", "\n".join(self.page().generate_all_lines()))

    def test_the_project_page_row_links_to_the_page(self):
        """And carries the dependency line as its tooltip"""
        section = "\n".join(ProjectPage(self.project, "p/banana00.md").packages())
        self.assertIn(
            "| cargo-installable repo | Version | Rust | Edition | Declared in |",
            section,
        )
        self.assertIn(
            '[`banana-sys`](../cargo-source/banana-sys.md "cargo add --git '
            f'https://github.com/{OWNER}/{REPO} banana-sys")',
            section,
        )
        self.assertIn("banana-sys/Cargo.toml", section)
