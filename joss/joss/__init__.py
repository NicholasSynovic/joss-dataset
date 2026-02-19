"""Global variables for the `joss` subcommand"""

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
    _id: int
    is_pull_request: bool
    labels: list[str]
    body: str
    creator: str
    state: str
    json_str: str


class JOSSPaperProjectIssue(BaseModel):
    _id: int
    _joss_github_issue_id: int
    github_repo_url: str
    joss_url: str
    joss_resolved_url: str
    journal: str = "joss"
