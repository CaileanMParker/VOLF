""" Interface for a client that can communicate over multiple
    ports asynchronously

Exports
-------
AsyncMassClient: Interface for a client that can communicate over multiple
    ports asynchronously
"""

from abc import ABC, abstractmethod
from multiprocessing.pool import AsyncResult
from typing import Any


class IAsyncMassClient(ABC):
    """Interface for a client that can communicate over multiple ports
    asynchronously

    Attributes
    ----------
    ports: A dictionary of available ports mapping port names to port objects

    Abstract Methods
    -------
    close: Close a port
    get_port: Get a port object by name
    mass_close: Close multiple ports
    mass_open: Open multiple ports
    mass_read: Read from multiple ports
    mass_write: Write to multiple ports
    open: Open a port
    read: Read from a port
    write: Write to a port
    """

    @abstractmethod
    def __init__(
        self,
        buad: int,
        timeout_seconds: int,
    ) -> None:
        """Parameters
        ----------
        baud: The bitrate for communications from the client
        timeout_seconds: The timeout for client connections in seconds (read &
            write)
        """

    @property
    @abstractmethod
    def ports(self) -> dict[str, Any]:
        """A dictionary of available ports mapping port names to port objects
        """

    @abstractmethod
    def close(self, port: Any) -> None:
        """Close a port

        Parameters
        ----------
        port: The port object to close
        """

    @abstractmethod
    def get_port(self, port_name: str) -> Any | None:
        """Get a port object by name

        Parameters
        ----------
        port_name: The name of the port to get

        Returns
        -------
        The port object if it exists, otherwise None
        """

    @abstractmethod
    def mass_close(self, ports: list[Any] | None = None) -> None:
        """Close multiple ports

        Parameters
        ----------
        ports: The list of port objects to close, or None to close all
        """

    @abstractmethod
    def mass_open(self, port_names: list[str] | None = None) -> dict[str, Any]:
        """Open multiple ports asynchronously

        Parameters
        ----------
        port_names (Optional): The list of port names to open, or None to open
            all

        Returns
        -------
        A dictionary of available ports mapping port names to port objects
        """

    @abstractmethod
    def mass_read(
        self,
        num_bytes: int = 0,
        ports: list[Any] | None = None
    ) -> list[tuple[str, AsyncResult]]:
        """Read from multiple ports asynchronously

        Parameters
        ----------
        num_bytes: The number of bytes to read from each port, or 0 to read all
        ports (Optional): The list of port objects to read from, or None to
            read from all

        Returns
        -------
        A list of tuples containing the port name and the async result of bytes
        read
        """

    @abstractmethod
    def mass_write(
        self,
        message: bytes,
        ports: list[Any] | None = None
    ) -> list[tuple[str, AsyncResult]]:
        """Write to multiple ports asynchronously

        Parameters
        ----------
        message: The bytes to write to each port
        ports (Optional): The list of port objects to write to, or None to
            write to all

        Returns
        -------
        A list of tuples containing the port name and the async result of
        number of bytes written
        """

    @abstractmethod
    def open(self, port_name: str) -> Any | None:
        """Open a port

        Parameters
        ----------
        port_name: The name of the port to open

        Returns
        -------
        The port object if it was able to be opened, otherwise None
        """

    @abstractmethod
    def read(self, port: Any, num_bytes: int = 0) -> bytes | None:
        """Read from a port

        Parameters
        ----------
        port: The port object to read from
        num_bytes (Optional): The number of bytes to read, or 0 to read all

        Returns
        -------
        The bytes read from the port if successful, otherwise None
        """

    @abstractmethod
    def write(self, port: Any, message: bytes) -> int | None:
        """Write to a port

        Parameters
        ----------
        port: The port object to write to
        message: The bytes to write

        Returns
        -------
        The number of bytes written if successful, otherwise None
        """
