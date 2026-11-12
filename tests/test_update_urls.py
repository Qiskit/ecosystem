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

"""Tests for Member.update_urls, which marks the submitted URLs that no longer resolve"""

from unittest import TestCase
from unittest.mock import patch

import requests

from ecosystem.github import GitHubData
from ecosystem.member import Member
from ecosystem.request import URL


class UpdateUrlsCase(TestCase):
    """Shared setup. No tests of its own: a subclass of a TestCase that has them re-runs
    every one of them, which is how 12 tests came to run three times each.

    Like every other updater `update_urls` mutates the member and returns nothing, so each
    test reads the field afterwards. `update` returns what reached the network, for the
    cases that are about which URL gets requested rather than what is stored.
    """

    def member(self, **fields):
        """A member with those URL fields and nothing else of interest"""
        return Member(
            name="Banana",
            url=fields.pop("url", "https://github.com/banana-org/banana"),
            maturity="experimental",
            **fields,
        )

    def update(self, member, answers):
        """Runs `update_urls` with `URL.status` answering out of `answers`

        `answers` maps a URL string to the status it returns; a URL that is not in it
        answers 200, which is the quiet case. Returns the URLs asked, in order.
        """
        asked = []

        def status(self, delay=None):  # pylint: disable=unused-argument
            asked.append(str(self))
            return answers.get(str(self), 200)

        with patch.object(URL, "status", status):
            member.update_urls()
        return asked


class MarkingTestCase(UpdateUrlsCase):
    """What a status does to a field that is not already marked"""

    def test_a_dead_url_is_marked_in_place(self):
        """The link it had is kept as the only clue to what it should be, plus the status"""
        dead = "https://qiskit.github.io/qiskit-addon-cutting/"
        member = self.member(documentation=dead)
        self.update(member, {dead: 404})
        self.assertEqual(
            "status-404://qiskit.github.io/qiskit-addon-cutting/",
            str(member.documentation),
        )

    def test_a_410_is_marked_with_its_own_status(self):
        """Gone is as dead as not found, and the member file says which it was"""
        dead = "https://x.example/docs"
        member = self.member(documentation=dead)
        self.update(member, {dead: 410})
        self.assertEqual("status-410://x.example/docs", str(member.documentation))

    def test_a_url_that_answers_is_left_exactly_as_submitted(self):
        """This detects dead links and nothing else, so a redirect is not its business: a
        project that renamed its repository keeps the URL it submitted, which still works
        """
        renamed = "https://github.com/cda-tum/mqt-qmap"
        member = self.member(url=renamed)
        self.update(member, {renamed: 200})
        self.assertEqual(renamed, str(member.url))

    def test_what_is_not_a_dead_link_is_not_marked(self):
        """Only 404 and 410 are a verdict: a bot wall, a 5xx and an unreachable host are
        all the host having a bad day, and marking one would be a false report"""
        url = "https://flaky.example/"
        for status in (403, 429, 500, 503, None):
            with self.subTest(status=status):
                member = self.member(website=url)
                self.update(member, {url: status})
                self.assertEqual(url, str(member.website))

    def test_a_field_that_is_not_set_is_skipped(self):
        """Most members have no website and no reference_paper"""
        member = self.member()
        self.assertIsNone(member.website)
        self.update(member, {})
        self.assertIsNone(member.website)

    def test_the_submitted_fields_are_asked_and_github_is_not(self):
        """`[github]` comes back from the API on every run, so it self-heals"""
        member = self.member(
            documentation="https://a.example/docs",
            website="https://b.example/",
            reference_paper="https://doi.org/10.5281/zenodo.1",
            github={"url": "https://github.com/old/repo"},
        )
        self.assertEqual(
            [
                "https://github.com/banana-org/banana",
                "https://a.example/docs",
                "https://b.example/",
                "https://doi.org/10.5281/zenodo.1",
            ],
            self.update(member, {}),
        )


class StatusTestCase(TestCase):
    """`URL.status` is the one network call, and HEAD is only ever an optimization"""

    def respond(self, head, get=None):
        """Patches requests.head/get to answer with those statuses, and returns the calls"""
        calls = []

        class Response:  # pylint: disable=too-few-public-methods
            """Only what `status` reads"""

            def __init__(self, code):
                self.status_code = code
                self.ok = code < 400

            def close(self):
                """`status` closes the streamed GET without reading its body"""

        def fake(method, code):
            def call(_url, **_kwargs):
                calls.append(method)
                return Response(code)

            return call

        with patch("ecosystem.request.requests.head", fake("head", head)), patch(
            "ecosystem.request.requests.get", fake("get", get if get else head)
        ):
            status = URL("https://x.example/").status()
        return status, calls

    def test_a_successful_head_is_the_answer(self):
        """The common case: one request per URL"""
        self.assertEqual((200, ["head"]), self.respond(200))

    def test_any_failing_head_is_re_asked_with_get(self):
        """The VS Code marketplace answers 404 to HEAD and 200 to GET for a published
        extension, and a 404 is the status that gets written into a member file"""
        for head in (403, 404, 405, 410, 429, 500, 501):
            with self.subTest(head=head):
                status, calls = self.respond(head, get=200)
                self.assertEqual(200, status)
                self.assertEqual(["head", "get"], calls)

    def test_a_genuine_404_survives_the_second_ask(self):
        """Both methods agree, so the link really is gone"""
        self.assertEqual((404, ["head", "get"]), self.respond(404))

    def test_marking_round_trips_every_part_of_the_url(self):
        """The marker is supposed to be the link the member file had, so marking and
        unmarking have to be exact. Rebuilding from hostname/path/query dropped a
        `;params` segment, which a SICI-style DOI carries"""
        for url in (
            "https://doi.org/10.1002/(SICI)1097-0258(19980815/30)17:15/16;2-2",
            "https://marketplace.visualstudio.com/items?itemName=qiskit.qiskit-vscode",
            "https://github.com/o/r/blob/HEAD/packages/*/pyproject.toml",
            "https://x.example/a;b/c?q=1;2",
        ):
            with self.subTest(url):
                marked = URL(url).marked(404)
                self.assertTrue(marked.is_broken)
                self.assertEqual(url, str(marked.unmarked))

    def test_a_connection_error_is_not_a_status(self):
        """None, rather than raising, so one unreachable host does not end the run"""
        with patch(
            "ecosystem.request.requests.head",
            side_effect=requests.ConnectionError("boom"),
        ):
            self.assertIsNone(URL("https://x.example/").status())


class MarkerLifecycleTestCase(UpdateUrlsCase):
    """What happens to a `status-<status>://` marker on the runs after it was written"""

    def test_a_marked_url_is_re_asked_at_its_own_address(self):
        """The marker is not itself a reachable URL, so the live one is what gets asked"""
        member = self.member(documentation="status-404://x.example/docs")
        asked = self.update(member, {"https://x.example/docs": 200})
        self.assertIn("https://x.example/docs", asked)

    def test_a_marked_url_is_cleared_when_it_answers_again(self):
        """A project that fixes its documentation should not need a hand-edit here"""
        member = self.member(documentation="status-404://x.example/docs")
        self.update(member, {"https://x.example/docs": 200})
        self.assertEqual("https://x.example/docs", str(member.documentation))

    def test_a_marked_url_that_is_still_dead_stays_as_it_is(self):
        """And `DAO.log_update` stays quiet, so a daily run does not re-report it"""
        marked = "status-404://x.example/docs"
        member = self.member(documentation=marked)
        self.update(member, {"https://x.example/docs": 404})
        self.assertEqual(marked, str(member.documentation))

    def test_a_marked_url_takes_the_new_status_when_it_changes(self):
        """404 becoming 410 is the host saying something different about the same link"""
        member = self.member(documentation="status-404://x.example/docs")
        self.update(member, {"https://x.example/docs": 410})
        self.assertEqual("status-410://x.example/docs", str(member.documentation))

    def test_a_marked_url_is_not_cleared_by_a_bot_wall(self):
        """403 does not say the link is back, so the marker stands until something does"""
        marked = "status-404://x.example/docs"
        member = self.member(documentation=marked)
        self.update(member, {"https://x.example/docs": 403})
        self.assertEqual(marked, str(member.documentation))


class PackagesTestCase(UpdateUrlsCase):
    """`packages` is checked too, and a pattern only as far as its first wildcard"""

    def test_a_pattern_is_asked_up_to_the_wildcard(self):
        """`.../packages/*/pyproject.toml` has no single target, the directory has"""
        member = self.member(
            packages=["https://github.com/o/r/blob/HEAD/packages/*/pyproject.toml"]
        )
        asked = self.update(member, {})
        self.assertIn("https://github.com/o/r/blob/HEAD/packages", asked)

    def test_a_dead_pattern_directory_marks_the_whole_entry(self):
        """The pattern is kept, wildcard and all: it is what has to be fixed"""
        pattern = (
            "https://github.com/QuBins/qiskit-images/blob/main/versions/"
            "*/requirements.txt"
        )
        member = self.member(packages=[pattern])
        self.update(
            member, {"https://github.com/QuBins/qiskit-images/blob/main/versions": 404}
        )
        self.assertEqual(
            "status-404://github.com/QuBins/qiskit-images/blob/main/versions/"
            "*/requirements.txt",
            str(member.packages[0]),
        )

    def test_a_live_pattern_directory_leaves_the_entry_alone(self):
        """The everyday case, and the wildcard survives it"""
        pattern = "https://github.com/o/r/blob/HEAD/packages/*/pyproject.toml"
        member = self.member(packages=[pattern])
        self.update(member, {})
        self.assertEqual(pattern, str(member.packages[0]))

    def test_a_working_blob_url_is_never_second_guessed(self):
        """Asked as submitted first: a ref that answers stands, whatever the member's
        `tree` says, so a link on another branch is not rewritten into a 404"""
        submitted = "https://github.com/o/r/blob/development/reqs.txt"
        member = self.member(
            packages=[submitted],
            github=GitHubData(owner="o", repo="r", tree="a-branch"),
        )
        asked = self.update(member, {})
        self.assertEqual([submitted], [a for a in asked if "blob" in a])
        self.assertEqual(submitted, str(member.packages[0]))

    def test_a_blob_url_dead_at_its_own_ref_is_retried_on_the_member_branch(self):
        """`declared_requirements` reads `[github] tree`, not the ref in the link, so a
        file missing from the ref the link names is not missing from the project"""
        submitted = "https://github.com/o/r/blob/HEAD/reqs.txt"
        member = self.member(
            packages=[submitted],
            github=GitHubData(owner="o", repo="r", tree="a-branch"),
        )
        self.update(member, {submitted: 404})
        self.assertEqual(submitted, str(member.packages[0]))

    def test_a_blob_url_dead_on_both_refs_is_marked(self):
        """Gone from the link's ref and from the member's branch is gone"""
        submitted = "https://github.com/o/r/blob/HEAD/reqs.txt"
        member = self.member(
            packages=[submitted],
            github=GitHubData(owner="o", repo="r", tree="a-branch"),
        )
        self.update(
            member,
            {submitted: 404, "https://github.com/o/r/blob/a-branch/reqs.txt": 404},
        )
        self.assertEqual(
            "status-404://github.com/o/r/blob/HEAD/reqs.txt", str(member.packages[0])
        )

    def test_a_blob_url_is_asked_as_submitted_with_no_tree(self):
        """Most members declare no branch, and then the ref they wrote is left alone
        rather than churned to `HEAD`"""
        member = self.member(packages=["https://github.com/o/r/blob/main/reqs.txt"])
        self.assertIn(
            "https://github.com/o/r/blob/main/reqs.txt", self.update(member, {})
        )

    def test_a_query_is_not_a_wildcard(self):
        """`?itemName=...` on the VS Code marketplace is a real URL, not a pattern, so the
        whole thing is asked rather than the `/items` path before the `?`"""
        marketplace = (
            "https://marketplace.visualstudio.com/items?itemName=qiskit.qiskit-vscode"
        )
        member = self.member(packages=[marketplace])
        self.assertIn(marketplace, self.update(member, {}))

    def test_a_marked_entry_keeps_its_query(self):
        """`marketplace.visualstudio.com/items` without `?itemName=...` is not the link:
        the marker has to round trip back to the URL it marked"""
        marketplace = (
            "https://marketplace.visualstudio.com/items?itemName=qiskit.qiskit-vscode"
        )
        member = self.member(packages=[marketplace])
        self.update(member, {marketplace: 404})
        self.assertEqual(
            "status-404://marketplace.visualstudio.com/items"
            "?itemName=qiskit.qiskit-vscode",
            str(member.packages[0]),
        )

    def test_one_dead_entry_does_not_cost_the_others(self):
        """Each entry stands on its own"""
        member = self.member(
            packages=[
                "https://pypi.org/project/gone/",
                "https://pypi.org/project/live/",
            ]
        )
        self.update(member, {"https://pypi.org/project/gone/": 404})
        self.assertEqual(
            ["status-404://pypi.org/project/gone/", "https://pypi.org/project/live/"],
            [str(package) for package in member.packages],
        )


class UpsertSectionsWithMarkedUrlsTestCase(TestCase):
    """`create_sections` does not read a section out of a URL that does not resolve

    `from_url` only parses, so a `status-404://` link would seed an `owner`/`repo`, or a
    distribution name, as if it were live — and every check up on that section would then
    report on something the URL itself says is gone.
    """

    @staticmethod
    def member(url, packages=()):
        """A member with no sections yet, as a fresh submission has"""
        return Member(
            name="Banana",
            url=url,
            maturity="experimental",
            packages=[URL(package) for package in packages],
        )

    def test_a_marked_url_seeds_no_github_section(self):
        """The whole repository is gone, which is `qubinsorg_6c640264` in the corpus"""
        member = self.member("status-404://github.com/QuBins/qiskit-images")
        member.upsert_sections()
        self.assertFalse(member.github)

    def test_a_live_url_still_seeds_one(self):
        """The guard is about the marker, not about being careful in general"""
        member = self.member("https://github.com/QuBins/qiskit-images")
        member.upsert_sections()
        self.assertEqual("QuBins", member.github.owner)
        self.assertEqual("qiskit-images", member.github.repo)

    def test_a_marked_package_is_skipped_and_the_live_ones_are_not(self):
        """One dead distribution does not cost the member its other sections"""
        member = self.member(
            "https://github.com/o/r",
            packages=[
                "status-404://pypi.org/project/gone/",
                "https://pypi.org/project/live/",
            ],
        )
        member.upsert_sections()
        self.assertEqual(["live"], [pypi.package_name for pypi in member.pypi])

    def test_a_stored_github_section_survives_its_url_being_marked(self):
        """`upsert_sections` only ever creates one, so a section already there is kept:
        dropping it would lose the owner/repo that is the only record of what it was"""
        member = self.member("status-404://github.com/QuBins/qiskit-images")
        member.github = GitHubData(owner="QuBins", repo="qiskit-images")
        member.upsert_sections()
        self.assertEqual("QuBins", member.github.owner)
