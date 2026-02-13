"""
Collect issues opened by `editorialbot` from `openjournals/joss-reviews`.

Copyright 2026 (C) Nicholas M. Synovic

This script queries the GitHub REST API for issues (open + closed) from the
`openjournals/joss-reviews` repository only, filters to those opened by the
`editorialbot` account, and writes each issue to an individual JSON file for
downstream analysis.

Authentication:
- Provide a GitHub Personal Access Token via the `GITHUB_TOKEN` env var.

Pagination:
- Uses `per_page=100` by default.

Output:
- data/raw/openjournals_joss-reviews/issues/issue_<N>.json
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import cast

import requests
from progress.spinner import Spinner

API_BASE: str = "https://api.github.com"
GITHUB_API_VERSION: str = "2022-11-28"

LOGGER: logging.Logger = logging.getLogger(__name__)

EMPTY: str = ""
HTTP_OK: int = 200
HTTP_FORBIDDEN: int = 403
PER_PAGE_REQUIRED: int = 100

JsonObject = dict[str, object]
JsonList = list[JsonObject]


@dataclass(frozen=True)
class RepoTarget:
    """A GitHub repository identifier."""

    owner: str
    repo: str

    def full_name(self) -> str:
        """
        Return the repository in 'owner/repo' form.

        Returns:
            The repository in 'owner/repo' form.

        """
        return f"{self.owner}/{self.repo}"


@dataclass(frozen=True)
class Config:
    """Runtime configuration for the ingestion script."""

    token: str
    target: RepoTarget
    per_page: int
    max_pages: int | None
    timestamp: int


def utc_now_iso() -> str:
    """
    Return the current UTC time in ISO-8601 format (seconds precision).

    Returns:
        The current UTC time in ISO-8601 format (seconds precision).

    """
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def get_token() -> str:
    """
    Read `GITHUB_TOKEN` from the environment.

    Returns:
        The GitHub token read from the `GITHUB_TOKEN` environment variable.

    Raises:
        RuntimeError: If `GITHUB_TOKEN` is missing/empty.

    """
    token: str = os.environ.get("GITHUB_TOKEN", EMPTY).strip()
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


def build_headers(token: str) -> dict[str, str]:
    """
    Build GitHub REST API headers for authenticated requests.

    Args:
        token: A GitHub personal access token.

    Returns:
        A dictionary of headers for GitHub REST API requests.

    """
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": GITHUB_API_VERSION,
        "User-Agent": "joss-dataset-ingest",
    }


def rate_limit_status(headers: requests.structures.CaseInsensitiveDict[str]) -> str:
    """
    Format GitHub rate limit headers for logging.

    Args:
        headers: Response headers from GitHub.

    Returns:
        A human-readable rate limit status string.

    """
    remaining: str | None = headers.get("X-RateLimit-Remaining")
    limit: str | None = headers.get("X-RateLimit-Limit")
    reset: str | None = headers.get("X-RateLimit-Reset")

    if remaining is None or limit is None:
        return "rate-limit: unknown"

    if reset is None:
        return f"rate-limit: {remaining}/{limit}"

    try:
        reset_dt = datetime.fromtimestamp(int(reset), tz=timezone.utc)
    except ValueError:
        return f"rate-limit: {remaining}/{limit} (reset parse error)"

    return f"rate-limit: {remaining}/{limit} (resets {reset_dt.isoformat()})"


def sleep_until_reset(resp: requests.Response) -> None:
    """
    Sleep until GitHub's rate limit reset if the response indicates limiting.

    Args:
        resp: A GitHub API response.

    """
    remaining: str | None = resp.headers.get("X-RateLimit-Remaining")
    reset: str | None = resp.headers.get("X-RateLimit-Reset")

    if resp.status_code != HTTP_FORBIDDEN or remaining != "0" or reset is None:
        return

    reset_ts = int(reset)
    now_ts = int(time.time())
    sleep_for = max(0, reset_ts - now_ts) + 5

    reset_dt = datetime.fromtimestamp(reset_ts, tz=timezone.utc)
    LOGGER.warning(
        "Rate limited. Sleeping %ss until %s.", sleep_for, reset_dt.isoformat()
    )
    time.sleep(sleep_for)


def fetch_issues_page(
    session: requests.Session,
    target: RepoTarget,
    *,
    page: int,
    per_page: int,
    state: str,
) -> JsonList:
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
    url: str = f"{API_BASE}/repos/{target.owner}/{target.repo}/issues"
    params: dict[str, object] = {
        "state": state,
        "per_page": per_page,
        "page": page,
        "sort": "created",
        "direction": "desc",
    }

    resp = session.get(url, params=params, timeout=30)
    if resp.status_code == HTTP_FORBIDDEN:
        sleep_until_reset(resp)
        resp = session.get(url, params=params, timeout=30)

    if resp.status_code != HTTP_OK:
        msg = (
            f"GitHub API error {resp.status_code} for {resp.url}\n"
            f"Response (first 500 chars): {resp.text[:500]}"
        )
        raise RuntimeError(msg)

    LOGGER.info(
        "Fetched page %s (%s). %s",
        page,
        target.full_name(),
        rate_limit_status(resp.headers),
    )

    data = resp.json()
    if not isinstance(data, list):
        err_msg = "Unexpected response type: expected list"
        raise RuntimeError(err_msg)

    return cast(JsonList, data)


def parse_args() -> argparse.Namespace:
    """
    Parse CLI arguments.

    Returns:
        The parsed CLI arguments namespace.

    """
    parser = argparse.ArgumentParser(
        description="Collect all issues from openjournals/joss-reviews."
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Maximum number of pages to fetch (for testing). Default: no limit.",
    )
    return parser.parse_args()


def build_config(args: argparse.Namespace, timestamp: int) -> Config:
    """
    Build a Config instance from parsed CLI arguments.

    Args:
        args: Parsed CLI arguments.
        timestamp: UNIX timestamp for file naming.

    Returns:
        A Config instance for the run.

    """
    token = get_token()
    target = RepoTarget(owner="openjournals", repo="joss-reviews")

    return Config(
        token=token,
        target=target,
        per_page=PER_PAGE_REQUIRED,
        max_pages=args.max_pages,
        timestamp=timestamp,
    )


def main() -> int:
    """
    Run the ingestion routine.

    Returns:
        Exit code (0 for success).

    """
    args = parse_args()

    # Get timestamp once for both log and JSON files
    timestamp = int(time.time())

    # Configure file logging with DEBUG level and UNIX timestamp filename
    log_filename = f"github_issues_{timestamp}.log"
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_filename),
        ],
    )
    LOGGER.info("Logging to file: %s", log_filename)

    config = build_config(args, timestamp)

    session = requests.Session()
    session.headers.update(build_headers(config.token))

    page = 1
    total_fetched = 0
    all_issues: JsonList = []

    LOGGER.info("Starting collection for %s.", config.target.full_name())

    spinner = Spinner("Getting issues from `gh:openjournals/joss-reviews`... ")

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

        LOGGER.info(
            "Page %s: fetched=%s total_collected=%s", page, len(issues), len(all_issues)
        )

        if len(issues) < config.per_page:
            break

        if config.max_pages is not None and page >= config.max_pages:
            LOGGER.info("Reached max-pages=%s; stopping early.", config.max_pages)
            break

        page += 1

    spinner.finish()

    # Write all issues to a single JSON file
    json_filename: Path = Path(f"github_issues_{config.timestamp}.json").absolute()
    json.dump(
        all_issues,
        json_filename.open(mode="w", encoding="utf-8"),
        indent=4,
    )

    LOGGER.info(
        "Done. total_fetched=%s total_issues=%s", total_fetched, len(all_issues)
    )
    LOGGER.info("Saved to: %s", json_filename)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
