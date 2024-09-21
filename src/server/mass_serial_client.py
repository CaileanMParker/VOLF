from multiprocessing.pool import AsyncResult, ThreadPool
from time import sleep

from serial import Serial, SerialException, SerialTimeoutException  # type: ignore

from configs import DEBUG
from interfaces import AsyncMassClient


class MassSerialClient(AsyncMassClient):
    def __init__(
        self,
        buad: int,
        serial_timeout_seconds: int,
    ) -> None:
        self.__available_ports: dict[str, Serial] = {}
        self.__baud: int = buad
        self.__timeout_seconds: int = serial_timeout_seconds

    @property
    def ports(self) -> dict[str, Serial]:
        return self.__available_ports

    def close(self, port: Serial) -> None:
        self.__available_ports.pop(port.port) # type: ignore
        port.close()

    def get_port(self, port_name: str) -> Serial | None:
        return self.__available_ports.get(port_name)

    def mass_close(self, ports: list[Serial] | None = None) -> None:
        if not ports:
            ports = list(self.__available_ports.values())
        for port in ports:
            self.close(port)

    def mass_open(self, port_names: list[str] | None = None) -> dict[str, Serial]:
        if not port_names:
            self.mass_close()
            port_names = [f"COM{i + 1}" for i in range(256)]
        else:
            for port_name in port_names:
                if port_name in self.__available_ports:
                    self.close(self.__available_ports[port_name])
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
        if not ports:
            ports = list(self.__available_ports.values())
        if not ports:
            raise RuntimeError("No ports available")
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
        if not ports:
            ports = list(self.__available_ports.values())
        if not ports:
            raise RuntimeError("No ports available")
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
        try:
            port = Serial(
                port_name,
                self.__baud,
                timeout=self.__timeout_seconds,
                write_timeout=self.__timeout_seconds
            )
            self.__available_ports[port.port] = port  # type: ignore
            sleep(self.__timeout_seconds)
            return port
        except (OSError, SerialException, SerialTimeoutException):
            return None

    def read(self, port: Serial, num_bytes: int = 0) -> bytes | None:
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
        try:
            bytes_sent = port.write(message)
            port.flush()
            if DEBUG:
                print(f"{port.port} out: {message} ({bytes_sent} bytes)") #  type: ignore
            return bytes_sent
        except (OSError, SerialException, SerialTimeoutException):
            return None
