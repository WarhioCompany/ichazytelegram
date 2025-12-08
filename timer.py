import logging
import threading
import time

logger = logging.getLogger(__name__)
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
            logger.info(f'TIMER: executing {self._func.__name__} each {self._seconds_delay / 3600} hours')
            self._func(*self._args)
            time.sleep(self._seconds_delay)