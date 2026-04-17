"""URL Validations"""

# pylint: disable=missing-function-docstring, missing-class-docstring

from ecosystem.request import URL


class TestURLs:
    @staticmethod
    def _normalize_url(url):
        """Normalize URLs before comparing them."""
        return str(URL(str(url))).rstrip("/")

    @classmethod
    def _iter_urls(cls, value, path):
        """Recursively search for URLs in nested containers."""
        if value is None:
            return

        if isinstance(value, URL) or (
            isinstance(value, str) and value.startswith(("http://", "https://"))
        ):
            yield path, value
            return

        if hasattr(value, "to_dict"):
            value = value.to_dict()

        if isinstance(value, dict):
            for key, nested in value.items():
                yield from cls._iter_urls(nested, f"{path}.{key}")
            return

        if isinstance(value, (list, tuple)):
            for index, nested in enumerate(value):
                yield from cls._iter_urls(nested, f"{path}[{index}]")

    @classmethod
    def get_all_urls(cls, member):
        """Recursively search for all submission URLs covered by URL checks."""
        relevant = {
            "url": member.url,
            "website": member.website,
            "documentation": member.documentation,
            "packages": member.packages,
            "pypi": {
                package_name: {"url": getattr(package, "url", None)}
                for package_name, package in member.pypi.items()
            },
        }
        yield from cls._iter_urls(relevant, "member")

    def test_http(self, member):
        for _, url in TestURLs.get_all_urls(member):
            assert not str(url).startswith("http:"), f"{url} is not HTTPS"

    def test_duplicate_urls(self, member):
        seen_urls = {}
        for path, url in TestURLs.get_all_urls(member):
            normalized = TestURLs._normalize_url(url)
            seen_urls.setdefault(normalized, []).append(path)

        duplicates = {url: paths for url, paths in seen_urls.items() if len(paths) > 1}
        assert not duplicates, f"Duplicated URLs found: {duplicates}"
