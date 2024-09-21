from abc import ABC, abstractmethod
from multiprocessing.pool import AsyncResult
from typing import Any


class AsyncMassClient(ABC):

    @abstractmethod
    def __init__(
        self,
        buad: int,
        timeout_seconds: int,
    ) -> None: ...

    @property
    @abstractmethod
    def ports(self) -> dict[str, Any]: ...

    @abstractmethod
    def get_port(self, port_name: str) -> Any: ...

    @abstractmethod
    def mass_close(self, ports: list[Any] | None = None) -> None: ...

    @abstractmethod
    def mass_open(self, port_names: list[str] | None = None) -> dict[str, Any]: ...

    @abstractmethod
    def mass_read(
        self,
        num_bytes: int = 0,
        ports: list[Any] | None = None
    ) -> list[tuple[str, AsyncResult]]: ...

    @abstractmethod
    def mass_write(
        self,
        message: bytes,
        ports: list[Any] | None = None
    ) -> list[tuple[str, AsyncResult]]: ...

    @abstractmethod
    def open(self, port_name: str) -> Any | None: ...

    @abstractmethod
    def read(self, port: Any, num_bytes: int = 0) -> bytes | None: ...

    @abstractmethod
    def write(self, port: Any, message: bytes) -> int | None: ...

    @abstractmethod
    def close(self, port: Any) -> None: ...