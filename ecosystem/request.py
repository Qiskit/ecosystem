"""Network request function."""

import os
import re
from urllib.parse import urlparse, urlunparse
import json
import csv
import gzip

import requests
import requests_cache
from bs4 import BeautifulSoup

from .error_handling import EcosystemError

# 86400 seconds == 1 day
requests_cache.install_cache(
    "_ecosystem_cache", expire_after=86400, allowable_codes=(200,)
)


def request_json(
    url: str,
    headers: dict[str, str] = None,
    post=None,
    parser=None,
    content_handler=None,
):
    """Requests the JSON in <url> with <headers>

    if post is set with a dictionary, then that dict is sent as POST's JSON
    """
    if parser is None:
        parser = json.loads
    url = URL(url)
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

    if url.hostname.endswith("bitly.com"):
        token = os.getenv("BITLY_TOKEN")
        if token:
            headers["Authorization"] = "Bearer " + token

    if post is None:
        response = requests.get(str(url), headers=headers, timeout=240)
    else:
        response = requests.post(str(url), headers=headers, timeout=240, json=post)

    if not response.ok:
        raise EcosystemError(
            f"Bad response {str(url)}: {response.reason} ({response.status_code})"
        )
    if content_handler:
        content = content_handler(response.content)
    else:
        content = response.text
    return parser(content)


class URL:
    """Wraps URLs"""

    def __init__(self, original_url: str):
        self.original_url = original_url
        self._parse_result = None
        self.logger = True

    def parse_url(self):
        """Normalizes and parses a URL"""
        logger_level = None if self.logger else lambda x: x
        if "_No response_" in self.original_url:
            raise EcosystemError(
                f"{self.original_url} does not look like a URL",
                logger_level=logger_level,
            )

        url = urlparse(self.original_url)
        scheme = "https"
        if url.netloc:
            netloc, path = url.hostname, url.path
        else:
            url_path_parts = url.path.split("/")
            netloc = url_path_parts[0]
            path = "/".join(url_path_parts[1:])
        self._parse_result = urlparse(
            urlunparse((scheme, netloc.lower(), path, url.params, url.query, ""))
        )

    @property
    def hostname(self):
        """Hostname part of the URL"""
        if self._parse_result is None:
            self.parse_url()
        return self._parse_result.hostname

    @property
    def path(self):
        """Path part of the URL"""
        if self._parse_result is None:
            self.parse_url()
        return self._parse_result.path

    def __eq__(self, other):
        return str(self) == str(other)

    def __str__(self):
        return self._parse_result.geturl() if self._parse_result else self.original_url


def parse_github_front_page(html_text):
    """
    Gets data from the front page github.com/<owner>/<repo>
    {
    estimated_contributors = int
    }
    """
    soup = BeautifulSoup(html_text, "html.parser")
    found = soup.find("a", {"href": re.compile(r"graphs/contributors")})
    if found is None:
        return None
    contributor_text = found.get_text()
    for line in contributor_text.split("\n"):
        candidate = line.strip()
        if candidate.isdigit():
            return {"estimated_contributors": int(candidate)}
    return {}


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


def parse_juliapackages(html_text):
    """
    Gets data from the front page https://juliapackages.com/p/<package>/
    {
    package_name = str
    repo_url = str
    }
    """
    ret = {}
    soup = BeautifulSoup(html_text, "html.parser")
    found = soup.find("h2")
    if found is not None:
        package_name = found.get_text().strip()
        if package_name.endswith(".jl"):
            package_name = package_name[:-3]
        ret["package_name"] = package_name

    found = soup.find("span", {"class": "shadow-sm rounded-md"}).find(
        "a", {"href": re.compile(r"github.com")}
    )
    if found is not None:
        ret["repo_url"] = found["href"].strip()

    return ret


# def request_julia_stats(pkg_uuid):
#     url = "https://julialang-logs.s3.amazonaws.com/public_outputs/current/package_requests.csv.gz"
#     r = requests.get(url)
#
#     i = BytesIO(r.content)
#     with gzip.open(i, "rt") as gz_file:
#         csv_reader = csv.DictReader(gz_file)
#         for row in csv_reader:
#             if row["package_uuid"] == pkg_uuid:
#                 return row


def find_first_in_csv_gz(subdict_to_find):
    """Returns a parser for csv after filtering based on subdict_to_find"""

    def parse_csv_gz(file_like):
        with gzip.open(file_like, "rt") as gz_file:
            csv_reader = csv.DictReader(gz_file)
            for row in csv_reader:
                if all(row[k] == v for k, v in subdict_to_find.items() if k in row):
                    return row
        return None

    return parse_csv_gz
