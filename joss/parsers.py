"""Parsing helpers for extracting structured metadata from JOSS issue bodies."""

# Copyright (c) 2025 Nicholas M. Synovic

import html
import os
import re
from urllib.parse import urlparse

from requests import head
from requests.exceptions import RequestException

TRAILING_URL_NOISE = ").,;:!?>]}"
PREFERRED_REPO_HOSTS = ("github.com", "gitlab.com", "bitbucket.org")
GITHUB_MIN_SEGMENTS = 2


def normalize_issue_body(body: str) -> str:
    r"""
    Normalize JOSS issue body text for robust parsing.

    This helper is intentionally pure (no network calls) and performs:
    - None-safe conversion to string
    - HTML entity unescaping
    - Newline normalization to ``\n``
    - Anchor replacement that preserves the link target (href) where present
    - Removal of remaining HTML tags

    Args:
        body: Raw issue body text from a JOSS GitHub issue.

    Returns:
        Normalized plain-text representation of the issue body.

    """
    if body is None:
        return ""

    normalized = html.unescape(body)
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")

    def _replace_anchor(match: re.Match[str]) -> str:
        href_match = re.search(
            r'href\s*=\s*["\']([^"\']+)["\']',
            match.group(0),
            flags=re.IGNORECASE,
        )
        if href_match:
            return href_match.group(1)
        return match.group(1)

    normalized = re.sub(
        r"<a\b[^>]*>(.*?)</a>",
        _replace_anchor,
        normalized,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return re.sub(r"<[^>]+>", " ", normalized)


def clean_url(url: str) -> str:
    """
    Clean extracted URL text by removing wrappers and trailing noise.

    Args:
        url: Raw URL text.

    Returns:
        Cleaned URL-like text.

    """
    cleaned = (url or "").strip()
    while cleaned and cleaned[0] in "<([{\"'":
        cleaned = cleaned[1:].strip()
    while cleaned and cleaned[-1] in ">)]}\"'":
        cleaned = cleaned[:-1].strip()
    while cleaned and cleaned[-1] in TRAILING_URL_NOISE:
        cleaned = cleaned[:-1].strip()
    while cleaned.endswith("/"):
        cleaned = cleaned[:-1]
    return cleaned


def normalize_repo_url(url: str) -> str:
    """
    Normalize extracted repository URLs with GitHub canonicalization.

    - Converts HTTP to HTTPS
    - Drops ``www.`` host prefix
    - Canonicalizes GitHub URLs to ``https://github.com/<owner>/<repo>``
    - Preserves non-GitHub path structure

    Args:
        url: Cleaned repository URL candidate.

    Returns:
        Normalized repository URL or empty string if invalid.

    """
    candidate = clean_url(url)
    if not re.match(r"^https?://", candidate, flags=re.IGNORECASE):
        return ""

    parsed = urlparse(candidate)
    hostname = (parsed.hostname or "").lower()
    if not hostname:
        return ""
    hostname = hostname.removeprefix("www.")

    path = (parsed.path or "").strip()

    if hostname == "github.com":
        segments = [segment for segment in path.split("/") if segment]
        if len(segments) < GITHUB_MIN_SEGMENTS:
            return ""
        owner = segments[0]
        repo = segments[1]
        if repo.lower().endswith(".git"):
            repo = repo[:-4]
        repo = clean_url(repo)
        if not owner or not repo:
            return ""
        return f"https://github.com/{owner}/{repo}"

    normalized_path = clean_url(path)
    if normalized_path and not normalized_path.startswith("/"):
        normalized_path = f"/{normalized_path}"
    return f"https://{hostname}{normalized_path}"


def repo_host_from_url(url: str) -> str | None:
    """
    Extract lowercase host from URL without a leading ``www.``.

    Args:
        url: Repository URL string.

    Returns:
        Lowercase host string, or ``None`` when host parsing fails.

    """
    parsed = urlparse((url or "").strip())
    hostname = (parsed.hostname or "").lower()
    if not hostname:
        return None
    return hostname.removeprefix("www.")


def _normalize_known_scheme(url: str) -> str:
    """
    Normalize known domains to HTTPS while keeping other URLs unchanged.

    Args:
        url: URL string to normalize.

    Returns:
        URL with normalized scheme/known host behavior.

    """
    cleaned = clean_url(url)
    lowered = cleaned.lower()

    if lowered.startswith("http://github.com/"):
        return "https://" + cleaned[len("http://") :]
    if lowered.startswith("http://joss.theoj.org/"):
        return "https://" + cleaned[len("http://") :]
    if lowered.startswith("http://orcid.org/"):
        return "https://" + cleaned[len("http://") :]

    if lowered.startswith("http://"):
        return "https://" + cleaned[len("http://") :]

    return clean_url(cleaned)


def _extract_url_candidates(text: str) -> list[str]:
    """
    Return URL-like candidates from text in encounter order.

    Args:
        text: Input text that may contain URLs.

    Returns:
        List of URL-like candidate tokens.

    """
    return re.findall(r"https?://[^\s\"'<>]+", text, flags=re.IGNORECASE)


def _select_preferred_repo_url(candidates: list[str]) -> str | None:
    """
    Select preferred repository URL, biasing GitHub/GitLab/Bitbucket.

    Args:
        candidates: URL candidate strings.

    Returns:
        Preferred normalized repository URL, or ``None``.

    """
    normalized: list[tuple[str, str | None]] = []
    for candidate in candidates:
        normalized_url = normalize_repo_url(candidate)
        if not normalized_url:
            continue
        normalized.append((normalized_url, repo_host_from_url(normalized_url)))

    if not normalized:
        return None

    for preferred_host in PREFERRED_REPO_HOSTS:
        for normalized_url, host in normalized:
            if host == preferred_host:
                return normalized_url

    return normalized[0][0]


def _extract_repository(raw_body: str, normalized_body: str) -> str | None:
    """
    Extract repository URL using marker-based parsing then legacy fallbacks.

    Args:
        raw_body: Original issue body.
        normalized_body: Normalized issue body text.

    Returns:
        Normalized repository URL, or ``None`` if not found.

    """
    marker_match = re.search(
        r"<!--target-repository-->(.*?)<!--end-target-repository-->",
        raw_body,
        flags=re.DOTALL,
    )
    candidate = marker_match.group(1).strip() if marker_match else None
    if candidate:
        normalized_candidate = normalize_repo_url(candidate)
        if normalized_candidate:
            return normalized_candidate

    if candidate is None:
        repository_line_match = re.search(
            r"(?:\*\*\s*)?Repository(?:\s*\*\*)?\s*:\s*([^\n]+)",
            normalized_body,
            flags=re.IGNORECASE,
        )
        if repository_line_match:
            repo_line_value = repository_line_match.group(1).strip()
            selected_from_line = _select_preferred_repo_url(
                _extract_url_candidates(repo_line_value)
            )
            if selected_from_line:
                return selected_from_line

    return _select_preferred_repo_url(_extract_url_candidates(normalized_body))


def _extract_joss_url(normalized_body: str) -> str | None:
    """
    Extract canonical JOSS paper URL from badge, direct URL, or status SVG.

    Args:
        normalized_body: Normalized issue body text.

    Returns:
        Canonical JOSS paper URL, or ``None``.

    """
    badge_match = re.search(
        r"\[!\[status\]\([^)]+\)\]\((https?://joss\.theoj\.org/papers/[A-Za-z0-9._-]+)\)",
        normalized_body,
        flags=re.IGNORECASE,
    )
    if badge_match:
        url = _normalize_known_scheme(badge_match.group(1))
        return clean_url(url)

    paper_match = re.search(
        r"https?://joss\.theoj\.org/papers/([A-Za-z0-9._-]+)(?=$|[\s\)\]\"'<>,}.])",
        normalized_body,
        flags=re.IGNORECASE,
    )
    if paper_match:
        return f"https://joss.theoj.org/papers/{paper_match.group(1)}"

    status_match = re.search(
        r"https?://joss\.theoj\.org/papers/([A-Za-z0-9._-]+)/status\.svg",
        normalized_body,
        flags=re.IGNORECASE,
    )
    if status_match:
        return f"https://joss.theoj.org/papers/{status_match.group(1)}"

    return None


def _resolve_url(url: str) -> str:
    """
    Resolve URL redirects safely.

    Args:
        url: URL to resolve.

    Returns:
        Redirect target URL, or original input URL when resolution fails.

    """
    try:
        return head(url=url, timeout=10, allow_redirects=True).url
    except (RequestException, TimeoutError, ValueError):
        return url


def _maybe_resolve_joss_url(url: str | None) -> str | None:
    """
    Resolve JOSS URLs only when explicitly enabled by environment variable.

    Args:
        url: Parsed JOSS URL.

    Returns:
        Resolved URL if enabled, original URL when disabled, or ``None``.

    """
    if not url:
        return None
    if os.getenv("JOSS_RESOLVE_URLS", "0") != "1":
        return url
    if not re.match(r"https?://joss\.theoj\.org/", url, flags=re.IGNORECASE):
        return url
    return clean_url(_resolve_url(url))


def parse_joss_issue(body: str) -> dict[str, str | list[str] | None]:
    r"""
    Parse JOSS issue body text into structured dictionary.

    Extracts metadata from both marker-based issue templates and legacy/
    freeform issue bodies. Supports ``http``/``https`` links, HTML anchors,
    and fallback URL extraction when HTML comment markers are missing.

    URL normalization converts known domains (GitHub, JOSS, ORCID) to
    ``https`` and strips common trailing punctuation noise. Network URL
    resolution is disabled by default to keep parsing deterministic and
    test-friendly; set ``JOSS_RESOLVE_URLS=1`` to enable redirect resolution
    for JOSS paper URLs.

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
    raw_body = body or ""
    normalized_body = normalize_issue_body(raw_body)
    result: dict[str, str | list[str] | None] = {}

    # Author handle: <!--author-handle-->@username<!--end-author-handle-->
    author_handle_match = re.search(
        r"<!--author-handle-->(.*?)<!--end-author-handle-->",
        raw_body,
    )
    result["author_handle"] = (
        author_handle_match.group(1).strip() if author_handle_match else None
    )

    # Author name and ORCID from the link: <a href="http://orcid.org/...">Name</a>
    orcid_link_match = re.search(
        r'<a[^>]*href="https?://orcid\.org/([^"]+)"[^>]*>([^<]+)</a>',
        normalized_body,
    )
    if orcid_link_match:
        result["orcid"] = _normalize_known_scheme(
            f"https://orcid.org/{orcid_link_match.group(1).strip()}"
        ).split("/")[-1]
        result["author_name"] = orcid_link_match.group(2).strip()
    else:
        orcid_url_match = re.search(
            r"https?://orcid\.org/([0-9X-]{15,19})",
            normalized_body,
            flags=re.IGNORECASE,
        )
        result["orcid"] = (
            _normalize_known_scheme(orcid_url_match.group(0)).split("/")[-1]
            if orcid_url_match
            else None
        )
        result["author_name"] = None

    # Repository: marker-based first, then fallback extraction
    result["repository"] = _extract_repository(raw_body, normalized_body)

    # Branch: <!--branch-->name<!--end-branch-->
    branch_match = re.search(r"<!--branch-->(.*?)<!--end-branch-->", raw_body)
    branch_value = branch_match.group(1).strip() if branch_match else None
    result["branch"] = branch_value or None

    # Version: <!--version-->vX.Y.Z<!--end-version-->
    version_match = re.search(r"<!--version-->(.*?)<!--end-version-->", raw_body)
    result["version"] = version_match.group(1).strip() if version_match else None

    # Editor: <!--editor-->Name<!--end-editor-->
    editor_match = re.search(r"<!--editor-->(.*?)<!--end-editor-->", raw_body)
    result["editor"] = editor_match.group(1).strip() if editor_match else None

    # Reviewers: <!--reviewers-list-->Names<!--end-reviewers-list-->
    reviewers_match = re.search(
        r"<!--reviewers-list-->(.*?)<!--end-reviewers-list-->",
        raw_body,
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
        normalized_body,
    )
    result["managing_eic"] = (
        managing_eic_match.group(1).strip() if managing_eic_match else None
    )

    # JOSS URL from status badge/direct URL/status.svg URL
    result["joss_url"] = _maybe_resolve_joss_url(_extract_joss_url(normalized_body))

    return result
