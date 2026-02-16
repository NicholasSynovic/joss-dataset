"""Entry point for the unified ``joss`` command-line application."""

import argparse
import sys
from pathlib import Path

from joss.cli import CLI
from joss.ingest.joss import JOSSIngest
from joss.logger import JOSSLogger
from joss.transform.joss import JOSSTransform
from joss.utils import JOSSUtils


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

    timestamp: int = JOSSUtils.get_timestamp()
    logger: JOSSLogger = JOSSLogger(name=__name__)

    if args.command == "ingest":
        # Get GitHub issues from openjournals/joss-review
        issues: list[dict] = JOSSIngest(
            token=CLI.get_token(),
            max_pages=args.max_pages,
        ).execute()

        # Save issues to a JSON file
        json_path: Path = Path(
            f"github_issues_{timestamp}.json",
        ).absolute()
        JOSSUtils.save_json(issues, json_path, indent=4)

        logger.get_logger().info("Saved to: %s", json_path)
        return 0

    elif args.command == "transform":
        # Normalize JOSS collected GitHub issues
        exit_code = JOSSTransform(in_file=args.in_file).execute()
    else:
        parser.print_help()
        sys.exit(1)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
