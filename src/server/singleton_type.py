""" A metaclass for singleton objects

Exports
-------
Singleton: A metaclass for singleton objects
"""

class Singleton(type):
    """A metaclass for singleton objects"""

    __instances: list[object] = []

    def __call__(cls, *args, **kwargs) -> object:
        """Check if the class has already been instantiated"""
        if cls not in cls.__instances:
            return super(Singleton, cls).__call__(*args, **kwargs)
        return cls.__instances[cls.__instances.index(cls)]
