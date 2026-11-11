# This code is part of Qiskit.
#
# (C) Copyright IBM 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at https://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Network request function."""

import re
from urllib.parse import urlparse, urlunparse
import json
import csv
import gzip
import time

import requests
import requests_cache
from bs4 import BeautifulSoup

from .error_handling import EcosystemError, logger

# 86400 seconds == 1 day
requests_cache.install_cache(
    "_ecosystem_cache", expire_after=86400, allowable_codes=(200,)
)


def request_json(
    url: str,
    headers: dict[str, str] = None,
    post=None,
    put=None,
    parser=None,
    content_handler=None,
    delay=None,
    token=None,
):
    # pylint: disable=too-many-branches
    """Request content from a URL and parse it into a JSON-like Python object.

    This helper applies default headers, the access token given by the caller,
    and an optional delay before making the request. It supports `GET` by default, or `POST`/`PUT`
    when `post` or `put` payloads are provided.

    Args:
        url: Target URL to fetch.
        headers: Optional request headers. If omitted, a broad set of accept
            headers is used.
        post: Optional JSON-serializable body for a `POST` request.
        put: Optional JSON-serializable body for a `PUT` request.
        parser: Callable used to parse the response payload. Defaults to
            `json.loads`.
        content_handler: Optional callable that receives raw `response.content`
            bytes and returns the text/blob expected by `parser`.
        delay: Optional delay (seconds) before sending the request.
        token: Optional access token (like a GitHub PAT). When given, it is sent
            as `Authorization: Bearer <token>`, no matter the target host. It is
            the caller's job to provide the right token for the URL.

    Returns:
        Parsed response data. Non-dict results are wrapped as `{"data": ...}`.
        Metadata keys `__requested_at__` and `__url__` are added when parsing
        returns a non-`None` value.

    Raises:
        EcosystemError: If the delay is too large, URL normalization fails,
            or the response status is not successful after retry handling.
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

    if token:
        headers["Authorization"] = "Bearer " + token

    if url.hostname.endswith("api.github.com"):
        headers["User-Agent"] = "github.com/Qiskit/ecosystem/"

    if delay:
        if delay < 0:
            logger.warning("Negative delay (%.0f sec) truncated to 0", delay)
            delay = 0
        if delay >= 900:
            raise EcosystemError(f"delay for fetching {url} too long: {delay:.0f} sec")
        if delay >= 5:
            logger.info("Wait %.0f secs before fetching %s", delay, url)
        time.sleep(delay)

    if post is not None:
        response = requests.post(str(url), headers=headers, timeout=240, json=post)
    elif put is not None:
        response = requests.put(str(url), headers=headers, timeout=240, json=put)
    else:
        response = requests.get(str(url), headers=headers, timeout=240)

    if not response.ok:
        if "rate" in response.reason or response.status_code == 429:
            wait_for = delay * 2 if delay else 60
            if "X-RateLimit-Reset" in response.headers:
                wait_for = int(response.headers["X-RateLimit-Reset"]) - int(time.time())
            return request_json(
                url=url.original_url,
                headers=headers,
                post=post,
                put=put,
                parser=parser,
                content_handler=content_handler,
                delay=wait_for,
                token=token,
            )
        raise EcosystemError(
            f"Bad response {str(url)}: {response.reason} ({response.status_code})"
        )
    if content_handler:
        content = content_handler(response.content)
    else:
        content = response.text
    ret = parser(content)
    if ret is None:
        return ret

    metadata = {"__requested_at__": response.created_at, "__url__": response.url}
    if not isinstance(ret, dict):
        ret = {"data": ret}
    return ret | metadata


class URL:
    """Wraps URLs"""

    def __init__(self, original_url: str, logger_level=None):
        """

        Args:
            original_url (str): Raw URL or URL-like text to normalize.
            logger_level (callable):  Something like logger.error . Default is quiet.
        """
        if not original_url:
            raise EcosystemError("original_url must be provided")
        self.original_url = original_url
        if logger_level is None:
            self.logger_level = lambda x: x
        else:
            if callable(logger_level):
                self.logger_level = logger_level
            else:
                raise EcosystemError("logger_level must be callable")
        self._normalized_url = self.normalize()

    def normalize(self):
        """Normalize URLs"""
        if "_No response_" in self.original_url:
            raise EcosystemError(
                f"{self.original_url} does not look like a URL",
                logger_level=self.logger_level,
            )

        url = urlparse(self.original_url)
        if " " in self.original_url:
            for word in self.original_url.split(" "):
                if any(x in word for x in (".com", "http")):
                    url = urlparse(word)
                    if url.netloc:
                        break
            else:
                raise EcosystemError(
                    f"Multiple words in '{self.original_url}' and none of them look like a URL",
                    logger_level=self.logger_level,
                )

        scheme = (
            url.scheme if url.scheme.startswith(URL.BROKEN_SCHEME_PREFIX) else "https"
        )
        if url.netloc:
            netloc, path = url.hostname, url.path
        else:
            url_path_parts = [p for p in url.path.split("/") if p]
            netloc = url_path_parts[0]
            path = "/".join(url_path_parts[1:])
        return urlparse(
            urlunparse((scheme, netloc.lower(), path, url.params, url.query, ""))
        )

    @property
    def hostname(self):
        """Hostname part of the URL"""
        return self._normalized_url.hostname

    @property
    def path(self):
        """Path part of the URL"""
        return self._normalized_url.path

    @property
    def query(self):
        """Query part of the URL"""
        return self._normalized_url.query

    def __eq__(self, other):
        return str(self) == str(other)

    def __str__(self):
        return self._normalized_url.geturl()

    def __repr__(self):
        return f"URL('{self}')"

    #: scheme prefix of a URL recorded as not resolving, as `status-404://<the url>`
    BROKEN_SCHEME_PREFIX = "status-"

    @property
    def is_broken(self):
        """Whether this URL carries the `status-<status>://` marker"""
        return str(self).startswith(self.BROKEN_SCHEME_PREFIX)

    def _with_scheme(self, scheme):
        """This URL with its scheme swapped, and everything after it left alone.

        Swapped textually rather than reassembled from `hostname`, `path` and `query`:
        that drops whatever component the reassembly forgets, and `path` in particular
        excludes a `;params` segment, which a SICI-style DOI carries
        (`...3.0.CO;2-2`). Marking and unmarking have to round trip exactly — the marker
        is supposed to be the link the member file had — so this takes the normalized URL
        as it stands and only replaces what is in front of the `://`.
        """
        return URL(f"{scheme}://{str(self).split('://', 1)[1]}")

    def marked(self, status):
        """This URL recorded as not resolving, as `status-<status>://<the url>`

        The member file keeps the link it had — a 404 is for a human to fix, and the old
        URL is the only clue to what it should be — while saying plainly that nothing is
        there. `[016]` is what reads it; note the other URL check ups are *not* fooled into
        skipping a marked link, because they match on hostname and path, which the marker
        preserves. `[013]` passes it only because `status-404://` does not start with
        `http:`, which is luck rather than design.
        """
        return self._with_scheme(f"{self.BROKEN_SCHEME_PREFIX}{status}")

    @property
    def unmarked(self):
        """The live URL a `status-<status>://` marker was made from"""
        return self._with_scheme("https")

    @property
    def checkable_prefix(self):
        """What of a `packages` URL can be requested, or None if there is nothing to ask.

        A pattern (`.../packages/*/pyproject.toml`) has no single target, so the part up to
        the first wildcard is what gets checked — `.../packages/`, one directory of the
        repository. A `?itemName=...` query is not a pattern even though `?` is a wildcard
        character elsewhere, so the query is dropped before looking.
        """
        without_query = f"https://{self.hostname}{self.path}"
        # `*` and `[` only: `urlparse` has already split everything after the first `?`
        # into `query`, so a `?` can never reach `path`, and a `?itemName=...` on the VS
        # Code marketplace is a real URL rather than a pattern. No corpus pattern uses `?`
        # as a wildcard; one that did would read as a query and be asked verbatim
        cut = min(
            (without_query.index(w) for w in "*[" if w in without_query),
            default=None,
        )
        if cut is None:
            return self
        prefix = without_query[:cut].rsplit("/", 1)[0]
        return URL(prefix) if prefix.count("/") > 2 else None

    def status(self):
        """The HTTP status this URL answers, or None if nothing answered at all.

        `HEAD` first, because the body is never wanted here and most hosts answer it, but
        it is only ever an optimization: **any** failing `HEAD` is re-asked with `GET`,
        which is the authoritative answer. Several hosts answer a perfectly good page with
        404 or 405 to a `HEAD` — the VS Code marketplace replies 404 to `HEAD` and 200 to
        `GET` for a published extension — and a 404 is the one status that gets written
        into a member file, so it is the one that most deserves the second ask. The cost is
        one extra request per failing URL, which is the minority of them.

        Redirects *are* followed, so the status is the one at the end of the chain: a 301
        onto a live page is not a dead link, and a 301 onto a missing one is. Where it
        landed is not reported, because nothing here records it.

        Nothing is raised for a 4xx or 5xx — a dead link is a result here, not an error —
        so this does not go through `request_json`, which raises and also caches. None is
        returned for a connection error or a timeout, which is not a verdict either way.

        Note a redirect done in JavaScript is invisible here, and should be: a project can
        serve a custom 404 page whose body carries the new address in a
        `window.location.replace`, which a browser follows and this does not. The Qiskit
        GitHub Pages site does exactly that for its renamed addons. The status is what the
        server said, and a 404 with a redirect in its body is still a 404.
        """
        headers = {
            # a plain python-requests UA is what several documentation hosts bot-wall
            "User-Agent": "Mozilla/5.0 (compatible; github.com/Qiskit/ecosystem)",
            "Accept": "text/html,application/xhtml+xml,application/xml,*/*",
        }
        try:
            with requests_cache.disabled():
                response = requests.head(
                    str(self), headers=headers, timeout=60, allow_redirects=True
                )
                if not response.ok:
                    # `stream` so the body is not downloaded: only the status is read
                    response = requests.get(
                        str(self),
                        headers=headers,
                        timeout=60,
                        allow_redirects=True,
                        stream=True,
                    )
                    response.close()
        except (requests.RequestException, ValueError) as err:
            # ValueError: `requests` re-parses a redirect target with a bare `urlparse`,
            # so a malformed `Location` header raises out of the redirect chain. One bad
            # host must not end a run over 217 members
            logger.warning("Could not reach %s: %s", self, type(err).__name__)
            return None
        return response.status_code


def parse_github_contributors_sidebar(html_text):
    """
    Gets data from the front page github.com/<owner>/<repo>/contributors_list?deferred=true
    {
    estimated_contributors = int
    }
    """
    soup = BeautifulSoup(html_text, "html.parser")
    found = soup.find("span", attrs={"title": "3"})
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


def find_first_in_csv_gz(subdict_to_find):
    """Returns a parser for csv after filtering based on subdict_to_find"""

    def parse_csv_gz(file_like):
        with gzip.open(file_like, "rt") as gz_file:
            csv_reader = csv.DictReader(gz_file)
            for row in csv_reader:
                if "statuses" in subdict_to_find:
                    for status in subdict_to_find["statuses"]:
                        to_find = dict(subdict_to_find)
                        del to_find["statuses"]
                        to_find["status"] = status
                        if all(row[k] == v for k, v in to_find.items() if k in row):
                            return row
                else:
                    if all(row[k] == v for k, v in subdict_to_find.items() if k in row):
                        return row
        return {}

    return parse_csv_gz
