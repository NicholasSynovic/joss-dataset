# Copyright (c) 2026.
# SPDX-License-Identifier: MIT

"""Unified transform sub-command for the JOSS CLI."""

import logging
from pathlib import Path
from typing import Any

from joss.logger import JOSSLogger
from joss.transform.joss_submission import from_github_issue_payload
from joss.transform.normalize_joss_submissions import _labels_from_issue
from joss.utils import JOSSUtils


class JOSSTransform:
    """
    Normalize raw GitHub issues into a stable JSON structure.

    This class encapsulates the transformation workflow used by the
    unified ``joss transform`` CLI sub-command.  It mirrors the logic
    in the standalone ``normalize_joss_submissions.py`` script but
    delegates file I/O, logging, and timestamp handling to the shared
    utility classes.
    """

    def __init__(self, in_file: str) -> None:
        """
        Initialise the transform runner.

        Args:
            in_file: Path to the input JSON file containing an array
                of raw GitHub issues.

        """
        self._in_file: str = in_file

    @staticmethod
    def _normalize_issues(
        issues: list[dict[str, Any]],
        logger: logging.Logger,
    ) -> tuple[list[dict[str, Any]], int, int]:
        """
        Normalize all issues into ``JOSSSubmission`` records.

        Each raw GitHub issue dictionary is validated, its fields
        extracted, and then passed to
        :func:`~joss.transform.joss_submission.from_github_issue_payload`
        for normalization.

        Args:
            issues: List of raw GitHub issue dictionaries.
            logger: Logger instance for warnings.

        Returns:
            A tuple of (normalized_issues, skipped_count, failed_count).

        """
        normalized: list[dict[str, Any]] = []
        skipped: int = 0
        failed: int = 0

        for issue in issues:
            if not isinstance(issue, dict):
                skipped += 1
                continue

            body = issue.get("body")
            if not isinstance(body, str) or "<!--author-handle-->" not in body:
                skipped += 1
                continue

            number = issue.get("number")
            created_at = issue.get("created_at")
            closed_at = issue.get("closed_at")

            if not isinstance(number, int) or not isinstance(created_at, str):
                skipped += 1
                continue

            labels = _labels_from_issue(issue)

            try:
                submission = from_github_issue_payload(
                    issue_number=number,
                    body=body,
                    created_at=created_at,
                    closed_at=closed_at if isinstance(closed_at, str) else None,
                    labels=labels,
                )
            except Exception as exc:  # noqa: BLE001
                failed += 1
                logger.warning(
                    "Failed to normalize issue #%s: %s",
                    number,
                    exc,
                )
                continue

            normalized.append(submission.model_dump(by_alias=True))

        return normalized, skipped, failed

    def execute(self) -> int:
        """
        Run the full normalization routine.

        Returns:
            Exit code (``0`` for success).

        Raises:
            RuntimeError: If the input file does not exist or does not
                contain a JSON array.

        """
        timestamp: int = JOSSUtils.get_timestamp()

        joss_logger = JOSSLogger(__name__)
        joss_logger.setup_file_logging(
            timestamp,
            "github_issues_normalized",
        )
        logger: logging.Logger = joss_logger.get_logger()

        in_path = Path(self._in_file)
        if not in_path.exists():
            msg = f"Input file does not exist: {in_path}"
            raise RuntimeError(msg)

        logger.info("Loading issues from %s", in_path)
        data: Any = JOSSUtils.load_json(in_path)

        if not isinstance(data, list):
            msg = f"Expected JSON array in {in_path}, got {type(data).__name__}"
            raise RuntimeError(msg)

        issues: list[dict[str, Any]] = data
        logger.info("Found %s issues to normalize", len(issues))

        normalized, skipped, failed = self._normalize_issues(issues, logger)

        out_path = Path(
            f"github_issues_normalized_{timestamp}.json",
        )
        JOSSUtils.save_json(normalized, out_path)

        logger.info(
            "Wrote %s normalized issues to %s (skipped=%s failed=%s).",
            len(normalized),
            out_path,
            skipped,
            failed,
        )
        return 0
