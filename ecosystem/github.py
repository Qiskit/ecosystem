"""GitHub section."""

from urllib.parse import ParseResult
from re import match
import json

from .serializable import JsonSerializable
from .error_handling import EcosystemError, logger
from .request import request_json


class GitHubData(JsonSerializable):
    """
    The GitHub data related to a project
    """

    aliases = {"stars": "stargazers_count"}
    dict_keys = ["owner", "repo", "tree", "stars"]

    def __init__(self, owner: str, repo: str, tree: str = None, **kwargs):
        self.owner = owner
        self.repo = repo
        self.tree = tree
        self._kwargs = kwargs or {}
        self._json_data = None

    def __eq__(self, other):
        return all([getattr(self, k, None) == getattr(other, k, None) for k in GitHubData.dict_keys])

    def __str__(self):
        return str(self.to_dict())

    def to_dict(self) -> dict:
        dictionary = {}
        for key in GitHubData.dict_keys:
            value = getattr(self, key, None)
            if value is not None:
                dictionary[key] = value
        return dictionary

    @classmethod
    def from_url(cls, github_project_url: ParseResult):
        """
        Builds a GitHubSection from an url. Returns None
        if the given url is not a GitHub url
        """
        if "github.com" not in github_project_url:
            # github_project_url is not a GitHub URL
            return None

        tree_path = None
        url_path = github_project_url.path.replace("github.com", "")
        if "/tree/" in url_path:
            new_path, tree_path = url_path.split("/tree/")
            logger.debug(
                "%s includes a branch or a subdirectories: %s | %s",
                url_path,
                new_path,
                tree_path,
            )
            url_path = new_path
        try:
            owner, repo = [
                c for c in url_path.split("/") if match(r"^[A-Za-z0-9_.-]+$", c)
            ]
        except ValueError as exc:
            raise EcosystemError(
                f"invalid GitHub url: {github_project_url}"
            ) from exc

        return GitHubData(owner=owner, repo=repo, tree=tree_path)

    def update_json(self):
        """
        Fetches remote json data from api.github.com/repos/{self.owner}/{self.repo}
        """
        self._json_data = request_json(f"api.github.com/repos/{self.owner}/{self.repo}")

    def __getattr__(self, item):
        if self._json_data:
            ret = self._json_data.get(GitHubData.aliases.get(item, item))
        else:
            ret = self._kwargs.get(item)
        if ret is None:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{item}'")
        return ret

    def update_owner_repo(self):
        if self._json_data is None:
            self.update_json()
        owner = self._json_data['owner']['login']
        repo = self._json_data['name']
        if self.owner != owner or self.repo != repo:
            logger.info(f"{self.owner}/{self.repo} move to {owner}/{repo}")
            self.owner = owner
            self.repo = repo
