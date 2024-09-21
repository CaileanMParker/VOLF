""" A metaclass for singleton classes

Exports
-------
Singleton: A metaclass for singleton classes
"""

class Singleton(type):
    """A metaclass for singleton classes"""
    __instances: list[object] = []

    def __call__(cls, *args, **kwargs) -> object:
        """Check if the class has already been instantiated"""
        if cls not in cls.__instances:
            return super(Singleton, cls).__call__(*args, **kwargs)
        raise RuntimeError(f"{cls.__name__} is a singleton class")
