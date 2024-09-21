""" A program for transmitting channel-restricted audio data over LiFi using a
    microphone

Exports
-------
ChannelTransmitter: A class for transmitting channels to Lifi transmitters
AudioStreamer: A class for streaming audio from a microphone to a LiFi
    transmitter
KeyboardCallbacks: A class for handling keyboard input callbacks
print_help: Print help text
"""


# pylint: disable=redefined-outer-name

from threading import Event, Thread
from time import sleep, time
from winsound import Beep

from pyaudio import PyAudio, paInt16
from pynput.keyboard import Key, KeyCode, Listener
from serial import Serial  # type: ignore

from asyncmassclients.interface import AsyncMassClient
from asyncmassclients.mass_serial_client import MassSerialClient
from singleton_type import Singleton


BAUD = 9600  # Baud rate for serial communication
SERIAL_TIMEOUT_SECONDS = 1 # Timeout for serial communication (read and write)
TRANSMISSION_CHANNELS_UPPER_BOUND = 9 # Maximum number of transmission channels

DEBUG = True


class ChannelTransmitter(metaclass=Singleton):
    """A class for transmitting channels to Lifi transmitters

    Attributes
    ----------
    channel: The currently set channel to transmit
    transmitters: A list of connected transmitters to send channels to

    Methods
    -------
    refresh_transmitters: Refresh the list of connected transmitters
    transmit_channel: Transmit the currently set channel to all connected
        transmitters
    """

    def __init__(
        self,
        channels_upper_bound: int,
        transmission_client: AsyncMassClient
    ) -> None:
        """Parameters
        ----------
        channels_upper_bound: The maximum channel value
        transmission_client: The client for transmitting channels
        """
        self.__channel: int = 0
        self.__channels_upper_bound: int = channels_upper_bound
        self.__transmission_client: AsyncMassClient = transmission_client
        self.__transmitter_ports: list[Serial] = []
        self.refresh_transmitters()

    @property
    def channel(self) -> int:
        """The currently set channel to transmit"""
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
        """A list of connected transmitters to send channels to"""
        return self.__transmitter_ports

    def refresh_transmitters(self) -> None:
        """Refresh the list of connected transmitters"""
        print("Refreshing transmitters...")
        start_time = time()
        self.__transmitter_ports = list(  # prime list with all available ports
            self.__transmission_client.mass_open().values()
        )

        # Send a byte to be echoed back by valid transmitters
        echo_byte = b"e"
        write_results = self.__transmission_client.mass_write(
            echo_byte,
            self.__transmitter_ports
        )
        # Remove ports for which writing failed
        for result in write_results:
            port, async_results = result
            if not async_results.get():
                self.__transmitter_ports.remove(
                    self.__transmission_client.get_port(port)  # type: ignore
                )

        # If no ports were successfully written to, return
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

        # Read from ports to check for echoed byte
        read_results = self.__transmission_client.mass_read(
            1, self.__transmitter_ports
        )
        # Remove ports for which reading failed or echoed byte is incorrect
        for result in read_results:
            port, async_results = result
            if async_results.get() != echo_byte:
                self.__transmitter_ports.remove(
                    self.__transmission_client.get_port(port)  # type: ignore
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
        """Transmit the currently set channel to all connected transmitters

        Returns
        -------
        Whether the channel was successfully transmitted to at least one
        transmitter
        """
        # If no transmitters are available, return
        if not self.__transmitter_ports:
            print(
                "ERROR: No valid transmitters found.",
                "Please check connections and refresh ports.",
                sep="\n"
            )
            return False
        start_time = time()
        message = str(self.__channel).encode()

        # Write the channel to all transmitters
        self.__transmission_client.mass_write(
            message,
            self.__transmitter_ports
        )
        # Confirm the channel was echoed correctly
        results = self.__transmission_client.mass_read(
            1, self.__transmitter_ports
        )

        # Remove ports for which reading failed or echoed byte is incorrect
        for result in results:
            port, async_results = result
            if async_results.get() != message:
                self.__transmitter_ports.remove(
                    self.__transmission_client.get_port(port)  # type: ignore
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
    """A class for streaming audio from a microphone to a LiFi transmitter

    Attributes
    ----------
    transmitting: Whether the audio is currently being streamed

    Methods
    -------
    close: Close the audio streamer
    run: Begin the audio streamer thread
    start_streaming: Start streaming audio
    stop_streaming: Stop streaming audio
    """

    def __init__(
        self,
        audio_channels = 2,
        chunk_size = 1024,
        sample_rate = 44100
    ) -> None:
        """Parameters
        ----------
        audio_channels (Optional): The number of audio channels to use in the
            stream
        chunk_size (Optional): The size of audio chunks to use in the stream
        sample_rate (Optional): The sample rate of the audio stream
        """
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
    def streaming(self) -> bool:
        """Whether the audio is currently being streamed"""
        return self.__transmit_flag.is_set()

    def __stream_audio(self) -> None:
        """Stream audio from the microphone to the transmitter"""
        self.__stream_in.start_stream()
        self.__stream_out.start_stream()
        print("* transmitting")
        while self.streaming:
            self.__stream_out.write(self.__stream_in.read(self.__chunk_size))
        print("* done transmitting")
        self.__stream_in.stop_stream()
        self.__stream_out.stop_stream()

    def close(self) -> None:
        """Close the audio streamer"""
        self.__kill_flag.set()
        self.__transmit_flag.set()
        sleep(0.2)
        self.__stream_in.close()
        self.__stream_out.close()
        self.__audio.terminate()

    def run(self) -> None:
        """Begin the audio streamer thread"""
        print("Ready to transmit")
        while not self.__kill_flag.is_set():
            self.__transmit_flag.wait()
            if self.__kill_flag.is_set():
                break
            self.__stream_audio()

    def start_streaming(self) -> None:
        """Start streaming audio"""
        self.__transmit_flag.set()

    def stop_streaming(self) -> None:
        """Stop streaming audio"""
        self.__transmit_flag.clear()


class KeyboardCallbacks(metaclass=Singleton):
    """A class for handling keyboard input callbacks

    Methods
    -------
    on_press: Handle key press events
    on_release: Handle key release events
    """

    def __init__(
        self,
        audio_streamer: AudioStreamer,
        channel_transmitter: ChannelTransmitter
    ) -> None:
        """Parameters
        ----------
        audio_streamer: The audio streamer to control
        channel_transmitter: The channel transmitter to control
        """
        self.__audio_streamer = audio_streamer
        self.__channel_transmitter = channel_transmitter
        self.__key_states: dict[Key, bool] = {}

    def on_press(self, key: Key) -> bool:
        """Handle key press events

        Parameters
        ----------
        key: The key that was pressed

        Returns
        -------
        Whether the key event listener should be closed
        """
        if not self.__key_states.get(key, False):
            for i in range(10):  # Set channel 0-9
                if key == KeyCode.from_char(str(i)):
                    self.__channel_transmitter.channel = i
                    print("Channel set to", self.__channel_transmitter.channel)
                    break
            if key == Key.esc:  # Exit program
                return False
            elif key == Key.space:  # Start transmitting
                if self.__channel_transmitter.transmit_channel():
                    self.__audio_streamer.start_streaming()
                else:  # Alert if channel transmission failed
                    for _ in range(3):
                        Beep(1000, 100)
            elif key == KeyCode.from_char("r"):  # Refresh ports
                self.__channel_transmitter.refresh_transmitters()
            elif key == KeyCode.from_char("p"):  # Print ports
                print("Serial ports:", self.__channel_transmitter.transmitters)
            elif key == KeyCode.from_char("h"):  # Print help
                print_help()
        self.__key_states[key] = True
        return True

    def on_release(self, key: Key) -> bool:
        """Handle key release events

        Parameters
        ----------
        key: The key that was released

        Returns
        -------
        Whether the key event listener should be closed
        """
        if self.__key_states.get(key, True):
            if key == Key.space:  # Stop transmitting
                self.__audio_streamer.stop_streaming()
        self.__key_states[key] = False
        return True


def print_help() -> None:
    """Print help text"""
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
