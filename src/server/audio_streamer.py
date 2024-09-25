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
