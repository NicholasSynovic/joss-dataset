import re
from collections import defaultdict
from json import dumps
from logging import Logger

from progress.bar import Bar
from requests.adapters import HTTPAdapter, Retry
from requests.exceptions import RequestException
from requests.sessions import Session

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

    @staticmethod
    def _extract_github_repo_url(body: str) -> str:
        data: str = ""

        # This works for `editorialbot` created issues
        repo_match = re.search(
            r"<!--target-repository-->(.*?)<!--end-target-repository-->",
            body,
        )
        data = repo_match.group(1).strip() if repo_match else ""

        if data != "":
            return data

        # This works for all other issues
        repo_match = re.search(
            r"\*\*Repository:\*\*.*?(https://github\.com/[\w\-/]+)", body
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

    def _resolve_joss_url(self, url: str) -> str:
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
                        issue.id,
                    )
                    bar.next()
                    continue

                # If not authored by `editorialbot`, ignore
                # if issue.creator != "editorialbot":
                #     self.logger.warning(
                #         "Skipped issue #%d because it's not authored by `editorialbot`",
                #         issue.id,
                #     )
                #     bar.next()
                #     continue

                # If not GitHub Repo URL is present, ignore
                github_repo_url: str = self._extract_github_repo_url(
                    body=issue.body,
                )
                if github_repo_url == "":
                    self.logger.warning(
                        "Skipped issue #%d because no GitHub Repo URL is present",
                        issue.id,
                    )
                    bar.next()
                    continue

                joss_url: str = self._extract_joss_url(body=issue.body)

                joss_resolved_url: str = ""
                if "accepted" in issue.labels:
                    if joss_url != "":  # Positive case, all checks pass
                        joss_resolved_url = self._resolve_joss_url(url=joss_url)
                    else:
                        self.logger.warning(
                            "Skipped issue #%d because no JOSS URL is present",
                            issue.id,
                        )
                        bar.next()
                        continue
                else:
                    self.logger.warning(
                        "Skipped issue #%d because the issue is missing an `accepted` label",
                        issue.id,
                    )
                    bar.next()
                    continue

                datum: JOSSPaperProjectIssue = JOSSPaperProjectIssue(
                    id=paper_project_id,
                    joss_github_issue_id=issue.id,
                    joss_url=joss_url,
                    joss_resolved_url=joss_resolved_url,
                    github_repo_url=github_repo_url,
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
        dict_tool = lambda foo: [bar.model_dump() for bar in foo]

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
