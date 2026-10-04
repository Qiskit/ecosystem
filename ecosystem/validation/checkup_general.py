# This code is part of Qiskit.
#
# (C) Copyright IBM 2023.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at https://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.


"""TODO General criteria

[000] Build on, interface with, or extend the Qiskit SDK in a meaningful way.
[Q20] Be compatible with the Qiskit SDK v2.0 (or newer).
[001] Have an OSI-approved open-source license (preferably Apache 2.0 or MIT).
[COC] Adhere to the Qiskit code of conduct.
[G00] Have maintainer activity within the last 6 months, such as a commit.
[P20] New projects should be compatible with the V2 primitives.
[Q02] Be installable with qiskit>=2.0.
[Q03] Have a cap on the major version for the qiskit dependency.
[Q04] Not depend on a pre-release of Qiskit.

"""

# pylint: disable=invalid-name

import pytest
from packaging.specifiers import SpecifierSet

from ecosystem.check import CheckData


def must_pass_all_requierements(requierements, failed_checkups, msg):
    """check for all the requierements to see if they are still in the cure period"""
    fail = []
    skip = []
    for failure, report in failed_checkups.items():
        if failure not in requierements:
            continue
        checkup = CheckData.from_report(report)
        if checkup.cure_period_expired:
            fail.append(checkup)
        else:
            skip.append(checkup)
    if fail:
        pytest.fail(msg + ": " + " ".join([f"`[{c.id}]`" for c in fail]))
    if skip:
        pytest.skip("Still in the cure period: " + " ".join([c.id for c in fail]))


@pytest.mark.order(after=["checkup_general.py::checkup_Q02"])
def checkup_Q20(request, pytestconfig):
    """Be compatible with the Qiskit SDK v2 or newer"""
    requierements = request.node.get_closest_marker("order").kwargs["after"]
    must_pass_all_requierements(
        requierements,
        pytestconfig.failed_checkups,
        "Not compatible with the Qiskit SDK v2 or newer",
    )


@pytest.mark.order(
    after=[
        "checkup_github.py::checkup_G05",
        "checkup_github.py::checkup_G07",
        "checkup_general.py::checkup_Q20",
    ]
)
def checkup_G00(request, pytestconfig):
    """Have a clear support expectation and, if actively maintained,
    show signs of that activity."""
    requierements = request.node.get_closest_marker("order").kwargs["after"]
    must_pass_all_requierements(
        requierements,
        pytestconfig.failed_checkups,
        "The project is probably abandoned",
    )


@pytest.mark.order(after=["checkup_github.py::checkup_G10"])
def checkup_001(request, pytestconfig):
    """Have an OSI-approved open-source license (preferably Apache 2.0 or MIT)"""
    requierements = request.node.get_closest_marker("order").kwargs["after"]
    must_pass_all_requierements(
        requierements,
        pytestconfig.failed_checkups,
        "A non-OSI-approved license?",
    )


def checkup_015(member):
    """URL should not be a GitHub organization url"""
    if not hasattr(member, "url"):
        pytest.skip("member.url does not exist")
    if not member.url.hostname.lower().endswith("github.com"):
        pytest.skip(f"{member.url} is not a GitHub URL")
    owner_repo = [i for i in member.url.path.split("/") if i]
    assert len(owner_repo) >= 2, f"{member.url} is a GitHub organization URL"


def qiskit_declarations(member):
    """Every qiskit dependency the member declares, and where it was read.

    A project can say which Qiskit it needs in three places, and the check ups below ask the
    same question of each: a published distribution (`[[pypi]]`), a packaging manifest in the
    repository (`[[python]]`), and a requirements file (`[[requirements]]`). They used to be
    one check up per place, `[PQ2]`/`[S01]`/`[R01]` for the compatibility and
    `[P10]`/`[S02]`/`[R02]` for the cap (all six removed with this): three copies of one
    assertion, grown one section at a time. The place is a subtest instead, so a failure still
    names what to edit.

    A member may store several of each, and every one of them is read: a qiskit requirement
    the project asks for is one somebody ends up installing, whichever file it is in.

    The Julia sections are left out, as they are in the `Qiskit requirements` table of a
    project page: their `requires_qiskit` is a range of `Qiskit.jl` releases rather than a
    PEP 440 specifier.
    """
    for package in member.pypi or []:
        if package.requires_qiskit:
            yield f"the {package.package_name} release on PyPI", package
    for package in member.python or []:
        if package.requires_qiskit:
            yield f"the {package.package_name} manifest in the repository", package
    for requirements in member.requirements or []:
        if requirements.requires_qiskit:
            yield requirements.file, requirements


def qiskit_dependencies(member):
    """`qiskit_declarations`, or a skip when the member declares no qiskit dependency"""
    declarations = list(qiskit_declarations(member))
    if not declarations:
        pytest.skip("The member declares no qiskit dependency")
    return declarations


def checkup_Q02(member, subtests):
    """Be installable with qiskit>=2.0"""
    for declared_in, section in qiskit_dependencies(member):
        with subtests.test(declared_in=declared_in):
            if section.compatible_with_qiskit_v2 is None:
                # a stored table with no flag is not a failure to be compatible
                pytest.skip(f"No compatible_with_qiskit_v2 for {declared_in}")
            assert section.compatible_with_qiskit_v2, (
                f"The qiskit requirement in {declared_in} is not compatible with "
                "Qiskit SDK v2"
            )


def checkup_Q03(member, subtests):
    """Have a cap on the major version for the qiskit dependency"""
    for declared_in, section in qiskit_dependencies(member):
        with subtests.test(declared_in=declared_in):
            assert not section.compatible_with_qiskit(3), (
                f"The qiskit requirement in {declared_in} allows a not-yet-released "
                "major version of Qiskit"
            )


def checkup_Q04(member, subtests):
    """Not depend on a pre-release of Qiskit"""
    for declared_in, section in qiskit_dependencies(member):
        with subtests.test(declared_in=declared_in):
            # `prereleases` is what the resolver reads: it is true only when one of the
            # specifiers names a pre-release, which is what turns them on for the dependency
            assert not SpecifierSet(section.requires_qiskit).prereleases, (
                f"The qiskit requirement in {declared_in} is written against a "
                f"pre-release ({section.requires_qiskit})"
            )
