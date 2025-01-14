import asyncio
import queue
import threading
from contextlib import asynccontextmanager, contextmanager
from typing import (
    AsyncGenerator,
    Callable,
    Generator,
    Generic,
    Self,
    TypeVar,
)

# Generic event type
T = TypeVar("T")


class SingleSourceEventGenerator(Generic[T]):
    def __init__(
        self,
        setup_queue: Callable[[queue.Queue[T]], None],
        cleanup: Callable[[], None],
        queue_size: int = 0,
    ):
        self._setup_queue = setup_queue
        self._cleanup = cleanup

        self._event_queue: queue.Queue[T] = queue.Queue(queue_size)
        self._lock = threading.Lock()
        self._async_lock = asyncio.Lock()

    def close(self):
        self._stop_generator()

    def _stop_generator(self):
        self._clear_queue()
        if self._lock.locked():
            self._event_queue.put_nowait(None)
            self._event_queue.join()

    def _clear_queue(self):
        while not self._event_queue.empty():
            self._event_queue.get_nowait()
            self._event_queue.task_done()

    def wait_event(self) -> Generator[T, None, None]:
        self._setup_queue(self._event_queue)

        @contextmanager
        def _get_event():
            event = self._event_queue.get()
            yield event
            self._event_queue.task_done()

        if self._lock.locked():
            self._stop_generator()

        with self._lock:
            try:
                while True:
                    with _get_event() as event:
                        if event is None:
                            break
                        yield event
            finally:
                self._clear_queue()
                self._cleanup()

    async def async_wait_event(self) -> AsyncGenerator[T, None]:
        loop = asyncio.get_event_loop()
        async_event_queue = asyncio.Queue()

        def _wait_thread_loop(generator: Self, on_event):
            for event in generator.wait_event():
                on_event(event)
            # print("Exiting button wait thread loop...")
            on_event(None)

        async def _put_event(event):
            await async_event_queue.put(event)

        # Only one async_wait_event task can run at a time. If another task
        # tries to run then it will cancel the previous task by calling
        # _stop_generator().
        if self._async_lock.locked():
            self._stop_generator()

        async with self._async_lock:
            button_wait_thread = threading.Thread(
                target=_wait_thread_loop,
                args=(
                    self,
                    lambda event: asyncio.run_coroutine_threadsafe(
                        _put_event(event), loop
                    ),
                ),
            )
            button_wait_thread.start()

            @asynccontextmanager
            async def _get_event():
                event = await async_event_queue.get()
                yield event
                async_event_queue.task_done()

            try:
                while True:
                    async with _get_event() as async_event:
                        if async_event is None:
                            break
                        yield async_event

            # except BaseException as e:
            #     match e:
            #         case (
            #             asyncio.exceptions.CancelledError()
            #             | Exception()
            #             | GeneratorExit()
            #         ):
            #             self.stop_generator()

            #     print(type(e).__name__)
            #     raise

            finally:
                # Kill the button wait thread.
                self._stop_generator()
