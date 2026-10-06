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
"""Tests for the qiskit-dependency check ups of ecosystem/validation/checkup_general.py

[Q02], [Q03] and [Q04] ask one question each of every place a project can declare its
qiskit dependency. They replaced two sets of three section-shaped check ups
([PQ2]/[S01]/[R01] and [P10]/[S02]/[R02]), so what each case here fixes is that the same
answer comes out of a `[[pypi]]`, a `[[python]]` and a `[[requirements]]` section.

The aggregating check ups of that module ([Q20], [G00], [001]) are about what other check
ups reported, so they belong to a run rather than to a member and are not covered here.
"""

# the test methods are named after the check up they cover, like [Q03], and a name
# that states what the case asserts needs no docstring saying it again
# pylint: disable=invalid-name,missing-function-docstring

from datetime import date

from ecosystem.check import CheckData
from ecosystem.github import GitHubData
from ecosystem.julia import JuliaData
from ecosystem.member import Member
from ecosystem.pypi import PyPIData
from ecosystem.python import PythonData
from ecosystem.requirements import RequirementsData
from tests.common import record
from tests.validation import CheckupTestCase

Q02 = "checkup_general.py::checkup_Q02"
Q03 = "checkup_general.py::checkup_Q03"
Q04 = "checkup_general.py::checkup_Q04"


class QiskitDependencyTestCase(CheckupTestCase):
    """The sections are built the way a member file is read back: stored values only, so
    nothing here reaches the network.
    """

    @staticmethod
    def member(**sections):
        """A member declaring its qiskit dependency in the given sections"""
        member = Member(
            name="banana", url="https://github.com/qiskit-community/banana-repo"
        )
        member.github = GitHubData(owner="qiskit-community", repo="banana-repo")
        for name, section in sections.items():
            setattr(member, name, [section])
        return member

    @classmethod
    def pypi(cls, **kwargs):
        """A member whose published distribution carries the requirement"""
        return cls.member(pypi=PyPIData(package_name="banana-compiler", **kwargs))

    @classmethod
    def python(cls, **kwargs):
        """A member whose repository declares the requirement in a manifest"""
        return cls.member(
            python=PythonData(
                package_name="banana-compiler",
                source=["pyproject.toml"],
                deferred=[],
                **kwargs,
            )
        )

    @classmethod
    def requirements(cls, file="requirements.txt", **kwargs):
        """A member whose repository declares the requirement in a file"""
        return cls.member(requirements=RequirementsData(file=file, **kwargs))

    def assert_same_everywhere(self, checker, expected, **kwargs):
        """The check up answers the same from each kind of section"""
        for build in (self.pypi, self.python, self.requirements):
            with self.subTest(section=build.__name__):
                self.assert_records(checker, expected, build(**kwargs))


class TestQ02(QiskitDependencyTestCase):
    """[Q02] wants every declaration to allow Qiskit v2"""

    def test_a_v2_compatible_requirement_passes(self):
        self.assert_same_everywhere(Q02, set(), requires_qiskit=">=1.4,<3")

    def test_a_v1_only_requirement_is_recorded(self):
        self.assert_same_everywhere(Q02, {"Q02"}, requires_qiskit="==1.4")

    def test_a_declaration_with_nothing_to_resolve_is_skipped(self):
        """A stored table with no flag is not a failure to be compatible"""
        self.assert_records(
            Q02, set(), self.requirements(compatible_with_qiskit_v2=None)
        )


class TestQ03(QiskitDependencyTestCase):
    """[Q03] wants a cap on the qiskit major version, wherever it is declared"""

    def test_a_capped_requirement_passes(self):
        self.assert_same_everywhere(Q03, set(), requires_qiskit=">=2.0,<3")

    def test_an_uncapped_requirement_is_recorded(self):
        """An uncapped requirement lets the next major version in untested"""
        self.assert_same_everywhere(Q03, {"Q03"}, requires_qiskit=">=2.0")

    def test_a_tilde_requirement_passes(self):
        """`~=2.1.0` caps the major version without saying so"""
        self.assert_same_everywhere(Q03, set(), requires_qiskit="~=2.1.0")


class TestQ04(QiskitDependencyTestCase):
    """[Q04] wants the dependency written against a released version"""

    def test_a_released_version_passes(self):
        self.assert_same_everywhere(Q04, set(), requires_qiskit="<3,>=1.3.0")

    def test_a_pre_release_is_recorded(self):
        """`Qiskit/benchpress` and its `>=1.3.0rc1` are what this was written for"""
        self.assert_same_everywhere(Q04, {"Q04"}, requires_qiskit=">=1.3.0rc1")

    def test_a_beta_is_recorded_too(self):
        """Any pre-release, not just a release candidate"""
        self.assert_records(Q04, {"Q04"}, self.python(requires_qiskit="<3,>=2.0.0b1"))


class TestEveryDeclarationIsRead(QiskitDependencyTestCase):
    """A member can declare its dependency more than once, and all of them count"""

    def test_a_failure_in_one_file_is_not_rescued_by_another(self):
        """The shape `Qiskit/qiskit-cpp` has: a bare `qiskit` beside the real pin"""
        member = self.member()
        member.requirements = [
            RequirementsData(file="requirements-dev.txt", requires_qiskit=">=0"),
            RequirementsData(file="requirements.txt", requires_qiskit="~=2.1.0"),
        ]
        self.assert_records(Q03, {"Q03"}, member)

    def test_a_release_and_a_repository_are_judged_apart(self):
        """A published release can be capped while the source it is built from is not"""
        member = self.member(
            pypi=PyPIData(package_name="banana-compiler", requires_qiskit=">=2.0,<3"),
            python=PythonData(
                package_name="banana-source",
                source=["pyproject.toml"],
                deferred=[],
                requires_qiskit=">=2.0",
            ),
        )
        self.assert_records(Q03, {"Q03"}, member)

    def test_the_failure_names_where_it_was_read(self):
        """A maintainer reading the project page needs to know what to edit"""
        member = self.requirements(
            file="requirements-qiskit.txt", requires_qiskit=">=1.3.0rc1"
        )
        self.records(Q04, member)

        details = record(member, "Q04").details
        self.assertIn("requirements-qiskit.txt", details)
        self.assertIn(">=1.3.0rc1", details)

    def test_the_failure_names_the_distribution_it_read(self):
        """For a distribution the name is what points at one of several"""
        member = self.pypi(requires_qiskit=">=2.0")
        self.records(Q03, member)

        self.assertIn("banana-compiler", record(member, "Q03").details)


class TestAMemberWithNoQiskitDependency(QiskitDependencyTestCase):
    """Nothing to read is not a failure to write it well"""

    def test_nothing_is_recorded(self):
        for checker in (Q02, Q03, Q04):
            with self.subTest(checker=checker):
                self.assert_records(checker, set(), self.member())

    def test_a_section_that_does_not_depend_on_qiskit_is_skipped(self):
        """Most members: a distribution with no qiskit among its dependencies"""
        for checker in (Q02, Q03, Q04):
            with self.subTest(checker=checker):
                self.assert_records(checker, set(), self.pypi())

    def test_a_julia_range_is_not_read_as_a_specifier(self):
        """`requires_qiskit` means something else there, and is not PEP 440"""
        self.assert_records(
            Q04,
            set(),
            self.member(
                julia=JuliaData(
                    package_name="Banana", registry="General", requires_qiskit=["0.1.0"]
                )
            ),
        )


class TestARecordPerPlace(QiskitDependencyTestCase):
    """A check up that reads several places keeps one record per place.

    Which is what lets a project be excused in one of them and keep counting in another:
    `Qiskit/qiskit-cpp` asks for an uncapped qiskit in `requirements-dev.txt`, above its
    black/ruff pins, and in `requirements.txt`, and only the first one is a lint file.
    """

    EXPLANATION = "lint pins, qiskit-cpp#167"

    def two_files(self, dev=">=0", main=">=2.1.0"):
        """A member declaring qiskit in a lint file and in the real one"""
        member = self.member()
        member.requirements = [
            RequirementsData(file="requirements-dev.txt", requires_qiskit=dev),
            RequirementsData(file="requirements.txt", requires_qiskit=main),
        ]
        return member

    def stored(self, member, **kwargs):
        """Gives the member a stored record, as a member file would have"""
        member.checks["Q03"] = [CheckData("Q03", **kwargs)]
        return member

    def test_each_failing_place_gets_its_own_record(self):
        member = self.two_files()
        self.records(Q03, member)

        self.assertEqual(
            ["requirements:requirements-dev.txt", "requirements:requirements.txt"],
            sorted(stored.subtest for stored in member.checks["Q03"]),
        )

    def test_the_details_of_each_record_name_its_own_place(self):
        """The old shape kept the last place only, so one of the two was lost"""
        member = self.two_files()
        self.records(Q03, member)

        self.assertEqual(
            ["requirements-dev.txt", "requirements.txt"],
            sorted(
                stored.details.split(" in ")[1].split(" allows")[0]
                for stored in member.checks["Q03"]
            ),
        )

    def test_an_explanation_for_one_place_leaves_the_other_failing(self):
        """The whole point: an explanation is about the file it was written for"""
        member = self.stored(
            self.two_files(),
            subtest="requirements:requirements-dev.txt",
            since=date(2026, 1, 5),
            xfailed=self.EXPLANATION,
            xfailed_until=date(2027, 3, 31),
        )
        self.records(Q03, member)

        explained = record(member, "Q03", "requirements:requirements-dev.txt")
        failing = record(member, "Q03", "requirements:requirements.txt")
        self.assertEqual(self.EXPLANATION, explained.xfailed)
        self.assertTrue(explained.xfail_applies)
        self.assertIsNone(failing.xfailed)
        self.assertEqual([failing], member.failing_checkups)
        self.assertEqual([explained], member.xfails)

    def test_each_place_keeps_its_own_cure_period(self):
        """A place that started failing later is not inheriting the other's deadline"""
        member = self.two_files()
        member.checks["Q03"] = [
            CheckData(
                "Q03", subtest="requirements:requirements.txt", since=date(2026, 4, 1)
            )
        ]
        self.records(Q03, member)

        self.assertEqual(
            date(2026, 4, 1),
            record(member, "Q03", "requirements:requirements.txt").since,
        )
        self.assertEqual(
            CheckData.today,
            record(member, "Q03", "requirements:requirements-dev.txt").since,
        )

    def test_an_explained_place_that_got_fixed_is_dropped(self):
        """The explanation does not keep a record alive once the file is capped"""
        member = self.stored(
            self.two_files(dev="~=2.1.0"),
            subtest="requirements:requirements-dev.txt",
            since=date(2026, 1, 5),
            xfailed=self.EXPLANATION,
        )
        self.records(Q03, member)

        self.assertEqual(
            ["requirements:requirements.txt"],
            [stored.subtest for stored in member.checks["Q03"]],
        )

    def test_a_specific_explanation_wins_over_a_blanket_one(self):
        """Both can be stored at once: the blanket one is what a migrated record looks like"""
        member = self.two_files()
        member.checks["Q03"] = [
            CheckData("Q03", since=date(2026, 1, 5), xfailed="about the repository"),
            CheckData(
                "Q03",
                subtest="requirements:requirements-dev.txt",
                since=date(2026, 1, 5),
                xfailed=self.EXPLANATION,
            ),
        ]
        self.records(Q03, member)

        self.assertEqual(
            self.EXPLANATION,
            record(member, "Q03", "requirements:requirements-dev.txt").xfailed,
        )
        self.assertEqual(
            "about the repository",
            record(member, "Q03", "requirements:requirements.txt").xfailed,
        )

    def test_a_record_that_names_no_place_explains_all_of_them(self):
        """What a record written before the places were recorded looks like"""
        member = self.stored(
            self.two_files(), since=date(2026, 1, 5), xfailed="agreed upstream"
        )
        self.records(Q03, member)

        self.assertEqual(2, len(member.checks["Q03"]))
        self.assertTrue(all(stored.xfail_applies for stored in member.checks["Q03"]))
        self.assertEqual([], member.failing_checkups)
