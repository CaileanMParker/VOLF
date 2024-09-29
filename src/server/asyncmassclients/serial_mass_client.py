""" A serial client that can communicate over multiple ports asynchronously

Exports
-------
MassSerialClient: A serial client that can communicate over multiple ports
    asynchronously
"""

from inspect import signature
from multiprocessing.pool import AsyncResult, ThreadPool
from time import sleep

from serial import Serial, SerialBase, SerialException, SerialTimeoutException  # type: ignore[import-untyped]
from serial.tools.list_ports import comports  # type: ignore[import-untyped]

from .interface import IAsyncMassClient


class SerialMassClient(IAsyncMassClient):
    """A serial client that can communicate over multiple ports asynchronously

    Attributes
    ----------
    ports: A dictionary of available ports mapping port names to port objects

    Methods
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

    def __init__(
        self,
        template: Serial | None = None
    ) -> None:
        """Parameters
        ----------
        template (Optional): A template (ideally closed) serial port
            whose parameters will be used for opening all new ports
        """
        self.__available_ports: dict[str, Serial] = {}
        self.__constructor_parameters = signature(SerialBase).parameters
        self.__template: Serial
        self.template = template

    @property
    def ports(self) -> dict[str, Serial]:
        """A dictionary of available ports mapping port names to port objects"""
        return self.__available_ports

    @property
    def template(self) -> Serial:
        """The template serial port whose parameters will be used for opening
            all new ports
        """
        return self.__template

    @template.setter
    def template(self, template: Serial | None) -> None:
        if not template:
            template = Serial(timeout=1, write_timeout=1)
        elif template.is_open:
            template.close()
        self.__template = template

    def close(self, port: str | Serial) -> None:
        """Close a port

        Parameters
        ----------
        port: The serial port to close
        """
        if isinstance(port, str):
            port = self.__available_ports.pop(port)
        else:
            self.__available_ports.pop(port.port) # type: ignore
        port.close()

    def get_port(self, port_name: str) -> Serial | None:
        """Get a serial port by name

        Parameters
        ----------
        port_name: The name of the port to get

        Returns
        -------
        The serial port if it exists, otherwise None
        """
        return self.__available_ports.get(port_name)

    def mass_close(self, ports: list[str | Serial] | None = None) -> None:
        """Close multiple ports

        Parameters
        ----------
        ports (Optional): The list of serial ports to close, or None to close
            all
        """
        if not ports:
            ports = list(self.__available_ports.values())
        for port in ports:
            self.close(port)

    def mass_open(self, port_names: list[str] | None = None) -> dict[str, Serial]:
        """Open multiple ports asynchronously

        Parameters
        ----------
        port_names (Optional): The list of port names to open, or None to open all

        Returns
        -------
        A dictionary of available ports mapping port names to serial ports
        """

        # Make sure target ports are closed
        if not port_names:
            self.mass_close()
            port_names = [port.device for port in comports()]
        else:
            for port_name in port_names:
                if port_name in self.__available_ports:
                    self.close(self.__available_ports[port_name])

        # Asynchronously attempt to open ports
        pool = ThreadPool(processes=len(port_names))
        async_results: list[AsyncResult] = []
        for port_name in port_names:
            async_results.append(
                pool.apply_async(
                    func=self.open,
                    args=(port_name,)
                )
            )
        pool.close()
        pool.join()

        # Collect available ports
        for result in async_results:
            port: Serial = result.get()
            if port:
                self.__available_ports[port.port] = port  # type: ignore
        return self.__available_ports

    def mass_read(
        self,
        num_bytes: int = 0,
        ports: list[Serial] | None = None
    ) -> list[tuple[str, AsyncResult]]:
        """Read from multiple ports asynchronously

        Parameters
        ----------
        num_bytes: The number of bytes to read from each port, or 0 to read all
        ports (Optional): The list of serial ports to read from, or None to
            read from all

        Returns
        -------
        A list of tuples containing the port name and the async result of bytes
        read
        """
        if not ports:
            ports = list(self.__available_ports.values())
        if not ports:
            raise RuntimeError("No ports available")

        # Asynchronously read from ports
        pool = ThreadPool(processes=len(ports))
        async_results = []
        for port in ports:
            async_results.append(
                (
                    port.port,
                    pool.apply_async(
                        func=self.read,
                        args=(port, num_bytes)
                    )
                )
            )
        pool.close()
        pool.join()
        return async_results

    def mass_write(
        self,
        message: bytes,
        ports: list[Serial] | None = None
    ) -> list[tuple[str, AsyncResult]]:
        """Write to multiple ports asynchronously

        Parameters
        ----------
        message: The bytes to write to each port
        ports (Optional): The list of serial ports to write to, or None to
            write to all

        Returns
        -------
        A list of tuples containing the port name and the async result of
        number of bytes written
        """
        if not ports:
            ports = list(self.__available_ports.values())
        if not ports:
            raise RuntimeError("No ports available")

        # Asynchronously write to ports
        pool = ThreadPool(processes=len(ports))
        async_results = []
        for port in ports:
            async_results.append(
                (
                    port.port,
                    pool.apply_async(
                        func=self.write,
                        args=(port, message)
                    )
                )
            )
        pool.close()
        pool.join()
        return async_results

    def open(self, port_name: str) -> Serial | None:
        """Open a port

        Parameters
        ----------
        port_name: The name of the port to open

        Returns
        -------
        The serial port if it was opened, otherwise None
        """
        try:
            args = {}
            for key, value in self.__template.__dict__.items():
                if key[0] == '_':
                    key = key[1:]
                if key in self.__constructor_parameters and key != 'port':
                    args[key] = value
            port = Serial(port=port_name, **args)
            self.__available_ports[port.port] = port  # type: ignore
            sleep(1)  # Wait for port to finish opening
            return port
        except (OSError, SerialException, SerialTimeoutException):
            return None

    def read(self, port: Serial, num_bytes: int = 0) -> bytes | None:
        """Read from a port

        Parameters
        ----------
        port: The serial port to read from
        num_bytes (Optional): The number of bytes to read, or 0 to read all

        Returns
        -------
        The bytes read if successful, otherwise None
        """
        try:
            if num_bytes > 0:
                bytes_read = port.read(num_bytes)
            else:
                bytes_read = port.read_all()
            return bytes_read
        except (OSError, SerialException, SerialTimeoutException):
            return None

    def write(self, port: Serial, message: bytes) -> int | None:
        """Write to a port

        Parameters
        ----------
        port: The serial port to write to
        message: The bytes to write

        Returns
        -------
        The number of bytes written if successful, otherwise None
        """
        try:
            bytes_sent = port.write(message)
            port.flush()
            return bytes_sent
        except (OSError, SerialException, SerialTimeoutException):
            return None
