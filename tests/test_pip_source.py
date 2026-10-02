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

"""Tests for the pip-source card and page, which render a `[python.<name>]` section."""

import tomllib
from datetime import date
from unittest import TestCase
from unittest.mock import patch

from ecosystem.docs.card import PipSourcePackageCard
from ecosystem.docs.pip_source_page import PipSourcePage
from ecosystem.docs.project_page import ProjectPage
from ecosystem.github import GitHubData
from ecosystem.member import Member
from ecosystem.python import PythonData

OWNER = "banana-org"
REPO = "banana-compiler"

PYPROJECT = """
[build-system]
requires = ["setuptools>=61"]
build-backend = "setuptools.build_meta"

[project]
name = "Banana_Compiler"
version = "0.3.1"
description = "Compiles bananas"
requires-python = ">=3.9"
dependencies = ["qiskit>=1.2,<3"]
dynamic = ["readme"]
"""

QISKIT_VERSIONS = {
    "1.0.0": {"upload_at": date(2024, 2, 15)},
    "2.1.0": {"upload_at": date(2026, 6, 10)},
}


class PipSourceTestCase(TestCase):
    """Base holding the fixtures the card and the page share."""

    def setUp(self):
        super().setUp()
        patcher = patch.object(
            PythonData, "all_qiskit_versions", return_value=QISKIT_VERSIONS
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    @staticmethod
    def package(path=None):
        """A PythonData as if `update_json` had read PYPROJECT."""
        data = PythonData(owner=OWNER, repo=REPO, path=path)
        data._pyproject = tomllib.loads(PYPROJECT)  # pylint: disable=protected-access
        return data

    @staticmethod
    def project(**kwargs):
        """A member with the `[github]` section the install line is built from."""
        return Member(
            name="Banana Compiler",
            url=f"https://github.com/{OWNER}/{REPO}",
            uuid="banana-uuid-0000-0000-000000000000",
            maturity="experimental",
            github=GitHubData(owner=OWNER, repo=REPO),
            **kwargs,
        )


class TestPipSourcePackageCard(PipSourceTestCase):
    """The card body, which is all declared metadata and no release information."""

    def card(self, path=None, project=True):
        """The card for `package(path)`, with or without a project behind it."""
        return PipSourcePackageCard.from_python_data(
            self.package(path=path), self.project() if project else None
        )

    def test_the_install_line_points_at_the_repository(self):
        """Nothing is published, so the only way in is the git URL."""
        self.assertEqual(
            f"git+https://github.com/{OWNER}/{REPO}", self.card().pip_target
        )

    def test_a_subdirectory_is_quoted(self):
        """`#` starts a comment in a shell, so a fragment has to be quoted."""
        self.assertEqual(
            f'"git+https://github.com/{OWNER}/{REPO}#subdirectory=packages/compiler"',
            self.card(path="packages/compiler/").pip_target,
        )

    def test_no_install_line_without_a_project(self):
        """Owner and repo live in `[github]`, so without it there is no URL to give."""
        self.assertIsNone(self.card(project=False).pip_target)
        self.assertFalse(
            any("pip install" in line for line in self.card(project=False).body())
        )

    def test_the_body_reports_what_the_manifests_declare(self):
        """The version, the Python requirement, the manifests and the backend."""
        body = "\n".join(self.card().body())
        self.assertIn("**declared version** 0.3.1", body)
        self.assertIn("**requires Python** >=3.9", body)
        self.assertIn("**declared in** `pyproject.toml`", body)
        self.assertIn("**build backend** `setuptools.build_meta`", body)

    def test_dynamic_fields_are_named_as_deferred(self):
        """A field the backend computes is reported as unknown, not as missing."""
        self.assertIn(
            "**computed at build time** `readme`", "\n".join(self.card().body())
        )

    def test_the_body_carries_the_qiskit_compatibility_table(self):
        """The same table the PyPI card shows, computed from the declared requirement."""
        body = "\n".join(self.card().body())
        self.assertIn("<3,>=1.2", body)
        self.assertIn("2.1.0", body)

    def test_every_bullet_is_its_own_paragraph(self):
        """Consecutive lines would collapse into one, so bullets are blank-separated."""
        body = self.card().body()
        # the compatibility table is shared with the PyPI card and spaces itself out
        end = next(i for i, line in enumerate(body) if "Qiskit Compatibility" in line)
        declared = body[:end]
        bullets = [index for index, line in enumerate(declared) if line.startswith(":")]
        self.assertEqual(6, len(bullets))
        for index in bullets:
            with self.subTest(bullet=declared[index]):
                self.assertEqual("", declared[index + 1])


class TestPipSourcePage(PipSourceTestCase):
    """The page assembled around the card."""

    def page(self, path=None, **kwargs):
        """The page for `package(path)`."""
        package = self.package(path=path)
        return PipSourcePage(
            package, self.project(**kwargs), f"pip-source/{package.package_name}.md"
        )

    def test_the_manifest_link_goes_to_the_file_it_read(self):
        """The branch is not stored, so the link goes through HEAD."""
        self.assertEqual(
            f"https://github.com/{OWNER}/{REPO}/blob/HEAD/pyproject.toml",
            self.page().manifest_url,
        )

    def test_the_manifest_link_includes_the_subdirectory(self):
        """In a monorepo the manifest is not at the repository root."""
        self.assertEqual(
            f"https://github.com/{OWNER}/{REPO}/blob/HEAD/packages/compiler/pyproject.toml",
            self.page(path="packages/compiler").manifest_url,
        )

    def test_the_page_says_it_is_not_published(self):
        """The whole point of the page, so it is stated and not just implied."""
        self.assertIn(
            "Not published to a package registry", "\n".join(self.page().description())
        )

    def test_the_page_holds_the_title_and_both_cards(self):
        """The distribution name titles it; the project card links back to the member."""
        lines = "\n".join(self.page().generate_all_lines())
        self.assertIn("# banana-compiler ", lines)
        self.assertIn("pip install", lines)
        self.assertIn("**Project** [Banana Compiler](../p/", lines)


class TestProjectPagePackages(PipSourceTestCase):
    """The `[python.*]` sections show up on the member's own page too, next to the
    `[pypi.*]` ones, so a project is not read as having no packages at all."""

    def packages_section(self, **kwargs):
        """The Packages section of the project page, as one string."""
        project = self.project(**kwargs)
        return "\n".join(ProjectPage(project, "p/banana.md").packages())

    def test_the_distribution_is_a_row_of_the_packages_section(self):
        """What the manifests declare, with the install command as a tooltip."""
        section = self.packages_section(python={"banana-compiler": self.package()})
        self.assertIn("### :material-package-variant: Packages", section)
        self.assertIn(
            "| pip-installable repo | Version | Requires Python | Declared in |",
            section,
        )
        self.assertIn("[`banana-compiler`](../pip-source/banana-compiler.md ", section)
        self.assertIn(
            f'(../pip-source/banana-compiler.md "pip install '
            f'git+https://github.com/{OWNER}/{REPO}")',
            section,
        )
        self.assertIn("| 0.3.1 | >=3.9 | `pyproject.toml` |", section)

    def test_the_compatibility_is_left_to_the_requirements_table(self):
        """The same four values for every distribution, so they are collected there."""
        section = self.packages_section(python={"banana-compiler": self.package()})
        self.assertNotIn("Qiskit Compatibility", section)

    def test_one_row_per_declared_distribution(self):
        """A monorepo declares several, each with its own install target."""
        section = self.packages_section(
            python={
                "banana-compiler": self.package(),
                "banana-vision": self.package(path="packages/vision"),
            }
        )
        self.assertEqual(2, section.count("(../pip-source/"))
        self.assertIn("#subdirectory=packages/vision", section)

    def test_a_deferred_value_says_why_it_is_missing(self):
        """A field the backend computes is reported as unknown, not as missing."""
        # a stored section, which is how a deferred field comes back: named, not valued
        package = PythonData(
            package_name="banana-compiler",
            requires_python=">=3.9",
            source=["pyproject.toml"],
            deferred=["version"],
        )
        section = self.packages_section(python={"banana-compiler": package})
        self.assertIn('*&mdash;*{ title="computed at build time" }', section)

    def test_a_value_the_manifests_never_mention_leaves_its_column_out(self):
        """Missing and computed-at-build-time are not the same thing"""
        section = self.packages_section(
            python={"banana-compiler": PythonData(package_name="banana-compiler")}
        )
        self.assertNotIn("Requires Python", section)

    def test_no_packages_section_without_any_package(self):
        """An empty section would read as a project with nothing to install."""
        self.assertEqual("", self.packages_section())
