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

"""Tests for ecosystem/docs/summary_charts.py, the data behind the summary page charts"""

import json
import re
import tempfile
from pathlib import Path
from unittest import TestCase

from ecosystem.docs import summary_charts
from ecosystem.github import GitHubData
from ecosystem.member import Member
from ecosystem.pypi import PyPIData
from ecosystem.python import PythonData
from ecosystem.requirements import RequirementsData

SUMMARY_PAGE = Path("docs/summary.md")


def member(name="Banana", **kwargs):
    """A member with whatever the chart under test reads"""
    return Member(name=name, url="https://github.com/banana-org/banana", **kwargs)


def totals(rows):
    """What each ring adds up to, which is what makes the rings line up"""
    sums = {}
    for row in rows:
        sums[row["ring"]] = sums.get(row["ring"], 0) + row["count"]
    return sums


def labels(rows, ring):
    """The sectors of one ring, in the order they are stacked"""
    return [row["label"] for row in rows if row["ring"] == ring]


class TestTheStatusRings(TestCase):
    """In the website or not, then the status, then how young a regular member is"""

    @staticmethod
    def rings(**counts):
        """The rings for a corpus holding that many projects of each status"""
        return summary_charts.status_rings(
            [
                member(status=status)
                for status, count in counts.items()
                for _ in range(count)
            ]
        )

    def test_every_ring_counts_every_project(self):
        """A ring that did not would draw sectors that do not line up with the ring inside"""
        rings = self.rings(Member=5, Alumni=2, **{"Qiskit Project": 3})
        self.assertEqual({1: 10, 2: 10, 3: 10}, totals(rings))

    def test_the_first_ring_is_the_website_split(self):
        """Which is the one thing the page used to say, with a hardcoded number"""
        rings = self.rings(Member=5, Alumni=2)
        self.assertEqual(["In the website", "Alumni"], labels(rings, 1))
        self.assertEqual([5, 2], [row["count"] for row in rings if row["ring"] == 1])

    def test_the_regular_members_are_one_sector_of_the_second_ring(self):
        """And three of the third, which is the point of having a third"""
        rings = self.rings(
            Member=5,
            **{"Early Project": 3, "Very Early Project": 2, "Under revision": 1}
        )
        self.assertEqual(["Regular member", "Under revision"], labels(rings, 2))
        self.assertEqual(10, [r["count"] for r in rings if r["ring"] == 2][0])
        self.assertEqual(
            ["Regular", "Early", "Very early", "Under revision"], labels(rings, 3)
        )

    def test_a_status_nobody_has_is_not_a_sector(self):
        """A zero-width arc is not a thing to draw"""
        self.assertNotIn("Unmaintained", labels(self.rings(Member=1), 2))

    def test_a_member_with_no_status_is_a_regular_one(self):
        """Most member files declare none"""
        self.assertEqual(
            ["Regular"], labels(summary_charts.status_rings([member()]), 3)
        )


class TestTheMaturityRings(TestCase):
    """The support a maturity promises, then the maturity itself"""

    @staticmethod
    def rings(*maturities, alumni=0):
        """The rings for a corpus with those maturities, plus some alumni"""
        return summary_charts.maturity_rings(
            [member(maturity=maturity) for maturity in maturities]
            + [
                member(status="Alumni", maturity="production-ready")
                for _ in range(alumni)
            ]
        )

    def test_the_support_level_groups_the_maturities(self):
        """The same three groups a project page promises in its summary card"""
        rings = self.rings(
            "production-ready", "experimental", "bugfixing only", "as-is"
        )
        self.assertEqual(
            ["Full support", "Limited support", "No support"], labels(rings, 1)
        )
        self.assertEqual([1, 2, 1], [r["count"] for r in rings if r["ring"] == 1])

    def test_the_maturities_follow_their_group(self):
        """Or the outer sectors would not sit inside the inner ones"""
        rings = self.rings("as-is", "experimental", "production-ready")
        self.assertEqual(
            ["production-ready", "experimental", "as-is"], labels(rings, 2)
        )

    def test_alumni_are_left_out(self):
        """A project that is no longer a member promises nothing, so its page says nothing"""
        self.assertEqual({1: 1, 2: 1}, totals(self.rings("experimental", alumni=3)))

    def test_a_member_with_no_maturity_is_counted_as_undeclared(self):
        """Leaving it out would make the rings disagree with the member count"""
        rings = self.rings("experimental", None)
        self.assertIn("Not declared", labels(rings, 1))
        self.assertIn("not declared", labels(rings, 2))
        self.assertEqual({1: 2, 2: 2}, totals(rings))


class TestThePackagingRings(TestCase):
    """Published or declared, then where from. One sector per member."""

    @staticmethod
    def rings(*projects):
        """The rings for those members"""
        return summary_charts.packaging_rings(list(projects))

    def test_a_member_is_counted_once_under_the_first_kind_it_has(self):
        """Otherwise the rings would add up to more than the number of members"""
        rings = self.rings(
            member(
                pypi=[PyPIData(package_name="banana")],
                python=[PythonData(package_name="banana")],
            )
        )
        self.assertEqual({1: 1, 2: 1}, totals(rings))
        self.assertEqual(["PyPI"], labels(rings, 2))

    def test_a_member_that_publishes_nothing_is_still_a_sector(self):
        """11 of them today, and a donut that hid them would be a lie"""
        rings = self.rings(member())
        self.assertEqual(["Nothing recorded"], labels(rings, 1))
        self.assertEqual(["Nothing recorded"], labels(rings, 2))

    def test_the_declared_kinds_are_their_own_group(self):
        """Which is the distinction the two pairs of sections are about"""
        rings = self.rings(
            member(requirements=[RequirementsData(file="requirements.txt")]),
            member(pypi=[PyPIData(package_name="banana")]),
        )
        self.assertEqual(["Published", "Declared in the repository"], labels(rings, 1))
        self.assertEqual(["PyPI", "A requirements file"], labels(rings, 2))

    def test_alumni_are_left_out(self):
        """The charts are about the ecosystem as it is today"""
        self.assertEqual({}, totals(self.rings(member(status="Alumni"))))


class TestTheRepositoryYears(TestCase):
    """A bar per year, stacked by the maturity the projects of that year declare"""

    @staticmethod
    def years(*created, alumni=None):
        """The rows for repositories created on those (date, maturity) pairs"""
        projects = [
            member(
                maturity=maturity,
                github=GitHubData(owner="o", repo="r", created_at=day),
            )
            for day, maturity in created
        ]
        if alumni:
            projects.append(
                member(
                    status="Alumni",
                    maturity="production-ready",
                    github=GitHubData(owner="o", repo="r", created_at=alumni),
                )
            )
        return summary_charts.repository_years(projects)

    def test_the_years_are_counted_and_sorted(self):
        """A reader follows the shape, so the order has to be the years' own"""
        rows = self.years(
            ("2026-01-15", "experimental"),
            ("2024-06-01", "production-ready"),
            ("2026-09-30", "experimental"),
        )
        self.assertEqual([2024, 2026], [row["year"] for row in rows])
        self.assertEqual([1, 2], [row["count"] for row in rows])

    def test_a_year_is_split_by_maturity(self):
        """Which is what the stack is for: how the promises of each year compare"""
        rows = self.years(
            ("2026-01-15", "experimental"), ("2026-02-15", "production-ready")
        )
        self.assertEqual(
            [("production-ready", 1), ("experimental", 1)],
            [(row["maturity"], row["count"]) for row in rows],
        )

    def test_a_maturity_links_to_its_section(self):
        """As the donut sectors do"""
        rows = self.years(("2026-01-15", "experimental"))
        self.assertEqual("../classifications/#experimental", rows[0]["url"])

    def test_a_repository_that_was_never_read_has_no_year(self):
        """`github.created_at` is fetched, so a fresh member file has none"""
        self.assertEqual([], summary_charts.repository_years([member()]))

    def test_alumni_are_left_out(self):
        """As in the other charts"""
        self.assertEqual([], self.years(alumni="2024-06-01"))


class TestTheSharesAndTheLinks(TestCase):
    """The two things a sector carries besides its size"""

    @staticmethod
    def rings(**counts):
        """The status rings for a corpus holding that many projects of each status"""
        return summary_charts.status_rings(
            [
                member(status=status)
                for status, count in counts.items()
                for _ in range(count)
            ]
        )

    def test_the_share_is_of_the_ring(self):
        """Every ring holds every project, so a share is comparable across rings"""
        rings = self.rings(Member=3, Alumni=1)
        self.assertEqual([0.75, 0.25], [r["share"] for r in rings if r["ring"] == 1])
        self.assertEqual(1, round(sum(r["share"] for r in rings if r["ring"] == 3)))

    def test_a_sector_links_to_the_section_about_it(self):
        """Which is the point of a chart somebody clicks"""
        links = {r["label"]: r["url"] for r in self.rings(Member=1, Alumni=1)}
        self.assertEqual("../classifications/#alumni", links["Alumni"])
        self.assertEqual("../classifications/#regular-members", links["Regular"])

    def test_a_maturity_links_to_its_own_section(self):
        """The anchor is built the way the heading's id was, rather than listed by hand"""
        rings = summary_charts.maturity_rings([member(maturity="bugfixing only")])
        links = {row["label"]: row["url"] for row in rings}
        self.assertEqual("../classifications/#bugfixing-only", links["bugfixing only"])
        self.assertEqual("../classifications/#maturity", links["Limited support"])

    def test_a_packaging_sector_links_to_the_table_below_it(self):
        """The table is what lists the members the sector counts"""
        rings = summary_charts.packaging_rings(
            [member(pypi=[PyPIData(package_name="banana")])]
        )
        links = {row["label"]: row["url"] for row in rings}
        self.assertEqual("#active-pypi-packages", links["PyPI"])

    def test_a_sector_with_nothing_to_point_at_stays_on_the_page(self):
        """An empty `href` would make a click reload the page instead of doing nothing"""
        rings = summary_charts.packaging_rings(
            [member(julia=[None])]  # a kind with no page of its own
        )
        self.assertEqual(
            summary_charts.HERE, {r["label"]: r["url"] for r in rings}["Julia"]
        )


class TestTheFragments(TestCase):
    """What the build writes, and what the page reads"""

    def test_every_chart_of_the_page_has_its_fragment(self):
        """A chart whose data file is missing renders as an empty box"""
        with tempfile.TemporaryDirectory() as directory:
            summary_charts.write_all([member(maturity="experimental")], directory)
            written = {path.name for path in Path(directory).glob("*.json")}
        asked_for = set(re.findall(r"assets/(\w+\.json)", SUMMARY_PAGE.read_text()))
        self.assertTrue(asked_for)
        self.assertTrue(asked_for <= written, asked_for - written)

    def test_the_badge_fragments_are_written_whether_the_page_uses_them_or_not(self):
        """They are for whoever renders a badge, which is usually not this page"""
        with tempfile.TemporaryDirectory() as directory:
            summary_charts.write_all([member(maturity="experimental")], directory)
            written = {path.name for path in Path(directory).glob("*.json")}
        self.assertIn("members_badge.json", written)
        self.assertIn("summary_totals.json", written)

    def test_the_json_carries_the_fields_the_specs_encode(self):
        """The spec names fields; a renamed one would silently empty the chart"""
        with tempfile.TemporaryDirectory() as directory:
            summary_charts.write_all([member(maturity="experimental")], directory)
            rows = json.loads((Path(directory) / "summary_status.json").read_text())
        self.assertEqual(
            ["ring", "order", "label", "count", "share", "url"], list(rows[0])
        )

    @staticmethod
    def highlight_param(spec):
        """The legend selection of a chart, wherever the spec is allowed to declare it.

        A layered spec declares it in a unit spec, which is one of its layers: declared at
        the top level, Vega-Lite emits the selection once per layer and Vega then refuses
        the whole chart with `Duplicate signal name: "highlight_tuple"` — three of the four
        charts rendered as nothing.
        """
        if "layer" in spec:
            declared = [layer for layer in spec["layer"] if "params" in layer]
            assert len(declared) == 1, "exactly one layer declares the selection"
            return declared[0]["params"][0]
        return spec["params"][0]

    def test_every_chart_highlights_what_the_legend_selects(self):
        """A point param bound to the legend, and the conditional opacity that shows it.

        An empty selection matches every mark, so nothing is dimmed until the first click.
        """
        for spec in re.findall(
            r"```vegalite\n(.*?)\n```", SUMMARY_PAGE.read_text(), re.S
        ):
            parsed = json.loads(spec)
            with self.subTest(chart=parsed["title"]["text"]):
                self.assertNotIn(
                    "params", parsed if "layer" in parsed else {}, "see highlight_param"
                )
                param = self.highlight_param(parsed)
                self.assertEqual("legend", param["bind"])
                self.assertEqual("point", param["select"]["type"])
                # the field the legend is keyed by, or clicking an entry selects nothing
                self.assertEqual(
                    [parsed["encoding"]["color"]["field"]], param["select"]["fields"]
                )
                encodings = [
                    layer.get("encoding", {}) for layer in parsed.get("layer", [])
                ] or [parsed["encoding"]]
                for encoding in encodings:
                    self.assertIn(param["name"], str(encoding["opacity"]))

    def test_a_label_layer_sees_the_same_rows_as_its_arcs(self):
        """A filter in a stacked layer re-stacks what is left, which moves every label.

        Filtering the small sectors out of a label layer put `Another registry` 6% on the
        edge of the sector after it: the labels have to be hidden, not dropped.
        """
        for spec in re.findall(
            r"```vegalite\n(.*?)\n```", SUMMARY_PAGE.read_text(), re.S
        ):
            parsed = json.loads(spec)
            for layer in parsed.get("layer", []):
                if layer["mark"]["type"] != "text":
                    continue
                with self.subTest(chart=parsed["title"]["text"]):
                    self.assertNotIn("share", layer["transform"][0]["filter"])
                    self.assertIn("share", str(layer["encoding"].get("opacity")))

    def test_the_specs_are_valid_json_pointing_at_those_files(self):
        """The charts plugin fails the build on invalid JSON, and renders nothing on a typo"""
        specs = re.findall(r"```vegalite\n(.*?)\n```", SUMMARY_PAGE.read_text(), re.S)
        self.assertEqual(4, len(specs))
        for spec in specs:
            parsed = json.loads(spec)
            with self.subTest(chart=parsed["title"]["text"]):
                self.assertTrue(parsed["data"]["url"].endswith(".json"))


class TestTheTotalsAndTheBadge(TestCase):
    """The two fragments that are numbers rather than chart data"""

    @staticmethod
    def projects():
        """Three members and an alumnus"""
        return [
            member(status="Qiskit Project"),
            member(),
            member(status="Under revision"),
            member(status="Alumni"),
        ]

    def test_the_totals_are_flat_so_a_badge_can_ask_for_one(self):
        """`$.members` has to be a number at the top level, not a path into chart data"""
        counted = summary_charts.totals(self.projects())
        self.assertEqual(4, counted["projects"])
        self.assertEqual(3, counted["members"])
        self.assertEqual(1, counted["alumni"])
        self.assertEqual(1, counted["qiskit_projects"])
        self.assertTrue(all(isinstance(value, int) for value in counted.values()))

    def test_the_members_count_leaves_the_alumni_out(self):
        """An alumnus is not a member, which is the one thing a badge must not get wrong"""
        self.assertEqual("3", summary_charts.members_badge(self.projects())["message"])

    def test_the_badge_is_what_a_shields_endpoint_expects(self):
        """shields.io renders nothing without the schema version"""
        badge = summary_charts.members_badge(self.projects())
        self.assertEqual(1, badge["schemaVersion"])
        self.assertIn("label", badge)
        self.assertIn("color", badge)

    def test_the_build_publishes_the_badge(self):
        """mkdocs only ships what it collected or what a plugin registered, and the badge
        is fetched from the site by shields.io, so it has to be registered"""
        script = Path("ecosystem/generate_docs_assets.py").read_text()
        self.assertIn("fragments(", script)
        self.assertIn('mkdocs_gen_files.open(f"assets/{name}"', script)
