"""Entry point for the unified ``joss`` command-line application."""

# Copyright (c) 2025 Nicholas M. Synovic

import sys
from pathlib import Path
from typing import Any

from progress.bar import Bar

from joss import APPLICATION_NAME
from joss.cli import CLI
from joss.ingest.joss import JOSSIngest
from joss.logger import JOSSLogger
from joss.parsers import parse_joss_issue
from joss.transform.joss import JOSSTransform
from joss.transform.schemas import NormalIssue
from joss.utils import JOSSUtils


def main() -> int:
    """
    Entry point for the JOSS CLI application.

    Raises:
        RuntimeError: If input file does not exist or has invalid format.

    """
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
        normalized_issues: list[NormalIssue] = JOSSTransform(
            jossLogger=logger,
            in_file=args.in_file,
        ).execute()
        JOSSUtils.save_json(
            data=[issue.model_dump() for issue in normalized_issues],
            path=out_path,
        )

        logger.get_logger().info(
            "Wrote %s normal issues to %s.", len(normalized_issues), out_path
        )

    elif args.command == "parse":
        # Parse JOSS issue bodies from normalized JSON
        in_path = Path(args.in_file)
        if not in_path.exists():
            msg = f"Input file does not exist: {in_path}"
            raise RuntimeError(msg)

        logger.get_logger().info("Loading normalized issues from %s", in_path)
        data: Any = JOSSUtils.load_json(in_path)

        if not isinstance(data, list):
            msg = f"Expected JSON array in {in_path}, got {type(data).__name__}"
            raise RuntimeError(msg)

        parsed_issues: list[dict] = []
        skipped_count: int = 0

        with Bar("Parsing issue bodies...", max=len(data)) as bar:
            for issue in data:
                issue_number: int = issue["issue_number"]
                body: str = issue.get("body", "")
                if not body:
                    skipped_count += 1
                    logger.get_logger().warning(
                        "Skipping issue %s: empty body",
                        issue.get("issue_number", "unknown"),
                    )
                    continue

                parsed_body = parse_joss_issue(body)
                parsed_body["issue_number"] = issue_number
                parsed_issues.append(parsed_body)
                bar.next()

        # Save parsed issues to a JSON file
        out_path = Path(f"github_issues_parsed_{logger.timestamp}.json")
        JOSSUtils.save_json(parsed_issues, out_path, indent=4)

        logger.get_logger().info(
            "Wrote %s parsed issues to %s (skipped %s empty bodies).",
            len(parsed_issues),
            out_path,
            skipped_count,
        )

    else:
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
