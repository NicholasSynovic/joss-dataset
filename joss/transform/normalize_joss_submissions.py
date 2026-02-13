"""
Normalize raw GitHub issue JSON files into a single normalized JSON file.

Copyright (C) Nicholas M. Synovic, 2026

"""

from __future__ import annotations

import argparse
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

LOGGER: logging.Logger = logging.getLogger(__name__)


class NormalGitHubIssue(BaseModel):
    """Normalized representation of a GitHub issue."""

    model_config = ConfigDict(populate_by_name=True)

    gh_id: int = Field(default=-1, alias="id")
    number: int = Field(default=-1)
    user_id: int = Field(default=-1, alias="user_id")
    user_login: str = Field(default="", alias="user_login")
    labels: list[str] = Field(default_factory=list)
    state: str = Field(default="")
    created_at: int = Field(default=-1, alias="created_at")
    updated_at: int = Field(default=-1, alias="updated_at")
    closed_at: int = Field(default=-1, alias="closed_at")
    body: str = Field(default="")


def _load_json(path: Path) -> Any:
    """
    Load a JSON file from disk.

    Returns:
        The decoded JSON object or array.

    """
    return json.loads(path.read_text(encoding="utf-8"))


def _iso_to_unix_timestamp(ts_str: str | None) -> int:
    """
    Convert ISO 8601 datetime to UNIX timestamp.

    Args:
        ts_str: ISO 8601 datetime string or None.

    Returns:
        UNIX timestamp as int, or -1 if invalid.

    """
    if not isinstance(ts_str, str):
        return -1
    try:
        dt = datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
        return int(dt.timestamp())
    except (ValueError, TypeError):
        return -1


def _extract_user_info(user_obj: Any) -> tuple[int, str]:
    """
    Extract user ID and login from user object.

    Args:
        user_obj: The user object from GitHub API.

    Returns:
        Tuple of (user_id, user_login) with defaults (-1, "") if invalid.

    """
    if not isinstance(user_obj, dict):
        return -1, ""
    user_id = user_obj.get("id")
    user_login = user_obj.get("login")
    return (
        user_id if isinstance(user_id, int) else -1,
        user_login if isinstance(user_login, str) else "",
    )


def _extract_labels(labels_list: Any) -> list[str]:
    """
    Extract label names from labels array.

    Args:
        labels_list: List of label objects from GitHub API.

    Returns:
        List of label names as strings, empty list if invalid.

    """
    if not isinstance(labels_list, list):
        return []
    names: list[str] = []
    for item in labels_list:
        if isinstance(item, dict):
            name = item.get("name")
            if isinstance(name, str):
                names.append(name)
    return names


def normalize_github_issue(issue: dict[str, Any]) -> NormalGitHubIssue:
    """
    Normalize a raw GitHub issue to NormalGitHubIssue with defaults for missing fields.

    Args:
        issue: Raw GitHub issue dict

    Returns:
        NormalGitHubIssue with defaults for any missing/invalid fields.

    """
    # Extract with defaults
    gh_id = issue.get("id")
    number = issue.get("number")
    user_obj = issue.get("user")
    user_id, user_login = _extract_user_info(user_obj)

    # Safely extract state with default
    state_val = issue.get("state")
    state = state_val if isinstance(state_val, str) else ""

    # Safely extract body with default
    body_val = issue.get("body")
    body = body_val if isinstance(body_val, str) else ""

    return NormalGitHubIssue(
        id=gh_id if isinstance(gh_id, int) else -1,
        number=number if isinstance(number, int) else -1,
        user_id=user_id,
        user_login=user_login,
        labels=_extract_labels(issue.get("labels")),
        state=state,
        created_at=_iso_to_unix_timestamp(issue.get("created_at")),
        updated_at=_iso_to_unix_timestamp(issue.get("updated_at")),
        closed_at=_iso_to_unix_timestamp(issue.get("closed_at")),
        body=body,
    )


def _labels_from_issue(issue: dict[str, Any]) -> list[str]:
    """
    Extract label names from a GitHub issue payload.

    Returns:
        A list of label names.

    """
    labels_obj = issue.get("labels", [])
    if not isinstance(labels_obj, list):
        return []

    names: list[str] = []
    for item in labels_obj:
        if isinstance(item, dict):
            name = item.get("name")
            if isinstance(name, str):
                names.append(name)
    return names


def _has_defaults(issue: NormalGitHubIssue) -> bool:
    """
    Check if the issue has any default values.

    Args:
        issue: A NormalGitHubIssue instance.

    Returns:
        True if any field has default values, False otherwise.

    """
    return (
        issue.gh_id == -1
        or issue.number == -1
        or issue.user_id == -1
        or not issue.user_login
        or not issue.state
        or issue.created_at == -1
    )


def parse_args() -> argparse.Namespace:
    """
    Parse CLI arguments.

    Returns:
        Parsed CLI args.

    """
    parser = argparse.ArgumentParser(
        description="Normalize GitHub issues JSON file into normalized format."
    )
    parser.add_argument(
        "--in-file",
        required=True,
        help="Path to input JSON file containing array of GitHub issues",
    )
    return parser.parse_args()


def _normalize_issues(issues: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    """
    Normalize all issues into NormalGitHubIssue records.

    Args:
        issues: List of raw GitHub issue dictionaries

    Returns:
        A tuple of (normalized_issues, defaults_used_count).

    """
    normalized: list[dict[str, Any]] = []
    defaults_used = 0

    for issue in issues:
        if not isinstance(issue, dict):
            defaults_used += 1
            continue

        try:
            normalized_issue = normalize_github_issue(issue)
            # Check if any defaults were used
            if _has_defaults(normalized_issue):
                defaults_used += 1

            normalized.append(normalized_issue.model_dump(by_alias=True))
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("Failed to normalize issue: %s", exc)
            defaults_used += 1
            # Still create with all defaults
            try:
                default_issue = NormalGitHubIssue()
                normalized.append(default_issue.model_dump(by_alias=True))
            except Exception as exc:  # noqa: BLE001
                LOGGER.warning("Failed to create default issue: %s", exc)

    return normalized, defaults_used


def main() -> int:
    """
    Run the normalization routine.

    Raises:
        RuntimeError: If the input file does not exist.

    Returns:
        Process exit code (0 for success).

    """
    args = parse_args()

    # Generate timestamp for both output and log files
    timestamp = int(time.time())
    log_filename = f"github_issues_normalized_{timestamp}.log"

    # Configure file logging with DEBUG level
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_filename)],
    )
    LOGGER.info("Logging to file: %s", log_filename)

    in_file = Path(str(args.in_file))
    if not in_file.exists():
        msg = f"Input file does not exist: {in_file}"
        raise RuntimeError(msg)

    # Load issues from single JSON file
    LOGGER.info("Loading issues from %s", in_file)
    data = _load_json(in_file)

    if not isinstance(data, list):
        msg = f"Expected JSON array in {in_file}, got {type(data).__name__}"
        raise RuntimeError(msg)

    issues: list[dict[str, Any]] = data
    LOGGER.info("Found %s issues to normalize", len(issues))

    # Normalize all issues
    normalized, defaults_used = _normalize_issues(issues)

    # Write normalized issues to output file
    out_filename = f"github_issues_normalized_{timestamp}.json"
    out_file = Path(out_filename)
    out_file.write_text(
        json.dumps(normalized, indent=2, sort_keys=True), encoding="utf-8"
    )

    LOGGER.info(
        "Wrote %s normalized issues to %s (defaults_used=%s).",
        len(normalized),
        out_file,
        defaults_used,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
