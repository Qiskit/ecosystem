"""GitHub section."""

from re import match
from functools import reduce
from jsonpath import findall

from .serializable import JsonSerializable, parse_datetime
from .error_handling import EcosystemError, logger
from .request import (
    request_json,
    parse_github_package_ids,
    parse_github_dependants,
    parse_github_front_page,
    URL,
)


class GitHubData(JsonSerializable):
    """
    The GitHub data related to a project
    """

    dict_keys = [
        "url",
        "owner",
        "repo",
        "tree",
        "stars",
        "homepage",
        "license",
        "description",
        "estimated_contributors",
        "total_dependent_repositories",
        "total_dependent_packages",
        "private",
        "archived",
        "disabled",
        "last_commit",
        "last_activity",
    ]
    aliases = {
        "stars": "stargazers_count",
        "last_commit": "pushed_at",
        "url": "html_url",
        "license": "license.name",
    }
    json_types = {
        "homepage": lambda x: x or None,
        "private": lambda x: x or None,
        "archived": lambda x: x or None,
        "disabled": lambda x: x or None,
        "description": lambda x: x[:131] + "..." if len(str(x)) > 135 else x,
        "pushed_at": parse_datetime,
    }
    reduce = {}

    def __init__(self, owner: str, repo: str, tree: str = None, **kwargs):
        self.owner = owner
        self.repo = repo
        self.tree = tree
        self._kwargs = kwargs or {}
        self._json_repo = None
        self._json_events = None
        self._json_package_ids = None
        self._json_dependants = None
        self._json_front_page = None

    def to_dict(self) -> dict:
        dictionary = {}
        for key in GitHubData.dict_keys:
            value = getattr(self, key, None)
            if value is not None:
                dictionary[key] = value
        return dictionary

    @classmethod
    def from_url(cls, github_project_url: URL):
        """
        Builds a GitHubSection from an url. Returns None
        if the given url is not a GitHub url
        """
        if "github.com" not in github_project_url.hostname:
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
            raise EcosystemError(f"invalid GitHub url: {github_project_url}") from exc

        return GitHubData(owner=owner, repo=repo, tree=tree_path)

    def update_json(self):
        """
        Fetches remote data from:
          - api.github.com/repos/{self.owner}/{self.repo}
          - github.com/{self.owner}/{self.repo}/network/dependents
          - github.com/{self.owner}/{self.repo}
          - api.github.com/networks/{self.owner}/{self.repo}/events

        """
        self._json_repo = request_json(f"api.github.com/repos/{self.owner}/{self.repo}")
        self._json_events = request_json(
            f"api.github.com/networks/{self.owner}/{self.repo}/events"
        )
        self._json_front_page = request_json(
            f"github.com/{self.owner}/{self.repo}/",
            parser=parse_github_front_page,
        )
        self._json_package_ids = request_json(
            f"github.com/{self.owner}/{self.repo}/network/dependents?dependent_type=REPOSITORY",
            parser=parse_github_package_ids,
        )
        self._json_dependants = {}
        for package, package_id in self._json_package_ids.items():
            self._json_dependants[package] = request_json(
                f"github.com/{self.owner}/{self.repo}/network/dependents?"
                f"dependent_type=REPOSITORY&package_id={package_id}",
                parser=parse_github_dependants,
            )

    def __getattr__(self, item):
        if self._json_repo:
            if item in GitHubData.aliases:
                item = GitHubData.aliases[item]

            json_elements = findall(item, self._json_repo)
            if item in GitHubData.json_types:
                json_elements = [GitHubData.json_types[item](e) for e in json_elements]

            if len(json_elements) == 1:
                return json_elements[0]

            if len(json_elements) >= 2:
                return reduce(GitHubData.reduce[item], json_elements)

            raise AttributeError(
                f"'{type(self).__name__}' object has no " f"attribute '{item}'"
            )

        if item in self._kwargs:
            return self._kwargs[item]

        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{item}'"
        )

    def update_owner_repo(self):
        """
        Updates GitHub page when the repo was moved or renamed
        """
        if self._json_repo is None:
            self.update_json()
        owner = self._json_repo["owner"]["login"]
        repo = self._json_repo["name"]
        if self.owner != owner or self.repo != repo:
            logger.info("%s/%s moved to %s/%s", self.owner, self.repo, owner, repo)
            self.owner = owner
            self.repo = repo

    def dependants(self, refresh=False):
        """get the dependant data from (cached) JSON"""
        if refresh:
            self.update_json()
        return self._json_dependants

    def front_page_data(self, refresh=False):
        """get the front page data from (cached) JSON"""
        if refresh:
            self.update_json()
        return self._json_front_page

    @property
    def estimated_contributors(self):
        """..."""
        if self.front_page_data():
            return self.front_page_data()["estimated_contributors"]
        return self._kwargs.get("estimated_contributors")

    @property
    def total_dependent_repositories(self):
        """Sum of repository dependants"""
        if self.dependants():
            return sum(r.get("repositories", 0) for r in self.dependants().values())
        return self._kwargs.get("total_dependent_repositories")

    @property
    def total_dependent_packages(self):
        """Sum of package dependants"""
        if self.dependants():
            return sum(r.get("packages", 0) for r in self.dependants().values())
        return self._kwargs.get("total_dependent_packages")

    @property
    def last_activity(self):
        """The creation of the last event"""
        if self._json_events:
            return parse_datetime(self._json_events[0]["created_at"])
        return self._kwargs.get("last_activity")
