"""Name Validations"""


def test_valid_name_no_test_substring(member):
    assert "test" not in member.name.lower()
