# pylint: disable=redefined-outer-name

from threading import Event, Thread
from time import sleep, time
from winsound import Beep

from pyaudio import PyAudio, paInt16
from pynput.keyboard import Key, KeyCode, Listener
from serial import Serial  # type: ignore

from configs import *  # pylint: disable=wildcard-import
from interfaces import AsyncMassClient
from mass_serial_client import MassSerialClient
from singleton_type import Singleton


class ChannelTransmitter(metaclass=Singleton):
    def __init__(
        self,
        channels_upper_bound: int,
        transmission_client: AsyncMassClient
    ) -> None:
        self.__channel: int = 0
        self.__channels_upper_bound: int = channels_upper_bound
        self.__transmission_client: AsyncMassClient = transmission_client
        self.__transmitter_ports: list[Serial] = []
        self.refresh_transmitters()

    @property
    def channel(self) -> int:
        return self.__channel

    @channel.setter
    def channel(self, value: int) -> None:
        if value < 0 or value > self.__channels_upper_bound:
            print(
                "ERROR: Channel must be between 0 and",
                self.__channels_upper_bound
            )
        self.__channel = value

    @property
    def transmitters(self) -> list[Serial]:
        return self.__transmitter_ports

    def refresh_transmitters(self) -> None:
        print("Refreshing transmitters...")
        start_time = time()
        self.__transmitter_ports = list(
            self.__transmission_client.mass_open().values()
        )
        echo_byte = b"e"
        write_results = self.__transmission_client.mass_write(
            echo_byte,
            self.__transmitter_ports
        )

        for result in write_results:
            port, async_results = result
            if not async_results.get():
                self.__transmitter_ports.remove(
                    self.__transmission_client.get_port(port)
                )

        if not self.__transmitter_ports:
            if DEBUG:
                print(
                    f"Refreshed transmitters in {time() - start_time} seconds"
                )
            print(
                "ERROR: No valid transmitters found.",
                "Please check connections and refresh ports.",
                sep="\n"
            )
            return

        read_results = self.__transmission_client.mass_read(
            1, self.__transmitter_ports
        )
        for result in read_results:
            port, async_results = result
            if async_results.get() != echo_byte:
                self.__transmitter_ports.remove(
                    self.__transmission_client.get_port(port)
                )

        if DEBUG:
            print(
                f"Refreshed transmitters in {time() - start_time} seconds"
            )

        if not self.__transmitter_ports:
            print(
                "ERROR: No valid transmitters found.",
                "Please check connections and refresh ports.",
                sep="\n"
            )
            return
        print(
            "Transmitters on ports:",
            [port.port for port in self.__transmitter_ports]
        )

    def transmit_channel(self) -> bool:
        if not self.__transmitter_ports:
            print(
                "ERROR: No valid transmitters found.",
                "Please check connections and refresh ports.",
                sep="\n"
            )
            return False
        start_time = time()
        message = str(self.__channel).encode()
        self.__transmission_client.mass_write(
            message,
            self.__transmitter_ports
        )
        results = self.__transmission_client.mass_read(
            1, self.__transmitter_ports
        )
        for result in results:
            port, async_results = result
            if async_results.get() != message:
                self.__transmitter_ports.remove(
                    self.__transmission_client.get_port(port)
                )
                print(
                    f"ERROR: Channel transmission failed on port {port}.",
                    "Please check connections and refresh ports.",
                    sep="\n"
                )
        if DEBUG:
            print(
                f"Transmitted channel in {time() - start_time} seconds"
            )
        return bool(self.__transmitter_ports)


class AudioStreamer(Thread):
    def __init__(
        self,
        audio_channels = 2,
        chunk_size = 1024,
        sample_rate = 44100
    ) -> None:
        super().__init__()
        self.__audio = PyAudio()
        self.__audio_channels = audio_channels
        self.__chunk_size = chunk_size
        self.__sample_rate = sample_rate
        self.__stream_in = self.__audio.open(
            format=paInt16,
            channels=self.__audio_channels,
            rate=self.__sample_rate,
            input=True,
            frames_per_buffer=self.__chunk_size
        )
        self.__stream_out = self.__audio.open(
            format=paInt16,
            channels=self.__audio_channels,
            rate=self.__sample_rate,
            output = True
        )
        self.__kill_flag = Event()
        self.__transmit_flag = Event()

    @property
    def transmitting(self) -> bool:
        return self.__transmit_flag.is_set()

    def __stream_audio(self) -> None:
        self.__stream_in.start_stream()
        self.__stream_out.start_stream()
        print("* transmitting")
        while self.transmitting:
            self.__stream_out.write(self.__stream_in.read(self.__chunk_size))
        print("* done transmitting")
        self.__stream_in.stop_stream()
        self.__stream_out.stop_stream()

    def close(self) -> None:
        self.__kill_flag.set()
        self.__transmit_flag.set()
        sleep(0.2)
        self.__stream_in.close()
        self.__stream_out.close()
        self.__audio.terminate()

    def run(self) -> None:
        print("Ready to transmit")
        while not self.__kill_flag.is_set():
            self.__transmit_flag.wait()
            if self.__kill_flag.is_set():
                break
            self.__stream_audio()

    def start_streaming(self) -> None:
        self.__transmit_flag.set()

    def stop_streaming(self) -> None:
        self.__transmit_flag.clear()


class KeyboardCallbacks(metaclass=Singleton):
    def __init__(
        self,
        audio_streamer: AudioStreamer,
        channel_transmitter: ChannelTransmitter
    ) -> None:
        self.__audio_streamer = audio_streamer
        self.__channel_transmitter = channel_transmitter
        self.__key_states: dict[Key, bool] = {}

    def on_press(self, key: Key) -> bool:
        if not self.__key_states.get(key, False):
            for i in range(10):
                if key == KeyCode.from_char(str(i)):
                    self.__channel_transmitter.channel = i
                    print("Channel set to", self.__channel_transmitter.channel)
                    break
            if key == Key.esc:
                return False
            elif key == Key.space:
                if self.__channel_transmitter.transmit_channel():
                    self.__audio_streamer.start_streaming()
                else:
                    for _ in range(3):
                        Beep(1000, 100)
            elif key == KeyCode.from_char("r"):
                self.__channel_transmitter.refresh_transmitters()
            elif key == KeyCode.from_char("p"):
                print("Serial ports:", self.__channel_transmitter.transmitters)
            elif key == KeyCode.from_char("h"):
                print_help()
        self.__key_states[key] = True
        return True

    def on_release(self, key: Key) -> bool:
        if self.__key_states.get(key, True):
            if key == Key.space:
                self.__audio_streamer.stop_streaming()
        self.__key_states[key] = False
        return True


def print_help() -> None:
    print("\nPress 0-9 to set channel,",
        "space to start/stop transmitting,",
        "r to refresh ports,",
        "p to print ports,",
        "h to print help",
        "esc to exit the program\n",
        sep="\n"
    )


if __name__ == "__main__":
    print("Initializing...")
    print_help()
    audio_streamer = AudioStreamer()
    channel_transmitter = ChannelTransmitter(
        TRANSMISSION_CHANNELS_UPPER_BOUND,
        MassSerialClient(BAUD, SERIAL_TIMEOUT_SECONDS)
    )
    keyboard_callbacks = KeyboardCallbacks(audio_streamer, channel_transmitter)
    audio_streamer.start()
    with Listener(
        on_press=keyboard_callbacks.on_press,  # type: ignore
        on_release=keyboard_callbacks.on_release  # type: ignore
    ) as listener:
        listener.join()
    audio_streamer.close()
    audio_streamer.join()
