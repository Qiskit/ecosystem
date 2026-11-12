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

"""Tests for ecosystem/github.py"""

from unittest import TestCase
from unittest.mock import patch
from datetime import date
from ecosystem.github import GitHubData
from ecosystem.request import URL
from ecosystem.error_handling import EcosystemError


class TestGitHubDataInit(TestCase):
    """Tests for GitHubData builder"""

    def test_init_basic(self):
        """onwer, repo are set and all _json_* fields default to None"""
        gh = GitHubData(owner="Qiskit", repo="qiskit-banana-compiler")
        self.assertEqual(gh.owner, "Qiskit")
        self.assertEqual(gh.repo, "qiskit-banana-compiler")
        self.assertIsNone(gh.tree)

    def test_init_with_tree(self):
        """tree argument is stored correctly."""
        gh = GitHubData(owner="Qiskit", repo="qiskit-banana-compiler", tree="main")
        self.assertEqual(gh.tree, "main")

    def test_init_with_kwargs(self):
        """extra kwargs are accessible as attributes"""
        gh = GitHubData(owner="Qiskit", repo="qiskit-banana-compiler", stars=100)
        self.assertEqual(gh.stars, 100)


class TestGitHubDataFromUrl(TestCase):
    """Tests for GitHubData.from_url"""

    def setUp(self):
        self.github_url = URL("https://github.com/Qiskit/qiskit-banana-compiler")
        self.gitlab_url = URL("https://gitlab.com/")
        self.tree_url = URL(
            "https://github.com/Qiskit/qiskit-banana-compiler/tree/main"
        )
        self.invalid_url = URL("https://github.com/Qiskit")
        self.too_many_parts_url = URL(
            "https://github.com/Qiskit/qiskit-banana-compiler/extra/parts"
        )

    def test_valid_github_url(self):
        """Valid GitHub URL creates object with correct owner, repo and no tree"""
        gh = GitHubData.from_url(self.github_url)
        self.assertIsNotNone(gh)
        self.assertEqual(gh.owner, "Qiskit")
        self.assertEqual(gh.repo, "qiskit-banana-compiler")
        self.assertIsNone(gh.tree)

    def test_non_github_url_returns_none(self):
        """Non-GitHub URL returns None"""
        result = GitHubData.from_url(self.gitlab_url)
        self.assertIsNone(result)

    def test_url_with_tree_path(self):
        """GitHub URL with /tree/ correctly splits out the tree path"""
        gh = GitHubData.from_url(self.tree_url)
        self.assertIsNotNone(gh)
        self.assertEqual(gh.owner, "Qiskit")
        self.assertEqual(gh.repo, "qiskit-banana-compiler")
        self.assertEqual(gh.tree, "main")

    def test_invalid_url_too_few_parts_raise_error(self):
        """GitHub URL with only one path segment raises EcosystemEror"""
        with self.assertRaises(EcosystemError):
            GitHubData.from_url(self.invalid_url)

    def test_invalid_url_too_many_parts_raise_error(self):
        """GitHub URL with more than two path segments raises EcosystemError"""
        with self.assertRaises(EcosystemError):
            GitHubData.from_url(self.too_many_parts_url)


class TestGitHubDataToDict(TestCase):
    """Tests for GitHubData.to_dict"""

    def test_to_dict_has_owner_and_repo(self):
        """to_dict always includes owner and repo"""
        gh = GitHubData(owner="Qiskit", repo="qiskit-banana-compiler")
        d = gh.to_dict()
        self.assertIn("owner", d)
        self.assertIn("repo", d)
        self.assertEqual(d["owner"], "Qiskit")
        self.assertEqual(d["repo"], "qiskit-banana-compiler")

    def test_to_dict_excludes_none_values(self):
        """Keys with None values are not included in the dictionary"""
        gh = GitHubData(owner="Qiskit", repo="qiskit-banana-compiler")
        d = gh.to_dict()
        self.assertNotIn("tree", d)
        self.assertNotIn("homepage", d)

    def test_to_dict_includes_created_at_when_set(self):
        """created_at appears in dict when provided"""
        gh = GitHubData(
            owner="Qiskit", repo="qiskit-banana-compiler", created_at=date(2024, 1, 1)
        )
        d = gh.to_dict()
        self.assertIn("created_at", d)
        self.assertEqual(d["created_at"], date(2024, 1, 1))

    def test_to_dict_includes_tree_when_set(self):
        """tree appears in dict when provided"""
        gh = GitHubData(owner="Qiskit", repo="qiskit-banana-compiler", tree="main")
        d = gh.to_dict()
        self.assertIn("tree", d)
        self.assertEqual(d["tree"], "main")


class TestGitHubDataGetattr(TestCase):
    """Tests for GitHubData.__getattr__"""

    def setUp(self):
        self.gh = GitHubData(owner="Qiskit", repo="qiskit-banana-compiler")

    def test_getattr_alias_stars(self):
        """gh.stars resolves via alias stargazers_count from _json_repo"""
        with patch("ecosystem.github.request_json") as mock_request:
            mock_request.side_effect = [
                {"stargazers_count": 42, "_requested_at_": "2024-01-01"},
                {"data": [], "_requested_at_": "2024-01-01"},
                None,
                {},
            ]
            self.gh.update_json()
        self.assertEqual(self.gh.stars, 42)

    def test_getattr_alias_url(self):
        """gh.url resolves via alias html_url from _json_repo"""
        with patch("ecosystem.github.request_json") as mock_request:
            mock_request.side_effect = [
                {
                    "html_url": "https://github.com/Qiskit/qiskit-banana-compiler",
                    "_requested_at_": "2024-01-01",
                },
                {"data": [], "_requested_at_": "2024-01-01"},
                None,
                {},
            ]
            self.gh.update_json()
        self.assertEqual(
            self.gh.url, "https://github.com/Qiskit/qiskit-banana-compiler"
        )

    def test_getattr_alias_last_commit(self):
        """gh.last_commit resolves via alias pushed_at and returns a date"""
        with patch("ecosystem.github.request_json") as mock_request:
            mock_request.side_effect = [
                {"pushed_at": "2024-01-01T12:00:00", "_requested_at_": "2024-01-01"},
                {"data": [], "_requested_at_": "2024-01-01"},
                None,
                {},
            ]
            self.gh.update_json()
        self.assertIsInstance(self.gh.last_commit, date)

    def test_getattr_created_at(self):
        """gh.created_at is read from _json_repo and returns a date"""
        with patch("ecosystem.github.request_json") as mock_request:
            mock_request.side_effect = [
                {"created_at": "2018-06-11T20:16:32", "_requested_at_": "2024-01-01"},
                {"data": [], "_requested_at_": "2024-01-01"},
                None,
                {},
            ]
            self.gh.update_json()
        self.assertEqual(self.gh.created_at, date(2018, 6, 11))

    def test_getattr_created_at_from_kwargs(self):
        """gh.created_at falls back to the kwargs value when there is no JSON"""
        gh = GitHubData(
            owner="Qiskit", repo="qiskit-banana-compiler", created_at=date(2018, 6, 11)
        )
        self.assertEqual(gh.created_at, date(2018, 6, 11))

    def test_getattr_description_truncated(self):
        """description longer than 135 characters is truncated with ellipsis"""
        with patch("ecosystem.github.request_json") as mock_request:
            mock_request.side_effect = [
                {"description": "x" * 200, "_requested_at_": "2024-01-01"},
                {"data": [], "_requested_at_": "2024-01-01"},
                None,
                {},
            ]
            self.gh.update_json()
        self.assertTrue(self.gh.description.endswith("..."))

    def test_getattr_missing_key_raises_attribute_error(self):
        """accessing a key not in _json_repo raises AttributeError"""
        with patch("ecosystem.github.request_json") as mock_request:
            mock_request.side_effect = [
                {"some_key": "value", "_requested_at_": "2024-01-01"},
                {"data": [], "_requested_at_": "2024-01-01"},
                None,
                {},
            ]
            self.gh.update_json()
        with self.assertRaises(AttributeError):
            _ = self.gh.nonexistent

    def test_getattr_from_kwargs_when_no_json(self):
        """returns value from _kwargs when _json_repo is None"""
        gh = GitHubData(owner="Qiskit", repo="qiskit-banana-compiler", stars=99)
        self.assertEqual(gh.stars, 99)

    def test_getattr_missing_raises_attribute_error_no_json(self):
        """raises AttributeError when key absent from both _json_repo and _kwargs"""
        with self.assertRaises(AttributeError):
            _ = self.gh.nonexistent


class TestGitHubDataUpdateOwnerRepo(TestCase):
    """Tests for GitHubData.update_owner_repo"""

    def test_update_owner_repo_no_change(self):
        """owner and repo unchanged when JSON matches"""
        gh = GitHubData(owner="Qiskit", repo="qiskit-banana-compiler")
        with patch("ecosystem.github.request_json") as mock_request:
            mock_request.side_effect = [
                {
                    "owner": {"login": "Qiskit"},
                    "name": "qiskit-banana-compiler",
                    "_requested_at_": "2024-01-01",
                },
                {"data": [], "_requested_at_": "2024-01-01"},
                None,
                {},
            ]
            gh.update_json()
        gh.update_owner_repo()
        self.assertEqual(gh.owner, "Qiskit")
        self.assertEqual(gh.repo, "qiskit-banana-compiler")

    def test_update_owner_repo_detects_rename(self):
        """owner and repo updated when JSON has different values"""
        gh = GitHubData(owner="Qiskit", repo="qiskit-banana-compiler")
        with patch("ecosystem.github.request_json") as mock_request:
            mock_request.side_effect = [
                {
                    "owner": {"login": "NewOwner"},
                    "name": "new-repo",
                    "_requested_at_": "2024-01-01",
                },
                {"data": [], "_requested_at_": "2024-01-01"},
                None,
                {},
            ]
            gh.update_json()
        gh.update_owner_repo()
        self.assertEqual(gh.owner, "NewOwner")
        self.assertEqual(gh.repo, "new-repo")


class TestGitHubDataUpdateJson(TestCase):
    """Tests for GitHubData.update_json"""

    def test_update_json_populates_json_repo(self):
        """after update_json, data is accessible via public attributes"""
        gh = GitHubData(owner="Qiskit", repo="qiskit-banana-compiler")
        with patch("ecosystem.github.request_json") as mock_request:
            mock_request.side_effect = [
                {"stargazers_count": 42, "_requested_at_": "2024-01-01"},
                {"data": [], "_requested_at_": "2024-01-01"},
                None,
                {},
            ]
            gh.update_json()
        self.assertEqual(gh.stars, 42)

    def test_update_json_fetches_dependants_per_package(self):
        """fetches dependants for each package returned"""
        gh = GitHubData(owner="Qiskit", repo="qiskit-banana-compiler")
        fake_response = {"data": {}, "_requested_at_": "2024-01-01"}
        with patch("ecosystem.github.request_json") as mock_request:
            mock_request.side_effect = [
                fake_response,  # for _json_repo
                fake_response,  # for _json_events
                fake_response,  # for _json_contributors_sidebar
                {"pkg1": "id123"},  # for _json_package_ids
                fake_response,  # for dependants of pkg1
            ]
            gh.update_json()
            self.assertIn("pkg1", gh.dependants())


class TestGitHubDataProperties(TestCase):
    """Tests for dependants, contributors, and property methods"""

    def test_dependants_refresh_calls_update_json(self):
        """refresh=True triggers update_json()"""
        gh = GitHubData(owner="Qiskit", repo="qiskit-banana-compiler")
        with patch.object(GitHubData, "update_json") as mock_update:
            gh.dependants(refresh=True)
            mock_update.assert_called_once()

    def test_total_dependent_repositories_sums_correctly(self):
        """sums repositories across all packages in dependants"""
        gh = GitHubData(owner="Qiskit", repo="qiskit-banana-compiler")
        with patch("ecosystem.github.request_json") as mock_request:
            mock_request.side_effect = [
                {"_requested_at_": "2024-01-01"},
                {"data": [], "_requested_at_": "2024-01-01"},
                None,
                {"pkg1": "id1", "pkg2": "id2"},
                {"repositories": 10, "_requested_at_": "2024-01-01"},
                {"repositories": 5, "_requested_at_": "2024-01-01"},
            ]
            gh.update_json()
        self.assertEqual(gh.total_dependent_repositories, 15)

    def test_total_dependent_packages_sums_correctly(self):
        """sums packages across all packages in dependants"""
        gh = GitHubData(owner="Qiskit", repo="qiskit-banana-compiler")
        with patch("ecosystem.github.request_json") as mock_request:
            mock_request.side_effect = [
                {"_requested_at_": "2024-01-01"},
                {"data": [], "_requested_at_": "2024-01-01"},
                None,
                {"pkg1": "id1", "pkg2": "id2"},
                {"packages": 3, "_requested_at_": "2024-01-01"},
                {"packages": 7, "_requested_at_": "2024-01-01"},
            ]
            gh.update_json()
        self.assertEqual(gh.total_dependent_packages, 10)


class TestGitHubDataTopics(TestCase):
    """Tests for the `topics` field, the repository topics `update_github` records"""

    @staticmethod
    def fetched(repo_json):
        """A GitHubData that has fetched `repo_json` as its repository response."""
        gh = GitHubData(owner="Qiskit", repo="qiskit-banana-compiler")
        with patch("ecosystem.github.request_json") as mock_request:
            mock_request.side_effect = [
                dict(repo_json, _requested_at_="2024-01-01"),
                {"data": [], "_requested_at_": "2024-01-01"},
                None,
                {},
            ]
            gh.update_json()
        return gh

    def test_topics_are_read_from_the_repository_json(self):
        """gh.topics is the list the repository declares"""
        gh = self.fetched({"topics": ["qiskit", "quantum-computing"]})
        self.assertEqual(gh.topics, ["qiskit", "quantum-computing"])

    def test_topics_are_written_to_the_dict(self):
        """topics reaches to_dict, so `update_github` stores it in the member file"""
        gh = self.fetched({"topics": ["qiskit"]})
        self.assertEqual(gh.to_dict()["topics"], ["qiskit"])

    def test_a_repository_with_no_topics_reads_as_absent(self):
        """GitHub answers `[]` for a repository with no topic, which is not a value."""
        gh = self.fetched({"topics": []})
        self.assertIsNone(gh.topics)
        self.assertNotIn("topics", gh.to_dict())

    def test_topics_missing_from_the_json_raises(self):
        """A response with no `topics` key at all behaves like any other missing field"""
        gh = self.fetched({"some_key": "value"})
        with self.assertRaises(AttributeError):
            _ = gh.topics

    def test_topics_fall_back_to_the_stored_value(self):
        """gh.topics is read from the member file when nothing was fetched"""
        gh = GitHubData(
            owner="Qiskit", repo="qiskit-banana-compiler", topics=["qiskit"]
        )
        self.assertEqual(gh.topics, ["qiskit"])
        self.assertEqual(gh.to_dict()["topics"], ["qiskit"])

    def test_topics_round_trip_through_a_dict(self):
        """from_dict(to_dict()) keeps the topics, which is what a read-write cycle does"""
        stored = GitHubData(
            owner="Qiskit",
            repo="qiskit-banana-compiler",
            topics=["qiskit", "quantum-computing"],
        ).to_dict()
        self.assertEqual(
            GitHubData.from_dict(stored).to_dict()["topics"],
            ["qiskit", "quantum-computing"],
        )

    def test_a_stored_empty_list_is_kept_as_it_was_written(self):
        """`topics = []` already in a member file round-trips, rather than being dropped."""
        gh = GitHubData(owner="Qiskit", repo="qiskit-banana-compiler", topics=[])
        self.assertEqual(gh.to_dict()["topics"], [])


class TestGitHubDataRef(TestCase):
    """`ref` and `subdirectory`, the two halves of `tree`"""

    @staticmethod
    def of(tree):
        """The ref and the subdirectory such a `tree` stands for"""
        github = GitHubData(owner="Qiskit", repo="qiskit-banana-compiler", tree=tree)
        return github.ref, github.subdirectory

    def test_a_branch_and_a_directory(self):
        """`main/chemistry/sqd_pcm` is a directory of the default branch"""
        self.assertEqual(
            ("main", "chemistry/sqd_pcm"), self.of("main/chemistry/sqd_pcm")
        )

    def test_a_branch_on_its_own(self):
        """A URL that names a branch and nothing else is the whole of that branch"""
        self.assertEqual(("migration-to-csharp", None), self.of("migration-to-csharp"))

    def test_a_branch_and_a_directory_below_it(self):
        """Both halves are read, which is what issue #1428 asks for"""
        self.assertEqual(
            ("migration-to-csharp", "src/QutesLang/PythonCode"),
            self.of("migration-to-csharp/src/QutesLang/PythonCode"),
        )

    def test_no_tree_is_the_default_branch(self):
        """A member that names no branch reads the default one, as before `ref` existed"""
        self.assertEqual((None, None), self.of(None))
