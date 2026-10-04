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

from ecosystem.github import GitHubData
from ecosystem.julia import JuliaData
from ecosystem.member import Member
from ecosystem.pypi import PyPIData
from ecosystem.python import PythonData
from ecosystem.requirements import RequirementsData
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

        details = member.checks["Q04"].details
        self.assertIn("requirements-qiskit.txt", details)
        self.assertIn(">=1.3.0rc1", details)

    def test_the_failure_names_the_distribution_it_read(self):
        """For a distribution the name is what points at one of several"""
        member = self.pypi(requires_qiskit=">=2.0")
        self.records(Q03, member)

        self.assertIn("banana-compiler", member.checks["Q03"].details)


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
