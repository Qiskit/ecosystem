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

"""Tests for the project pages in docs/p/, and the cards they are built from."""

from datetime import timedelta
from unittest import TestCase
from unittest.mock import patch

from mkdocs_gen_files.editor import FilesEditor

from ecosystem.badge import BadgeData
from ecosystem.check import CheckData
from ecosystem.docs.project_page import ProjectPage
from ecosystem.github import GitHubData
from ecosystem.julia import JuliaData
from ecosystem.member import Member
from ecosystem.pypi import PyPIData
from ecosystem.request import URL

OWNER = "banana-org"
REPO = "banana-repo"
UUID = "banana00-0000-0000-0000-000000000000"


def banana_on_pypi():
    """A published distribution, as a member file stores one"""
    return PyPIData(
        package_name="banana",
        version="1.0.0",
        url="https://pypi.org/project/banana/",
        last_release_date="2026-01-15",
        last_month_downloads=1234,
        last_180_days_downloads=56789,
        requires_qiskit=">=1.4,<3",
        compatible_with_qiskit_v1=True,
        compatible_with_qiskit_v2=True,
        highest_supported_qiskit_version="2.1.0",
        highest_supported_qiskit_release_date="2026-06-10",
    )


class ProjectPageTestCase(TestCase):
    """A page rendered from a stored member, the way the documentation build does.

    Everything these build carries stored values only, so nothing here reaches the
    network and nothing is written to disk.
    """

    @staticmethod
    def project(**kwargs):
        """A member with the fields every page needs, plus whatever the test adds"""
        kwargs.setdefault("github", GitHubData(owner=OWNER, repo=REPO))
        kwargs.setdefault("maturity", "experimental")
        return Member(
            name="Banana",
            url=f"https://github.com/{OWNER}/{REPO}",
            uuid=UUID,
            **kwargs,
        )

    def page(self, **kwargs):
        """The page object for such a member"""
        return ProjectPage(self.project(**kwargs), "p/banana00.md")

    def rendered(self, **kwargs):
        """The whole page, as one string"""
        return "\n".join(self.page(**kwargs).generate_all_lines())

    @staticmethod
    def checkup(id_, since=0, **kwargs):
        """A failing check up that started `since` days ago"""
        return CheckData(
            id_, since=str(CheckData.today - timedelta(days=since)), **kwargs
        )


class TestTheWholePage(ProjectPageTestCase):
    """What `generate_all_lines` puts together, in the order it does"""

    def test_the_sections_are_in_their_order(self):
        """The reader meets the project before its packages and its check ups"""
        page = self.rendered(
            description="Compiles bananas",
            badge=BadgeData(url="https://bit.ly/banana", style="flat"),
            pypi={"banana": banana_on_pypi()},
        )
        headings = [
            "# Banana [:material-file-edit-outline:]",
            "Compiles bananas",
            "### :material-web: URLs",
            "### :simple-shieldsdotio: Badge",
            "### :material-list-status: Checkups",
            "### :material-package-variant: Packages",
        ]
        found = [page.index(heading) for heading in headings]
        self.assertEqual(sorted(found), found)

    def test_a_bare_member_renders_without_the_optional_sections(self):
        """Most members have no badge, no packages and nothing to describe"""
        page = self.rendered()
        self.assertNotIn("Badge", page)
        self.assertNotIn("Packages", page)
        self.assertIn(":material-check-all: All good", page)

    def test_the_description_is_quoted(self):
        """It is somebody else's prose, so it is rendered as a block quote"""
        self.assertEqual(
            [">", "Compiles bananas"],
            self.page(description="Compiles bananas").description(),
        )
        self.assertEqual([], self.page().description())

    def test_the_title_links_to_the_member_file(self):
        """The pencil beside the name is how a maintainer finds what to edit"""
        self.assertIn(
            "(https://github.com/Qiskit/ecosystem/edit/main/resources/"
            "members/banana_banana00.toml)",
            self.page().title()[0],
        )

    def test_the_title_can_be_something_other_than_the_name(self):
        """The PyPI pages reuse it for a package name"""
        self.assertIn("# banana ", self.page().title("banana")[0])

    def test_the_page_is_written_where_the_filename_says(self):
        """And the edit link points at the member file, not at the generated Markdown"""
        # mkdocs_gen_files forwards every call to the editor of the running build,
        # so that editor is what there is to stand in for outside one
        with patch.object(FilesEditor, "current") as editor:
            self.page().write_page()
        editor.return_value.open.assert_called_once_with("p/banana00.md", "w")
        editor.return_value.set_edit_path.assert_called_once_with(
            "p/banana00.md", "resources/members/banana00.toml"
        )


class TestTheFrontMatter(ProjectPageTestCase):
    """The icon beside the page in the navigation, which is the status"""

    def assert_icon(self, icon, **kwargs):
        """The front matter of such a member asks for `icon`"""
        self.assertEqual(
            ["---", f"icon: {icon}", "---"], self.page(**kwargs).front_matter()
        )

    def test_every_status_has_its_own_icon(self):
        """They are the same icons the summary page lists the projects with"""
        self.assert_icon("simple/qiskit", status="Qiskit Project")
        self.assert_icon("material/account-remove", status="Alumni")
        self.assert_icon("material/account-alert", status="Under review")
        self.assert_icon("material/heart-broken", status="Unmaintained")
        self.assert_icon("material/sprout", status="Early Project")
        self.assert_icon("material/seed", status="Very Early Project")

    def test_a_regular_member_gets_the_plain_icon(self):
        """Which is most of them: `Member`, or nothing stored yet"""
        self.assert_icon("material/account", status="Member")
        self.assert_icon("material/account")


class TestTheSummaryCard(ProjectPageTestCase):
    """The classifications card, which is the first thing on the page"""

    def card(self, **kwargs):
        """The summary card of such a member, as one string"""
        return "\n".join(self.page(**kwargs).classification_card())

    def test_every_status_titles_the_card(self):
        """The title is what tells a reader what kind of member this is"""
        for status, title in [
            ("Qiskit Project", "**Qiskit Project**"),
            ("Alumni", "**Alumni project**"),
            ("Under revision", "**Project under revision**"),
            ("Unmaintained", "**Unmaintained project**"),
            ("Early Project", "**Early Project**"),
            ("Very Early Project", "**Very Early Project**"),
            ("Member", "**Qiskit Ecosystem Member**"),
        ]:
            with self.subTest(status=status):
                card = self.card(status=status)
                self.assertIn(title, card)
                self.assertIn("../classifications.md#", card)

    def test_the_maturity_says_what_support_to_expect(self):
        """Three groups: full support, limited support and none"""
        self.assertIn(
            ":material-check-outline: **production-ready**",
            self.card(maturity="production-ready"),
        )
        self.assertIn("**Limited support**", self.card(maturity="bugfixing only"))
        self.assertIn("**No support**", self.card(maturity="as-is"))

    def test_an_alumni_project_has_no_maturity_to_promise(self):
        """It is retired, so what it used to declare is not a promise anymore"""
        card = self.card(status="Alumni", maturity="production-ready")
        self.assertNotIn("production-ready", card)

    def test_the_license_is_a_bullet_of_its_own(self):
        """A member with no license is a failing check up, not a blank bullet"""
        self.assertIn(
            ":material-scale-balance: **License** Apache-2.0",
            self.card(license="Apache-2.0"),
        )
        self.assertNotIn("**License**", self.card())

    def test_the_interfaces_are_counted_in_the_label(self):
        """One interface is an interface, two are interfaces"""
        self.assertIn(
            "**Interface** `qiskit.transpiler`",
            self.card(interfaces=["qiskit.transpiler"]),
        )
        self.assertIn(
            "**Interfaces**", self.card(interfaces=["qiskit.transpiler", "BackendV2"])
        )

    def test_each_interface_links_to_the_projects_with_it(self):
        """The annotations are numbered in the order of the values"""
        card = self.card(interfaces=["qiskit.transpiler", "BackendV2"])
        self.assertIn("`qiskit.transpiler`(1)", card)
        self.assertIn("`BackendV2`(2)", card)
        self.assertIn("1.  [All the projects with qiskit.transpiler interface]", card)

    def test_the_category_links_to_its_section(self):
        """Every project has one, and it is what the summary page groups by"""
        card = self.card(category="Circuit compilation")
        self.assertIn("**Category** `Circuit compilation`", card)
        self.assertIn("../classifications.md#circuit-compilation", card)

    def test_having_no_labels_is_said_out_loud(self):
        """A blank where the labels go would read as a rendering bug"""
        self.assertIn(":material-tag-off-outline: **No labels**", self.card())
        self.assertIn("**Labels** `C++`(1)", self.card(labels=["C++"]))

    def test_ibm_maintained_is_only_mentioned_when_it_is_true(self):
        """It says who to ask about the project, so there is nothing to say otherwise"""
        self.assertIn(
            ":material-office-building: IBM maintained", self.card(ibm_maintained=True)
        )
        self.assertNotIn("IBM maintained", self.card())


class TestTheURLsCard(ProjectPageTestCase):
    """The links card beside the summary"""

    def card(self, **kwargs):
        """The URLs card of such a member, as one string"""
        return "\n".join(self.page(**kwargs).urls_card())

    def test_every_stored_url_gets_a_line(self):
        """In reading order: where it lives, its code, its docs"""
        card = self.card(
            website="https://banana-org.example",
            documentation="https://banana.readthedocs.io",
        )
        self.assertIn("[Website](https://banana-org.example)", card)
        self.assertIn("[Source code](https://github.com/banana-org/banana-repo)", card)
        self.assertIn("[Documentation](https://banana.readthedocs.io)", card)

    def test_the_reference_paper_is_iconed_after_its_host(self):
        """A reader recognizes arXiv or IEEE faster than a generic newspaper"""
        for host, icon in [
            ("https://arxiv.org/abs/2601.00001", ":simple-arxiv:"),
            ("https://doi.org/10.1000/banana", ":simple-doi:"),
            ("https://ieeexplore.ieee.org/document/1", ":simple-ieee:"),
            ("https://dl.acm.org/doi/10.1145/banana", ":simple-acm:"),
            ("https://banana-org.example/paper.pdf", ":material-newspaper:"),
        ]:
            with self.subTest(paper=host):
                self.assertIn(
                    f"{icon} [Reference paper]({host})", self.card(reference_paper=host)
                )


class TestThePackagesSection(ProjectPageTestCase):
    """One card per distribution, whatever registry it is published in"""

    def packages(self, **kwargs):
        """The packages section of such a member, as one string"""
        return "\n".join(self.page(**kwargs).packages())

    def test_there_is_no_heading_without_packages(self):
        """Which is the case for a repository that publishes nothing"""
        self.assertEqual("", self.packages())

    def test_a_pypi_package_gets_its_card(self):
        """The release, the downloads and the qiskit compatibility table"""
        section = self.packages(pypi={"banana": banana_on_pypi()})
        self.assertIn("### :material-package-variant: Packages", section)
        self.assertIn("#### :simple-python: PyPI `banana`", section)
        self.assertIn("**last month** 1,234", section)
        self.assertIn("Qiskit Compatibility", section)

    def test_a_julia_package_names_its_registry_and_its_users(self):
        """JuliaHub is the only place to link to, and it is keyed by registry"""
        section = self.packages(
            julia={
                "Banana": JuliaData(
                    package_name="Banana",
                    version="1.2.3",
                    release_date="Jan 2026",
                    estimated_unique_users=4242,
                )
            }
        )
        self.assertIn("#### :simple-julia: Julia `Banana`", section)
        self.assertIn("https://juliahub.com/ui/Packages/General/Banana", section)
        self.assertIn('"Released: Jan 2026"', section)
        self.assertIn("**estimated unique users** 4,242", section)

    def test_a_julia_package_with_nothing_fetched_says_so(self):
        """A section can be stored before any of it has been read"""
        section = self.packages(julia={"Banana": JuliaData(package_name="Banana")})
        self.assertIn("[N/A]", section)
        self.assertIn('"Released: N/A"', section)
        self.assertNotIn("estimated unique users", section)

    def test_each_other_registry_is_recognized_by_its_host(self):
        """`member.packages` is a list of URLs, so the host is all there is to go by"""
        for url, expected in [
            (
                "https://marketplace.visualstudio.com/items?itemName=banana",
                ":material-microsoft-visual-studio: [Visual Studio Marketplace: banana]",
            ),
            (
                "https://ocaml.org/p/banana/latest",
                ":simple-ocaml: [opam (OCaml Package Manager): banana]",
            ),
            (
                "https://github.com/banana-org/banana-repo/pkgs/container/banana",
                ":simple-github: [GitHub Package: banana]",
            ),
            ("https://crates.io/crates/banana", ":simple-rust: [Crate: banana]"),
            (
                "https://www.npmjs.com/package/banana",
                ":octicons-package-16: [www.npmjs.com]",
            ),
        ]:
            with self.subTest(package=url):
                self.assertIn(expected, self.packages(packages=[URL(url)]))


class TestTheCheckupsTable(ProjectPageTestCase):
    """One row per check up the project is not passing"""

    def table(self, **kwargs):
        """The check ups section of such a member, as one string"""
        return "\n".join(self.page(**kwargs).checkups())

    def test_a_passing_project_is_told_so(self):
        """Most of them, and an empty table would read as a missing one"""
        self.assertIn(":material-check-all: All good", self.table())
        self.assertNotIn("| Check up |", self.table())

    def test_a_row_carries_what_the_check_up_knows(self):
        """Its id, its title, its importance and what it found"""
        table = self.table(checks={"010": self.checkup("010", details="it says TEST")})
        self.assertIn("[`[010]`](../checkups.md#010)", table)
        self.assertIn("RECOMMENDATION", table)
        self.assertIn("it says TEST", table)

    def test_the_most_severe_check_up_comes_first(self):
        """A reader should meet the one that can retire the project first"""
        table = self.table(
            checks={"010": self.checkup("010"), "COC": self.checkup("COC")}
        )
        self.assertLess(table.index("[`[COC]`]"), table.index("[`[010]`]"))

    def test_a_column_with_nothing_in_it_is_dropped(self):
        """A check up with no details of its own leaves that column empty"""
        table = self.table(checks={"COC": self.checkup("COC")})
        self.assertNotIn("What is failing", table)
        self.assertNotIn("Discussion", table)
        self.assertIn("Days left", table)

    def test_the_days_column_goes_too_when_no_row_can_count(self):
        """Every cure period of an alumni project reads the same placeholder"""
        table = self.table(status="Alumni", checks={"COC": self.checkup("COC")})
        self.assertNotIn("Days left", table)


class TestTheDaysLeftCell(ProjectPageTestCase):
    """How long a check up can stay as it is, which is the larger of two clocks"""

    def days_left(self, checkup, **kwargs):
        """The cell for such a check up on such a project"""
        return ProjectPage.days_left(self.project(**kwargs), checkup)

    def test_an_alumni_project_has_nothing_left_to_count(self):
        """Its cure period is what retired it in the first place"""
        self.assertEqual(
            "&mdash;", self.days_left(self.checkup("010"), status="Alumni")
        )

    def test_an_infinite_cure_period_never_runs_out(self):
        """A legacy check up stays pending without ever becoming a reason to retire"""
        self.assertEqual("&infin;", self.days_left(self.checkup("PQ1")))

    def test_an_explanation_with_no_expiry_never_runs_out_either(self):
        """`xfailed` without `xfailed_until` is a permanent waiver"""
        self.assertEqual(
            "&infin;", self.days_left(self.checkup("010", xfailed="by design"))
        )

    def test_the_cure_period_is_counted_from_the_day_it_started_failing(self):
        """[010] is a RECOMMENDATION, so 180 days to fix it"""
        self.assertEqual("180", self.days_left(self.checkup("010")))
        self.assertEqual("150", self.days_left(self.checkup("010", since=30)))

    def test_the_later_of_the_two_clocks_is_the_one_that_matters(self):
        """The check up needs attention again when both have run out"""
        until = str(CheckData.today + timedelta(days=200))
        checkup = self.checkup(
            "010", xfailed="waiting on upstream", xfailed_until=until
        )
        self.assertEqual("200", self.days_left(checkup))

    def test_a_cure_period_behind_us_is_overdue(self):
        """The number itself is not news anymore; that it ran out is"""
        self.assertEqual("overdue", self.days_left(self.checkup("010", since=200)))

    def test_there_is_nothing_to_count_without_a_starting_day(self):
        """A check up written by hand may not say when it started failing"""
        self.assertEqual("&mdash;", self.days_left(CheckData("010")))


class TestTheDiscussionCell(ProjectPageTestCase):
    """Why a check up is not being acted on"""

    def test_an_explanation_that_applies_is_shown(self):
        """As the Markdown it was written as, so a link in a member file is a link"""
        cell = ProjectPage.discussion_cell(
            self.checkup("010", xfailed="[agreed](http://x)")
        )
        self.assertEqual("[agreed](http://x)", cell)

    def test_an_expired_explanation_is_not(self):
        """It does not excuse the check up anymore, so it does not excuse it here"""
        yesterday = str(CheckData.today - timedelta(days=1))
        cell = ProjectPage.discussion_cell(
            self.checkup("010", xfailed="was agreed", xfailed_until=yesterday)
        )
        self.assertEqual("", cell)

    def test_the_explanation_and_the_link_sit_side_by_side(self):
        """Both answer the same question, so neither replaces the other"""
        cell = ProjectPage.discussion_cell(
            self.checkup(
                "010", xfailed="agreed", discussion="https://github.com/x/y/issues/1"
            )
        )
        self.assertEqual(
            "agreed &middot; [discussion](https://github.com/x/y/issues/1)", cell
        )


class TestTheBadgeSection(ProjectPageTestCase):
    """The snippet a maintainer copies into their README"""

    def test_there_is_no_section_without_a_badge(self):
        """The badge is created when the member is accepted, not before"""
        self.assertEqual([], self.page().badge())

    def test_the_section_carries_the_image_the_style_and_the_snippet(self):
        """Everything needed to paste it and to understand what it says"""
        section = "\n".join(
            self.page(
                badge=BadgeData(url="https://bit.ly/banana", style="flat")
            ).badge()
        )
        self.assertIn("### :simple-shieldsdotio: Badge", section)
        self.assertIn('<img src="https://bit.ly/banana">', section)
        self.assertIn(
            "[![Qiskit Ecosystem](https://bit.ly/banana)](https://qisk.it/e)", section
        )
        self.assertIn("**style** `flat`", section)
