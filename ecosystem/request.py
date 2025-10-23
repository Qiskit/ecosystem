"""Network request function."""

import os

import requests
import requests_cache

from .error_handling import EcosystemError


def request(url: str, headers: dict[str, str] = None):
    """Requests the page in <url> with <headers>"""
    headers = headers or {}
    if url.startswith("api.github.com"):
        # 86400 seconds == 1 day
        requests_cache.install_cache(
            "_github_cache", expire_after=86400, allowable_codes=(200,)
        )
        token = os.getenv("GH_TOKEN")
        if token:
            headers["Authorization"] = "token" + token
    response = requests.get(f"https://{url}", headers=headers, timeout=240)
    if not response.ok:
        raise EcosystemError(f"Bad response for project {url}")
    return response
