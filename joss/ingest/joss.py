"""Unified ingest sub-command for the JOSS CLI."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import requests
from progress.spinner import Spinner

from joss.ingest.github_issues import (
    Config,
    RepoTarget,
    build_headers,
    fetch_issues_page,
    get_token,
)
from joss.logger import JOSSLogger
from joss.utils import JOSSUtils

JsonObject = dict[str, Any]
JsonList = list[JsonObject]


class JOSSIngest:
    """
    Collect all issues from ``openjournals/joss-reviews``.

    This class encapsulates the ingestion workflow used by the unified
    ``joss ingest`` CLI sub-command.  It mirrors the logic in the
    standalone ``github_issues.py`` script but delegates file I/O,
    logging, and timestamp handling to the shared utility classes.
    """

    def __init__(self, max_pages: int | None = None) -> None:
        """
        Initialise the ingest runner.

        Args:
            max_pages: Optional cap on the number of API pages to
                fetch.  ``None`` means fetch all available pages.

        """
        self._max_pages: int | None = max_pages

    def execute(self) -> int:
        """
        Run the full ingestion routine.

        Returns:
            Exit code (``0`` for success).

        """
        timestamp: int = JOSSUtils.get_timestamp()

        joss_logger = JOSSLogger(__name__)
        joss_logger.setup_file_logging(timestamp, "github_issues")
        logger: logging.Logger = joss_logger.get_logger()

        token: str = get_token()
        target = RepoTarget(owner="openjournals", repo="joss-reviews")
        config = Config(
            token=token,
            target=target,
            per_page=100,
            max_pages=self._max_pages,
            timestamp=timestamp,
        )

        session = requests.Session()
        session.headers.update(build_headers(config.token))

        page: int = 1
        total_fetched: int = 0
        all_issues: JsonList = []

        logger.info("Starting collection for %s.", config.target.full_name())

        spinner = Spinner(
            "Getting issues from `gh:openjournals/joss-reviews`... ",
        )

        while True:
            issues = fetch_issues_page(
                session,
                config.target,
                page=page,
                per_page=config.per_page,
                state="all",
            )
            spinner.next()

            if issues == []:
                break

            total_fetched += len(issues)
            all_issues.extend(issues)

            logger.info(
                "Page %s: fetched=%s total_collected=%s",
                page,
                len(issues),
                len(all_issues),
            )

            if len(issues) < config.per_page:
                break

            if config.max_pages is not None and page >= config.max_pages:
                logger.info(
                    "Reached max-pages=%s; stopping early.",
                    config.max_pages,
                )
                break

            page += 1

        spinner.finish()

        json_path: Path = Path(
            f"github_issues_{config.timestamp}.json",
        ).absolute()
        JOSSUtils.save_json(all_issues, json_path, indent=4)

        logger.info(
            "Done. total_fetched=%s total_issues=%s",
            total_fetched,
            len(all_issues),
        )
        logger.info("Saved to: %s", json_path)
        return 0
