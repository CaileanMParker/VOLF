""" A program for transmitting channel-restricted audio data over LiFi using a
    microphone

Exports
-------
KeyboardCallbacks: A class for handling keyboard input callbacks
print_help: Print help text
"""


# pylint: disable=redefined-outer-name


from winsound import Beep

from pynput.keyboard import Key, KeyCode, Listener
from serial import Serial  # type: ignore[import-untyped]

from audio_streamer import AudioStreamer
from asyncmassclients import SerialMassClient
from channel_transmitter import ChannelTransmitter
from singleton_type import Singleton


BAUD = 9600  # Baud rate for serial communication
SERIAL_TIMEOUT_SECONDS = 1 # Timeout for serial communication (read and write)
TRANSMISSION_CHANNELS_UPPER_BOUND = 9 # Maximum number of transmission channels


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
                self.__channel_transmitter.print_transmitters()
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
        "\"space\" to start/stop transmitting,",
        "\"r\" to refresh ports,",
        "\"p\" to print ports,",
        "\"h\" to print help,",
        "\"esc\" to exit the program\n",
        sep="\n"
    )


if __name__ == "__main__":
    print("Initializing...")
    print_help()
    audio_streamer = AudioStreamer()
    channel_transmitter = ChannelTransmitter(
        TRANSMISSION_CHANNELS_UPPER_BOUND,
        SerialMassClient(
            Serial(
                baudrate=BAUD,
                timeout=SERIAL_TIMEOUT_SECONDS,
                write_timeout=SERIAL_TIMEOUT_SECONDS
            )
        )
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
