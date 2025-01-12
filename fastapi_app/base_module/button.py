import asyncio
import time
from enum import Enum
from typing import AsyncGenerator

from common import pi_gpio_factory
from gpiozero import Button as GPIOButton


class ButtonEvent(Enum):
    PRESSED = 1
    RELEASED = 2


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

        self.gpio_button.when_pressed = (
            lambda: asyncio.run_coroutine_threadsafe(
                _put_event(ButtonEvent.PRESSED), loop
            )
        )

        self.gpio_button.when_released = (
            lambda: asyncio.run_coroutine_threadsafe(
                _put_event(ButtonEvent.RELEASED), loop
            )
        )

        while True:
            yield await event_queue.get()


async def main():
    button = Button(26)
    print("Waiting for button press...")

    async for event in button.wait_event():
        current_time = time.time()

        match event:
            case ButtonEvent.PRESSED:
                print("Button pressed! at ", current_time)
            case ButtonEvent.RELEASED:
                print("Button released! at ", current_time)


if __name__ == "__main__":
    asyncio.run(main())
