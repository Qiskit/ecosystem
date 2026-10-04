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


"""Tests for entities."""

import tempfile
import shutil
from pathlib import Path
from unittest import TestCase

from ecosystem.badge import BadgeData
from ecosystem.check import CheckData
from ecosystem.dao import DAO, dumps
from ecosystem.github import GitHubData
from ecosystem.pypi import PyPIData
from ecosystem.python import PythonData
from ecosystem.requirements import RequirementsData
from ecosystem.member import Member


def get_main_repo() -> Member:
    """Return main mock repo."""
    return Member(
        name="mock-qiskit-terra-with-success-dev-test",
        url="https://github.com/MockQiskit/mock-qiskit-wsdt.terra",
        description="Mock description for repo. wsdt",
        license="Apache 2.0",
        labels=["mock", "tests", "wsdt"],
        website="https://example.org",
    )


class TestTheFileLayout(TestCase):
    """The order the tables of a member file are written in.

    `toml` puts every `[[array]]` above every `[table]`, whatever the dict says, so without
    `ecosystem.dao.dumps` a member's `[[pypi]]` would sit above its `[github]` and every
    file would be reshuffled by the next update.
    """

    @staticmethod
    def headers(member):
        """The table headers of that member, in the order they are written"""
        return [
            line.strip()
            for line in dumps(member.to_dict()).splitlines()
            if line.startswith("[")
        ]

    @staticmethod
    def member(**kwargs):
        """A member with a repository, a badge and a check up"""
        return Member(
            name="Banana",
            url="https://github.com/banana-org/banana",
            maturity="experimental",
            github=GitHubData(owner="banana-org", repo="banana"),
            badge=BadgeData(url="https://bit.ly/banana"),
            checks={"G07": CheckData("G07")},
            **kwargs,
        )

    def test_the_repository_comes_before_the_packages(self):
        """Which is where a reader of a member file looks for it"""
        self.assertEqual(
            ["[github]", "[badge]", "[[pypi]]", "[checks.G07]"],
            self.headers(self.member(pypi=[PyPIData(package_name="banana")])),
        )

    def test_every_package_section_sits_between_the_badge_and_the_check_ups(self):
        """In the order `SECTION_ORDER` gives, whatever order the member was built in"""
        member = self.member(
            python=[PythonData(package_name="banana", source=["pyproject.toml"])],
            requirements=[RequirementsData(file="requirements.txt")],
            pypi=[PyPIData(package_name="banana")],
        )
        self.assertEqual(
            [
                "[github]",
                "[badge]",
                "[[pypi]]",
                "[[python]]",
                "[[requirements]]",
                "[checks.G07]",
            ],
            self.headers(member),
        )

    def test_the_scalars_stay_at_the_top(self):
        """They are what the submission said, and the tables are what was read"""
        text = dumps(self.member().to_dict())
        self.assertTrue(text.startswith('name = "Banana"'))

    def test_a_member_with_no_tables_is_just_its_values(self):
        """Nothing to arrange, and no empty section left behind"""
        member = Member(
            name="Banana", url="https://github.com/o/r", maturity="experimental"
        )
        self.assertEqual([], self.headers(member))


class TestDao(TestCase):
    """Tests repository related functions."""

    def setUp(self) -> None:
        self.path = Path(tempfile.mkdtemp())
        self.path.mkdir(exist_ok=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.path)

    def test_repository_insert_and_delete(self):
        """Tests repository."""
        main_repo = get_main_repo()
        dao = DAO(self.path)

        # insert entry
        dao.write(main_repo)
        fetched_repo = dao.get_by_url(str(main_repo.url))
        self.assertEqual(main_repo, fetched_repo)

        # delete entry
        dao.delete(main_repo.name_id)
        dao.refresh_files()
        self.assertEqual(0, len(dao.get_all()))
