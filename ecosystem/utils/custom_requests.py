"""Custom requests for GitHub to get statuses of workflows for main repos."""
import json
from typing import Optional

import requests

from ecosystem.models.utils import UnknownPackageVersion
from ecosystem.utils import logger


def get_workflow_status(
    repo: str,
    name_of_workflow: str,
    owner: str = "Qiskit",
    branch: str = "main",
    event: str = "push",
) -> Optional[bool]:
    """Get status for GitHub workflow."""
    url = "https://api.github.com/repos/{owner}/{repo}/actions/runs".format(
        owner=owner, repo=repo
    )
    params = {"event": event, "branch": branch, "name": name_of_workflow, "per_page": 1}
    response = requests.get(url, params=params)
    result = None
    if response.ok:
        response_data = json.loads(response.text)
        runs = response_data.get("workflow_runs", [])
        if len(runs) > 0:
            last_run = runs[0]
            conclusion = last_run.get("conclusion", None)
            logger.info("Workflow run status conclusion: %s", str(conclusion))
            result = conclusion == "success"
        else:
            logger.warning("No workflow runs for params: %s", str(params))
            result = False
    else:
        logger.error("Response from GitHub is not ok: %s", response.text)
    return result


def get_stable_terra_version() -> str:
    """Returns stable Qiskit-terra version."""
    url = "https://api.github.com/repos/Qiskit/qiskit-terra/releases"
    response = requests.get(url, params={"per_page": 1})
    version = UnknownPackageVersion
    if response.ok:
        releases = json.loads(response.text)
        if len(releases) > 0:
            latest_release = releases[0]
            version = latest_release["tag_name"].strip()
        else:
            logger.warning("No releases found during terra version fetch.")
    else:
        logger.warning(
            "GitHub api returned non success code during terra release fetch."
        )
    return version


def get_dev_terra_version() -> str:
    """Returns dev Qiskit-terra version."""
    url = (
        "https://raw.githubusercontent.com/Qiskit/qiskit-terra/main/qiskit/VERSION.txt"
    )
    response = requests.get(url)
    version = UnknownPackageVersion
    if response.ok:
        version = response.text.strip()
    else:
        logger.warning("Cannot fetch terra version.")
    return version
