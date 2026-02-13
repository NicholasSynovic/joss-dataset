#!/usr/bin/env python3
# Copyright (c) 2026.
# SPDX-License-Identifier: MIT

"""
Plot issue spoilage (time-to-close) per year.

Definition (used here):
- "Issue spoilage" is the time an issue remains open before it is closed.
- For each opened year, compute the median time-to-close (in days) for issues
  that have a non-zero Closed timestamp.

Pipeline:
- ingest:    src/ingest/github_issues.py (raw issue JSONs; not committed)
- transform: src/transform/normalize_joss_submissions.py
  -> data/derived/joss_submissions.json
- analysis:  src/analysis/issue_spoilage_per_year.py
  -> data/plots/issue_spoilage_per_year.png

Inputs:
- data/derived/joss_submissions.json

Outputs:
- data/plots/issue_spoilage_per_year.png
"""

from __future__ import annotations

import argparse
import logging
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any

import matplotlib.pyplot as plt

from .utils import load_submissions, unix_to_year

LOGGER: logging.Logger = logging.getLogger(__name__)


def _days_open(opened_ts: int, closed_ts: int) -> int | None:
    """
    Compute number of days an issue was open.

    Args:
        opened_ts: Opened UNIX timestamp seconds.
        closed_ts: Closed UNIX timestamp seconds.

    Returns:
        Integer days open (rounded down), or None if timestamps are invalid.

    """
    if opened_ts <= 0 or closed_ts <= 0:
        return None
    if closed_ts < opened_ts:
        return None

    opened_dt = datetime.fromtimestamp(opened_ts, tz=timezone.utc)
    closed_dt = datetime.fromtimestamp(closed_ts, tz=timezone.utc)
    delta = closed_dt - opened_dt
    return int(delta.days)


def _opened_year(submission: dict[str, Any]) -> int | None:
    """
    Extract the opened year from a normalized submission.

    Args:
        submission: A normalized submission record.

    Returns:
        The opened year (UTC), or None if not available.

    """
    opened = submission.get("Opened")
    if not isinstance(opened, int):
        return None
    return unix_to_year(opened)


def _closed_ts(submission: dict[str, Any]) -> int | None:
    """
    Extract the closed timestamp from a normalized submission.

    Args:
        submission: A normalized submission record.

    Returns:
        The closed UNIX timestamp seconds, or None if not available.

    """
    closed = submission.get("Closed")
    if not isinstance(closed, int):
        return None
    if closed <= 0:
        return None
    return closed


def _median_spoilage_by_year(submissions: list[dict[str, Any]]) -> dict[int, float]:
    """
    Compute median time-to-close (days) grouped by opened year.

    Args:
        submissions: Normalized submissions list.

    Returns:
        Mapping year -> median days-to-close.

    """
    per_year: dict[int, list[int]] = {}

    for sub in submissions:
        year = _opened_year(sub)
        if year is None:
            continue

        opened = sub.get("Opened")
        closed = _closed_ts(sub)
        if not isinstance(opened, int) or closed is None:
            continue

        days = _days_open(opened, closed)
        if days is None:
            continue

        per_year.setdefault(year, []).append(days)

    medians: dict[int, float] = {}
    for year, days_list in per_year.items():
        if days_list:
            medians[year] = float(median(days_list))

    return dict(sorted(medians.items()))


def _plot_median_spoilage(medians: dict[int, float], out_path: Path) -> None:
    """
    Plot median spoilage per year and save to PNG.

    Args:
        medians: Mapping year -> median days-to-close.
        out_path: Output PNG path.

    Raises:
        RuntimeError: If there is no data to plot.

    """
    if not medians:
        msg = "No closed-issue data available to plot spoilage."
        raise RuntimeError(msg)

    years = sorted(medians.keys())
    values = [medians[y] for y in years]

    fig, ax = plt.subplots()
    ax.bar(years, values)
    ax.set_title("Issue spoilage per year (median days-to-close)")
    ax.set_xlabel("Year (opened)")
    ax.set_ylabel("Median days to close")
    ax.set_xticks(years)
    ax.tick_params(axis="x", rotation=45)

    fig.tight_layout()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    """
    Parse CLI args.

    Returns:
        Parsed CLI namespace.

    """
    parser = argparse.ArgumentParser(
        description="Plot issue spoilage per year (median days-to-close)."
    )
    parser.add_argument(
        "--in-file",
        default="data/derived/joss_submissions.json",
        help="Input normalized submissions JSON",
    )
    parser.add_argument(
        "--out-file",
        default="data/plots/issue_spoilage_per_year.png",
        help="Output PNG file path",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (DEBUG/INFO/WARNING/ERROR)",
    )
    return parser.parse_args()


def main() -> int:
    """
    Run the issue spoilage plotter.

    Returns:
        Process exit code.

    Raises:
        RuntimeError: If the input file is missing or no spoilage data exists.

    """
    args = parse_args()

    level_name = str(args.log_level).upper()
    logging.basicConfig(
        level=getattr(logging, level_name, logging.INFO),
        format="%(levelname)s: %(message)s",
    )

    in_file = Path(str(args.in_file))
    out_file = Path(str(args.out_file))

    if not in_file.exists():
        msg = (
            f"Input file not found: {in_file}\n"
            "Run the normalization step first to generate "
            "data/derived/joss_submissions.json"
        )
        raise RuntimeError(msg)

    submissions = load_submissions(in_file)
    LOGGER.info("Loaded %s submissions from %s", len(submissions), in_file)

    medians = _median_spoilage_by_year(submissions)
    LOGGER.info("Computed spoilage medians for %s years", len(medians))

    _plot_median_spoilage(medians, out_file)
    LOGGER.info("Wrote spoilage plot to %s", out_file)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
