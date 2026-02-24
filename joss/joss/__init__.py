"""Models and constants used by the JOSS dataset ETL subcommand."""

# Copyright (c) 2025 Nicholas M. Synovic
# ruff: noqa: RUF067

from string import Template

from pydantic import BaseModel

GITHUB_REPO_OWNER: str = "openjournals"
GITHUB_REPO_PROJECT: str = "joss-reviews"

JOSS_ACTIVE_PAPERS_TEMPLATE: Template = Template(
    template="https://joss.theoj.org/papers/active.atom?page=$page"
)
JOSS_PUBLISHED_PAPERS_TEMPLATE: Template = Template(
    template="https://joss.theoj.org/papers/published.atom?page=$page"
)

HTTP_GET_TIMEOUT: int = 60
HTTP_HEAD_TIMEOUT: int = 60


class JOSSGHIssue(BaseModel):
    """Normalized representation of a raw GitHub issue row."""

    id: int
    is_pull_request: bool
    labels: str
    body: str
    creator: str
    state: str
    json_str: str


class JOSSPaperProjectIssue(BaseModel):
    """Derived mapping between JOSS issues and their repository metadata."""

    id: int
    joss_github_issue_id: int
    github_repo_url: str
    repo_host: str | None
    joss_url: str | None
    joss_resolved_url: str | None
    is_accepted: bool
    journal: str = "joss"
