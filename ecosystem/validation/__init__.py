"""Validation module"""

from ecosystem.error_handling import logger

from .base import MemberValidator
from .labels import *

# pylint: disable=pointless-string-statement

"""  
TODO json:
 - check no member repetition
 - check against schema
TODO member:
 - check license unification naming
 - check that is has a category (or Other, otherwise)
 - if label "research" check if there is a paper
 - if cannot be fixed, collect an "issues" property in the member toml
 - check description length
 - check "website" is not the github repo or similar
"""

def _all_subclasses(cls):
    return set(cls.__subclasses__()).union(
        [s for c in cls.__subclasses__() for s in _all_subclasses(c)]
    )


def validate_member(member):
    """Runs all the validation for a member"""
    passing = []
    not_passing = []
    for subclass in _all_subclasses(MemberValidator):
        sc = subclass()
        validation_name = (
            f"{sc.__class__.__module__.replace('ecosystem.validation.','')}"
            f".{str(sc.__class__.__name__)}"
        )
        try:
            sc.validate(member)
            passing.append(validation_name)
        except NotImplementedError:
            continue
        except AssertionError as assertion:
            logger.error(str(assertion))
            not_passing.append(validation_name)
    return passing, not_passing
