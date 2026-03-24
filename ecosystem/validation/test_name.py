"""Name Validations"""


def test_valid_name_no_test_substring(member):
    """010"""
    assert "ae" not in member.name.lower()
