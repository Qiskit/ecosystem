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

"""Tests for the files the member commands generate: the fragments the documentation
build reads, the shields.io endpoints and the feed behind the ibm.com listing"""

import json
import shutil
import tempfile
from datetime import date, timedelta
from pathlib import Path
from unittest import TestCase

from ecosystem.badge import BadgeData
from ecosystem.check import CheckData
from ecosystem.github import GitHubData
from ecosystem.cli import CliMembers, build_website
from tests.test_cli import UpdateStatusTestCase


class TestCheckupAssets(UpdateStatusTestCase):
    """The fragments behind qisk.it/ecosystem-checkups, generated from checks.toml
    and the member files. See `CliMembers.update_assets_checkups`"""

    def setUp(self):
        super().setUp()
        (self.path / "docs" / "assets").mkdir(parents=True, exist_ok=True)

    def generate(self):
        """Runs the generator and returns (summary rows, page body)"""
        self.cli_members.update_assets_checkups()
        assets = self.path / "docs" / "assets"
        return (
            json.loads((assets / "checkup.json").read_text()),
            (assets / "checkup.md").read_text(),
        )

    def failing(self, checkup_id, *, xfailed=None):
        """A member failing `checkup_id`, optionally with an explanation for it"""
        member = self.add_member()
        member.checks = {
            checkup_id: [CheckData(checkup_id, since=date.today(), xfailed=xfailed)]
        }
        self.cli_members.dao.write(member)
        return member

    def test_every_checkup_gets_a_section(self):
        """One section per check up in checks.toml, with the id as the anchor"""
        summary, body = self.generate()
        ids = set(self.cli_members.checks_toml.checkups)
        self.assertEqual(len(summary), len(ids))
        for id_ in ids:
            with self.subTest(checkup=id_):
                self.assertIn(f"{{ #{id_} }}", body)

    def test_a_failing_project_is_listed(self):
        """The project shows up under its check up, linked to its project page"""
        member = self.failing("G07")
        summary, body = self.generate()
        self.assertIn("There is 1 project failing this check up", body)
        self.assertIn(f"[{member.name}](p/{member.short_uuid}.md)", body)
        row = next(r for r in summary if "[G07]" in r["Check up"])
        self.assertEqual(row["Failing"], 1)

    def test_a_checkup_nobody_fails_says_so(self):
        """[G07] is the only one failing, so [G05] has nothing to list"""
        self.failing("G07")
        _, body = self.generate()
        section = body.split("{ #G05 }")[1].split("## ")[0]
        self.assertIn("**No project is failing this check up**", section)

    def test_an_explained_checkup_is_not_counted_as_failing(self):
        """A valid explanation is listed apart, and out of the failing count"""
        self.failing("G07", xfailed="the maintainers still answer issues")
        summary, body = self.generate()
        self.assertIn("1 project with an explanation for this check up", body)
        self.assertNotIn('failing this check up"', body.split("{ #G07 }")[1])
        row = next(r for r in summary if "[G07]" in r["Check up"])
        self.assertEqual(row["Failing"], 0)

    def test_the_summary_links_to_the_sections(self):
        """Every row of the summary table points at a section of the same page"""
        summary, body = self.generate()
        for row in summary:
            with self.subTest(row=row["Check up"]):
                anchor = row["Check up"].rpartition("(#")[2].rstrip(")")
                self.assertIn(f"{{ #{anchor} }}", body)


class TestCheckupProjectTable(UpdateStatusTestCase):
    """The table inside each collapsible: maturity, status, and what is left of the cure
    period. See `CliMembers.update_assets_checkups`"""

    def setUp(self):
        super().setUp()
        (self.path / "docs" / "assets").mkdir(parents=True, exist_ok=True)

    def body_of(self, checkup_id, days_ago=0, **member_kwargs):
        """The generated section of `checkup_id`, for a member failing it"""
        self.row_of(checkup_id, days_ago, **member_kwargs)
        body = (self.path / "docs" / "assets" / "checkup.md").read_text()
        return body.split(f"{{ #{checkup_id} }}")[1].split("\n## ")[0]

    def row_of(self, checkup_id, days_ago=0, **member_kwargs):
        """The table row that `checkup_id` gets for a member failing it `days_ago` days ago"""
        xfailed = member_kwargs.pop("xfailed", None)
        xfailed_until = member_kwargs.pop("xfailed_until", None)
        discussion = member_kwargs.pop("discussion", None)
        member = self.add_member(**member_kwargs)
        member.status = member_kwargs.get("status")
        member.checks = {
            checkup_id: [
                CheckData(
                    checkup_id,
                    since=date.today() - timedelta(days=days_ago),
                    xfailed=xfailed,
                    xfailed_until=xfailed_until,
                    discussion=discussion,
                )
            ]
        }
        self.cli_members.dao.write(member)
        self.cli_members.update_assets_checkups()
        body = (self.path / "docs" / "assets" / "checkup.md").read_text()
        section = body.split(f"{{ #{checkup_id} }}")[1].split("\n## ")[0]
        return next(
            line.strip() for line in section.splitlines() if line.startswith("    | [")
        )

    def test_maturity_and_status_are_shown(self):
        """[G07] has a 90 day cure period, so a fresh failure has all of it left"""
        row = self.row_of("G07", maturity="experimental", status="Under revision")
        self.assertIn("| experimental |", row)
        self.assertIn("| Under revision |", row)
        self.assertTrue(row.endswith("| 90 |"), row)

    def test_the_default_status_is_member(self):
        """A regular member has no `member.status` of its own"""
        self.assertIn("| Member |", self.row_of("G07"))

    def test_the_days_count_down_from_since(self):
        """The deadline does not move while the check up keeps failing"""
        self.assertTrue(self.row_of("G07", days_ago=30).endswith("| 60 |"))

    def test_a_passed_deadline_is_overdue(self):
        """Past the cure period, but not retired (yet, or because it is excluded)"""
        self.assertTrue(self.row_of("G07", days_ago=91).endswith("| overdue |"))

    def test_an_infinite_cure_period_has_no_countdown(self):
        """[PQ1] is LEGACY, an importance whose cure period is -1"""
        self.assertTrue(self.row_of("PQ1", days_ago=10_000).endswith("| &infin; |"))

    def test_alumni_are_not_rows_in_the_table(self):
        """Their cure period is what retired them, so they are listed apart. See
        `TestCheckupAlumniList`"""
        with self.assertRaises(StopIteration):
            self.row_of("G07", days_ago=30, status="Alumni")

    def test_an_explanation_shows_its_own_expiration(self):
        """An explained check up has no cure period ticking, so the column is what is left
        of the explanation instead"""
        row = self.row_of(
            "G07",
            xfailed="the maintainers still answer issues",
            xfailed_until=date.today() + timedelta(days=45),
        )
        self.assertTrue(row.endswith("| 45 days |"), row)

    def test_the_explanation_is_a_column(self):
        """The `xfailed` text itself, next to when it expires"""
        row = self.row_of("G07", xfailed="the project is feature complete")
        self.assertIn("| the project is feature complete |", row)
        self.assertIn(
            "| Project | Maturity | Status | Explanation | Explanation expires in |",
            self.body_of("G07", xfailed="the project is feature complete"),
        )

    def test_no_explanation_no_column(self):
        """A pending check up has nothing to explain"""
        self.assertNotIn("Explanation", self.body_of("G07"))

    def test_a_discussion_is_linked(self):
        """The column only shows up when one of the projects has a `discussion`"""
        row = self.row_of(
            "G07", discussion="https://github.com/Qiskit/ecosystem/issues/1"
        )
        self.assertIn(
            "| [discussion](https://github.com/Qiskit/ecosystem/issues/1) |", row
        )

    def test_no_discussion_no_column(self):
        """Nothing extra when none of the projects has one"""
        body = self.body_of("G07")
        self.assertNotIn("Discussion", body)
        self.assertIn(
            "| Project | Maturity | Status | Days left in the cure period |", body
        )

    def test_an_explanation_without_expiration_never_expires(self):
        """`xfailed` without `xfailed_until`"""
        row = self.row_of("G07", xfailed="this project is feature complete")
        self.assertTrue(row.endswith("| never |"), row)


class TestCheckupAlumniList(UpdateStatusTestCase):
    """The alumni that were failing a check up are listed apart, out of the headline count.
    See `CliMembers.update_assets_checkups`"""

    def setUp(self):
        super().setUp()
        (self.path / "docs" / "assets").mkdir(parents=True, exist_ok=True)

    def section(self, *members):
        """Writes the members, generates, and returns the [G07] section of the page"""
        for status in members:
            member = self.add_member()
            member.status = status
            member.checks = {"G07": [CheckData("G07", since=date.today())]}
            self.cli_members.dao.write(member)
        self.cli_members.update_assets_checkups()
        body = (self.path / "docs" / "assets" / "checkup.md").read_text()
        return body.split("{ #G07 }")[1].split("\n## ")[0]

    def summary_count(self, column):
        """A count column of the [G07] row of the summary table"""
        summary = json.loads(
            (self.path / "docs" / "assets" / "checkup.json").read_text()
        )
        return next(r for r in summary if "[G07]" in r["Check up"])[column]

    def test_only_members_are_counted_as_failing(self):
        """Two alumni and one member: the headline is about the member"""
        section = self.section("Alumni", None, "Alumni")
        self.assertIn("There is 1 project failing this check up", section)
        self.assertIn('??? info "2 Alumni projects also failed', section)
        self.assertEqual(self.summary_count("Failing"), 1)

    def test_the_alumni_are_counted_in_their_own_column(self):
        """The count the table hid: visible without opening the section"""
        self.section("Alumni", None, "Alumni")
        self.assertEqual(self.summary_count("Alumni"), 2)

    def test_a_checkup_no_alumni_ever_failed_counts_zero(self):
        """An empty column reads as none, not as missing data"""
        self.section(None)
        self.assertEqual(self.summary_count("Alumni"), 0)

    def test_the_alumni_list_is_nested_in_the_table(self):
        """Indented inside the collapsible that holds the table"""
        section = self.section("Alumni", None)
        self.assertIn('    ??? info "1 Alumni project also failed', section)
        self.assertRegex(section, r"\n        - \[")

    def test_only_alumni_says_no_current_member(self):
        """With nothing to put in the table, the list goes to the top level"""
        section = self.section("Alumni")
        self.assertIn("**No current member is failing this check up**", section)
        self.assertIn('\n??? info "1 Alumni project also failed', section)
        self.assertEqual(self.summary_count("Failing"), 0)
        self.assertEqual(self.summary_count("Alumni"), 1)

    def test_no_alumni_no_list(self):
        """Nothing extra when no alumni ever failed it"""
        section = self.section(None)
        self.assertIn("There is 1 project failing this check up", section)
        self.assertNotIn("Alumni", section)


class TestMemberBadgeEndpoints(UpdateStatusTestCase):
    """The endpoint behind the badge of an actual member, served at its `short_uuid`.
    See `CliMembers.create_badge_endpoints`"""

    def endpoint_of(self, member):
        """The member endpoint, as shields.io reads it"""
        self.cli_members.create_badge_endpoints()
        return json.loads((self.path / "badges" / str(member.short_uuid)).read_text())

    def test_a_member_without_a_badge_section_has_no_endpoint(self):
        """Nothing links to a badge it never asked for, so there is nothing to serve"""
        self.add_member()
        self.cli_members.create_badge_endpoints()
        self.assertEqual([], sorted((self.path / "badges").iterdir()))

    def test_the_message_is_the_name_of_the_member(self):
        """The badge says which project it is about"""
        member = self.add_member(badge=BadgeData())
        self.assertEqual("mock-qiskit", self.endpoint_of(member)["message"])

    def test_an_alumni_badge_is_labelled_as_one(self):
        """The badge keeps being served after the project leaves, saying what it now means"""
        member = self.add_member(badge=BadgeData(), status="Alumni")
        self.assertEqual("Qiskit Ecosystem Alumni", self.endpoint_of(member)["label"])

    def test_a_member_under_revision_gets_the_warning_color(self):
        """Orange instead of the Qiskit purple, while a check up is pending"""
        member = self.add_member(badge=BadgeData(), status="Under revision")
        self.assertEqual("c46929", self.endpoint_of(member)["color"])

    def test_the_badge_section_overrides_what_is_derived(self):
        """A member file can state any of the shields.io fields"""
        member = self.add_member(
            badge=BadgeData(label="Banana", color="ff0000"), status="Under revision"
        )
        endpoint = self.endpoint_of(member)
        self.assertEqual("Banana", endpoint["label"])
        self.assertEqual("ff0000", endpoint["color"])


class TestExampleBadgeEndpoints(UpdateStatusTestCase):
    """The endpoints behind the example badges in qisk.it/ecosystem-badges.

    They are about a project that does not exist, so they are built from the name given
    and not from the database. See `CliMembers.create_badge_endpoints`
    """

    EXAMPLE = "Qiskit Banana Compiler"

    def endpoint(self, filename):
        """One of the example endpoints, as shields.io reads it"""
        self.cli_members.create_badge_endpoints(example=self.EXAMPLE)
        return json.loads((self.path / "badges" / filename).read_text())

    def test_one_endpoint_per_style(self):
        """The page shows them side by side, so every style shields.io has is there"""
        for style in ["flat", "flat-square", "plastic", "for-the-badge", "social"]:
            with self.subTest(style=style):
                self.assertEqual(style, self.endpoint(f"example_{style}")["style"])

    def test_the_message_is_the_name_given(self):
        """Which is what makes the example look like a member badge"""
        self.assertEqual(self.EXAMPLE, self.endpoint("example_flat")["message"])

    def test_the_alumni_example_is_labelled_as_one(self):
        """The label is the only thing telling the two badges apart"""
        self.assertEqual(
            "Qiskit Ecosystem Alumni", self.endpoint("example_alumni")["label"]
        )

    def test_the_under_revision_example_is_a_warning(self):
        """Here the status is the message, in the orange of the triadic palette"""
        under_revision = self.endpoint("example_under-revision")
        self.assertEqual("Under revision", under_revision["message"])
        self.assertEqual("c46929", under_revision["color"])

    def test_without_a_name_there_are_no_examples(self):
        """They are regenerated with the member endpoints, and only then"""
        self.cli_members.create_badge_endpoints()
        self.assertEqual([], sorted((self.path / "badges").iterdir()))


class TestDocsAssets(UpdateStatusTestCase):
    """`update_docs_assets` regenerates the fragments in docs/assets/ that the
    documentation build reads, one per classification"""

    CLASSIFICATIONS = ("status", "maturity", "category", "labels", "interfaces")

    def generate(self, **kwargs):
        """Adds a member, regenerates the fragments, and returns where they are"""
        self.add_member(**kwargs)
        self.cli_members.update_docs_assets()
        return self.path / "docs" / "assets"

    def test_every_classification_gets_a_page_and_a_summary_table(self):
        """The page is read into the classifications page, the json into the website"""
        assets = self.generate()
        for classification in self.CLASSIFICATIONS:
            with self.subTest(classification=classification):
                self.assertTrue((assets / f"{classification}.md").is_file())
                self.assertTrue((assets / f"{classification}.json").is_file())

    def test_a_project_is_listed_under_each_of_its_values(self):
        """A member has one category but any number of labels and interfaces"""
        assets = self.generate(
            category="Tooling", labels=["optimization", "QML"], interfaces=["Python"]
        )
        for classification in ("category", "labels", "interfaces"):
            with self.subTest(classification=classification):
                self.assertIn(
                    "mock-qiskit", (assets / f"{classification}.md").read_text()
                )

    def test_a_value_that_classifications_toml_does_not_have_is_not_a_section(self):
        """The vocabulary is the one in resources/, so a member cannot add to it"""
        assets = self.generate(labels=["bananas"])
        self.assertNotIn("bananas", (assets / "labels.md").read_text())

    def test_a_scalar_value_outside_the_vocabulary_is_not_a_section_either(self):
        """`category` is one value rather than a list, and it is read the same way"""
        assets = self.generate(category="bananas")
        self.assertNotIn("bananas", (assets / "category.md").read_text())

    def test_a_value_nobody_has_says_so(self):
        """Rather than an empty table, which reads as a broken page"""
        assets = self.generate(labels=["optimization"])
        self.assertIn(
            "**No project with this classification**",
            (assets / "labels.md").read_text(),
        )

    def test_the_section_text_comes_from_resources(self):
        """A classification value can have a page of prose, as `provider` does"""
        (self.path / "labels").mkdir(parents=True, exist_ok=True)
        (self.path / "labels" / "optimization.md").write_text("About optimization.")
        assets = self.generate(labels=["optimization"])
        self.assertIn("About optimization.", (assets / "labels.md").read_text())

    def test_other_is_the_last_section(self):
        """It is the catch-all, so it reads out of place anywhere else"""
        body = (self.generate(category="Other") / "category.md").read_text()
        self.assertEqual(
            body.rindex("### Other "),
            max(
                body.rindex(f"### {name} ")
                for name in self.cli_members.classifications_toml.category_names
            ),
        )

    def test_ibm_maintained_is_a_list_of_its_own(self):
        """It is a flag and not a classification value, so it has no page"""
        assets = self.generate(ibm_maintained=True)
        self.assertIn("mock-qiskit", (assets / "ibm-maintained.md").read_text())
        self.assertFalse((assets / "ibm-maintained.json").exists())

    def test_the_badge_table_is_regenerated_too(self):
        """It is the page maintainers copy their badge from"""
        self.add_member(badge=BadgeData(url="https://bit.ly/banana"))
        self.cli_members.update_docs_assets()
        self.assertIn(
            "https://bit.ly/banana",
            (self.path / "docs" / "assets" / "badges_table.md").read_text(),
        )


class TestCompileJson(UpdateStatusTestCase):
    """`compile_json` writes the v0 feed that ibm.com reads"""

    def setUp(self) -> None:
        super().setUp()
        shutil.copy(
            Path(self.current_dir, "..", "resources", "classifications.toml"),
            self.path / "classifications.toml",
        )

    def compile_json(self, **kwargs):
        """The exported feed, with one member in it"""
        self.add_member(**kwargs)
        output = self.path / "ecosystem.json"
        self.cli_members.compile_json(str(output))
        return json.loads(output.read_text())

    def test_a_member_is_exported_with_its_uuid(self):
        """Which is what the consumer keys the entry by"""
        member = self.add_member()
        output = self.path / "ecosystem.json"
        self.cli_members.compile_json(str(output))
        exported = json.loads(output.read_text())["members"]
        self.assertEqual([str(member.uuid)], [each["uuid"] for each in exported])

    def test_an_alumni_is_not_exported(self):
        """It is no longer a member, and the feed is the list of members"""
        self.assertEqual([], self.compile_json(status="Alumni")["members"])

    def test_a_very_early_project_is_not_exported(self):
        """It is not announced anywhere else either, until it is three months old"""
        self.assertEqual([], self.compile_json(status="Very Early Project")["members"])

    def test_the_classification_vocabulary_is_exported(self):
        """Under the names the consumer uses: categories are Types, labels Subjects"""
        labels = self.compile_json()["labels"]
        self.assertEqual(["Types", "Subjects"], list(labels))
        for name in labels["Types"] + labels["Subjects"]:
            with self.subTest(name=name["name"]):
                self.assertIn("description", name)

    def test_the_first_alias_that_resolves_is_the_one_exported(self):
        """`url` is read from the GitHub section first, and from the member after it"""
        self.add_member(months_old=1)
        output = self.path / "ecosystem.json"
        self.cli_members.compile_json(str(output))
        self.assertEqual(
            "https://github.com/MockQiskit/mock-qiskit",
            json.loads(output.read_text())["members"][0]["url"],
        )

    def test_the_declared_license_is_what_the_feed_carries(self):
        """GitHub's is a guess from the repository contents, the member file is a statement"""
        member = self.add_member(months_old=1)
        member.license = "Apache-2.0"
        member.github = GitHubData(owner="MockQiskit", repo="m", license="GPL-3.0")
        self.cli_members.dao.write(member)
        output = self.path / "ecosystem.json"
        self.cli_members.compile_json(str(output))

        exported = json.loads(output.read_text())["members"][0]
        self.assertEqual("Apache-2.0", exported["licence"])

    def test_the_license_github_detected_is_the_fallback(self):
        """Most members declare none, so the feed would be empty without it"""
        member = self.add_member(months_old=1)
        member.license = None
        member.github = GitHubData(owner="MockQiskit", repo="m", license="GPL-3.0")
        self.cli_members.dao.write(member)
        output = self.path / "ecosystem.json"
        self.cli_members.compile_json(str(output))

        exported = json.loads(output.read_text())["members"][0]
        self.assertEqual("GPL-3.0", exported["licence"])

    def test_a_falsy_value_is_exported_rather_than_dropped(self):
        """A zero and a false are answers, and dropping them reads as unknown"""
        member = self.add_member(months_old=1)
        member.github = GitHubData(
            owner="MockQiskit", repo="m", stars=0, archived=False
        )
        self.cli_members.dao.write(member)
        output = self.path / "ecosystem.json"
        self.cli_members.compile_json(str(output))

        github = json.loads(output.read_text())["members"][0]["github"]
        self.assertEqual(0, github["stars"])
        self.assertIs(False, github["archived"])

    def test_ibm_maintained_is_stated_either_way(self):
        """The one field with no unknown state, so absence would be a worse answer than false"""
        self.assertIs(False, self.compile_json()["members"][0]["ibm_maintained"])

    def test_an_ibm_maintained_project_says_so(self):
        """The 44 members that carry the flag keep carrying it"""
        self.assertIs(
            True, self.compile_json(ibm_maintained=True)["members"][0]["ibm_maintained"]
        )

    def test_a_field_no_alias_resolves_is_left_out(self):
        """And not filled in with the value of the field before it"""
        exported = self.compile_json()["members"][0]
        self.assertNotIn("contact_info", exported)
        self.assertNotEqual(exported.get("description"), exported["url"])


class TestFilterData(TestCase):
    """`CliMembers.filter_data` maps a member onto the shape the feed wants"""

    def test_a_nested_map_is_a_nested_object(self):
        """As `badge` is in the feed: a table of its own, built from one of ours"""
        self.assertEqual(
            {"repo": {"stars": 7}},
            CliMembers.filter_data(
                {"github": {"stars": 7}}, {"repo": {"stars": "github.stars"}}
            ),
        )

    def test_a_nested_map_that_resolves_to_nothing_is_left_out(self):
        """An empty object in the feed says less than no key at all"""
        self.assertEqual(
            {}, CliMembers.filter_data({}, {"repo": {"stars": "github.stars"}})
        )

    def test_a_selector_collects_one_object_per_match(self):
        """How the package sections are exported: a list, with the fields picked"""
        self.assertEqual(
            {"packages": [{"version": "1.0.0"}]},
            CliMembers.filter_data(
                {"pypi": {"banana": {"package_name": "banana", "version": "1.0.0"}}},
                {"packages": ("pypi.*", ["version"])},
            ),
        )

    def test_a_selector_without_a_query_and_a_field_list_is_an_error(self):
        """It is a mistake in the map above, so it stops the export"""
        with self.assertRaises(ValueError):
            CliMembers.filter_data({}, {"packages": ("pypi.*",)})

    def test_an_alias_matching_more_than_once_is_an_error(self):
        """There is no way to know which of them the feed wants"""
        with self.assertRaises(ValueError):
            CliMembers.filter_data(
                {"a": {"version": 1}, "b": {"version": 2}}, {"version": "*.version"}
            )

    def test_a_forced_field_is_exported_as_null(self):
        """For a field the consumer reads unconditionally"""
        self.assertEqual(
            {"description": None},
            CliMembers.filter_data(
                {}, {"description": ["description"]}, forced_addition=True
            ),
        )


class TestBuildWebsite(TestCase):
    """What is left where the ecosystem website used to be"""

    def setUp(self) -> None:
        self.path = Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        shutil.rmtree(self.path)

    def test_the_page_redirects_to_the_new_one(self):
        """Three ways, so it works without javascript and without the meta refresh"""
        output = self.path / "site" / "index.html"
        build_website(str(output))
        html = output.read_text()
        self.assertIn(
            '<meta http-equiv="refresh" content="0; url=https://ibm.com/quantum/ecosystem">',
            html,
        )
        self.assertIn(
            'window.location.href = "https://ibm.com/quantum/ecosystem"', html
        )
        self.assertIn('<a href="https://ibm.com/quantum/ecosystem">', html)
