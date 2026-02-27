from logging import Logger

from fastcore.foundation import AttrDict, L
from ghapi.all import GhApi
from ghapi.graphql import GhGql
from progress.spinner import Spinner
from requests import post
from requests.exceptions import RequestException

from joss.interfaces import ExtractInterface
from joss.joss import GITHUB_REPO_OWNER, GITHUB_REPO_PROJECT, HTTP_POST_TIMEOUT
from joss.logger import JOSSLogger


class JOSSExtract(ExtractInterface):
    def __init__(self, joss_logger: JOSSLogger) -> None:
        self._per_page: int = 100

        self.logger: Logger = joss_logger.get_logger()
        # Assumes setting the `GITHUB_TOKEN` environment variable
        self.gh: GhApi = GhApi(
            owner=GITHUB_REPO_OWNER,
            repo=GITHUB_REPO_PROJECT,
        )
        self.ghgql: GhGql = GhGql()

    def __distill_fastcore(self, obj):
        """Recursively convert L and AttrDict to standard Python types."""
        # Handle AttrDict (or any dict-like object)
        if isinstance(obj, (dict, AttrDict)):
            return {k: self.__distill_fastcore(v) for k, v in obj.items()}

        # Handle L (or any list/tuple)
        elif isinstance(obj, (list, L, tuple)):
            return [self.__distill_fastcore(v) for v in obj]

        # Return everything else as-is
        return obj

    def _query_api(self, page: int = 1) -> list[AttrDict]:
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

    def _get_commits(self) -> int:
        """
        Queries GH GraphQL API to get the commit count of the default branch.
        """
        url = "https://api.github.com/graphql"

        headers = {
            "Authorization": self.gh.headers["Authorization"],
            "Content-Type": "application/json",
        }

        query = """
        query($owner: String!, $name: String!) {
        repository(owner: $owner, name: $name) {
            defaultBranchRef {
            target {
                ... on Commit {
                history {
                    totalCount

                }
                }
            }
            }
        }
        }
        """

        payload = {
            "query": query,
            "variables": {
                "owner": GITHUB_REPO_OWNER,
                "name": GITHUB_REPO_PROJECT,
            },
        }

        try:
            # Using a simple post, but you can use your session object here
            response = post(
                url,
                json=payload,
                headers=headers,
                timeout=HTTP_POST_TIMEOUT,
            )
            response.raise_for_status()

            data = response.json()

            # Guard against cases where the repository or branch might not exist
            repo_data = data.get("data", {}).get("repository")
            if not repo_data or not repo_data.get("defaultBranchRef"):
                return 0

            return repo_data["defaultBranchRef"]["target"]["history"]["totalCount"]

        except RequestException as e:
            print(f"Error querying GitHub GraphQL: {e}")
            return -1

    def download_data(self) -> list[dict]:
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
