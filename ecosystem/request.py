"""Network request function."""

import os

import requests
import requests_cache

from .error_handling import EcosystemError
import json
from urllib.parse import urlparse, urlunparse

def parse_url(original_url: str):
    # raise EcosystemError(f"Bad URL {original_url}")
    url = urlparse(original_url)
    scheme = 'https'
    if url.netloc:
        netloc, path = url.hostname, url.path
    else:
      netloc, path = url.path.split('/', 1)
    return urlparse(urlunparse((scheme, netloc, path, '', '', '')))

def request_json(url: str, headers: dict[str, str] = None):
    """Requests the JSON in <url> with <headers>"""
    url = parse_url(url)
    headers = headers or {}
    if url.hostname == "api.github.com":
        # 86400 seconds == 1 day
        requests_cache.install_cache(
            "_github_cache", expire_after=86400, allowable_codes=(200,)
        )
        token = os.getenv("GH_TOKEN")
        if token:
            headers["Authorization"] = "token" + token

    response = requests.get(url.geturl(), headers=headers, timeout=240)
    if not response.ok:
        raise EcosystemError(f"Bad response {url.geturl()}: {response.reason} ({response.status_code})")
    return json.loads(response.text)