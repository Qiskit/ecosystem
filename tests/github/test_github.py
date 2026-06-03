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
