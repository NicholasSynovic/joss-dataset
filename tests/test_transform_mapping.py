"""Tests for JOSS paper-project mapping transform behavior."""

# Copyright (c) 2025 Nicholas M. Synovic

from json import dumps

import pytest

from joss.joss import JOSSGHIssue
from joss.joss.transform import JOSSTransform
from joss.logger import JOSSLogger


def expect(*, condition: bool, message: str) -> None:
    """Fail the current test with a clear message when condition is false."""
    if not condition:
        pytest.fail(message)


def _build_issue(
    issue_id: int,
    body: str,
    labels: list[str],
    *,
    is_pull_request: bool = False,
) -> JOSSGHIssue:
    """
    Construct a normalized issue model for transform tests.

    Returns:
        Normalized issue model.

    """
    return JOSSGHIssue(
        id=issue_id,
        is_pull_request=is_pull_request,
        labels=dumps(labels),
        body=body,
        creator="editorialbot",
        state="open",
        json_str="{}",
    )


def _build_transform() -> JOSSTransform:
    """
    Construct a transform instance with a test logger.

    Returns:
        Ready-to-use transform instance.

    """
    return JOSSTransform(joss_logger=JOSSLogger(name="test-transform"))


def test_captures_nonaccepted_github_issue_without_joss_url() -> None:
    """Capture non-accepted GitHub submissions when repository is present."""
    transform = _build_transform()
    issue = _build_issue(
        issue_id=1,
        body="**Repository:** https://github.com/org/repo",
        labels=["review"],
    )

    rows = transform.normalize_joss_paper_project_issues([issue])

    expect(condition=len(rows) == 1, message="expected one captured row")
    expect(
        condition=rows[0].joss_github_issue_id == 1,
        message="unexpected issue id mapping",
    )
    expect(
        condition=rows[0].github_repo_url == "https://github.com/org/repo",
        message="unexpected github_repo_url",
    )
    expect(condition=rows[0].repo_host == "github.com", message="unexpected repo_host")
    expect(
        condition=rows[0].is_accepted is False,
        message="expected is_accepted=False",
    )
    expect(condition=rows[0].joss_url is None, message="expected joss_url None")
    expect(
        condition=rows[0].joss_resolved_url is None,
        message="expected joss_resolved_url None",
    )


def test_captures_accepted_bitbucket_issue_without_joss_url() -> None:
    """Capture accepted non-GitHub submissions with repo_host populated."""
    transform = _build_transform()
    issue = _build_issue(
        issue_id=2,
        body=(
            '**Repository:** <a href="https://bitbucket.org/dghoshal/frieda">'
            "https://bitbucket.org/dghoshal/frieda</a>"
        ),
        labels=["accepted"],
    )

    rows = transform.normalize_joss_paper_project_issues([issue])

    expect(condition=len(rows) == 1, message="expected one captured row")
    expect(
        condition=rows[0].is_accepted is True,
        message="expected is_accepted=True",
    )
    expect(
        condition=rows[0].github_repo_url == "https://bitbucket.org/dghoshal/frieda",
        message="unexpected github_repo_url",
    )
    expect(
        condition=rows[0].repo_host == "bitbucket.org",
        message="unexpected repo_host",
    )
    expect(condition=rows[0].joss_url is None, message="expected joss_url None")
    expect(
        condition=rows[0].joss_resolved_url is None,
        message="expected joss_resolved_url None",
    )


def test_skips_issue_when_repository_cannot_be_extracted() -> None:
    """Skip non-plausible submissions with no extractable GitHub repository URL."""
    transform = _build_transform()
    issue = _build_issue(
        issue_id=3,
        body="No repository link in this issue body",
        labels=["accepted"],
    )

    rows = transform.normalize_joss_paper_project_issues([issue])

    expect(condition=rows == [], message="expected row skip when repository is missing")


def test_does_not_resolve_network_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Do not perform network URL resolution unless explicitly enabled."""
    transform = _build_transform()
    monkeypatch.delenv("JOSS_RESOLVE_URLS", raising=False)

    def _failing_resolve(_: str) -> str:
        msg = (
            "_resolve_joss_url should not be called when JOSS_RESOLVE_URLS is disabled"
        )
        raise AssertionError(msg)

    monkeypatch.setattr(transform, "_resolve_joss_url", _failing_resolve)

    issue = _build_issue(
        issue_id=4,
        body=(
            "[![status](http://joss.theoj.org/papers/abc123/status.svg)]"
            "(http://joss.theoj.org/papers/abc123)\n"
            "**Repository:** https://github.com/org/repo"
        ),
        labels=["accepted"],
    )

    rows = transform.normalize_joss_paper_project_issues([issue])

    expect(condition=len(rows) == 1, message="expected one captured row")
    expect(
        condition=rows[0].joss_url == "https://joss.theoj.org/papers/abc123",
        message="unexpected joss_url",
    )
    expect(
        condition=rows[0].joss_resolved_url is None,
        message="expected joss_resolved_url None",
    )
