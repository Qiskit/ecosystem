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

"""Tests for the per-package pages in docs/pypi/"""

from unittest import TestCase

from ecosystem.docs.pypi_page import PypiPage
from ecosystem.github import GitHubData
from ecosystem.member import Member
from ecosystem.pypi import PyPIData

OWNER = "banana-org"
REPO = "banana-repo"
UUID = "banana00-0000-0000-0000-000000000000"


class PypiPageTestCase(TestCase):
    """A page about one published distribution, rendered from stored values only"""

    @staticmethod
    def package(**kwargs):
        """A distribution as a member file stores it"""
        kwargs.setdefault("version", "1.0.0")
        kwargs.setdefault("last_release_date", "2026-01-15")
        return PyPIData(package_name="banana", **kwargs)

    def page(self, package=None, **kwargs):
        """The page about such a package, belonging to such a member"""
        project = Member(
            name="Banana",
            url=f"https://github.com/{OWNER}/{REPO}",
            uuid=UUID,
            maturity="experimental",
            github=GitHubData(owner=OWNER, repo=REPO),
            **kwargs,
        )
        return PypiPage(package or self.package(), project, "pypi/banana.md")

    def rendered(self, package=None, **kwargs):
        """The whole page, as one string"""
        return "\n".join(self.page(package, **kwargs).generate_all_lines())


class TestThePypiPage(PypiPageTestCase):
    """What a reader who arrived looking for the package needs"""

    def test_the_page_is_titled_after_the_package(self):
        """Not after the project: several packages can share one member file"""
        page = self.rendered()
        self.assertIn("# banana [:material-file-edit-outline:]", page)
        self.assertIn("resources/members/banana_banana00.toml", page)

    def test_the_description_is_the_package_summary(self):
        """The one PyPI shows, which is not necessarily the project description"""
        page = self.rendered(self.package(description="Compiles bananas"))
        self.assertIn("> Compiles bananas", page)

    def test_the_install_line_is_the_point_of_the_page(self):
        """Whatever else is on it, this is what a reader came for"""
        self.assertIn("```bash\npip install banana\n```", self.rendered())

    def test_the_pypi_project_page_is_linked(self):
        """As the stored URL, which is what PyPI itself reported"""
        page = self.rendered(self.package(url="https://pypi.org/project/banana/"))
        self.assertIn(
            ":simple-pypi: [https://pypi.org/project/banana/]"
            "(https://pypi.org/project/banana/)",
            page,
        )

    def test_the_link_is_built_from_the_name_when_none_was_fetched(self):
        """A package that was never fetched still has a page, and a predictable URL"""
        self.assertEqual("https://pypi.org/project/banana/", self.page().pypi_url)

    def test_the_package_card_carries_no_title(self):
        """The page is already about the package, so the card would repeat the name"""
        card = "\n".join(self.page().pypi_card())
        self.assertNotIn("PyPI `banana`", card)
        self.assertEqual("-   ", card.splitlines()[0])

    def test_the_project_card_links_back_to_the_project_page(self):
        """Which is the only way from here to the rest of what the ecosystem knows"""
        card = "\n".join(self.page().project_card())
        self.assertIn(
            ":material-code-tags: **Project** [Banana](../p/banana00.md)", card
        )
        self.assertIn("**Qiskit Ecosystem Member**", card)

    def test_the_front_matter_is_the_status_of_the_project(self):
        """The package has no status of its own; it is as retired as its project is"""
        self.assertIn("icon: material/account-remove", self.rendered(status="Alumni"))
