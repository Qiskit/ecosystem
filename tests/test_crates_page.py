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

"""Tests for the per-crate pages in docs/crates/"""

from unittest import TestCase

from tests.common import named
from ecosystem.crates import CratesData
from ecosystem.docs.card import CratesPackageCard
from ecosystem.docs.crates_page import CratesPage
from ecosystem.docs.project_page import ProjectPage
from ecosystem.github import GitHubData
from ecosystem.member import Member

OWNER = "banana-org"
REPO = "banana-repo"
UUID = "banana00-0000-0000-0000-000000000000"


class CratesPageTestCase(TestCase):
    """A page about one published crate, rendered from stored values only"""

    @staticmethod
    def crate(**kwargs):
        """A crate as a member file stores it"""
        kwargs.setdefault("version", "0.7.0")
        kwargs.setdefault("last_release_date", "2024-10-30")
        kwargs.setdefault("description", "Parses bananas")
        kwargs.setdefault("license", "Apache-2.0")
        kwargs.setdefault("rust_version", "1.70")
        kwargs.setdefault("edition", "2021")
        kwargs.setdefault("total_downloads", 939802)
        kwargs.setdefault("last_90_days_downloads", 166899)
        kwargs.setdefault("maintainers", ["https://github.com/banana"])
        return CratesData.from_dict({"package_name": "banana_parser"} | kwargs)

    def project(self, **kwargs):
        """The member that publishes it"""
        kwargs.setdefault("crates", [self.crate()])
        return Member(
            name="Banana Parser",
            url=f"https://github.com/{OWNER}/{REPO}",
            uuid=UUID,
            maturity="experimental",
            github=GitHubData(owner=OWNER, repo=REPO),
            **kwargs,
        )

    def page(self, crate=None, **kwargs):
        """The page about that crate"""
        project = self.project(**kwargs)
        crate = crate or named(project.crates, "banana_parser")
        return CratesPage(crate, project, "crates/banana_parser.md")

    def rendered(self, crate=None, **kwargs):
        """The whole page, as one string"""
        return "\n".join(self.page(crate, **kwargs).generate_all_lines())


class TestTheCratesPage(CratesPageTestCase):
    """What a reader who arrived looking for the crate needs"""

    def test_the_page_is_titled_after_the_crate(self):
        """Not after the project: a member can publish a workspace full of them"""
        self.assertIn("# banana_parser [:material-file-edit-outline:]", self.rendered())

    def test_the_page_says_how_to_depend_on_it(self):
        """Which is the first thing a reader of a crate page wants"""
        page = self.rendered()
        self.assertIn("```bash\ncargo add banana_parser\n```", page)
        self.assertIn("https://crates.io/crates/banana_parser", page)

    def test_the_description_is_quoted(self):
        """It is the crate's own summary, so it is rendered as a block quote"""
        self.assertIn("> Parses bananas", self.rendered())

    def test_the_card_carries_the_release_and_the_downloads(self):
        """The numbers the project page shows as a row, with their units spelled out"""
        page = self.rendered()
        self.assertIn(
            "**Current release** [0.7.0](https://crates.io/crates/banana_parser/0.7.0 "
            '"Released: 2024-10-30")',
            page,
        )
        self.assertIn("**All time** 939,802 **Last 90 days** 166,899", page)

    def test_the_card_carries_the_rust_version_the_license_and_the_owners(self):
        """Everything stored about the crate itself, rather than about the project"""
        page = self.rendered()
        self.assertIn("**Requires Rust** 1.70 **Edition** 2021", page)
        self.assertIn("**License** Apache-2.0", page)
        self.assertIn("**Owners** [banana](https://github.com/banana)", page)

    def test_the_page_links_back_to_the_project(self):
        """A crate page is a way into the member file, which is where edits go"""
        page = self.rendered()
        self.assertIn(f"**Project** [Banana Parser](../p/{UUID[:8]}.md)", page)
        self.assertIn("members/bananapars_banana00.toml", page)

    def test_a_crate_with_nothing_but_a_name_still_renders(self):
        """A section can be stored before anything has been read"""
        page = self.rendered(crate=CratesData(package_name="banana_parser"))
        self.assertIn("# banana_parser ", page)
        self.assertNotIn("current release", page)

    def test_a_crate_with_no_release_links_the_crate_itself(self):
        """There is no version page to point the card at before the first release"""
        page = self.rendered(
            crate=CratesData(package_name="banana_parser", total_downloads=7)
        )
        self.assertIn("**All time** 7", page)
        self.assertNotIn("current release", page)
        crate = CratesData(package_name="banana_parser")
        card = CratesPackageCard.from_crates_data(crate)
        self.assertEqual(crate.url, card.version_url)

    def test_the_project_page_row_links_to_the_page(self):
        """Which is what makes the crate page reachable"""
        section = "\n".join(ProjectPage(self.project(), "p/banana00.md").packages())
        self.assertIn("[`banana_parser`](../crates/banana_parser.md)", section)
