"""Global variables for the `joss` subcommand"""

from string import Template

GITHUB_REPO_ISSUES: str = "https://github.com/openjournals/joss-reviews"
JOSS_ACTIVE_PAPERS_TEMPLATE: Template = Template(
    template="https://joss.theoj.org/papers/active.atom?page=$page"
)
JOSS_PUBLISHED_PAPERS_TEMPLATE: Template = Template(
    template="https://joss.theoj.org/papers/published.atom?page=$page"
)
