import threading
from abc import ABCMeta, abstractmethod


class Observable(object):

    def __init__(self):
        # in our application there is only one observer, so we simplify the pattern
        self.observer = None

    def register(self, observer):
        self.observer = observer

    def notify(self, *args, **kwargs):
        t = threading.Thread(target=self.observer.update)
        print('staring thread t ' + t.name)
        t.start()
        #self.observer.update(*args, **kwargs)


class Observer(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def update(self, *args, **kwargs):
        pass


class Data(object):
    """
    This class is a container of data.
    """
    def __init__(self, slice, **kwargs):
        self.slice = slice
        for key in kwargs:
            setattr(self, key, kwargs[key])


class Event(object):
    """
    This class is a container of event.
    """
    def __init__(self, **kwargs):
        for key in kwargs:
            setattr(self, key, kwargs[key])
