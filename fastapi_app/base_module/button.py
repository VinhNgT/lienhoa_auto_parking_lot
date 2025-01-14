import asyncio
import contextlib
import os
import queue
import sys
import threading
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Generator

# Add current script folder to Python path.
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from common import pi_gpio_factory
from gpiozero import Button as GPIOButton


class ButtonEvent(Enum):
    PRESSED = 1
    RELEASED = 0


class ButtonWhenPressReleaseMng:
    def __init__(
        self,
        gpio_button: GPIOButton,
        when_pressed: Callable[[], None],
        when_released: Callable[[], None],
    ):
        self.gpio_button = gpio_button
        self.gpio_button.when_pressed = when_pressed
        self.gpio_button.when_released = when_released

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # print("Cleaning up button callbacks...")
        self.gpio_button.when_pressed = None
        self.gpio_button.when_released = None


class Button:
    def __init__(self, pin: int):
        # Use PiGPIO to avoid vscode freeze bug.
        self.gpio_button = GPIOButton(
            pin,
            pin_factory=pi_gpio_factory,
            # Debounce time set to 1 FPS
            bounce_time=1 / 60,
        )

        self._event_queue: queue.Queue[ButtonEvent] = queue.Queue(2)
        self._lock = threading.Lock()
        self._async_lock = asyncio.Lock()

    def close(self):
        self._stop_generator()
        self.gpio_button.close()

    def _stop_generator(self):
        self._clear_queue()
        if self._lock.locked():
            self._event_queue.put_nowait(None)
            self._event_queue.join()

    def _clear_queue(self):
        while not self._event_queue.empty():
            self._event_queue.get_nowait()
            self._event_queue.task_done()

    def wait_event(self) -> Generator[ButtonEvent, None, None]:
        with ButtonWhenPressReleaseMng(
            self.gpio_button,
            when_pressed=lambda: self._event_queue.put(ButtonEvent.PRESSED),
            when_released=lambda: self._event_queue.put(ButtonEvent.RELEASED),
        ):

            @contextmanager
            def _get_event():
                event = self._event_queue.get()
                yield event
                self._event_queue.task_done()

            with self._lock:
                try:
                    while True:
                        with _get_event() as event:
                            if event is None:
                                break
                            yield event
                finally:
                    self._clear_queue()

    async def async_wait_event(self):
        loop = asyncio.get_event_loop()
        async_event_queue = asyncio.Queue()

        def _wait_thread_loop(button: Button, on_event):
            for event in button.wait_event():
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


def main():
    button = Button(26)
    print("Waiting for button press...")

    for event in button.wait_event():
        current_time = str(datetime.now(timezone.utc).isoformat())

        match event:
            case ButtonEvent.PRESSED:
                print("Button pressed! at ", current_time)
            case ButtonEvent.RELEASED:
                print("Button released! at ", current_time)


async def async_main():
    button = Button(26)
    print("Waiting for button press...")

    async with contextlib.aclosing(button.async_wait_event()) as wait_event:
        async for event in wait_event:
            current_time = str(datetime.now(timezone.utc).isoformat())

            match event:
                case ButtonEvent.PRESSED:
                    print("Button pressed! at ", current_time)
                case ButtonEvent.RELEASED:
                    print("Button released! at ", current_time)


if __name__ == "__main__":
    # main()
    asyncio.run(async_main())
