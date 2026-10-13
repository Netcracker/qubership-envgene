import abc
import threading

class Singleton(abc.ABCMeta):
    _instances = {}
    _lock = threading.RLock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

    # method needed for tests
    @classmethod
    def reset(cls):
        cls._instances = dict()
