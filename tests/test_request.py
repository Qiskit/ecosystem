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

"""Tests for ecosystem/request.py.

All the tests here are network independent: ``requests.get``, ``requests.post``,
``requests.put`` and ``time.sleep`` are patched, so nothing reaches the network
and nothing blocks.
"""

import gzip
import io
import os
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from ecosystem.error_handling import EcosystemError, logger
from ecosystem.request import (
    URL,
    find_first_in_csv_gz,
    parse_github_contributors_sidebar,
    parse_github_dependants,
    parse_github_package_ids,
    parse_juliapackages,
    request_json,
)

REQUESTED_AT = "2026-08-03T00:00:00+00:00"
RESPONSE_URL = "https://example.com/resource"
METADATA = {"__requested_at__": REQUESTED_AT, "__url__": RESPONSE_URL}
# Frozen clock, so the X-RateLimit-Reset arithmetic is deterministic
NOW = 1_000_000


def fake_response(text="{}", ok=True, reason="OK", status_code=200, headers=None):
    """Builds a stand-in for a response as returned by a patched requests_cache.

    ``created_at`` is set because requests_cache adds it to every response it
    hands back (see ``OriginalResponse.wrap_response``).
    """
    return SimpleNamespace(
        text=text,
        content=text.encode(),
        ok=ok,
        reason=reason,
        status_code=status_code,
        headers=headers or {},
        url=RESPONSE_URL,
        created_at=REQUESTED_AT,
    )


def gzipped_csv(text):
    """Returns a file-like object with the gzipped version of <text>."""
    raw = io.BytesIO()
    with gzip.GzipFile(fileobj=raw, mode="wb") as gz_file:
        gz_file.write(text.encode())
    return io.BytesIO(raw.getvalue())


class TestURL(TestCase):
    """Test class for ecosystem.request.URL."""

    def test_normal_url(self):
        """Tests parsing a normal url."""
        url = URL("https://github.com/banana?key=value")
        self.assertEqual(url.hostname, "github.com")
        self.assertEqual(url.path, "/banana")
        self.assertEqual(url.query, "key=value")

    def test_no_response(self):
        """Tests parsing _No response_."""
        with self.assertRaises(EcosystemError):
            _ = URL("_No response_")

    def test_contains_url(self):
        """Tests parsing a string that contains a url"""
        url = URL(" - https://github.com/banana?key=value and somehting else")
        self.assertEqual(url.hostname, "github.com")
        self.assertEqual(url.path, "/banana")
        self.assertEqual(url.query, "key=value")

    def test_no_schema(self):
        """Tests parsing a url without a schema"""
        url = URL("github.com/banana?key=value")
        self.assertEqual(url.hostname, "github.com")
        self.assertEqual(url.path, "/banana")
        self.assertEqual(url.query, "key=value")

    def test_trailing_bar(self):
        """Tests parsing a url with a trailing bar"""
        url = URL("github.com/banana/")
        self.assertEqual(url.hostname, "github.com")
        self.assertEqual(url.path, "/banana")

    def test_hostname_case(self):
        """Tests parsing a url with casing in the hostname"""
        url = URL("GitHub.com/banana?key=value")
        self.assertEqual(url.hostname, "github.com")
        self.assertEqual(url.path, "/banana")
        self.assertEqual(url.query, "key=value")

    def test_path_case_is_preserved(self):
        """Tests that the casing of the path is not normalized"""
        url = URL("GitHub.com/Banana/Split")
        self.assertEqual(url.hostname, "github.com")
        self.assertEqual(url.path, "/Banana/Split")

    def test_fragment_is_dropped(self):
        """Tests that the fragment is removed from the normalized url"""
        url = URL("https://github.com/banana#readme")
        self.assertEqual(str(url), "https://github.com/banana")

    def test_str(self):
        """Tests the string representation of a url"""
        self.assertEqual(str(URL("GitHub.com/banana")), "https://github.com/banana")

    def test_repr(self):
        """Tests the repr of a url"""
        self.assertEqual(
            repr(URL("GitHub.com/banana")), "URL('https://github.com/banana')"
        )

    def test_equality(self):
        """Tests that equality is based on the normalized url"""
        self.assertEqual(URL("GitHub.com/banana"), URL("https://github.com/banana"))
        self.assertEqual(URL("GitHub.com/banana"), "https://github.com/banana")
        self.assertNotEqual(URL("github.com/banana"), URL("github.com/split"))

    def test_trailing_bar_with_a_schema_is_kept(self):
        """Tests that a trailing bar survives when the url has a schema.

        Note the asymmetry with test_trailing_bar: the bar is only dropped when
        the url has no schema, so the same url written in the two ways does not
        normalize to the same string. Trailing bars are meaningful for some of
        the requested APIs (juliapkgstats), so this only documents the current
        behavior.
        """
        self.assertEqual(URL("https://github.com/banana/").path, "/banana/")

    def test_original_url_is_kept(self):
        """Tests that the original url is available after normalization"""
        self.assertEqual(URL("GitHub.com/banana/").original_url, "GitHub.com/banana/")

    def test_multiple_words_and_no_url(self):
        """Tests a multi word string in which no word looks like a url"""
        with self.assertRaises(EcosystemError):
            _ = URL("there is no url in here")

    def test_logger_level_is_called(self):
        """Tests that the logger_level argument is the callable used to report.
        """
        with self.assertRaises(EcosystemError):
            _ = URL("_No response_", logger_level="string")

    def test_empty_url(self):
        """Tests that an empty string is reported as a bad url.
        """
        with self.assertRaises(EcosystemError):
            _ = URL("")


class TestRequestJson(TestCase):
    """Test class for ecosystem.request.request_json."""

    def test_json_response(self):
        """Tests that a json response is parsed and gets the metadata"""
        with patch(
            "ecosystem.request.requests.get", return_value=fake_response('{"a": 1}')
        ):
            self.assertEqual(request_json("example.com/x"), {"a": 1} | METADATA)

    def test_non_dict_result_is_wrapped(self):
        """Tests that a non dict payload is wrapped in a data key"""
        with patch(
            "ecosystem.request.requests.get", return_value=fake_response("[1, 2]")
        ):
            self.assertEqual(request_json("example.com/x"), {"data": [1, 2]} | METADATA)

    def test_parser_returning_none(self):
        """Tests that a None from the parser is returned without metadata"""
        with patch(
            "ecosystem.request.requests.get", return_value=fake_response("banana")
        ):
            self.assertIsNone(request_json("example.com/x", parser=lambda _: None))

    def test_custom_parser_gets_the_text(self):
        """Tests that the parser is called with the response text"""
        with patch(
            "ecosystem.request.requests.get", return_value=fake_response("banana")
        ):
            result = request_json("example.com/x", parser=lambda text: {"text": text})
        self.assertEqual(result, {"text": "banana"} | METADATA)

    def test_content_handler_gets_the_content(self):
        """Tests that, when set, the content handler pre processes the content"""
        seen = {}

        def content_handler(content):
            seen["content"] = content
            return content.decode().upper()

        with patch(
            "ecosystem.request.requests.get", return_value=fake_response("banana")
        ):
            result = request_json(
                "example.com/x",
                parser=lambda text: {"text": text},
                content_handler=content_handler,
            )
        self.assertEqual(seen["content"], b"banana")
        self.assertEqual(result, {"text": "BANANA"} | METADATA)

    def test_default_accept_header(self):
        """Tests the default Accept header of a plain request"""
        with patch(
            "ecosystem.request.requests.get", return_value=fake_response()
        ) as requests_get:
            request_json("example.com/x")
        headers = requests_get.call_args.kwargs["headers"]
        self.assertEqual(list(headers), ["Accept"])
        self.assertIn("application/json", headers["Accept"])

    def test_custom_headers(self):
        """Tests that custom headers replace the default ones"""
        with patch(
            "ecosystem.request.requests.get", return_value=fake_response()
        ) as requests_get:
            request_json("example.com/x", headers={"Accept": "text/csv"})
        self.assertEqual(
            requests_get.call_args.kwargs["headers"], {"Accept": "text/csv"}
        )

    def test_url_is_normalized_before_requesting(self):
        """Tests that the requested url is the normalized one"""
        with patch(
            "ecosystem.request.requests.get", return_value=fake_response()
        ) as requests_get:
            request_json("Example.com/x")
        self.assertEqual(requests_get.call_args.args[0], "https://example.com/x")

    def test_github_token_argument(self):
        """Tests that the token argument is used for api.github.com"""
        with patch(
            "ecosystem.request.requests.get", return_value=fake_response()
        ) as requests_get:
            request_json("api.github.com/repos/banana/split", token="banana-token")
        headers = requests_get.call_args.kwargs["headers"]
        self.assertEqual(headers["Authorization"], "token banana-token")
        self.assertEqual(headers["User-Agent"], "github.com/Qiskit/ecosystem/")

    def test_github_token_from_environment(self):
        """Tests that GH_TOKEN is used for api.github.com when no token is given"""
        with patch.dict(os.environ, {"GH_TOKEN": "env-token"}):
            with patch(
                "ecosystem.request.requests.get", return_value=fake_response()
            ) as requests_get:
                request_json("api.github.com/repos/banana/split")
        headers = requests_get.call_args.kwargs["headers"]
        self.assertEqual(headers["Authorization"], "token env-token")

    def test_github_without_token(self):
        """Tests that an empty token adds no Authorization header"""
        with patch(
            "ecosystem.request.requests.get", return_value=fake_response()
        ) as requests_get:
            request_json("api.github.com/repos/banana/split", token="")
        headers = requests_get.call_args.kwargs["headers"]
        self.assertNotIn("Authorization", headers)
        self.assertEqual(headers["User-Agent"], "github.com/Qiskit/ecosystem/")

    def test_non_github_host_gets_no_token(self):
        """Tests that a non github host does not get the github headers"""
        with patch.dict(os.environ, {"GH_TOKEN": "env-token"}):
            with patch(
                "ecosystem.request.requests.get", return_value=fake_response()
            ) as requests_get:
                request_json("example.com/x")
        headers = requests_get.call_args.kwargs["headers"]
        self.assertNotIn("Authorization", headers)
        self.assertNotIn("User-Agent", headers)

    def test_bitly_token_from_environment(self):
        """Tests that BITLY_TOKEN is sent as a bearer token to bitly.com"""
        with patch.dict(os.environ, {"BITLY_TOKEN": "bitly-token"}):
            with patch(
                "ecosystem.request.requests.get", return_value=fake_response()
            ) as requests_get:
                request_json("api-ssl.bitly.com/v4/bitlinks")
        headers = requests_get.call_args.kwargs["headers"]
        self.assertEqual(headers["Authorization"], "Bearer bitly-token")

    def test_post(self):
        """Tests that a post payload is sent as json with post"""
        with patch(
            "ecosystem.request.requests.post", return_value=fake_response('{"a": 1}')
        ) as requests_post:
            self.assertEqual(
                request_json("example.com/x", post={"banana": "split"}),
                {"a": 1} | METADATA,
            )
        self.assertEqual(requests_post.call_args.kwargs["json"], {"banana": "split"})

    def test_put(self):
        """Tests that a put payload is sent as json with put"""
        with patch(
            "ecosystem.request.requests.put", return_value=fake_response('{"a": 1}')
        ) as requests_put:
            self.assertEqual(
                request_json("example.com/x", put={"banana": "split"}),
                {"a": 1} | METADATA,
            )
        self.assertEqual(requests_put.call_args.kwargs["json"], {"banana": "split"})

    def test_bad_response(self):
        """Tests that a non ok response raises EcosystemError"""
        response = fake_response(ok=False, reason="Not Found", status_code=404)
        with patch("ecosystem.request.requests.get", return_value=response):
            with self.assertRaises(EcosystemError) as context:
                request_json("example.com/x")
        self.assertIn("Not Found", str(context.exception))
        self.assertIn("404", str(context.exception))


class TestRequestJsonDelay(TestCase):
    """Test class for the delay and rate limit handling of request_json."""

    def rate_limited(self, headers=None):
        """A rate limited response, optionally with rate limit headers"""
        return fake_response(
            ok=False, reason="Too Many Requests", status_code=429, headers=headers
        )

    def test_delay_sleeps_before_requesting(self):
        """Tests that the delay is awaited before the request"""
        with patch("ecosystem.request.time.sleep") as sleep:
            with patch("ecosystem.request.requests.get", return_value=fake_response()):
                request_json("example.com/x", delay=7)
        sleep.assert_called_once_with(7)

    def test_delay_too_long(self):
        """Tests that a delay of 15 minutes or more is an error"""
        with patch("ecosystem.request.time.sleep") as sleep:
            with patch(
                "ecosystem.request.requests.get", return_value=fake_response()
            ) as requests_get:
                with self.assertRaises(EcosystemError) as context:
                    request_json("example.com/x", delay=900)
        self.assertIn("too long", str(context.exception))
        sleep.assert_not_called()
        requests_get.assert_not_called()

    def test_rate_limit_by_status_code(self):
        """Tests that a 429 is retried after the default minute"""
        responses = [self.rate_limited(), fake_response('{"a": 1}')]
        with patch("ecosystem.request.time.sleep") as sleep:
            with patch(
                "ecosystem.request.requests.get", side_effect=responses
            ) as requests_get:
                self.assertEqual(request_json("example.com/x"), {"a": 1} | METADATA)
        self.assertEqual(requests_get.call_count, 2)
        sleep.assert_called_once_with(60)

    def test_rate_limit_by_reason(self):
        """Tests that a reason mentioning the rate is retried"""
        limited = fake_response(ok=False, reason="rate limit exceeded", status_code=403)
        with patch("ecosystem.request.time.sleep") as sleep:
            with patch(
                "ecosystem.request.requests.get",
                side_effect=[limited, fake_response('{"a": 1}')],
            ):
                self.assertEqual(request_json("example.com/x"), {"a": 1} | METADATA)
        sleep.assert_called_once_with(60)

    def test_rate_limit_doubles_a_given_delay(self):
        """Tests that an ongoing delay is doubled on a rate limited response"""
        responses = [self.rate_limited(), fake_response('{"a": 1}')]
        with patch("ecosystem.request.time.sleep") as sleep:
            with patch("ecosystem.request.requests.get", side_effect=responses):
                request_json("example.com/x", delay=10)
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [10, 20])

    def test_rate_limit_reset_header(self):
        """Tests that X-RateLimit-Reset sets how long to wait"""
        limited = self.rate_limited({"X-RateLimit-Reset": str(NOW + 120)})
        with patch("ecosystem.request.time.time", return_value=NOW):
            with patch("ecosystem.request.time.sleep") as sleep:
                with patch(
                    "ecosystem.request.requests.get",
                    side_effect=[limited, fake_response('{"a": 1}')],
                ):
                    request_json("example.com/x")
        sleep.assert_called_once_with(120)

    def test_rate_limit_reset_too_far_in_the_future(self):
        """Tests that a reset further than 15 minutes away is an error"""
        limited = self.rate_limited({"X-RateLimit-Reset": str(NOW + 1000)})
        with patch("ecosystem.request.time.time", return_value=NOW):
            with patch("ecosystem.request.time.sleep"):
                with patch("ecosystem.request.requests.get", return_value=limited):
                    with self.assertRaises(EcosystemError) as context:
                        request_json("example.com/x")
        self.assertIn("too long", str(context.exception))

    def test_rate_limit_reset_in_the_past(self):
        """Tests a rate limited response whose reset time has already passed.
        """
        limited = self.rate_limited({"X-RateLimit-Reset": str(NOW - 300)})
        slept = []
        with patch("ecosystem.request.time.time", return_value=NOW):
            with patch("ecosystem.request.time.sleep", side_effect=slept.append):
                with patch(
                    "ecosystem.request.requests.get",
                    side_effect=[limited, fake_response('{"a": 1}')],
                ):
                    request_json("example.com/x")
        self.assertTrue(all(seconds >= 0 for seconds in slept), f"slept {slept}")


class TestParseGithubContributorsSidebar(TestCase):
    """Test class for ecosystem.request.parse_github_contributors_sidebar."""

    @staticmethod
    def sidebar(count):
        """The contributors sidebar of a repo with <count> contributors"""
        return (
            '<h2 class="h4">Contributors'
            f'<span class="Counter ml-1" title="{count}">{count}</span></h2>'
        )

    def test_contributors(self):
        """Tests reading the number of contributors"""
        self.assertEqual(
            parse_github_contributors_sidebar(self.sidebar(3)),
            {"estimated_contributors": 3},
        )

    def test_multiline_counter(self):
        """Tests reading a count surrounded by whitespace"""
        html = '<span title="3">\n            3\n          </span>'
        self.assertEqual(
            parse_github_contributors_sidebar(html), {"estimated_contributors": 3}
        )

    def test_no_counter(self):
        """Tests that a page without the counter returns None"""
        self.assertIsNone(parse_github_contributors_sidebar("<h2>Contributors</h2>"))

    def test_counter_without_a_number(self):
        """Tests that a counter with no digits returns an empty dict"""
        html = '<span title="3">many</span>'
        self.assertEqual(parse_github_contributors_sidebar(html), {})

class TestParseGithubPackageIds(TestCase):
    """Test class for ecosystem.request.parse_github_package_ids."""

    @staticmethod
    def menu(*anchors):
        """A select menu listing the given anchors"""
        return f'<div class="select-menu-list">{"".join(anchors)}</div>'

    @staticmethod
    def status(package):
        """The paragraph naming the package being shown by default"""
        return f'<p role="status">Showing <strong>{package}</strong></p>'

    def test_one_package(self):
        """Tests reading a single package id"""
        html = self.menu('<a href="/o/r/network/dependents?package_id=PKG1">banana</a>')
        self.assertEqual(parse_github_package_ids(html), {"banana": "PKG1"})

    def test_several_packages(self):
        """Tests reading more than one package id"""
        html = self.menu(
            '<a href="?package_id=PKG1">banana</a>',
            '<a href="?package_id=PKG2">split</a>',
        )
        self.assertEqual(
            parse_github_package_ids(html), {"banana": "PKG1", "split": "PKG2"}
        )

    def test_package_name_is_normalized(self):
        """Tests that the whitespace of the package name is collapsed"""
        html = self.menu('<a href="?package_id=PKG1">\n  banana   split\n</a>')
        self.assertEqual(parse_github_package_ids(html), {"banana split": "PKG1"})

    def test_no_menu_with_a_default_package(self):
        """Tests a page with no menu, where the shown package is the only one"""
        self.assertEqual(
            parse_github_package_ids(self.status("banana")), {"banana": ""}
        )

    def test_no_menu_and_no_default_package(self):
        """Tests a page with neither a menu nor a default package"""
        self.assertEqual(
            parse_github_package_ids("<div>nothing here</div>"), {None: ""}
        )

    def test_empty_menu(self):
        """Tests a menu without entries, meaning there are no dependents"""
        html = self.status("banana") + self.menu()
        self.assertEqual(parse_github_package_ids(html), {"banana": ""})


class TestParseGithubDependants(TestCase):
    """Test class for ecosystem.request.parse_github_dependants."""

    @staticmethod
    def counters(repositories=None, packages=None):
        """The dependents counters, as a menu of anchors"""
        anchors = [f"<a>{text}</a>" for text in (repositories or []) + (packages or [])]
        return "".join(anchors)

    def test_counters(self):
        """Tests reading both counters"""
        html = self.counters(["1,234 Repositories"], ["56 Packages"])
        self.assertEqual(
            parse_github_dependants(html), {"repositories": 1234, "packages": 56}
        )

    def test_singular_counters(self):
        """Tests reading counters of a single repository and package"""
        html = self.counters(["1 Repository"], ["1 Package"])
        self.assertEqual(
            parse_github_dependants(html), {"repositories": 1, "packages": 1}
        )

    def test_counter_without_a_number(self):
        """Tests that a counter with no digits is left out of the result"""
        html = self.counters(["no number Repositories"], ["56 Packages"])
        self.assertEqual(parse_github_dependants(html), {"packages": 56})

    def test_no_repositories_counter(self):
        """Tests that a missing repositories counter is an error"""
        with self.assertRaises(EcosystemError):
            parse_github_dependants(self.counters(packages=["56 Packages"]))

    def test_duplicated_repositories_counter(self):
        """Tests that two repositories counters are an error"""
        html = self.counters(["1 Repository", "2 Repositories"], ["56 Packages"])
        with self.assertRaises(EcosystemError):
            parse_github_dependants(html)

class TestParseJuliapackages(TestCase):
    """Test class for ecosystem.request.parse_juliapackages."""

    REPO_URL = "https://github.com/banana/Split.jl"

    @classmethod
    def page(cls, title="<h2>Split.jl</h2>", anchors=None):
        """The juliapackages front page of a package"""
        if anchors is None:
            anchors = [f'<a href="{cls.REPO_URL}">GitHub</a>']
        badge = f'<span class="shadow-sm rounded-md">{"".join(anchors)}</span>'
        return title + badge

    def test_package(self):
        """Tests reading the package name and the repository url"""
        self.assertEqual(
            parse_juliapackages(self.page()),
            {"package_name": "Split", "repo_url": self.REPO_URL},
        )

    def test_name_without_the_jl_suffix(self):
        """Tests that a name not ending in .jl is kept as it is"""
        self.assertEqual(
            parse_juliapackages(self.page(title="<h2>  Split  </h2>"))["package_name"],
            "Split",
        )

    def test_no_name(self):
        """Tests a page without the package name"""
        self.assertEqual(
            parse_juliapackages(self.page(title="")), {"repo_url": self.REPO_URL}
        )

    def test_no_github_link(self):
        """Tests a page whose repository badge does not link to github"""
        anchors = ['<a href="https://gitlab.com/banana/Split.jl">GitLab</a>']
        self.assertEqual(
            parse_juliapackages(self.page(anchors=anchors)), {"package_name": "Split"}
        )

    def test_github_link_among_others(self):
        """Tests that the github link is picked among other links"""
        anchors = [
            '<a href="https://juliahub.com/ui/Packages/General/Split">docs</a>',
            f'<a href="{self.REPO_URL}">GitHub</a>',
        ]
        self.assertEqual(
            parse_juliapackages(self.page(anchors=anchors))["repo_url"], self.REPO_URL
        )


class TestFindFirstInCsvGz(TestCase):
    """Test class for ecosystem.request.find_first_in_csv_gz."""

    CSV = (
        "package_uuid,status,client_type,request_addrs\n"
        "banana-uuid,200,ci,10\n"
        "banana-uuid,302,user,20\n"
        "split-uuid,200,user,30\n"
    )

    def test_first_match(self):
        """Tests that the first row matching the subdict is returned"""
        parser = find_first_in_csv_gz({"package_uuid": "split-uuid"})
        self.assertEqual(
            parser(gzipped_csv(self.CSV)),
            {
                "package_uuid": "split-uuid",
                "status": "200",
                "client_type": "user",
                "request_addrs": "30",
            },
        )

    def test_any_of_the_statuses(self):
        """Tests that a row matching any of the statuses is returned"""
        parser = find_first_in_csv_gz(
            {
                "package_uuid": "banana-uuid",
                "statuses": ["302", "301"],
                "client_type": "user",
            }
        )
        self.assertEqual(parser(gzipped_csv(self.CSV))["request_addrs"], "20")

    def test_none_of_the_statuses(self):
        """Tests that no row is returned when no status matches"""
        parser = find_first_in_csv_gz(
            {"package_uuid": "banana-uuid", "statuses": ["404"], "client_type": "user"}
        )
        self.assertEqual(parser(gzipped_csv(self.CSV)), {})

    def test_no_match(self):
        """Tests that an empty dict is returned when nothing matches"""
        parser = find_first_in_csv_gz({"package_uuid": "no-such-uuid"})
        self.assertEqual(parser(gzipped_csv(self.CSV)), {})

    def test_columns_not_in_the_csv_are_ignored(self):
        """Tests that a filter on a column that is not there does not exclude rows"""
        parser = find_first_in_csv_gz(
            {"package_uuid": "split-uuid", "not_a_column": "banana"}
        )
        self.assertEqual(parser(gzipped_csv(self.CSV))["request_addrs"], "30")
