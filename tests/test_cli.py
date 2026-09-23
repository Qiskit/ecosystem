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

"""Tests for cli."""

import io
import json
import os
import shutil
import tempfile
from datetime import date, timedelta
from unittest import TestCase, mock
from contextlib import redirect_stdout
from pathlib import Path

from dateutil.relativedelta import relativedelta

from ecosystem.check import CheckData
from ecosystem.cli import CliCI, CliMembers
from ecosystem.dao import DAO
from ecosystem.github import GitHubData
from ecosystem.member import Member


def get_community_repo() -> Member:
    """Return main mock repo."""
    return Member(
        name="mock-qiskit",
        url="https://github.com/MockQiskit/mock-qiskit",
        description="Mock description for repo",
        license="Apache 2.0",
        labels=["mock", "tests"],
        badge="https://qisk.it/e",
        maturity="production-ready",
    )


def mocked_get_request(*_args, **_kwargs):
    """For mocking a 200 response to a http request"""
    return type(
        "MockResponse",
        (object,),
        {
            "status_code": 200,
            "elapsed": 100,
            "ok": True,
            "created_at": None,
            "text": "<title>Qiskit Ecosystem:</title>",
        },
    )()


class TestCli(TestCase):
    """Test class for cli."""

    def setUp(self) -> None:
        self.path = Path(tempfile.mkdtemp())
        (self.path / "members").mkdir(parents=True, exist_ok=True)
        with open(self.path / "labels.json", "w") as file:
            file.write("{}")
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        with open(f"{self.current_dir}/resources/issue.md", "r") as issue_body_file:
            self.issue_body = issue_body_file.read()
        with open(f"{self.current_dir}/resources/issue_2.md", "r") as issue_body_file:
            self.issue_body_2 = issue_body_file.read()
        with open(
            f"{self.current_dir}/resources/issue_skip.md", "r"
        ) as issue_body_file:
            self.issue_body_skip = issue_body_file.read()
        with open(
            f"{self.current_dir}/resources/issue_extra.md", "r"
        ) as issue_body_file:
            self.issue_body_extra = issue_body_file.read()

    def tearDown(self) -> None:
        shutil.rmtree(self.path)

    def test_add_member_from_issue(self):
        """Tests /resources/issue.md parsing function.
        Function: Cli
                -> parser_issue
        """

        # /resources/issue.md
        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            CliCI.add_member_from_issue(self.issue_body, resources_dir=self.path)

        output_value = captured_output.getvalue().split("\n")
        self.assertEqual("SUBMISSION_NAME=Qiskit Banana Compiler", output_value[0])

        retrieved_repos = DAO(self.path).get_all()
        expected = {
            "name": "Qiskit Banana Compiler",
            "url": "https://github.com/somebody/banana-compiler",
            "description": "Compile bananas into Qiskit quantum circuits. "
            "Supports all modern devices, including Musa × paradisiaca.",
            "contact_info": "author@banana-compiler.org",
            "labels": ["error mitigation", "quantum information", "optimization"],
            "interfaces": ["Python"],
            "website": "https://banana-compiler.org",
            "documentation": "https://banana-compiler.org/documentation",
            "reference_paper": "https://arxiv.org/abs/5555.22222",
            "category": "circuit manipulation",
            "maturity": "production-ready",
            "packages": [
                "https://pypi.org/project/banana-compiler",
                "https://pypi.org/project/banana-compiler-hpc",
                "https://crates.io/crates/rusty-banana-compiler",
                "https://marketplace.visualstudio.com/items?itemName=banana-code-assistance",
            ],
        }
        self.assertEqual(len(retrieved_repos), 1)
        retrieved = list(retrieved_repos)[0].to_dict()
        self.assertIsInstance(retrieved.pop("uuid"), str)
        self.assertDictEqual(expected, retrieved)

    def test_add_member_from_issue_2(self):
        """Tests /resources/issue_2.md parsing function.
        Function: Cli
                -> parser_issue
        """

        # /resources/issue_2.md
        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            CliCI.add_member_from_issue(self.issue_body_2, resources_dir=self.path)

        output_value = captured_output.getvalue().split("\n")
        self.assertEqual("SUBMISSION_NAME=Qiskit Banana Compiler", output_value[0])

        retrieved_repos = DAO(self.path).get_all()
        expected = {
            "name": "Qiskit Banana Compiler",
            "url": "https://github.com/somebody/banana-compiler",
            "description": "Compile bananas into Qiskit quantum circuits. "
            "Supports all modern devices, including Musa × paradisiaca.",
            "labels": [],
            "interfaces": ["Other"],
            "category": "circuit manipulation",
            "maturity": "production-ready",
            "packages": [],
        }
        self.assertEqual(len(retrieved_repos), 1)
        retrieved = list(retrieved_repos)[0].to_dict()
        self.assertIsInstance(retrieved.pop("uuid"), str)
        self.assertDictEqual(expected, retrieved)

    def test_add_member_from_issue_skip(self):
        """Tests /resources/issue_skip.md parsing function.
        An issue with skip checks
        """

        # /resources/issue_skip.md
        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            CliCI.add_member_from_issue(self.issue_body_skip, resources_dir=self.path)

        output_value = captured_output.getvalue().split("\n")
        self.assertEqual("SUBMISSION_NAME=Qiskit Banana Compiler", output_value[0])

        retrieved_repos = DAO(self.path).get_all()
        expected = {
            "name": "Qiskit Banana Compiler",
            "url": "https://github.com/somebody/banana-compiler",
            "description": "Compile bananas into Qiskit quantum circuits. "
            "Supports all modern devices, including Musa × paradisiaca.",
            "labels": [],
            "interfaces": ["Python"],
            "category": "SDK",
            "maturity": "production-ready",
            "packages": [],
            "checks": {
                "010": {
                    "importance": "RECOMMENDATION",
                    "xfailed": 'This project is allow to have "test" in its name',
                    "xfailed_until": date.today()
                    + relativedelta(months=Member.DEFAULT_XFAILED_PERIOD_IN_MONTHS),
                },
                "COC": {
                    "importance": "CRITICAL",
                    "xfailed": "This project does not need to agree the CoC",
                    "xfailed_until": date.today()
                    + relativedelta(months=Member.DEFAULT_XFAILED_PERIOD_IN_MONTHS),
                },
            },
        }
        self.assertEqual(len(retrieved_repos), 1)
        retrieved = list(retrieved_repos)[0].to_dict()
        self.assertIsInstance(retrieved.pop("uuid"), str)
        self.assertDictEqual(expected, retrieved)

    def test_add_member_from_issue_extra(self):
        """Tests /resources/issue_extra.md parsing function.
        An issue with extra sections that can be ignored
        (like in https://github.com/Qiskit/ecosystem/issues/1123)
        """

        # /resources/issue_extra.md
        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            CliCI.add_member_from_issue(self.issue_body_extra, resources_dir=self.path)

        output_value = captured_output.getvalue().split("\n")
        self.assertEqual("SUBMISSION_NAME=Qiskit Banana Compiler", output_value[0])

        retrieved_repos = DAO(self.path).get_all()
        expected = {
            "name": "Qiskit Banana Compiler",
            "url": "https://github.com/somebody/banana-compiler",
            "description": "Compile bananas into Qiskit quantum circuits. "
            "Supports all modern devices, including Musa × paradisiaca.",
            "labels": [],
            "interfaces": ["Python"],
            "category": "SDK",
            "maturity": "production-ready",
            "packages": [],
        }
        self.assertEqual(len(retrieved_repos), 1)
        retrieved = list(retrieved_repos)[0].to_dict()
        self.assertIsInstance(retrieved.pop("uuid"), str)
        self.assertDictEqual(expected, retrieved)

    @mock.patch("requests.get", new=mocked_get_request)
    def test_create_badge_endpoints(self):
        """Tests creating badges."""
        commu_success = get_community_repo()
        dao = DAO(self.path)

        # insert entry
        dao.write(commu_success)

        cli_members = CliMembers(root_path=os.path.join(self.current_dir, ".."))
        cli_members.resources_dir = self.path
        cli_members.current_dir = self.path
        cli_members.dao = dao

        # create badge endpoints
        cli_members.create_badge_endpoints()

        # gets a short url and updates the list in qisk.it/ecosystem-badges
        cli_members.update_badge_list()

        badges_folder_path = f"{cli_members.current_dir}/badges"
        self.assertTrue(
            os.path.isfile(f"{badges_folder_path}/{commu_success.short_uuid}")
        )

        # check version status
        with open(
            f"{badges_folder_path}/{commu_success.short_uuid}", "r"
        ) as json_blueviolet:
            json_success = json_blueviolet.read()
        self.assertTrue('"color": "6929C4"' in json_success)

        os.remove(f"{badges_folder_path}/{commu_success.short_uuid}")


class UpdateStatusTestCase(TestCase):
    """Shared setup for the CliMembers.update_status tests"""

    def setUp(self) -> None:
        self.path = Path(tempfile.mkdtemp())
        (self.path / "members").mkdir(parents=True, exist_ok=True)
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.cli_members = CliMembers(root_path=os.path.join(self.current_dir, ".."))
        self.cli_members.resources_dir = self.path
        self.cli_members.current_dir = self.path
        self.cli_members.dao = DAO(self.path)

    def tearDown(self) -> None:
        shutil.rmtree(self.path)

    def add_member(
        self, months_old=None, maturity="production-ready", **kwargs
    ) -> Member:
        """Writes a member in the temporary DAO. If months_old is given,
        the GitHub repository was created that many months ago."""
        member = Member(
            name="mock-qiskit",
            url="https://github.com/MockQiskit/mock-qiskit",
            description="Mock description for repo",
            license="Apache 2.0",
            maturity=maturity,
            **kwargs,
        )
        if months_old is not None:
            member.github = GitHubData(
                owner="MockQiskit",
                repo="mock-qiskit",
                created_at=date.today() - relativedelta(months=months_old),
            )
        self.cli_members.dao.write(member)
        return member

    def status_after_update(self, exclude=None, **kwargs):
        """Adds a member, runs update_status, and returns the resulting status"""
        member = self.add_member(**kwargs)
        self.cli_members.update_status(exclude=exclude)
        return self.cli_members.dao[member.name_id].status

    # the two statuses that are not derived here, so every caller that updates every
    # member excludes them. See `CliMembers.update_status`
    GOVERNED_ELSEWHERE = ("qiskit-project", "alumni")


class TestUpdateStatus(UpdateStatusTestCase):
    """Tests for CliMembers.update_status"""

    def test_very_early_project(self):
        """A repository younger than 3 months is a "Very Early Project" """
        self.assertEqual(self.status_after_update(months_old=2), "Very Early Project")

    def test_early_project(self):
        """A repository between 3 and 12 months old is an "Early Project" """
        self.assertEqual(self.status_after_update(months_old=10), "Early Project")

    def test_three_months_old_is_early_project(self):
        """The "Very Early Project" status ends at 3 months"""
        self.assertEqual(self.status_after_update(months_old=3), "Early Project")

    def test_old_project_has_no_age_status(self):
        """A repository older than 12 months is a regular member (status None)"""
        self.assertIsNone(self.status_after_update(months_old=12))

    def test_no_created_at(self):
        """Without member.github.created_at there is no age-derived status"""
        self.assertIsNone(self.status_after_update())

    def test_age_status_is_recomputed(self):
        """An outdated age-derived status is removed"""
        self.assertIsNone(
            self.status_after_update(months_old=30, status="Very Early Project")
        )

    def test_unmaintained(self):
        """An `as-is` project is "Unmaintained" """
        self.assertEqual(self.status_after_update(maturity="as-is"), "Unmaintained")

    def test_deprecated_is_unmaintained(self):
        """A `deprecated` project is "Unmaintained" too"""
        self.assertEqual(
            self.status_after_update(maturity="deprecated"), "Unmaintained"
        )

    def test_unmaintained_takes_precedence_over_age(self):
        """`as-is` is a stronger signal than the age of the repository"""
        self.assertEqual(
            self.status_after_update(months_old=2, maturity="as-is"), "Unmaintained"
        )

    def test_unmaintained_is_recomputed(self):
        """An outdated "Unmaintained" status is removed"""
        self.assertIsNone(self.status_after_update(status="Unmaintained"))

    def test_qiskit_project_is_not_updated(self):
        """ "Qiskit Project" is governed differently, so it is not age-derived"""
        self.assertEqual(
            self.status_after_update(
                months_old=2, status="Qiskit Project", exclude=self.GOVERNED_ELSEWHERE
            ),
            "Qiskit Project",
        )

    def test_alumni_is_not_updated(self):
        """Alumni projects stay alumni, no matter how young they are"""
        self.assertEqual(
            self.status_after_update(
                months_old=2, status="Alumni", exclude=self.GOVERNED_ELSEWHERE
            ),
            "Alumni",
        )

    def test_early_projects_share_one_table(self):
        """Both early statuses are listed in a single docs/assets/early-projects.md table"""
        self.add_member(months_old=2)
        self.add_member(months_old=10)
        self.add_member(months_old=30)
        self.cli_members.update_status()

        # pylint: disable=protected-access
        projects = self.cli_members._all_projects_classifications("status")["status"]
        self.cli_members.update_assets_status(projects)

        table = (self.path / "docs" / "assets" / "early-projects.md").read_text()
        self.assertIn("There are 2 projects with these statuses", table)
        self.assertIn("| Project | Status | Repository created | Age (months) |", table)
        # youngest project first
        statuses = [
            line.split("|")[2].strip()
            for line in table.splitlines()
            if line.strip().startswith("| [")
        ]
        self.assertEqual(statuses, ["Very Early Project", "Early Project"])
        self.assertFalse((self.path / "docs" / "assets" / "early-project.md").exists())


class TestUpdateStatusXfails(UpdateStatusTestCase):
    """An explained check up (check.xfailed) does not affect the status of a project,
    unless the explanation expired (check.xfailed_until)"""

    def member_with_xfail(self, **xfail_kwargs):
        """A member failing check up 001 since yesterday, with an explanation for it"""
        member = self.add_member()
        member.checks = {
            "001": CheckData(
                "001",
                since=date.today() - timedelta(days=1),
                xfailed="the license is fine",
                **xfail_kwargs,
            )
        }
        self.cli_members.dao.write(member)
        return member

    def test_valid_xfail_does_not_affect_the_status(self):
        """An explained check up, still within its expiration date, is ignored"""
        member = self.member_with_xfail(xfailed_until=date.today() + timedelta(days=30))
        self.cli_members.update_status()
        self.assertIsNone(self.cli_members.dao[member.name_id].status)

    def test_xfail_expiring_today_does_not_affect_the_status(self):
        """The explanation is valid during the whole xfailed_until day"""
        member = self.member_with_xfail(xfailed_until=date.today())
        self.cli_members.update_status()
        self.assertIsNone(self.cli_members.dao[member.name_id].status)

    def test_xfail_without_expiration_does_not_affect_the_status(self):
        """An explanation without an expiration date is ignored forever"""
        member = self.member_with_xfail()
        self.cli_members.update_status()
        self.assertIsNone(self.cli_members.dao[member.name_id].status)

    def test_expired_xfail_affects_the_status(self):
        """Once the explanation expired, the check up counts for the status again"""
        member = self.member_with_xfail(xfailed_until=date.today() - timedelta(days=1))
        self.cli_members.update_status()
        self.assertEqual(self.cli_members.dao[member.name_id].status, "Alumni")


class TestUpdateStatusCheckups(UpdateStatusTestCase):
    """A failing check up, and how much of its cure period is left,
    decides between "Under revision" and "Alumni"."""

    def test_expired_cure_period_is_alumni(self):
        """An expired cure period moves the project to "Alumni" """
        member = self.add_member()
        member.checks = {
            "001": CheckData("001", since=date.today() - timedelta(days=1))
        }
        self.cli_members.dao.write(member)
        self.cli_members.update_status()
        self.assertEqual(self.cli_members.dao[member.name_id].status, "Alumni")

    def test_under_revision_takes_precedence(self):
        """A pending check up is more important than the age of the repository"""
        member = self.add_member(months_old=2)
        member.checks = {"001": CheckData("001", since=date.today())}
        self.cli_members.dao.write(member)
        self.cli_members.update_status()
        self.assertEqual(
            self.cli_members.dao[member.name_id].status,
            "Under revision",
        )


class TestUpdateStatusInfiniteCurePeriod(UpdateStatusTestCase):
    """A check up with a negative cure_period_in_days ([P10] states -1 instead of taking
    the default of its importance) keeps the project "Under revision" forever, but never
    retires it."""

    def status_with_p10_failing_since(self, days_ago):
        """Adds a member failing [P10] since `days_ago` days ago and updates its status"""
        member = self.add_member()
        member.checks = {
            "P10": CheckData("P10", since=date.today() - timedelta(days=days_ago))
        }
        self.cli_members.dao.write(member)
        self.cli_members.update_status()
        return self.cli_members.dao[member.name_id].status

    def test_fresh_failure_is_under_revision(self):
        """The check up is pending, like any other"""
        self.assertEqual(self.status_with_p10_failing_since(1), "Under revision")

    def test_old_failure_is_still_not_alumni(self):
        """No matter how long it has been failing, the cure period never expires"""
        self.assertEqual(self.status_with_p10_failing_since(10_000), "Under revision")

    def test_the_importance_can_still_be_excluded(self):
        """An infinite cure period does not override the exclusion by importance"""
        member = self.add_member()
        member.checks = {
            "P10": CheckData("P10", since=date.today() - timedelta(days=10_000))
        }
        self.cli_members.dao.write(member)
        self.cli_members.update_status(exclude="recommendation")
        self.assertIsNone(self.cli_members.dao[member.name_id].status)


class TestUpdateStatusExclusions(UpdateStatusTestCase):
    """`exclude` names check up importances, check up categories and membership statuses.
    See `CliMembers.update_status`"""

    # [G07] is a STRONG-RECOMMENDATION in the ACTIVITY category
    # [P10] is a RECOMMENDATION in the BEST-PRACTICE category
    def member_failing(self, checkup_id):
        """A member failing `checkup_id` since yesterday"""
        member = self.add_member()
        member.checks = {
            checkup_id: CheckData(checkup_id, since=date.today() - timedelta(days=1))
        }
        self.cli_members.dao.write(member)
        return member

    def status_with(self, checkup_id, exclude):
        """The status of a member failing `checkup_id`, after excluding `exclude`"""
        member = self.member_failing(checkup_id)
        self.cli_members.update_status(exclude=exclude)
        return self.cli_members.dao[member.name_id].status

    def test_a_pending_checkup_is_under_revision(self):
        """The baseline: nothing excluded"""
        self.assertEqual(self.status_with("G07", exclude=None), "Under revision")

    def test_exclude_by_importance(self):
        """The importance of the check up"""
        self.assertIsNone(self.status_with("G07", "strong-recommendation"))
        self.assertEqual(self.status_with("G07", "recommendation"), "Under revision")

    def test_exclude_by_category(self):
        """The category of the check up"""
        self.assertIsNone(self.status_with("G07", "activity"))
        self.assertEqual(self.status_with("G07", "oss"), "Under revision")

    def status_of_excluded(self, status, exclude):
        """The status of a project already in `status` and failing [G07], after `exclude`"""
        member = self.member_failing("G07")
        self.cli_members.dao.update(member.name_id, status=status)
        self.cli_members.update_status(exclude=exclude)
        return self.cli_members.dao[member.name_id].status

    def test_exclude_by_status(self):
        """A membership status leaves the projects that are already in it alone"""
        self.assertEqual(
            self.status_of_excluded("Qiskit Project", "qiskit-project"),
            "Qiskit Project",
        )
        self.assertEqual(self.status_of_excluded("Alumni", "alumni"), "Alumni")

    def test_a_status_that_is_not_excluded_is_not_protected(self):
        """This is why every caller that updates every member excludes these two: without
        it, a pending check up drags them into "Under revision" like any other project
        """
        self.assertEqual(
            self.status_of_excluded("Qiskit Project", None), "Under revision"
        )
        self.assertEqual(self.status_of_excluded("Alumni", None), "Under revision")

    def test_several_values_at_once(self):
        """What Fire hands over for `-e "a, b, c"`"""
        self.assertIsNone(
            self.status_with("P10", ("activity", "best-practice", "alumni"))
        )

    def test_the_values_are_slugified(self):
        """`-e "Best Practice"`, `-e best_practice` and `-e BEST-PRACTICE` are the same"""
        for spelling in ["Best Practice", "best_practice", "BEST-PRACTICE"]:
            with self.subTest(exclude=spelling):
                self.assertIsNone(self.status_with("P10", spelling))

    def test_an_unknown_value_excludes_nothing(self):
        """A value that names no importance, category or status is simply not a match"""
        self.assertEqual(self.status_with("G07", "not-a-thing"), "Under revision")


class TestUpdateCheckupsExclusions(UpdateStatusTestCase):
    """`exclude` leaves the projects already in one of those statuses alone.
    See `CliMembers.update_checkups`"""

    def checks_after_update(self, status, exclude):
        """The check ups of a project in `status` after running [014] on it.

        The member description is too long, so [014] is recorded unless the project is
        left out of the run."""
        member = self.add_member()
        member.description = "banana " * 30
        member.status = status
        self.cli_members.dao.write(member)
        with redirect_stdout(io.StringIO()):
            self.cli_members.update_checkups(
                checker="test_description.py::test_description_len_135", exclude=exclude
            )
        return set(self.cli_members.dao[member.name_id].checks)

    def test_the_checkups_run_by_default(self):
        """The baseline: nothing excluded"""
        self.assertEqual(self.checks_after_update("Alumni", exclude=None), {"014"})

    def test_an_excluded_status_is_left_alone(self):
        """The usual call: alumni keep the check up data they were retired with"""
        self.assertEqual(self.checks_after_update("Alumni", exclude="alumni"), set())

    def test_another_status_is_not_affected(self):
        """Only the excluded statuses are skipped"""
        self.assertEqual(
            self.checks_after_update("Under revision", exclude="alumni"), {"014"}
        )

    def test_the_values_are_slugified(self):
        """`-e "Qiskit Project"` and `-e qiskit-project` are the same"""
        for spelling in ["Qiskit Project", "qiskit-project", "QISKIT_PROJECT"]:
            with self.subTest(exclude=spelling):
                self.assertEqual(
                    self.checks_after_update("Qiskit Project", spelling), set()
                )


class TestUpdateCheckupsKeepsSince(UpdateStatusTestCase):
    """`member.checks.<id>.since` is the day a check up started failing, so a run that finds
    it still failing has to keep it. See `Member.update_checkups`"""

    CHECKER = "test_description.py::test_description_len_135"

    def failing_member(self):
        """A member whose description is too long, so [014] is recorded on it"""
        member = self.add_member()
        member.description = "banana " * 30
        self.cli_members.dao.write(member)
        self.update_checkups()
        return member.name_id

    def update_checkups(self):
        """Runs only the check up this test case is about"""
        with redirect_stdout(io.StringIO()):
            self.cli_members.update_checkups(checker=self.CHECKER)

    def checkup(self, name_id):
        """The [014] check up as it is recorded in the member file"""
        return self.cli_members.dao[name_id].checks["014"]

    def failing_for(self, name_id, days, xfailed_until=None):
        """Backdates the check up, as one recorded `days` ago, optionally with an explanation
        valid until `xfailed_until`"""
        member = self.cli_members.dao[name_id]
        member.checks["014"].since = date.today() - timedelta(days=days)
        if xfailed_until:
            member.checks["014"].xfailed = "explained: shortened upstream"
            member.checks["014"].xfailed_until = xfailed_until
        self.cli_members.dao.write(member)

    def test_a_plain_failure_keeps_its_since(self):
        """The baseline: a check up that keeps failing keeps the date it started failing"""
        name_id = self.failing_member()
        self.failing_for(name_id, 100)
        self.update_checkups()
        self.assertEqual(
            self.checkup(name_id).since, date.today() - timedelta(days=100)
        )

    def test_an_explained_failure_keeps_its_since(self):
        """A valid explanation does not erase the date: the report carries the explanation
        and not the date, so the one in the member file is the only one there is"""
        name_id = self.failing_member()
        self.failing_for(name_id, 100, xfailed_until=date.today() + timedelta(days=30))
        self.update_checkups()
        self.assertEqual(
            self.checkup(name_id).since, date.today() - timedelta(days=100)
        )

    def test_the_cure_period_does_not_restart_after_an_explanation(self):
        """What the date is for: when the explanation expires, the cure period is counted
        from the original failure and not from the day the explanation ran out"""
        name_id = self.failing_member()
        self.failing_for(name_id, 100, xfailed_until=date.today() + timedelta(days=3))
        self.update_checkups()  # a run while the explanation is still valid

        member = self.cli_members.dao[name_id]
        member.checks["014"].xfailed_until = date.today() - timedelta(days=1)
        self.cli_members.dao.write(member)
        self.update_checkups()  # and one after it expired

        checkup = self.checkup(name_id)
        self.assertEqual(checkup.since, date.today() - timedelta(days=100))
        self.assertTrue(checkup.cure_period_expired)


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
            checkup_id: CheckData(checkup_id, since=date.today(), xfailed=xfailed)
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
            checkup_id: CheckData(
                checkup_id,
                since=date.today() - timedelta(days=days_ago),
                xfailed=xfailed,
                xfailed_until=xfailed_until,
                discussion=discussion,
            )
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
        """[P10] states a cure period of -1 of its own"""
        self.assertTrue(self.row_of("P10", days_ago=10_000).endswith("| &infin; |"))

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
            member.checks = {"G07": CheckData("G07", since=date.today())}
            self.cli_members.dao.write(member)
        self.cli_members.update_assets_checkups()
        body = (self.path / "docs" / "assets" / "checkup.md").read_text()
        return body.split("{ #G07 }")[1].split("\n## ")[0]

    def failing_count(self):
        """The `Failing` column of the [G07] row of the summary table"""
        summary = json.loads(
            (self.path / "docs" / "assets" / "checkup.json").read_text()
        )
        return next(r for r in summary if "[G07]" in r["Check up"])["Failing"]

    def test_only_members_are_counted(self):
        """Two alumni and one member: the headline is about the member"""
        section = self.section("Alumni", None, "Alumni")
        self.assertIn("There is 1 project failing this check up", section)
        self.assertIn('??? info "2 Alumni projects also failed', section)
        self.assertEqual(self.failing_count(), 1)

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
        self.assertEqual(self.failing_count(), 0)

    def test_no_alumni_no_list(self):
        """Nothing extra when no alumni ever failed it"""
        section = self.section(None)
        self.assertIn("There is 1 project failing this check up", section)
        self.assertNotIn("Alumni", section)
