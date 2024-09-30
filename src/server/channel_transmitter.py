""" A class for sending integers representing channels over mass async clients
    to LiFi transmitters

Exports
-------
ChannelTransmitter: A class for sending integers representing channels over
    mass async clients to LiFi transmitters
"""


from random import randint
from time import time
from typing import Any

from asyncmassclients import IAsyncMassClient
from singleton_type import Singleton


_DEBUG = False


class ChannelTransmitter(Singleton):
    """A class for transmitting channels to LiFi transmitters

    Attributes
    ----------
    channel: The currently set channel to transmit
    transmitters: A list of connected transmitters to send channels to

    Methods
    -------
    print_transmitters: Print the port names of connected transmitters
    refresh_transmitters: Refresh the list of connected transmitters
    transmit_channel: Transmit the currently set channel to all connected
        transmitters
    """

    def __init__(
        self,
        channels_upper_bound: int,
        transmission_client: IAsyncMassClient
    ) -> None:
        """Parameters
        ----------
        channels_upper_bound: The maximum channel value
        transmission_client: The client for transmitting channels
        """
        self.__channel: int = 0
        self.__channels_upper_bound: int = channels_upper_bound
        self.__transmission_client: IAsyncMassClient = transmission_client
        self.refresh_transmitters()

    @property
    def channel(self) -> int:
        """The currently set channel to transmit"""
        return self.__channel

    @channel.setter
    def channel(self, value: int) -> None:
        if not isinstance(value, int):
            print("ERROR: Channel must be an integer")
        elif value < 0 or value > self.__channels_upper_bound:
            print(
                "ERROR: Channel must be between 0 and",
                self.__channels_upper_bound
            )
        self.__channel = value

    @property
    def transmitters(self) -> list[Any]:
        """A list of connected transmitters to send channels to"""
        return list(self.__transmission_client.ports.values())

    def print_transmitters(self) -> None:
        """Print the port names of connected transmitters"""
        print(
            "Transmitters on ports:",
            list(self.__transmission_client.ports.keys())
        )

    def refresh_transmitters(self) -> None:
        """Refresh the list of connected transmitters"""
        print("Refreshing transmitters...")
        start_time = time()
        self.__transmission_client.mass_open()

        # Send a byte to be echoed back by valid transmitters
        message_int = randint(58, 126)
        write_results = self.__transmission_client.mass_write(
            chr(message_int).encode()
        )
        # Remove ports for which writing failed
        for result in write_results:
            port_name, async_results = result
            if not async_results.get():
                self.__transmission_client.close(port_name)

        # If no ports were successfully written to, return
        if not self.__transmission_client.ports:
            if _DEBUG:
                print(
                    f"Refreshed transmitters in {time() - start_time} seconds"
                )
            print(
                "ERROR: No valid transmitters found.",
                "Please check connections and refresh ports.",
                sep="\n"
            )
            return

        # Read from ports to check for expected response
        read_results = self.__transmission_client.mass_read(1)
        # Remove ports for which reading failed or response is incorrect
        for result in read_results:
            port_name, async_results = result
            if async_results.get() != chr(message_int ^ 49).encode():
                self.__transmission_client.close(port_name)

        if _DEBUG:
            print(
                f"Refreshed transmitters in {time() - start_time} seconds"
            )

        if not self.__transmission_client.ports:
            print(
                "ERROR: No valid transmitters found.",
                "Please check connections and refresh ports.",
                sep="\n"
            )
            return
        self.print_transmitters()

    def transmit_channel(self) -> bool:
        """Transmit the currently set channel to all connected transmitters

        Returns
        -------
        Whether the channel was successfully transmitted to at least one
        transmitter
        """
        # If no transmitters are available, return
        if not self.__transmission_client.ports:
            print(
                "ERROR: No valid transmitters found.",
                "Please check connections and refresh ports.",
                sep="\n"
            )
            return False
        start_time = time()
        channel_str = str(self.__channel)
        message = channel_str.encode()
        expected_response = chr(ord(channel_str) ^ 49).encode()

        self.__transmission_client.mass_write(message)  # Write the channel to all transmitters
        results = self.__transmission_client.mass_read(1)  # Confirm the channel was echoed correctly

        # Remove ports for which reading failed or response is incorrect
        for result in results:
            port_name, async_results = result
            if async_results.get() != expected_response:
                self.__transmission_client.close(port_name)
                print(
                    f"ERROR: Channel transmission failed on port {port_name}.",
                    "Please check the connection and refresh ports.",
                    sep="\n"
                )
        if _DEBUG:
            print(
                f"Transmitted channel in {time() - start_time} seconds"
            )
        return bool(self.__transmission_client.ports)
