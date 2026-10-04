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

"""Reading files out of a GitHub repository, for the sections built from a source tree.

Both `PythonData` and `RequirementsData` describe what a repository's default branch
says today, so both need the same two requests: what is in the directory, and what one
of those files contains. Mix this into a class that provides `owner` and `repo`.
"""

from os import getenv
from json import loads as json_loads

from .error_handling import logger
from .request import request_json


# Mixed into a data class that has the public surface; everything here is a helper.
class GitHubContentsMixin:  # pylint: disable=too-few-public-methods
    """Fetches a directory listing and single files from a repository's default branch."""

    #: Subdirectory holding the files, when they are not at the repository root.
    #: A class that cannot be pointed at a subdirectory leaves this alone.
    path = None

    @property
    def _contents_url(self):
        """Contents API endpoint for the directory the files are read from."""
        directory = f"{self.path.strip('/')}/" if self.path else ""
        return f"api.github.com/repos/{self.owner}/{self.repo}/contents/{directory}"

    def _request_listing(self):
        """Names of the files in the directory.

        Listing first means a project without, say, a setup.cfg costs no request
        for it. Asking for each file blindly would raise (and log an error) once
        per name for a repository that has none, which is a normal thing for
        a repository to be.
        """
        listing = request_json(
            self._contents_url,
            parser=lambda text: {"entries": json_loads(text)},
            token=getenv("GH_TOKEN"),
        )
        return {
            entry["name"]
            for entry in listing["entries"]
            if isinstance(entry, dict) and entry.get("type") == "file"
        }

    def _request_file(self, filename, parser):
        """Fetches one file as raw text.

        The `raw` media type makes the contents API return the file itself
        instead of a JSON envelope with base64, so `parser` can be a plain
        text parser. `request_json` caches for a day via requests_cache.
        """
        return request_json(
            f"{self._contents_url}{filename}",
            headers={"Accept": "application/vnd.github.raw"},
            content_handler=lambda content: content.decode("utf-8"),
            parser=parser,
            token=getenv("GH_TOKEN"),
        )

    def _request_tree(self):
        """Every file of the repository's default branch, as repository-relative paths.

        One request, unlike the per-directory `_request_listing`, which is what makes a
        pattern like `versions/*/requirements.txt` affordable: it is resolved against this
        list on every run, so a file added to the repository later is picked up.

        A repository too big for one response comes back truncated. The paths that did
        arrive are still usable, so they are returned, with a warning saying the match may
        be short.
        """
        tree = request_json(
            f"api.github.com/repos/{self.owner}/{self.repo}/git/trees/HEAD?recursive=1",
            token=getenv("GH_TOKEN"),
        )
        if tree.get("truncated"):
            logger.warning(
                "the file list of %s/%s is truncated, so a pattern may match less than it "
                "should",
                self.owner,
                self.repo,
            )
        return [
            entry["path"]
            for entry in tree.get("tree", [])
            if entry.get("type") == "blob"
        ]
