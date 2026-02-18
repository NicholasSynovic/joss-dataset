"""CLI argument helpers for the unified JOSS command."""

from __future__ import annotations

import argparse
import os


class CLI:
    """Reusable argument definitions for JOSS sub-commands."""

    @staticmethod
    def add_max_pages_argument(parser: argparse.ArgumentParser) -> None:
        """
        Add the ``--max-pages`` optional argument to a parser.

        Args:
            parser: The argument parser to augment.

        """
        parser.add_argument(
            "--max-pages",
            type=int,
            default=None,
            help=("Maximum number of pages to fetch (for testing). Default: no limit."),
        )

    @staticmethod
    def add_in_file_argument(
        parser: argparse.ArgumentParser,
        *,
        required: bool = True,
    ) -> None:
        """
        Add the ``--in-file`` argument to a parser.

        Args:
            parser: The argument parser to augment.
            required: Whether the argument is mandatory.

        """
        parser.add_argument(
            "--in-file",
            required=required,
            help="Path to input JSON file containing array of GitHub issues.",
        )

    @staticmethod
    def get_token() -> str:
        """
        Read `GITHUB_TOKEN` from the environment.

        Returns:
            The GitHub token read from the `GITHUB_TOKEN` environment variable.

        Raises:
            RuntimeError: If `GITHUB_TOKEN` is missing/empty.

        """
        token: str = os.environ.get("GITHUB_TOKEN", "").strip()
        if not token:
            msg = (
                "Missing GITHUB_TOKEN environment variable.\n"
                "Set it before running, e.g.:\n"
                "  export GITHUB_TOKEN='ghp_...'\n"
                "or (PowerShell):\n"
                '  setx GITHUB_TOKEN "ghp_..."'
            )
            raise RuntimeError(msg)
        return token
