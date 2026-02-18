"""Repository target model for the JOSS ingest sub-package."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RepoTarget:
    """A GitHub repository identifier."""

    owner: str
    repo: str

    def full_name(self) -> str:
        """
        Return the repository in 'owner/repo' form.

        Returns:
            The repository in 'owner/repo' form.

        """
        return f"{self.owner}/{self.repo}"
