from abc import ABC, abstractmethod


class BaseMemory(ABC):

    @abstractmethod
    def add(self, data):
        pass

    @abstractmethod
    def retrieve(self, query):
        pass