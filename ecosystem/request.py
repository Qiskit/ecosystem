"""Network request function."""

import os
from urllib.parse import urlparse, urlunparse
import json
import requests
import requests_cache

from .error_handling import EcosystemError

# 86400 seconds == 1 day
requests_cache.install_cache(
    "_ecosystem_cache", expire_after=86400, allowable_codes=(200,)
)


def parse_url(original_url: str):
    """Normalizes and parses a URL"""
    url = urlparse(original_url)
    scheme = "https"
    if url.netloc:
        netloc, path = url.hostname, url.path
    else:
        url_path_parts = url.path.split("/")
        netloc = url_path_parts[0]
        path = "/".join(url_path_parts[1:])
    return urlparse(urlunparse((scheme, netloc.lower(), path, "", "", "")))


def request_json(url: str, headers: dict[str, str] = None):
    """Requests the JSON in <url> with <headers>"""
    url = parse_url(url)
    headers = headers or {"Accept": "application/json,application/vnd.github+json,application/vnd.github.diff"}

    if url.hostname == "api.github.com":
        token = os.getenv("GH_TOKEN")
        if token:
            headers["Authorization"] = "token " + token
        headers['User-Agent'] = 'github.com/Qiskit/ecosystem/'

        response = requests.get(url.geturl(), headers=headers, timeout=240)

    if not response.ok:
        raise EcosystemError(
            f"Bad response {url.geturl()}: {response.reason} ({response.status_code})"
        )
    return json.loads(response.text)
