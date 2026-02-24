"""Extraction stage for downloading JOSS review issues from GitHub."""

# Copyright (c) 2025 Nicholas M. Synovic

from logging import Logger

from fastcore.foundation import AttrDict, L
from ghapi.all import GhApi
from progress.spinner import Spinner

from joss.interfaces import ExtractInterface
from joss.joss import GITHUB_REPO_OWNER, GITHUB_REPO_PROJECT
from joss.logger import JOSSLogger


class JOSSExtract(ExtractInterface):
    """Download and normalize raw issue payloads from the GitHub API."""

    def __init__(self, joss_logger: JOSSLogger) -> None:
        """
        Initialize API client and logger.

        Args:
            joss_logger: Logger wrapper used for extraction progress logs.

        """
        self._per_page: int = 100

        self.logger: Logger = joss_logger.get_logger()
        # Assumes setting the `GITHUB_TOKEN` environment variable
        self.gh: GhApi = GhApi(
            owner=GITHUB_REPO_OWNER,
            repo=GITHUB_REPO_PROJECT,
        )

    def __distill_fastcore(self, obj: object) -> object:
        """
        Recursively convert `L` and `AttrDict` values to standard Python types.

        Args:
            obj: Input value from ghapi/fastcore structures.

        Returns:
            Converted value containing only standard Python containers/scalars.

        """
        # Handle AttrDict (or any dict-like object)
        if isinstance(obj, (dict, AttrDict)):
            return {k: self.__distill_fastcore(v) for k, v in obj.items()}

        # Handle L (or any list/tuple)
        if isinstance(obj, (list, L, tuple)):
            return [self.__distill_fastcore(v) for v in obj]

        # Return everything else as-is
        return obj

    def _query_api(self, page: int = 1) -> list[AttrDict]:
        """
        Query a single page of issues from the GitHub API.

        Args:
            page: 1-based page number.

        Returns:
            List of issue dictionaries converted to standard Python types.

        """
        self.logger.info(
            "Logging page %d of %s/%s",
            page,
            GITHUB_REPO_OWNER,
            GITHUB_REPO_PROJECT,
        )
        issues: L = self.gh.issues.list_for_repo(
            page=page,
            per_page=self._per_page,
            state="all",
            sort="created",
            direction="asc",
        )

        return [self.__distill_fastcore(issue) for issue in issues]

    def download_data(self) -> list[dict]:
        """
        Download all available repository issues from paginated API responses.

        Returns:
            Complete list of issue dictionaries across all pages.

        """
        page_counter: int = 1
        data: list[dict] = []

        with Spinner(
            message=f"Getting issues for {GITHUB_REPO_OWNER}/{GITHUB_REPO_PROJECT}... ",
        ) as spinner:
            while True:
                issues: list[dict] = self._query_api(page=page_counter)
                data.extend(issues)

                if len(issues) < self._per_page:
                    break

                page_counter += 1
                spinner.next()

        self.logger.info("Number of issues collected: %d", len(data))

        return data
