from .base import MemberValidator


def all_subclasses(cls):
    return set(cls.__subclasses__()).union(
        [s for c in cls.__subclasses__() for s in all_subclasses(c)]
    )


def validate_member(member):
    for subclass in all_subclasses(MemberValidator):
        sc = subclass()
        sc.validate(member)
        return sc
