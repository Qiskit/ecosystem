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
"""Tests for ecosystem/validation/checkup_pypi.py"""

# the test methods are named after the check up they cover, like [PQ2], and a name
# that states what the case asserts needs no docstring saying it again
# pylint: disable=invalid-name,missing-function-docstring

from ecosystem.member import Member
from ecosystem.pypi import PyPIData
from tests.validation import CheckupTestCase


class PyPICheckupsTestCase(CheckupTestCase):
    """The sections are built the way a member file is read back: stored values only,
    no PyPI JSON, so nothing here reaches the network.
    """

    @staticmethod
    def member(maturity="experimental", **section):
        """A member releasing one distribution to PyPI"""
        member = Member(
            name="banana",
            url="https://github.com/banana-org/banana-repo",
            maturity=maturity,
        )
        member.pypi = [PyPIData(package_name="banana", version="1.0.0", **section)]
        return member


class TestPQ2(PyPICheckupsTestCase):
    """[PQ2] wants the release to be installable beside Qiskit v2"""

    checker = "checkup_pypi.py::checkup_PQ2"

    def test_a_v2_compatible_requirement_passes(self):
        self.assert_records(
            self.checker, set(), self.member(requires_qiskit=">=1.4,<3")
        )

    def test_a_v1_only_requirement_fails(self):
        self.assert_records(self.checker, {"PQ2"}, self.member(requires_qiskit="==1.4"))

    def test_a_release_that_does_not_depend_on_qiskit_is_skipped(self):
        """No requirement is not an incompatible requirement"""
        self.assert_records(self.checker, set(), self.member())


class TestP10(PyPICheckupsTestCase):
    """[P10] wants a cap on the qiskit major version"""

    checker = "checkup_pypi.py::checkup_P10"

    def test_a_capped_requirement_passes(self):
        self.assert_records(
            self.checker, set(), self.member(requires_qiskit=">=2.0,<3")
        )

    def test_an_uncapped_requirement_fails(self):
        """An uncapped requirement lets the next major version in untested"""
        self.assert_records(self.checker, {"P10"}, self.member(requires_qiskit=">=2.0"))


class TestP11(PyPICheckupsTestCase):
    """[P11] wants a production-ready project to have released something stable"""

    checker = "checkup_pypi.py::checkup_P11"

    def test_a_stable_classifier_passes(self):
        self.assert_records(
            self.checker,
            set(),
            self.member(
                maturity="production-ready", development_status="5 - Production/Stable"
            ),
        )

    def test_only_a_beta_classifier_fails(self):
        self.assert_records(
            self.checker,
            {"P11"},
            self.member(maturity="bugfixing only", development_status="4 - Beta"),
        )

    def test_a_project_that_does_not_claim_to_be_ready_is_skipped(self):
        self.assert_records(
            self.checker, set(), self.member(development_status="4 - Beta")
        )

    def test_a_release_with_no_classifier_is_skipped(self):
        """Nothing was declared, so there is no claim to contradict"""
        self.assert_records(
            self.checker, set(), self.member(maturity="production-ready")
        )


class TestP12AndP13(PyPICheckupsTestCase):
    """[P12] wants a declared license, [P13] wants it OSI-approved"""

    def test_P12_passes_on_a_declared_license(self):
        self.assert_records(
            "checkup_pypi.py::checkup_P12", set(), self.member(license="Apache-2.0")
        )

    def test_P12_fails_when_nothing_is_declared(self):
        self.assert_records("checkup_pypi.py::checkup_P12", {"P12"}, self.member())

    def test_P13_passes_on_an_osi_approved_license(self):
        self.assert_records(
            "checkup_pypi.py::checkup_P13", set(), self.member(license="Apache-2.0")
        )

    def test_P13_fails_on_a_source_available_license(self):
        self.assert_records(
            "checkup_pypi.py::checkup_P13",
            {"P13"},
            self.member(license="PolyForm-Strict-1.0.0"),
        )

    def test_P13_has_nothing_to_judge_without_a_license(self):
        """[P12] is the one that complains about a missing license"""
        self.assert_records("checkup_pypi.py::checkup_P13", set(), self.member())


class TestAMemberThatReleasesNothing(PyPICheckupsTestCase):
    """The section is absent, so every check up in the file has nothing to read"""

    def test_nothing_is_recorded(self):
        member = Member(name="banana", url="https://github.com/banana-org/banana-repo")
        self.assert_records("checkup_pypi.py", set(), member)
