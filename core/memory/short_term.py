from collections import deque

from .base import BaseMemory


class ShortTermMemory(BaseMemory):

    def __init__(self, size=5):
        self.memory = deque(maxlen=size)

    def add(self, data):
        self.memory.append(data)

    def retrieve(self, query=None):
        return list(self.memory)
