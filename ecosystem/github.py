"""GitHub section."""

from urllib.parse import ParseResult
from re import match
import json

from .serializable import JsonSerializable
from .error_handling import EcosystemError, logger
from .request import request


class GitHubData(JsonSerializable):
    """
    The GitHub data related to a project
    """

    aliases = {"stars": "stargazers_count"}
    dict_keys = ["org", "repo", "tree", "stars"]

    def __init__(self, org: str, repo: str, tree: str = None, **kwargs):
        self.org = org
        self.repo = repo
        self.tree = tree
        self._kwargs = kwargs or {}
        self._json_data = None

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
            user_org, repo = [
                c for c in url_path.split("/") if c and match(r"^[A-Za-z0-9_.-]+$", c)
            ]
        except ValueError as exc:
            raise EcosystemError(
                f"invalid repository url: {github_project_url}"
            ) from exc

        return GitHubData(org=user_org, repo=repo, tree=tree_path)

        # if detect_redirect:
        #     headers = {'Authorization': 'token ' + 'ghp_XXXX'}
        #     response = requests.get(f'https://api.github.com/repos/
        #     {user_org}/{repo}', headers=headers)
        #     print(response.status_code)
        #     if not response.ok:
        #         raise EcosystemError(f"api.github.com/repos/{user_org}/{repo} returned
        #         {response.status_code} ({response.reason})")
        #     json_response = json.loads(response.text)
        #     try:
        #         github_project_url = json_response['html_url']
        #     except AttributeError:
        #         EcosystemError(
        #             f"Bad JSON response for project: {user_org}/{repo}
        #             (Status: {response.status_code})")
        #     return self.github_org_and_repo_from_url(github_project_url, detect_redirect=False)

    def update_json(self):
        """
        Fetches remote json data from api.github.com/repos/{self.org}/{self.repo}
        """
        response = request(f"api.github.com/repos/{self.org}/{self.repo}")
        self._json_data = json.loads(response.text)

    def __getattr__(self, item):
        if self._json_data:
            ret = self._json_data.get(GitHubData.aliases.get(item, item))
        else:
            ret = self._kwargs.get(item)
        if ret is None:
            raise AttributeError
        return ret

    # def __setattr__(self, name, value):
    #     if name in GitHubData.dict_keys:
    #
    #     else:
    #         super().__setattr__(name, value)
