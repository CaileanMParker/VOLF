""" A class for streaming audio from a microphone to a LiFi
    transmitter

Exports
-------
AudioStreamer: A class for streaming audio from a microphone to a LiFi
    transmitter
"""


from threading import Event, Thread
from time import sleep

from pyaudio import PyAudio, paInt16


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
        audio_channels: int = 2,
        chunk_size: int = 1024,
        sample_rate: int = 44100,
        input_device_name: str | None = None,
        output_device_name: str | None = None
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
        input_device_index = None
        output_device_index = None
        if input_device_name:
            input_device_index = self.__get_device_index(input_device_name)
        if output_device_name:
            output_device_index = self.__get_device_index(
                output_device_name, True
            )
        self.__stream_in = self.__audio.open(
            channels=self.__audio_channels,
            format=paInt16,
            frames_per_buffer=self.__chunk_size,
            rate=self.__sample_rate,
            input=True,
            input_device_index=input_device_index
        )
        self.__stream_out = self.__audio.open(
            channels=self.__audio_channels,
            format=paInt16,
            rate=self.__sample_rate,
            output = True,
            output_device_index=output_device_index
        )
        self.__kill_flag = Event()
        self.__transmit_flag = Event()

    @property
    def streaming(self) -> bool:
        """Whether the audio is currently being streamed"""
        return self.__transmit_flag.is_set()

    def __get_device_index(self, device_name: str, output: bool = False) -> int:
        """Get the index of an audio device by name

        Parameters
        ----------
        device_name: The name of the audio device to find
        output (Optional): Whether the device is an output device

        Returns
        -------
        The index of the audio device

        Raises
        ------
        ValueError: If the device is not found
        RuntimeError: If the device is not of the specified type
        """
        for i in range(0, self.__audio.get_device_count()):
            device_info = self.__audio.get_device_info_by_index(i)
            if (device_name in device_info["name"]):  # type: ignore
                if output and not device_info.get("maxOutputChannels"):
                    raise RuntimeError(
                        f"Device '{device_name}' is not an output device"
                    )
                if output and device_info.get("maxInputChannels"):
                    raise RuntimeError(
                        f"Device '{device_name}' is not an input device"
                    )
                return i
        raise ValueError(f"Device '{device_name}' not found")

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
