"""Test types for specific repository."""


# pylint: disable=too-few-public-methods
class TestType:
    """Test types for specific repository.

    Types:
    - STABLE_COMPATIBLE - compatibility of repository with stable branch of qiskit-terra
    - DEV_COMPATIBLE - compatibility if repository with dev/main branch of qiskit-terra
    - STANDARD - regular tests that comes with repo
    - LAST_WORKING_VERSION - last stable working version of qiskit
    """

    STABLE_COMPATIBLE: str = "STABLE_COMPATIBLE"
    DEV_COMPATIBLE: str = "DEV_COMPATIBLE"
    STANDARD: str = "STANDARD"
    LAST_WORKING_VERSION: str = "LAST_WORKING_VERSION"

    @classmethod
    def all(cls):
        """Return all test types"""
        return [
            cls.STANDARD,
            cls.DEV_COMPATIBLE,
            cls.STABLE_COMPATIBLE,
            cls.LAST_WORKING_VERSION,
        ]
