"""TODO General criteria

[000] Build on, interface with, or extend the Qiskit SDK in a meaningful way.
[Q20] Be compatible with the Qiskit SDK v2.0 (or newer).
[001] Have an OSI-approved open-source license (preferably Apache 2.0 or MIT).
[COC] Adhere to the Qiskit code of conduct.
[G00] Have maintainer activity within the last 6 months, such as a commit.
[P20] New projects should be compatible with the V2 primitives.

"""

# pylint: disable=invalid-name

import pytest
from ecosystem.check import CheckData


def must_pass_all_requierements(requierements, failed_checkups, msg):
    """check for all the requierements to see if they are still in the cure period"""
    fail = []
    skip = []
    for failure, report in failed_checkups.items():
        if failure not in requierements:
            continue
        checkup = CheckData.from_report(report)
        if checkup.cure_period_in_days < checkup.days_since_failure:
            fail.append(checkup)
        else:
            skip.append(checkup)
    if fail:
        pytest.fail(msg + ": " + " ".join([c.id for c in fail]))
    if skip:
        pytest.skip("Still in the cure period: " + " ".join([c.id for c in fail]))


@pytest.mark.order(after=["test_pypi.py::test_PQ2"])
def test_Q20(request, pytestconfig):
    """Be compatible with the Qiskit SDK v2 or newer"""
    requierements = request.node.get_closest_marker("order").kwargs["after"]
    must_pass_all_requierements(
        requierements,
        pytestconfig.failed_checkups,
        "Not compatible with the Qiskit SDK v2 or newer",
    )


@pytest.mark.order(after=["test_github.py::test_G05"])
def test_001(request, pytestconfig):
    """Have a clear support expectation and, if actively maintained,
    show signs of that activity."""
    requierements = request.node.get_closest_marker("order").kwargs["after"]
    must_pass_all_requierements(
        requierements,
        pytestconfig.failed_checkups,
        "The project is probably abandoned",
    )
