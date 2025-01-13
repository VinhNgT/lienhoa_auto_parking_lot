import asyncio
import contextlib
import os
import sys
from datetime import datetime
from enum import Enum
from typing import AsyncGenerator, Callable

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

    async def wait_event(self) -> AsyncGenerator[ButtonEvent, None]:
        event_queue: asyncio.Queue = asyncio.Queue(2)
        loop = asyncio.get_running_loop()

        async def _put_event(event: ButtonEvent):
            await event_queue.put(event)

        with ButtonWhenPressReleaseMng(
            self.gpio_button,
            when_pressed=lambda: asyncio.run_coroutine_threadsafe(
                _put_event(ButtonEvent.PRESSED), loop
            ),
            when_released=lambda: asyncio.run_coroutine_threadsafe(
                _put_event(ButtonEvent.RELEASED), loop
            ),
        ):
            while True:
                yield await event_queue.get()


async def main():
    button = Button(26)
    print("Waiting for button press...")

    async with contextlib.aclosing(button.wait_event()) as wait_event:
        try:
            async for event in wait_event:
                current_time = str(datetime.now())

                match event:
                    case ButtonEvent.PRESSED:
                        print("Button pressed! at ", current_time)
                    case ButtonEvent.RELEASED:
                        print("Button released! at ", current_time)
        except asyncio.exceptions.CancelledError:
            pass


if __name__ == "__main__":
    asyncio.run(main())
