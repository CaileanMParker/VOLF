class Singleton(type):
    __instances: list[object] = []

    def __call__(cls, *args, **kwargs) -> object:
        if cls not in cls.__instances:
            return super(Singleton, cls).__call__(*args, **kwargs)
        raise RuntimeError(f"{cls.__name__} is a singleton class")