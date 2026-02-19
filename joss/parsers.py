"""Parsers for JOSS issue bodies and related text formats."""

import re

from requests import head


def parse_joss_issue(body: str) -> dict[str, str | list[str] | None]:
    """
    Parse JOSS issue body text into structured dictionary.

    Extracts metadata fields from JOSS submission issue bodies using
    regex patterns to match HTML comment markers and structured text.

    Args:
        body: Raw issue body text from a JOSS GitHub issue.

    Returns:
        Dictionary with the following keys:
        - author_handle: GitHub username with @ symbol (e.g., "@username")
        - author_name: Full name from ORCID link
        - orcid: ORCID identifier (e.g., "0000-0000-0000-0000")
        - repository: Target repository URL
        - branch: Branch name containing paper.md
        - version: Software version string
        - editor: Assigned editor name or "Pending"
        - reviewers: List of reviewer names (split by comma)
        - managing_eic: Managing Editor in Chief name
        - joss_url: JOSS paper page URL from status badge

        Missing fields have None values. Empty strings are treated as None.

    Example:
        >>> body = "**Submitting author:** <!--author-handle-->@user"
        ... "<!--end-author-handle-->"
        >>> result = parse_joss_issue(body)
        >>> result["author_handle"]
        '@user'

    """
    result: dict[str, str | list[str] | None] = {}

    # Author handle: <!--author-handle-->@username<!--end-author-handle-->
    author_handle_match = re.search(
        r"<!--author-handle-->(.*?)<!--end-author-handle-->",
        body,
    )
    result["author_handle"] = (
        author_handle_match.group(1).strip() if author_handle_match else None
    )

    # Author name and ORCID from the link: <a href="http://orcid.org/...">Name</a>
    orcid_link_match = re.search(
        r'<a[^>]*href="https?://orcid\.org/([^"]+)"[^>]*>([^<]+)</a>',
        body,
    )
    if orcid_link_match:
        result["orcid"] = orcid_link_match.group(1).strip()
        result["author_name"] = orcid_link_match.group(2).strip()
    else:
        result["orcid"] = None
        result["author_name"] = None

    # Repository: <!--target-repository-->URL<!--end-target-repository-->
    repo_match = re.search(
        r"<!--target-repository-->(.*?)<!--end-target-repository-->",
        body,
    )
    result["repository"] = repo_match.group(1).strip() if repo_match else None

    # Branch: <!--branch-->name<!--end-branch-->
    branch_match = re.search(r"<!--branch-->(.*?)<!--end-branch-->", body)
    branch_value = branch_match.group(1).strip() if branch_match else None
    result["branch"] = branch_value or None

    # Version: <!--version-->vX.Y.Z<!--end-version-->
    version_match = re.search(r"<!--version-->(.*?)<!--end-version-->", body)
    result["version"] = version_match.group(1).strip() if version_match else None

    # Editor: <!--editor-->Name<!--end-editor-->
    editor_match = re.search(r"<!--editor-->(.*?)<!--end-editor-->", body)
    result["editor"] = editor_match.group(1).strip() if editor_match else None

    # Reviewers: <!--reviewers-list-->Names<!--end-reviewers-list-->
    reviewers_match = re.search(
        r"<!--reviewers-list-->(.*?)<!--end-reviewers-list-->",
        body,
    )
    if reviewers_match:
        reviewers_raw = reviewers_match.group(1).strip()
        if reviewers_raw:
            result["reviewers"] = [
                r.strip() for r in reviewers_raw.split(",") if r.strip()
            ]
        else:
            result["reviewers"] = None
    else:
        result["reviewers"] = None

    # Managing EiC: **Managing EiC:** Name
    managing_eic_match = re.search(
        r"\*\*Managing EiC:\*\*\s*(.+?)(?:\n|$)",
        body,
    )
    result["managing_eic"] = (
        managing_eic_match.group(1).strip() if managing_eic_match else None
    )

    # JOSS URL from status badge: [![status](...)](URL)
    joss_url_match = re.search(
        r"\[!\[status\]\([^)]+\)\]\((https://joss\.theoj\.org/papers/[^)]+)\)",
        body,
    )
    result["joss_url"] = (
        head(url=joss_url_match.group(1), timeout=60, allow_redirects=True).url
        if joss_url_match
        else None
    )

    return result
