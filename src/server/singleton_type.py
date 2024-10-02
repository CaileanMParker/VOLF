""" A process-safe metaclass for singleton objects

Exports
-------
Singleton: A process-safe  metaclass for singleton objects
"""

from multiprocessing import Lock
from typing import Self


class Singleton:
    """A process-safe metaclass for singleton objects"""
    __instance = None
    __lock = Lock()

    def __new__(cls, *args, **kwargs) -> Self:  # pylint: disable=unused-argument
        """Create new instance only if one does not already exist, otherwise
        return existing instance
        """
        if cls.__instance is None:
            with cls.__lock:
                if not cls.__instance:
                    cls.__instance = super().__new__(cls)
        return cls.__instance
