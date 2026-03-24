"""Name Validations"""


def test_valid_name_no_test_substring(member):
    assert (
        "ae" not in member.name.lower()
    ), "member.name should not include the substring 'test'"
