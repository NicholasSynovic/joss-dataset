"""Shared utility functions for the JOSS dataset toolkit."""

# Copyright (c) 2025 Nicholas M. Synovic

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

JSONScalar = str | int | float | bool | None
JSONValue = JSONScalar | list["JSONValue"] | dict[str, "JSONValue"]


class JOSSUtils:
    """Common utility methods for file I/O and timestamp handling."""

    @staticmethod
    def load_json(path: Path) -> JSONValue:
        """
        Load and decode a JSON file from disk.

        Args:
            path: Path to the JSON file.

        Returns:
            The decoded JSON object or array.

        """
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def save_json(
        data: JSONValue,
        path: Path,
        *,
        indent: int = 4,
    ) -> None:
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
        Return the current UTC time in ISO-8601 format (seconds precision).

        Returns:
            The current UTC time in ISO-8601 format (seconds precision).

        """
        return int(
            datetime.now(tz=timezone.utc)
            .replace(
                microsecond=0,
            )
            .timestamp()
        )

    @staticmethod
    def iso_to_unix(ts: str | None) -> int:
        """
        Convert a ISO timestamp to unix seconds.

        Returns:
            Unix seconds. Returns 0 if `ts` is None to keep the schema strictly
            int.

        """
        if ts is None:
            return 0
        dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc,
        )
        return int(dt.timestamp())

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
