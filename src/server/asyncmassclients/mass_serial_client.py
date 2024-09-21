""" A serial client that can communicate over multiple ports asynchronously

Exports
-------
MassSerialClient: A serial client that can communicate over multiple ports
    asynchronously
"""

from multiprocessing.pool import AsyncResult, ThreadPool
from time import sleep

from serial import Serial, SerialException, SerialTimeoutException  # type: ignore

from interface import AsyncMassClient


DEBUG = False


class MassSerialClient(AsyncMassClient):
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
        buad: int,
        serial_timeout_seconds: int,
    ) -> None:
        """Parameters
        ----------
        baud: The baud of the serial connections
        timeout_seconds: The timeout for connections in seconds (read & write)
        """
        self.__available_ports: dict[str, Serial] = {}
        self.__baud: int = buad
        self.__timeout_seconds: int = serial_timeout_seconds

    @property
    def ports(self) -> dict[str, Serial]:
        """A dictionary of available ports mapping port names to port objects
        """
        return self.__available_ports

    def close(self, port: Serial) -> None:
        """Close a port

        Parameters
        ----------
        port: The serial port to close
        """
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

    def mass_close(self, ports: list[Serial] | None = None) -> None:
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
        port_names: The list of port names to open, or None to open all

        Returns
        -------
        A dictionary of available ports mapping port names to serial ports
        """

        # Make sure target ports are closed
        if not port_names:
            self.mass_close()
            port_names = [f"COM{i + 1}" for i in range(256)]
        else:
            for port_name in port_names:
                if port_name in self.__available_ports:
                    self.close(self.__available_ports[port_name])

        # Asynchronously attempt to open ports
        pool = ThreadPool(processes=len(port_names))
        async_results = []
        for port_name in port_names:
            async_results.append(
                pool.apply_async(
                    self.open,
                    (port_name,)
                )
            )
        pool.close()
        pool.join()

        # Collect available ports
        for result in async_results:
            port = result.get()
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
                        self.read,
                        (port, num_bytes)
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
                        self.write,
                        (port, message)
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
            port = Serial(
                port_name,
                self.__baud,
                timeout=self.__timeout_seconds,
                write_timeout=self.__timeout_seconds
            )
            self.__available_ports[port.port] = port  # type: ignore
            sleep(self.__timeout_seconds)  # Wait for port to finish opening
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
            if DEBUG:
                print(f"{port.port} in: {bytes_read}")
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
            if DEBUG:
                print(f"{port.port} out: {message} ({bytes_sent} bytes)") # type: ignore
            return bytes_sent
        except (OSError, SerialException, SerialTimeoutException):
            return None
