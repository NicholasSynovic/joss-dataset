"""Entry point for the unified ``joss`` command-line application."""

import argparse
import sys

from joss.cli import CLI
from joss.ingest.joss import JOSSIngest
from joss.transform.joss import JOSSTransform


def main() -> None:
    """
    Parse sub-commands and dispatch to the appropriate handler.

    Sub-commands:
        ingest    -- Collect issues from ``openjournals/joss-reviews``.
        transform -- Normalize a raw issues JSON file.

    """
    parser = argparse.ArgumentParser(
        prog="joss",
        description="JOSS dataset toolkit.",
    )
    subparsers = parser.add_subparsers(
        dest="command",
    )

    # -- ingest sub-command ------------------------------------
    ingest_parser = subparsers.add_parser(
        "ingest",
        help="Collect all issues from openjournals/joss-reviews.",
    )
    CLI.add_max_pages_argument(ingest_parser)

    # -- transform sub-command ---------------------------------
    transform_parser = subparsers.add_parser(
        "transform",
        help="Normalize raw GitHub issues JSON into a stable format.",
    )
    CLI.add_in_file_argument(transform_parser)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    if args.command == "ingest":
        exit_code = JOSSIngest(max_pages=args.max_pages).execute()
    elif args.command == "transform":
        exit_code = JOSSTransform(in_file=args.in_file).execute()
    else:
        parser.print_help()
        sys.exit(1)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
