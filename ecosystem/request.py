"""Network request function."""

import os
import re
from urllib.parse import urlparse, urlunparse
import json
import requests
import requests_cache
from bs4 import BeautifulSoup


from .error_handling import EcosystemError

# 86400 seconds == 1 day
requests_cache.install_cache(
    "_ecosystem_cache", expire_after=86400, allowable_codes=(200,)
)


def request_json(url: str, headers: dict[str, str] = None, parser=None):
    """Requests the JSON in <url> with <headers>"""
    if parser is None:
        parser = json.loads
    url = parse_url(url)
    headers = headers or {
        "Accept": "application/json,"
        "application/vnd.github+json,"
        "application/vnd.github.diff,"
        "text/html,"
        "application/xhtml+xml,"
        "application/xml"
    }

    if url.hostname.endswith("api.github.com"):
        token = os.getenv("GH_TOKEN")
        if token:
            headers["Authorization"] = "token " + token
        headers["User-Agent"] = "github.com/Qiskit/ecosystem/"

    response = requests.get(url.geturl(), headers=headers, timeout=240)
    if not response.ok:
        raise EcosystemError(
            f"Bad response {url.geturl()}: {response.reason} ({response.status_code})"
        )
    return parser(response.text)


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
    return urlparse(
        urlunparse((scheme, netloc.lower(), path, url.params, url.query, ""))
    )


def parse_github_package_ids(html_text):
    """
    Find the package ids for github.com/<owner>/repo/network/
    dependents?dependent_type=REPOSITORY&package_id=PACKAGE_ID
    """
    soup = BeautifulSoup(html_text, "html.parser")
    pkgs_selector = soup.find("div", {"class": "select-menu-list"})

    def format_pkg_name(pkg_name):
        single_line = re.sub(r"\s+", " ", pkg_name)
        return single_line.strip()

    is_there_a_default_pkg = soup.find("p", {"role": "status"})
    default_pkg = (
        is_there_a_default_pkg.find("strong").get_text().strip()
        if is_there_a_default_pkg
        else None
    )
    if pkgs_selector is None:
        return {default_pkg: ""}

    pkgs = pkgs_selector.find_all("a")
    if len(pkgs) == 0:  # there are no dependents in {response.url}
        return {default_pkg: ""}

    return {
        format_pkg_name(pkg.get_text()): pkg.get("href").split("=")[1] for pkg in pkgs
    }


def parse_github_dependants(html_text):
    """
    {
    "repositories": 99,
    "packages": 99
    }
    """
    ret = {}

    def raw_texts_to_int(raw_text):
        for l in raw_text.replace("\n", " ").split(" "):
            l = l.replace(",", "")
            if not l.strip() or not l.isdigit():
                continue
            return int(l)

    soup = BeautifulSoup(html_text, "html.parser")

    rep_raw_texts = soup.find_all(text=re.compile(r"( Repository| Repositories)\s*$"))
    if len(rep_raw_texts) != 1:
        raise EcosystemError(
            "BeautifulSoup had problems finding the repository DOM node"
        )
    rep_stat = raw_texts_to_int(rep_raw_texts[0])
    if rep_stat is not None:
        ret["repositories"] = rep_stat

    pkg_raw_texts = soup.find_all(text=re.compile(r"( Packages| Package)\s*$"))
    if len(rep_raw_texts) != 1:
        raise EcosystemError("BeautifulSoup had problems finding the package DOM node")
    pkg_stat = raw_texts_to_int(pkg_raw_texts[0])
    if pkg_stat is not None:
        ret["packages"] = pkg_stat

    return ret
