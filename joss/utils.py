"""Shared utility functions for the JOSS dataset toolkit."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


class JOSSUtils:
    """Common utility methods for file I/O and timestamp handling."""

    @staticmethod
    def load_json(path: Path) -> Any:  # noqa: ANN401
        """
        Load and decode a JSON file from disk.

        Args:
            path: Path to the JSON file.

        Returns:
            The decoded JSON object or array.

        """
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def save_json(data: Any, path: Path, *, indent: int = 2) -> None:  # noqa: ANN401
        """
        Serialize data to a JSON file on disk.

        Args:
            data: The Python object to serialize.
            path: Destination file path.
            indent: Number of spaces for indentation.

        """
        path.write_text(
            json.dumps(data, indent=indent, sort_keys=True),
            encoding="utf-8",
        )

    @staticmethod
    def get_timestamp() -> int:
        """
        Return the current UNIX timestamp in seconds.

        Returns:
            Current UNIX timestamp as an integer.

        """
        return int(time.time())

    @staticmethod
    def extract_timestamp_from_filename(filename: str) -> int | None:
        """
        Extract a UNIX timestamp embedded at the end of a filename.

        The timestamp is expected to be the last underscore-separated
        segment of the stem.  For example,
        ``github_issues_1234567890.json`` yields ``1234567890``.

        Args:
            filename: The filename (not a full path) to parse.

        Returns:
            The extracted timestamp, or ``None`` if parsing fails.

        """
        stem = Path(filename).stem
        parts = stem.split("_")
        try:
            return int(parts[-1])
        except (ValueError, IndexError):
            return None
