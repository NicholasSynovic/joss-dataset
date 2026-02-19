"""Global variables for the `joss` subcommand"""

from string import Template

GITHUB_REPO_OWNER: str = "openjournals"
GITHUB_REPO_PROJECT: str = "joss-reviews"

JOSS_ACTIVE_PAPERS_TEMPLATE: Template = Template(
    template="https://joss.theoj.org/papers/active.atom?page=$page"
)
JOSS_PUBLISHED_PAPERS_TEMPLATE: Template = Template(
    template="https://joss.theoj.org/papers/published.atom?page=$page"
)

HTTP_GET_TIMEOUT: int = 60
