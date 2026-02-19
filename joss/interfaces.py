from abc import ABC, abstractmethod


class ExtractInterface(ABC):
    @abstractmethod
    def download_data(self) -> list[dict]: ...


class TransformInterface(ABC):
    @abstractmethod
    def transform_data(self, data: list[dict]) -> dict[str, list]: ...


class LoadInterface(ABC):
    @abstractmethod
    def load_data(self, data: dict[str, list]) -> bool: ...
