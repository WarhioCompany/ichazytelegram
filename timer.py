import threading
import time


class Timer:
    def __init__(self, func, seconds_delay, *args):
        self._func = func
        self._seconds_delay = seconds_delay
        self._args = args
        self._stop = False

        self.start_function()

    def start_function(self):
        thread = threading.Thread(target=self._launch)
        thread.start()

    def stop(self):
        self._stop = True

    def _launch(self):
        while not self._stop:
            self._func(*self._args)
            time.sleep(self._seconds_delay)