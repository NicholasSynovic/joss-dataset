import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from logging import Logger

from requests import Response, Session
from requests.structures import CaseInsensitiveDict

from joss.ingest.repo_target import RepoTarget
from joss.logger import JOSSLogger
from joss.utils import JOSSUtils

HTTP_FORBIDDEN: int = 403


class GitHubIngest(ABC):
    def __init__(
        self, jossLogger: JOSSLogger, token: str, max_pages: int | None = None
    ) -> None:
        self._api_base: str = "https://api.github.com"
        self._github_api_version: str = "2022-11-28"
        self._max_pages: int | None = max_pages

        self.logger: Logger = jossLogger.get_logger()
        self.token = token

    def _build_headers(self) -> dict:
        """
        Build GitHub REST API headers for authenticated requests.

        Args:
            token: A GitHub personal access token.

        Returns:
            A dictionary of headers for GitHub REST API requests.

        """
        return {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": self._github_api_version,
            "User-Agent": "joss-dataset-ingest",
        }

    @staticmethod
    def _rate_limit_status(headers: CaseInsensitiveDict[str]) -> str:
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

    def _sleep_until_reset(self, resp: Response) -> None:
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
        now_ts = JOSSUtils.get_timestamp()
        sleep_for = max(0, reset_ts - now_ts) + 5

        reset_dt = datetime.fromtimestamp(reset_ts, tz=timezone.utc)
        self.logger.warning(
            "Rate limited. Sleeping %ss until %s.", sleep_for, reset_dt.isoformat()
        )
        time.sleep(sleep_for)

    @abstractmethod
    def fetch_issue_page(
        self,
        session: Session,
        target: RepoTarget,
        page: int,
        per_page: int = 100,
    ) -> list[dict]: ...

    @abstractmethod
    def execute(self) -> list[dict]: ...
