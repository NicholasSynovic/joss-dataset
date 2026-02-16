"""Logging configuration for the JOSS dataset toolkit."""

from __future__ import annotations

import logging


class JOSSLogger:
    """
    File-based logger scoped to a named component.

    Each instance wraps a standard :class:`logging.Logger` and provides
    a convenience method to attach a timestamped file handler at
    ``DEBUG`` level.
    """

    def __init__(self, name: str) -> None:
        """
        Initialise the logger wrapper.

        Args:
            name: Logger name passed to :func:`logging.getLogger`.

        """
        self._logger: logging.Logger = logging.getLogger(name)

    def setup_file_logging(self, timestamp: int, prefix: str) -> str:
        """
        Attach a ``DEBUG``-level file handler to the logger.

        The log file is named ``<prefix>_<timestamp>.log`` and is
        written to the current working directory.

        Args:
            timestamp: UNIX timestamp used in the log filename.
            prefix: Filename prefix (e.g. ``"github_issues"``).

        Returns:
            The log filename that was created.

        """
        log_filename: str = f"{prefix}_{timestamp}.log"
        handler = logging.FileHandler(log_filename)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        handler.setFormatter(formatter)
        self._logger.setLevel(logging.DEBUG)
        self._logger.addHandler(handler)
        self._logger.info("Logging to file: %s", log_filename)
        return log_filename

    def get_logger(self) -> logging.Logger:
        """
        Return the underlying :class:`logging.Logger`.

        Returns:
            The configured logger instance.

        """
        return self._logger
