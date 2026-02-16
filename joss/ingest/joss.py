"""Unified ingest sub-command for the JOSS CLI."""

import logging
from logging import Logger

import requests
from progress.spinner import Spinner
from requests import Session

from joss.ingest.github import GitHubIngest
from joss.ingest.repo_target import RepoTarget
from joss.logger import JOSSLogger
from joss.utils import JOSSUtils

HTTP_FORBIDDEN: int = 403
HTTP_OK: int = 200


class JOSSIngest(GitHubIngest):
    """
    Collect all issues from ``openjournals/joss-reviews``.

    This class encapsulates the ingestion workflow used by the unified
    ``joss ingest`` CLI sub-command.  It mirrors the logic in the
    standalone ``github_issues.py`` script but delegates file I/O,
    logging, and timestamp handling to the shared utility classes.
    """

    def __init__(self, token: str, max_pages: int | None = None) -> None:
        """
        Initialise the ingest runner.

        Args:
            token: GitHub personal access token for API authentication.
            max_pages: Optional cap on the number of API pages to
                fetch. ``None`` means fetch all available pages.

        """
        super().__init__(
            logger=JOSSLogger(name=__name__),
            token=token,
            max_pages=max_pages,
        )

    def fetch_issue_page(
        self,
        session: Session,
        target: RepoTarget,
        page: int,
        per_page: int = 100,
    ) -> list[dict]:
        """
        Fetch a single page of issues/PRs from GitHub.

        Note: GitHub's /issues endpoint can include pull requests. We keep the raw
        objects and filter later to avoid discarding data prematurely.

        Args:
            session: A configured requests session.
            target: Repository identifier.
            page: The page number to fetch (1-indexed).
            per_page: Items per page (GitHub max is 100).
            state: Issue state filter ("open", "closed", or "all").

        Returns:
            A list of issue/PR JSON objects.

        Raises:
            RuntimeError: If the GitHub API returns a non-200 response or an
                unexpected JSON payload type.

        """
        url: str = f"{self._api_base}/repos/{target.owner}/{target.repo}/issues"
        params: dict[str, object] = {
            "state": "all",
            "per_page": per_page,
            "page": page,
            "sort": "created",
            "direction": "desc",
        }

        resp = session.get(url, params=params, timeout=30)
        if resp.status_code == HTTP_FORBIDDEN:
            self._sleep_until_reset(resp)
            resp = session.get(url, params=params, timeout=30)

        if resp.status_code != HTTP_OK:
            msg = (
                f"GitHub API error {resp.status_code} for {resp.url}\n"
                f"Response (first 500 chars): {resp.text[:500]}"
            )
            raise RuntimeError(msg)

        self.logger.get_logger().info(
            "Fetched page %s (%s). %s",
            page,
            target.full_name(),
            self._rate_limit_status(resp.headers),
        )

        data = resp.json()
        if not isinstance(data, list):
            err_msg = "Unexpected response type: expected list"
            raise RuntimeError(err_msg)

        return data

    def execute(self) -> list[dict]:
        """
        Run the full ingestion routine.

        Returns:
            Exit code (``0`` for success).

        """
        timestamp: int = JOSSUtils.get_timestamp()

        joss_logger = JOSSLogger(__name__)
        joss_logger.setup_file_logging(timestamp, "github_issues")
        logger: logging.Logger = joss_logger.get_logger()

        target: RepoTarget = RepoTarget(owner="openjournals", repo="joss-reviews")

        session = requests.Session()
        session.headers.update(self._build_headers())

        page: int = 1
        total_fetched: int = 0
        all_issues: list[dict] = []

        logger.info("Starting collection for %s.", target.full_name())

        spinner = Spinner(
            "Getting issues from `gh:openjournals/joss-reviews`... ",
        )

        while True:
            issues = self.fetch_issue_page(
                session=session,
                target=target,
                page=page,
                per_page=100,
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

            if len(issues) < 100:
                break

            if self._max_pages is not None and page >= self._max_pages:
                logger.info(
                    "Reached max-pages=%s; stopping early.",
                    self._max_pages,
                )
                break

            page += 1

        spinner.finish()

        self.logger.get_logger().info(
            "Done. total_fetched=%s total_issues=%s",
            total_fetched,
            len(all_issues),
        )

        return all_issues
