import re
from collections import defaultdict
from json import dumps
from logging import Logger

from progress.bar import Bar
from requests import head

from joss.interfaces import TransformInterface
from joss.joss import HTTP_HEAD_TIMEOUT, JOSSGHIssue, JOSSPaperProjectIssue
from joss.logger import JOSSLogger


class JOSSTransform(TransformInterface):
    def __init__(self, joss_logger: JOSSLogger) -> None:
        self.logger: Logger = joss_logger.get_logger()

    def normalize_joss_gh_issues(
        self,
        issues: list[dict],
    ) -> list[JOSSGHIssue]:
        data: list[JOSSGHIssue] = []

        with Bar(
            "Normalizing issues for the `_joss_gh_issues` table... ",
            max=len(issues),
        ) as bar:
            issue: dict
            for issue in issues:
                datum: JOSSGHIssue = JOSSGHIssue(
                    _id=issue["number"],
                    is_pull_request="pull_request" in issue,
                    labels=[label["name"] for label in issue["labels"]],
                    body=issue["body"],
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

    @staticmethod
    def _extract_github_repo_url(body: str) -> str:
        repo_match = re.search(
            r"<!--target-repository-->(.*?)<!--end-target-repository-->",
            body,
        )
        return repo_match.group(1).strip() if repo_match else ""

    @staticmethod
    def _extract_joss_url(body: str) -> str:
        # JOSS URL from status badge: [![status](...)](URL)
        joss_url_match = re.search(
            r"\[!\[status\]\([^)]+\)\]\((https://joss\.theoj\.org/papers/[^)]+)\)",
            body,
        )
        return joss_url_match.group(1) if joss_url_match else ""

    @staticmethod
    def _resolve_joss_url(url: str) -> str:
        return head(
            url=url,
            timeout=HTTP_HEAD_TIMEOUT,
            allow_redirects=True,
        ).url

    def normalize_joss_paper_project_issues(
        self, issues: list[JOSSGHIssue]
    ) -> list[JOSSPaperProjectIssue]:
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
                        issue._id,
                    )
                    bar.next()
                    continue

                # If not authored by `editorialbot`, ignore
                if issue.creator != "editorialbot":
                    self.logger.warning(
                        "Skipped issue #%d because it's not authored by `editorialbot`",
                        issue._id,
                    )
                    bar.next()
                    continue

                joss_url: str = self._extract_github_repo_url(body=issue.body)
                joss_resolved_url: str = (
                    self._resolve_joss_url(url=joss_url)
                    if "accepted" in issue.labels
                    else ""
                )

                datum: JOSSPaperProjectIssue = JOSSPaperProjectIssue(
                    _id=paper_project_id,
                    _joss_github_issue_id=issue._id,
                    joss_url=joss_url,
                    joss_resolved_url=joss_resolved_url,
                    github_repo_url=self._extract_github_repo_url(
                        body=issue.body,
                    ),
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
        normalized_data: dict[str, list] = defaultdict(list)

        normalized_data["_joss_github_issues"] = self.normalize_joss_gh_issues(
            issues=data,
        )
        normalized_data["_joss_paper_project_issues"] = (
            self.normalize_joss_paper_project_issues(
                issues=normalized_data["_joss_github_issues"]
            )
        )

        return normalized_data
