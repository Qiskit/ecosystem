"""Ecosystem main module."""
import fire

from ecosystem.cli import CliMembers, CliCI, build_website


def main():
    fire.Fire(
        {
            "members": CliMembers,
            "build": build_website,
            "ci": CliCI,
        }
    )
