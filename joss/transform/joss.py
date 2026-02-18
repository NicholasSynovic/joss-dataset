"""Unified transform sub-command for the JOSS CLI."""

from collections import defaultdict
from json import dumps
from logging import Logger
from pathlib import Path
from typing import Any

from progress.bar import Bar
from pydantic_core import ValidationError

from joss.logger import JOSSLogger
from joss.transform.schemas import NormalIssue
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

    def __init__(self, jossLogger: JOSSLogger, in_file: Path) -> None:
        """
        Initialise the transform runner.

        Args:
            in_file: Path to the input JSON file containing an array
                of raw GitHub issues.

        """
        self._in_file: Path = in_file

        self.logger: Logger = jossLogger.get_logger()
        self.timestamp: int = jossLogger.timestamp

    @staticmethod
    def extract(jsonObj: dict) -> NormalIssue:
        data: dict = defaultdict()

        data["body"] = "" if jsonObj["body"] is None else jsonObj["body"]
        data["closed_at"] = (
            0
            if jsonObj["closed_at"] is None
            else JOSSUtils.iso_to_unix(ts=jsonObj["closed_at"])
        )
        data["created_at"] = JOSSUtils.iso_to_unix(ts=jsonObj["created_at"])
        data["issue_number"] = jsonObj["number"]
        data["json_str"] = dumps(obj=jsonObj)
        data["labels"] = [label["name"] for label in jsonObj["labels"]]

        return NormalIssue(**data)

    def execute(self) -> list[NormalIssue]:
        in_path = Path(self._in_file)
        if not in_path.exists():
            msg = f"Input file does not exist: {in_path}"
            raise RuntimeError(msg)

        self.logger.info("Loading issues from %s", in_path)
        data: Any = JOSSUtils.load_json(in_path)

        if not isinstance(data, list):
            msg = f"Expected JSON array in {in_path}, got {type(data).__name__}"
            raise RuntimeError(msg)

        issues: list[dict[str, Any]] = data
        self.logger.info("Found %s issues to normalize", len(issues))

        normalizedIssues: list[NormalIssue] = []
        with Bar("Normalizing issues...", max=len(issues)) as bar:
            issue: dict
            for issue in issues:
                normalizedIssues.append(self.extract(jsonObj=issue))
                bar.next()

        return normalizedIssues
