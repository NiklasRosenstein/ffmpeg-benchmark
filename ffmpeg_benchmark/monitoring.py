import time
import psutil


class Monitoring:
    def __init__(self, interval=5):
        self.interval = interval
        self.running = False
        self.values = {}

    def clear(self):
        self.values = {}

    def start(self):
        self.running = True

    def stop(self):
        self.running = False

    def record(self):
        pass

    def timeit(self, func, func_args, func_kwargs):
        t0 = time.time()
        result = func(*func_args, **func_kwargs)
        elapsed = time.time() - t0
        return result, elapsed
