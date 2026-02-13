#!/usr/bin/env python3
# Copyright (c) 2026.
# SPDX-License-Identifier: MIT

"""
Normalize JOSS review issue bodies into a stable JSON structure.

JOSS issue bodies include HTML comment sentinels like:
<!--author-handle-->...<!--end-author-handle-->
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class JOSSSubmission(BaseModel):
    """Normalized representation of a JOSS review issue."""

    model_config = ConfigDict(populate_by_name=True)

    issue_number: int = Field(..., alias="Issue Number")
    submitting_author: str = Field("", alias="Submitting Author")
    repository: str = Field("", alias="Repository")
    branch: str = Field("", alias="Branch")
    version: str = Field("", alias="Version")
    editor: str = Field("", alias="Editor")
    reviewers: list[str] = Field(default_factory=list, alias="Reviewers")
    archive: str = Field("", alias="Archive")
    opened: int = Field(..., alias="Opened")  # unix seconds
    closed: int = Field(..., alias="Closed")  # unix seconds; 0 if not closed
    labels: list[str] = Field(default_factory=list, alias="Labels")
    json_str: str = Field(..., alias="JSON_str")


_TAG_RE_TEMPLATE = r"<!--{tag}-->\s*([\s\S]*?)\s*<!--end-{tag}-->"


def _extract_tag(body: str, tag: str) -> str:
    """
    Extract content between JOSS HTML comment sentinels for `tag`.

    Returns:
        The extracted tag contents (stripped), or an empty string if not found.

    """
    pattern = _TAG_RE_TEMPLATE.format(tag=re.escape(tag))
    match = re.search(pattern, body)
    return match.group(1).strip() if match else ""


def _parse_reviewers(raw: str) -> list[str]:
    """
    Parse reviewers from a comma/line-separated string.

    Returns:
        A list of reviewer handles/names.

    """
    if not raw.strip():
        return []
    parts = re.split(r"[,\n]+", raw)
    return [p.strip() for p in parts if p.strip()]


def _iso_to_unix(ts: str | None) -> int:
    """
    Convert a GitHub ISO timestamp to unix seconds.

    Returns:
        Unix seconds. Returns 0 if `ts` is None to keep the schema strictly int.

    """
    if ts is None:
        return 0
    dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


def from_github_issue_payload(
    *,
    issue_number: int,
    body: str,
    created_at: str,
    closed_at: str | None,
    labels: list[str],
) -> JOSSSubmission:
    """
    Create a JOSSSubmission from raw GitHub issue fields.

    Returns:
        A normalized JOSSSubmission record.

    """
    opened_unix = _iso_to_unix(created_at)
    closed_unix = _iso_to_unix(closed_at)

    reviewers = _parse_reviewers(_extract_tag(body, "reviewers-list"))
    archive = _extract_tag(body, "archive")

    base: dict[str, Any] = {
        "Issue Number": issue_number,
        "Submitting Author": _extract_tag(body, "author-handle"),
        "Repository": _extract_tag(body, "target-repository"),
        "Branch": _extract_tag(body, "branch"),
        "Version": _extract_tag(body, "version"),
        "Editor": _extract_tag(body, "editor"),
        "Reviewers": reviewers,
        "Archive": archive,
        "Opened": opened_unix,
        "Closed": closed_unix,
        "Labels": labels,
    }

    # Build a normalized object WITHOUT JSON_str first, then compute JSON_str from it.
    tmp = JOSSSubmission(**{**base, "JSON_str": ""})
    tmp_dict = tmp.model_dump(by_alias=True)

    without_json_str = {k: v for k, v in tmp_dict.items() if k != "JSON_str"}
    json_str = json.dumps(without_json_str, sort_keys=True)

    return JOSSSubmission(**{**base, "JSON_str": json_str})
