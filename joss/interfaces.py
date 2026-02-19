from abc import ABC, abstractmethod


class ExtractInterface(ABC):
    @abstractmethod
    def download_data(self) -> list[dict]: ...


class TransformInterface(ABC):
    @abstractmethod
    def normalaize_data(self) -> list[dict]: ...

    @abstractmethod
    def parse_field_factory(self, field: str) -> str: ...


class LoadInterface(ABC):
    @abstractmethod
    def load_data(self, table: str) -> bool: ...
