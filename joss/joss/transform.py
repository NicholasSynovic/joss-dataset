"""Transformation logic for deriving normalized JOSS issue tables."""

# Copyright (c) 2025 Nicholas M. Synovic

import os
from collections import defaultdict
from collections.abc import Sequence
from json import dumps
from logging import Logger

from progress.bar import Bar
from requests.adapters import HTTPAdapter, Retry
from requests.exceptions import RequestException
from requests.sessions import Session

from joss.interfaces import TransformInterface
from joss.joss import HTTP_HEAD_TIMEOUT, JOSSGHIssue, JOSSPaperProjectIssue
from joss.logger import JOSSLogger
from joss.parsers import parse_joss_issue, repo_host_from_url


class JOSSTransform(TransformInterface):
    """Normalize extracted GitHub issue payloads into database-ready rows."""

    def __init__(self, joss_logger: JOSSLogger) -> None:
        """
        Initialize the transformer.

        Args:
            joss_logger: Logger wrapper for structured progress and warnings.

        """
        self.logger: Logger = joss_logger.get_logger()

    def normalize_joss_gh_issues(
        self,
        issues: list[dict],
    ) -> list[JOSSGHIssue]:
        """
        Normalize raw API issues into `_joss_github_issues` table records.

        Args:
            issues: Raw GitHub issue objects returned by the API.

        Returns:
            List of normalized issue rows.

        """
        data: list[JOSSGHIssue] = []

        with Bar(
            "Normalizing issues for the `_joss_gh_issues` table... ",
            max=len(issues),
        ) as bar:
            issue: dict
            for issue in issues:
                datum: JOSSGHIssue = JOSSGHIssue(
                    id=issue["number"],
                    is_pull_request="pull_request" in issue,
                    labels=dumps(
                        obj=[label["name"] for label in issue["labels"]],
                    ),
                    body=issue["body"] if isinstance(issue["body"], str) else "",
                    creator=issue["user"]["login"],
                    state=issue["state"],
                    json_str=dumps(obj=issue, indent=4),
                )

                data.append(datum)
                bar.next()

        self.logger.info(
            "Normalized %d issues for the `_joss_gh_issues` table",
            len(data),
        )
        return data

    def _resolve_joss_url(self, url: str) -> str:
        """
        Resolve a JOSS URL through redirects.

        Args:
            url: Candidate JOSS paper URL.

        Returns:
            Final redirected URL, or the original URL on request failure.

        """
        session: Session = Session()

        # Define exponential backoff strategy
        # backoff_factor=1 means sleep for [0s, 2s, 4s, 8s, ...] between retries
        retry_strategy = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[403, 429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET"],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        try:
            response = session.head(
                url=url, timeout=HTTP_HEAD_TIMEOUT, allow_redirects=True
            )
            # Final URL after all redirects
            return response.url
        except RequestException as e:
            # Log error or return original URL
            self.logger.info("Failed to resolve %s: %s", url, e)
            return url

    def _maybe_resolve_joss_url(self, url: str | None) -> str | None:
        """
        Resolve JOSS URLs only when explicitly enabled by environment variable.

        Args:
            url: Parsed JOSS paper URL.

        Returns:
            Resolved URL when enabled and available, otherwise ``None``.

        """
        if not url:
            return None
        if os.getenv("JOSS_RESOLVE_URLS", "0") != "1":
            return None
        return self._resolve_joss_url(url=url)

    def normalize_joss_paper_project_issues(
        self, issues: list[JOSSGHIssue]
    ) -> list[JOSSPaperProjectIssue]:
        """
        Build `_joss_paper_project_issues` rows from normalized issue rows.

        Args:
            issues: Normalized GitHub issue records.

        Returns:
            List of paper-project mapping rows.

        """
        paper_project_id: int = 0
        data: list[JOSSPaperProjectIssue] = []

        with Bar(
            "Normalizing issues for the `_joss_paper_project_issue_mapping` table... ",
            max=len(issues),
        ) as bar:
            issue: JOSSGHIssue
            for issue in issues:
                if issue.is_pull_request:  # If pull request, ignore
                    self.logger.warning(
                        "Skipped issue #%d because it's a pull request",
                        issue.id,
                    )
                    bar.next()
                    continue

                parsed_issue = parse_joss_issue(issue.body)
                github_repo_url = parsed_issue.get("repository")
                if not github_repo_url:
                    github_repo_url = None
                if not isinstance(github_repo_url, str) or not github_repo_url:
                    self.logger.warning(
                        (
                            "Skipped issue #%d because no repository URL "
                            "could be extracted"
                        ),
                        issue.id,
                    )
                    bar.next()
                    continue

                joss_url = parsed_issue.get("joss_url")
                if not isinstance(joss_url, str) or not joss_url:
                    joss_url = None

                is_accepted = "accepted" in issue.labels
                if not is_accepted:
                    self.logger.info(
                        "Captured issue #%d; is_accepted=0",
                        issue.id,
                    )

                joss_resolved_url = self._maybe_resolve_joss_url(url=joss_url)
                repo_host = repo_host_from_url(github_repo_url)
                if repo_host and repo_host != "github.com":
                    self.logger.info(
                        "Captured issue #%d with non-GitHub repository host `%s`",
                        issue.id,
                        repo_host,
                    )

                datum: JOSSPaperProjectIssue = JOSSPaperProjectIssue(
                    id=paper_project_id,
                    joss_github_issue_id=issue.id,
                    joss_url=joss_url,
                    joss_resolved_url=joss_resolved_url,
                    github_repo_url=github_repo_url,
                    repo_host=repo_host,
                    is_accepted=is_accepted,
                )

                data.append(datum)
                paper_project_id += 1
                bar.next()

        self.logger.info(
            "Normalized %d issues for the `_joss_paper_project_issue_mapping` table",
            len(data),
        )
        return data

    def transform_data(self, data: list[dict]) -> dict[str, list]:
        """
        Transform extracted API payload into all load-ready table datasets.

        Args:
            data: Raw extracted GitHub API payload.

        Returns:
            Mapping from table name to serializable row dictionaries.

        """
        normalized_data: dict[str, list] = defaultdict(list)

        def dict_tool(
            rows: Sequence[JOSSGHIssue | JOSSPaperProjectIssue],
        ) -> list[dict]:
            """
            Convert pydantic model rows into dictionaries.

            Args:
                rows: Sequence of pydantic row models.

            Returns:
                List of serialized row dictionaries.

            """
            return [row.model_dump() for row in rows]

        normalized_data["_joss_github_issues"] = self.normalize_joss_gh_issues(
            issues=data,
        )
        normalized_data["_joss_paper_project_issues"] = (
            self.normalize_joss_paper_project_issues(
                issues=normalized_data["_joss_github_issues"]
            )
        )

        normalized_data["_joss_github_issues"] = dict_tool(
            normalized_data["_joss_github_issues"]
        )
        normalized_data["_joss_paper_project_issues"] = dict_tool(
            normalized_data["_joss_paper_project_issues"]
        )

        return normalized_data
