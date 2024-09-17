from multiprocessing.pool import ThreadPool
from threading import Event, Thread
from time import sleep

from pyaudio import PyAudio, paInt16
from pynput.keyboard import Key, KeyCode, Listener
from serial import Serial, SerialException, SerialTimeoutException


BAUD = 19200
CHANNELS = 2
CHUNK = 1024
FORMAT = paInt16
RATE = 44100


class Transmitter(Thread):
    def __init__(self) -> None:
        super().__init__()
        self.__audio = PyAudio()
        self.__channel = 0
        self.__ports = self.__enumerate_serial_ports()
        print("Serial ports:", self.__ports)
        self.__kill_flag = Event()
        self.__transmit_flag = Event()

    @property
    def channel(self) -> int:
        return self.__channel

    @channel.setter
    def channel(self, value: int) -> None:
        self.__channel = value

    @property
    def ports(self) -> list[str]:
        return self.__ports

    @property
    def transmitting(self) -> bool:
        return self.__transmit_flag.is_set()

    def __enumerate_serial_ports(self) -> list[str]:
        possible_ports: list[str] = [f"COM{i + 1}" for i in range(256)]
        valid_ports: list[str] = []
        for port in possible_ports:
            try:
                s = Serial(port)
                s.close()
                valid_ports.append(port)
            except (OSError, SerialException):
                pass
        return valid_ports

    def __mass_serial_job(self, port: str, value: bytes) -> tuple[bool, str]:
        try:
            with Serial(port, BAUD, timeout=1, write_timeout=1) as serial_port:
                serial_port.write(value)
                serial_port.flush()
                confirmation = serial_port.read()
                if confirmation != value:
                    return False, port
            return True, port
        except SerialTimeoutException:
            return False, port

    def __serial_callback(self, result: tuple[bool, str]) -> None:
        success, port = result
        if not success:
            print(f"ERROR: Channel transmission failed on port {port}")

    def __serial_error_callback(self, exception: BaseException) -> None:
        print("ERROR: Channel transmission failed with unexpected exception",
            f"\"{exception}\""
        )

    def __stream_audio(self) -> None:
        stream_in = self.__audio.open(format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK
        )
        stream_out = self.__audio.open(format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            output = True
        )
        print("* transmitting")
        while self.transmitting:
            stream_out.write(stream_in.read(CHUNK))
        print("* done transmitting")
        stream_in.stop_stream()
        stream_out.stop_stream()
        stream_in.close()
        stream_out.close()

    def __transmit_channel(self) -> None:
        pool = ThreadPool(processes=len(self.__ports))
        channel = self.__channel.to_bytes(1, "big")
        for port in self.__ports:
            pool.apply_async(
                self.__mass_serial_job,
                (port, channel),
                callback=self.__serial_callback,
                error_callback=self.__serial_error_callback
            )
        pool.close()
        pool.join()

    def close(self) -> None:
        self.__kill_flag.set()
        self.__transmit_flag.set()
        sleep(0.2)
        self.__audio.terminate()

    def refresh_ports(self) -> None:
        self.__ports = self.__enumerate_serial_ports()
        print("Serial ports:", self.__ports)

    def run(self) -> None:
        print("Ready to transmit")
        while not self.__kill_flag.is_set():
            self.__transmit_flag.wait()
            if self.__kill_flag.is_set():
                break
            self.__transmit_channel()
            self.__stream_audio()

    def start_transmitting(self) -> None:
        self.__transmit_flag.set()

    def stop_transmitting(self) -> None:
        self.__transmit_flag.clear()


class KeyboardCallbacks:
    key_states: dict[Key, bool] = {}
    transmitter: Transmitter | None = None

    @classmethod
    def on_press(cls, key: Key) -> bool:
        if cls.transmitter and not cls.key_states.get(key, False):
            # print(key, "pressed")
            for i in range(10):
                if key == KeyCode.from_char(str(i)):
                    cls.transmitter.channel = i
                    print("Channel set to", cls.transmitter.channel)
                    break
            if key == Key.esc:
                return False
            elif key == Key.space:
                cls.transmitter.start_transmitting()
            elif key == KeyCode.from_char("r"):
                cls.transmitter.refresh_ports()
            elif key == KeyCode.from_char("p"):
                print("Serial ports:", cls.transmitter.ports)
            elif key == KeyCode.from_char("h"):
                print_help()
        cls.key_states[key] = True
        return True

    @classmethod
    def on_release(cls, key: Key) -> bool:
        if cls.transmitter and cls.key_states.get(key, True):
            # print(key, "released")
            if key == Key.space:
                cls.transmitter.stop_transmitting()
        cls.key_states[key] = False
        return True


def print_help() -> None:
    print("Press 0-9 to set channel,",
        "space to start/stop transmitting,",
        "r to refresh ports,",
        "p to print ports,",
        "h to print help",
        "esc to exit the program",
        sep="\n"
    )


if __name__ == "__main__":
    print("Initializing...")
    key_states: dict[Key, bool] = {}
    transmitter = Transmitter()
    KeyboardCallbacks.transmitter = transmitter
    transmitter.start()
    with Listener(
        on_press=KeyboardCallbacks.on_press,  # type: ignore
        on_release=KeyboardCallbacks.on_release  # type: ignore
    ) as listener:
        listener.join()
    transmitter.close()
    transmitter.join()
