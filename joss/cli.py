"""CLI argument helpers for the unified JOSS command."""

# Copyright (c) 2025 Nicholas M. Synovic

import argparse
import os
from argparse import ArgumentParser, Namespace

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
            dest="command",
        )

        # Create ingest subparser
        ingest_parser = subparsers.add_parser(
            "ingest",
            help="Collect all issues from openjournals/joss-reviews.",
        )
        self.add_max_pages_argument(parser=ingest_parser)

        # Create transform subparser
        transform_parser = subparsers.add_parser(
            "transform",
            help="Normalize raw GitHub issues JSON into a stable format.",
        )
        self.add_in_file_argument(transform_parser)

        # Create parse subparser
        parse_parser = subparsers.add_parser(
            "parse",
            help="Parse JOSS issue bodies from normalized JSON into structured data.",
        )
        self.add_in_file_argument(parse_parser)

        # Parse args
        return parser.parse_args()
