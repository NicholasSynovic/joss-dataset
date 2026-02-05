#!/usr/bin/env python3
# Copyright (c) 2026.
# SPDX-License-Identifier: MIT

"""
Shared analysis utilities.

This module contains small, reusable helpers for analysis scripts that operate
on the normalized JOSS submissions dataset.

Typical input:
- data/derived/joss_submissions.json
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def unix_to_year(ts: int) -> int:
    """
    Convert unix seconds to UTC year.

    Args:
        ts: UNIX timestamp in seconds.

    Returns:
        The UTC year corresponding to the timestamp.

    """
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    return int(dt.year)


def load_submissions(path: Path) -> list[dict[str, Any]]:
    """
    Load normalized submissions JSON list.

    Args:
        path: Path to a JSON file containing a top-level list of submissions.

    Returns:
        A list of submission objects (dicts).

    Raises:
        RuntimeError: If the JSON is not a top-level list.

    """
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        msg = "Expected top-level JSON list of submissions"
        raise RuntimeError(msg)

    return [item for item in data if isinstance(item, dict)]


def count_years(
    submissions: list[dict[str, Any]],
    key: str,
    *,
    skip_zero: bool,
) -> Counter[int]:
    """
    Count occurrences per UTC year for a given UNIX timestamp key.

    Args:
        submissions: Normalized submissions list.
        key: Field name containing UNIX timestamp seconds (e.g., "Opened", "Closed").
        skip_zero: Whether to skip timestamps equal to 0.

    Returns:
        A Counter mapping year -> count.

    """
    counts: Counter[int] = Counter()

    for sub in submissions:
        ts = sub.get(key)
        if not isinstance(ts, int):
            continue
        if skip_zero and ts == 0:
            continue

        year = unix_to_year(ts)
        counts[year] += 1

    return counts
