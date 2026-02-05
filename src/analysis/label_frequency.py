#!/usr/bin/env python3
# Copyright (c) 2026.
# SPDX-License-Identifier: MIT

"""
Compute the frequency of each issue label in the JOSS dataset.

This script reads the normalized submissions file produced by the transform step
and emits a CSV table where:

- Left column: label name
- Right column: frequency (count of submissions that contain that label)

Pipeline:
- ingest:    src/ingest/github_issues.py (raw issue JSONs; not committed)
- transform: src/transform/normalize_joss_submissions.py
  -> data/derived/joss_submissions.json
- analysis:  src/analysis/label_frequency.py
  -> data/derived/label_frequency.csv

Inputs:
- data/derived/joss_submissions.json

Outputs:
- data/derived/label_frequency.csv
"""

from __future__ import annotations

import argparse
import csv
import logging
from collections import Counter
from pathlib import Path
from typing import Any

from .utils import load_submissions

LOGGER: logging.Logger = logging.getLogger(__name__)


def _extract_labels(submission: dict[str, Any]) -> list[str]:
    """
    Extract label names from a normalized submission.

    Args:
        submission: A normalized submission record.

    Returns:
        A list of label names (strings). Non-string values are ignored.

    """
    labels_obj = submission.get("Labels", [])
    if not isinstance(labels_obj, list):
        return []

    return [item for item in labels_obj if isinstance(item, str)]


def _count_label_frequency(submissions: list[dict[str, Any]]) -> Counter[str]:
    """
    Count label frequency across submissions.

    Note: This counts labels per submission (i.e., each submission contributes
    +1 to each label it contains). Duplicate label strings within a single
    submission are deduplicated defensively.

    Args:
        submissions: Normalized submissions list.

    Returns:
        A Counter mapping label -> frequency.

    """
    counts: Counter[str] = Counter()

    for sub in submissions:
        labels = _extract_labels(sub)
        for label in set(labels):
            counts[label] += 1

    return counts


def _write_label_frequency_csv(counts: Counter[str], out_path: Path) -> None:
    """
    Write label frequencies to a CSV file.

    Args:
        counts: Counter mapping label -> frequency.
        out_path: Output CSV path.

    Raises:
        RuntimeError: If there are no labels to write.

    """
    if not counts:
        msg = "No labels found to write."
        raise RuntimeError(msg)

    out_path.parent.mkdir(parents=True, exist_ok=True)

    rows = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))

    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["label", "frequency"])
        for label, freq in rows:
            writer.writerow([label, freq])


def parse_args() -> argparse.Namespace:
    """
    Parse CLI args.

    Returns:
        Parsed CLI namespace.

    """
    parser = argparse.ArgumentParser(
        description=(
            "Create a CSV table of label frequencies from normalized JOSS submissions."
        )
    )
    parser.add_argument(
        "--in-file",
        default="data/derived/joss_submissions.json",
        help="Input normalized submissions JSON",
    )
    parser.add_argument(
        "--out-file",
        default="data/derived/label_frequency.csv",
        help="Output CSV file path",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (DEBUG/INFO/WARNING/ERROR)",
    )
    return parser.parse_args()


def main() -> int:
    """
    Run the label frequency analysis.

    Returns:
        Process exit code.

    Raises:
        RuntimeError: If the input file is missing or no labels are found.

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

    counts = _count_label_frequency(submissions)
    LOGGER.info("Found %s unique labels", len(counts))

    _write_label_frequency_csv(counts, out_file)
    LOGGER.info("Wrote label frequency CSV to %s", out_file)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
