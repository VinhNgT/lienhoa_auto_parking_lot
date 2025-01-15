import asyncio
import contextlib
import os
import queue
import sys
from datetime import datetime, timezone
from enum import Enum

# Add current script folder to Python path.
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from common import pi_gpio_factory
from event_generator import SingleSourceEventGenerator
from gpiozero import Button as GPIOButton


class ButtonEvent(Enum):
    PRESSED = 1
    RELEASED = 0


class Button:
    def __init__(self, pin: int):
        # Use PiGPIO to avoid vscode freeze bug.
        self.gpio_button = GPIOButton(
            pin,
            pin_factory=pi_gpio_factory,
            # Debounce time set to 1 FPS
            bounce_time=1 / 60,
        )

        self._event_generator = self._setup_event_generator()

    def _setup_event_generator(self) -> SingleSourceEventGenerator[ButtonEvent]:
        def _setup_gpio(queue: queue.Queue[ButtonEvent]):
            self.gpio_button.when_pressed = lambda: queue.put(
                ButtonEvent.PRESSED
            )
            self.gpio_button.when_released = lambda: queue.put(
                ButtonEvent.RELEASED
            )

        def _clear_gpio():
            self.gpio_button.when_pressed = None
            self.gpio_button.when_released = None
            # print("Clearing GPIO")

        return SingleSourceEventGenerator(
            setup_queue=_setup_gpio, cleanup=_clear_gpio
        )

    def close(self):
        self._event_generator.close()
        self.gpio_button.close()

    def wait_event(self):
        return self._event_generator.wait_event()

    def async_wait_event(self):
        return self._event_generator.async_wait_event()


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

    press_count = 0

    async with contextlib.aclosing(button.async_wait_event()) as wait_event:
        async for event in wait_event:
            current_time = str(datetime.now(timezone.utc).isoformat())

            match event:
                case ButtonEvent.PRESSED:
                    print("Button pressed! at ", current_time)
                case ButtonEvent.RELEASED:
                    print("Button released! at ", current_time)
                    press_count += 1

            if press_count >= 5:
                button.close()


if __name__ == "__main__":
    test = 2

    match test:
        case 1:
            print("Running main()")
            main()
        case 2:
            print("Running async_main()")
            asyncio.run(async_main())
