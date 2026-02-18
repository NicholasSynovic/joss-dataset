"""Entry point for the unified ``joss`` command-line application."""

import argparse
import sys
from pathlib import Path

from joss import APPLICATION_NAME
from joss.cli import CLI
from joss.ingest.joss import JOSSIngest
from joss.logger import JOSSLogger
from joss.transform.joss import JOSSTransform
from joss.transform.schemas import NormalIssue
from joss.utils import JOSSUtils


def main() -> int:
    args = CLI().run()

    if args.command is None:
        sys.exit(1)

    logger: JOSSLogger = JOSSLogger(name=__name__)
    logger.setup_file_logging(prefix=APPLICATION_NAME)

    if args.command == "ingest":
        # Get GitHub issues from openjournals/joss-review
        issues: list[dict] = JOSSIngest(
            jossLogger=logger,
            token=CLI.get_token(),
            max_pages=args.max_pages,
        ).execute()

        # Save issues to a JSON file
        json_path: Path = Path(
            f"github_issues_{logger.timestamp}.json",
        ).absolute()
        JOSSUtils.save_json(issues, json_path, indent=4)

        logger.get_logger().info("Saved to: %s", json_path)

    elif args.command == "transform":
        # Normalize JOSS collected GitHub issues
        out_path = Path(
            f"github_issues_normalized_{logger.timestamp}.json",
        )
        normalizedIssues: list[NormalIssue] = JOSSTransform(
            jossLogger=logger,
            in_file=args.in_file,
        ).execute()
        JOSSUtils.save_json(
            data=[issue.model_dump() for issue in normalizedIssues],
            path=out_path,
        )

        logger.get_logger().info(
            "Wrote %s normal issues to %s.", len(normalizedIssues), out_path
        )

    else:
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
