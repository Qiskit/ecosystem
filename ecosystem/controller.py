"""Entrypoint for CLI."""
from typing import Optional, List

from tinydb import TinyDB, Query

from ecosystem.entities import Repository, MainRepository, Tier


class Controller:
    """Controller for repo database."""

    def __init__(self, path: Optional[str] = None):
        """Controller for repository database.

        Args:
            path: path to store database in
        """
        self.path = path if path is not None else "./"
        self.database = TinyDB('{}/members.json'.format(self.path), indent=4)

    def insert(self, repo: Repository) -> int:
        """Inserts repository into database."""
        table = self.database.table(repo.tier)
        return table.insert(repo.to_dict())

    def get_all_main(self) -> List[MainRepository]:
        """Returns all repositories from database."""
        table = self.database.table(Tier.MAIN)
        return [MainRepository(**r) for r in table.all()]

    def delete(self, repo: Repository) -> List[int]:
        """Deletes entry."""
        table = self.database.table(repo.tier)
        query = Query()
        return table.remove(query.name == repo.name and query.url == repo.url)
