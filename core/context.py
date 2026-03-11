from collections import deque


class ContextManager:

    def __init__(self, size=3):

        self.buffer = deque(maxlen=size)

    def add(self, text):

        self.buffer.append(text)

    def get_context(self):

        return "\n".join(self.buffer)