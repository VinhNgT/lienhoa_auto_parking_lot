import queue
import threading
from contextlib import contextmanager
from typing import (
    Callable,
    Generic,
    TypeVar,
)

# Generic request type
T = TypeVar("T")


class RequestQueuedThread(Generic[T]):
    def __init__(
        self,
        serve_request: Callable[[T, bool], None],
        cleanup: Callable[[], None],
        queue_size: int = 0,
    ):
        self._serve_request = serve_request
        self._cleanup = cleanup

        self._queue: queue.Queue[T] = queue.Queue(queue_size)
        self._buzzer_thread = threading.Thread(
            target=self._thread,
            # args=(self._queue, self._serve_request, self._cleanup),
        )
        self._buzzer_thread.start()

    def _thread(
        self,
        # queue: queue.Queue[T],
        # serve_request: Callable[[T], None],
        # cleanup: Callable[[], None],
    ):
        @contextmanager
        def _get_request():
            request = self._queue.get()
            yield request
            self._queue.task_done()

        try:
            while True:
                with _get_request() as request:
                    if request is None:
                        break

                    self._serve_request(request, self._queue.qsize() != 0)
        finally:
            self._cleanup()
            self._clear_queue()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        try:
            self._clear_queue()
            self._queue.put_nowait(None)
            self._buzzer_thread.join()
        finally:
            self._cleanup()

    def _clear_queue(self):
        while not self._queue.empty():
            self._queue.get_nowait()
            self._queue.task_done()

    def schedule(self, request: T, block=True):
        if request is None:
            raise ValueError("Request cannot be None")

        self._queue.put(request, block=block)

    # Use this if you put a bunch of requests in the queue and want to wait for
    # all of them to finish.
    def join_queue(self):
        self._queue.join()
