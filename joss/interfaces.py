"""Abstract interfaces for extract, transform, and load pipeline stages."""

# Copyright (c) 2025 Nicholas M. Synovic

from abc import ABC, abstractmethod


class ExtractInterface(ABC):
    """Contract for extraction stages that return raw records."""

    @abstractmethod
    def download_data(self) -> list[dict]:
        """
        Download and return source records.

        Returns:
            List of raw record dictionaries.

        """
        raise NotImplementedError


class TransformInterface(ABC):
    """Contract for normalization/transformation stages."""

    @abstractmethod
    def transform_data(self, data: list[dict]) -> dict[str, list]:
        """
        Transform raw records into table-oriented outputs.

        Args:
            data: Raw extracted records.

        Returns:
            Mapping of table name to output rows.

        """
        raise NotImplementedError


class LoadInterface(ABC):
    """Contract for persistence stages that write transformed rows."""

    @abstractmethod
    def load_data(self, data: dict[str, list]) -> bool:
        """
        Persist transformed records to a target store.

        Args:
            data: Mapping of table name to transformed rows.

        Returns:
            ``True`` when persistence succeeds.

        """
        raise NotImplementedError
