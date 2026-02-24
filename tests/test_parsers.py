"""Tests for robust JOSS issue parsing."""

# Copyright (c) 2025 Nicholas M. Synovic

import pytest

from joss import parsers
from joss.parsers import parse_joss_issue, repo_host_from_url


def expect(*, condition: bool, message: str) -> None:
    """Fail the current test with a clear message when condition is false."""
    if not condition:
        pytest.fail(message)


@pytest.mark.parametrize(
    ("body", "expected_repository", "expected_repo_host"),
    [
        (
            """
**Repository:** <a href="https://bitbucket.org/dghoshal/frieda">https://bitbucket.org/dghoshal/frieda</a>
""",
            "https://bitbucket.org/dghoshal/frieda",
            "bitbucket.org",
        ),
        (
            """
**Repository:** https://gitlab.com/cerfacs/batman
""",
            "https://gitlab.com/cerfacs/batman",
            "gitlab.com",
        ),
        (
            """
**Repository:** https://savannah.nongnu.org/projects/complot/
""",
            "https://savannah.nongnu.org/projects/complot",
            "savannah.nongnu.org",
        ),
        (
            """
**Repository:** https://www.github.com/singularityhub/sregistry
""",
            "https://github.com/singularityhub/sregistry",
            "github.com",
        ),
        (
            """
**Repository:** https://github.com/org/repo/blob/main/README.md
""",
            "https://github.com/org/repo",
            "github.com",
        ),
        (
            """
**Repository:** https://github.com/org.with.dots/repo.with.dots).
""",
            "https://github.com/org.with.dots/repo.with.dots",
            "github.com",
        ),
    ],
)
def test_parse_joss_issue_repository_and_host(
    body: str,
    expected_repository: str | None,
    expected_repo_host: str | None,
) -> None:
    """Parse repository URLs across repository hosts with normalization."""
    parsed = parse_joss_issue(body)

    expect(
        condition=parsed["repository"] == expected_repository,
        message=(
            f"repository mismatch: {parsed['repository']} != {expected_repository}"
        ),
    )
    expect(
        condition=repo_host_from_url(parsed["repository"] or "") == expected_repo_host,
        message=(
            "repo_host mismatch: "
            f"{repo_host_from_url(parsed['repository'] or '')} != "
            f"{expected_repo_host}"
        ),
    )


@pytest.mark.parametrize(
    ("body", "expected_joss_url"),
    [
        (
            (
                "[![status](http://joss.theoj.org/papers/3cfdd80abcde/status.svg)]"
                "(http://joss.theoj.org/papers/3cfdd80abcde)"
            ),
            "https://joss.theoj.org/papers/3cfdd80abcde",
        ),
        (
            "See paper at https://joss.theoj.org/papers/abcdef12345",
            "https://joss.theoj.org/papers/abcdef12345",
        ),
        (
            "http://joss.theoj.org/papers/abcdef12345/status.svg",
            "https://joss.theoj.org/papers/abcdef12345",
        ),
    ],
)
def test_parse_joss_issue_joss_url_formats(
    body: str,
    expected_joss_url: str,
) -> None:
    """Normalize JOSS URLs across badge, direct, and status.svg forms."""
    parsed = parse_joss_issue(body)

    expect(
        condition=parsed["joss_url"] == expected_joss_url,
        message=f"joss_url mismatch: {parsed['joss_url']} != {expected_joss_url}",
    )


def test_parse_joss_issue_noneish_body() -> None:
    """Treat None-ish body values as empty input without failing."""
    parsed = parse_joss_issue(None)  # type: ignore[arg-type]

    expect(condition=parsed["repository"] is None, message="repository should be None")
    expect(condition=parsed["joss_url"] is None, message="joss_url should be None")


def test_parse_joss_issue_does_not_resolve_network_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Do not perform HEAD resolution unless explicitly enabled."""

    def _failing_head(*_args: object, **_kwargs: object) -> object:
        msg = "head() should not be called when JOSS_RESOLVE_URLS is disabled"
        raise AssertionError(msg)

    monkeypatch.delenv("JOSS_RESOLVE_URLS", raising=False)
    monkeypatch.setattr(parsers, "head", _failing_head)

    body = (
        "[![status](http://joss.theoj.org/papers/abc123/status.svg)]"
        "(http://joss.theoj.org/papers/abc123)"
    )
    parsed = parse_joss_issue(body)

    expect(
        condition=parsed["joss_url"] == "https://joss.theoj.org/papers/abc123",
        message="joss_url should normalize without network resolution",
    )
