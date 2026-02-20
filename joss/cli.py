"""CLI argument helpers for the unified JOSS command."""

# Copyright (c) 2025 Nicholas M. Synovic

import argparse
import os
from argparse import ArgumentParser, Namespace
from pathlib import Path

from joss import APPLICATION_NAME


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
            "-i",
            "--in-file",
            required=required,
            help="Path to input JSON file containing array of GitHub issues.",
        )

    @staticmethod
    def add_out_file_argument(
        parser: argparse.ArgumentParser,
        *,
        required: bool = True,
    ) -> None:
        """
        Add the ``--our-file`` argument to a parser.

        Args:
            parser: The argument parser to augment.
            required: Whether the argument is mandatory.

        """
        parser.add_argument(
            "-o",
            "--out-file",
            required=required,
            help="SQLite3 database path to write to.",
            type=Path,
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

    def run(self) -> Namespace:
        """
        Build and run the CLI argument parser.

        Returns:
            Parsed command-line arguments as a Namespace object.

        """
        # Setup top level parser
        parser = ArgumentParser(
            prog=APPLICATION_NAME,
            description=f"{APPLICATION_NAME} dataset toolkit.",
        )

        # Setup subparser handler
        subparsers = parser.add_subparsers(
            dest="dataset",
        )

        # Create ingest subparser
        ingest_parser = subparsers.add_parser(
            "joss",
            help="Get all Journal of Open Source Software (JOSS) projects.",
        )
        self.add_out_file_argument(parser=ingest_parser, required=True)

        # Parse args
        return parser.parse_args()
