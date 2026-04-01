"""URL Validations"""

# pylint: disable=missing-function-docstring, missing-class-docstring


class TestURLs:
    @classmethod
    def get_all_urls(cls, member):
        """recursevly search for URLs in the member data"""
        for key, value in member.to_dict().items():
            if isinstance(value, str) and value.startswith("http"):
                yield getattr(member, key)
            elif hasattr(getattr(member, key), "to_dict"):
                yield from TestURLs.get_all_urls(getattr(member, key))
            else:
                continue

    def test_http(self, member):
        for url in TestURLs.get_all_urls(member):
            assert not str(url).startswith("http:"), f"{url} is not HTTPS"
