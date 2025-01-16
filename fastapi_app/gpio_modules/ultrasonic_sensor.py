import asyncio
import contextlib
import os
import queue
import sys
import threading
import time
from datetime import datetime, timezone
from typing import Callable

from gpiozero import DistanceSensor

# from adafruit_hcsr04 import HCSR04

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from common import pi_gpio_factory
from event_generator import SingleSourceEventGenerator


class UltrasonicSensor:
    def __init__(self, trigger_pin: int, echo_pin: int):
        self._sensor = DistanceSensor(
            trigger=trigger_pin, echo=echo_pin, pin_factory=pi_gpio_factory
        )

        self._event_thread: threading.Thread | None = None
        self._stop_event_flag = threading.Event()

        self._current_sample_interval = None
        self._event_generator = self._setup_event_generator()

    def set_sample_interval(self, sample_interval: float):
        if self._current_sample_interval != sample_interval:
            self.close()
            self._event_generator = self._setup_event_generator(sample_interval)

    def _setup_event_generator(
        self, sample_interval: float = 1
    ) -> SingleSourceEventGenerator[float]:
        self._current_sample_interval = sample_interval

        def _live_thread_loop(
            on_event: Callable[[float], None], stop_event_flag: threading.Event
        ):
            while True:
                if stop_event_flag.is_set():
                    break
                # Use cm instead of m
                current_value = self._sensor.distance * 100
                on_event(round(current_value, 3))

                time.sleep(sample_interval)

        def _setup_gpio(queue: queue.Queue[float]):
            def on_event(distance: float):
                queue.put(distance)

            self._event_thread = threading.Thread(
                target=_live_thread_loop,
                args=(on_event, self._stop_event_flag),
            )
            self._stop_event_flag.clear()
            self._event_thread.start()

        def cleanup():
            self._stop_event_flag.set()
            if self._event_thread is not None:
                # Max wait for the thread to close, max 5 secs
                self._event_thread.join(5)

        return SingleSourceEventGenerator(
            setup_queue=_setup_gpio, cleanup=cleanup
        )

    def close(self):
        self._event_generator.close()

    def wait_event(self):
        return self._event_generator.wait_event()

    def async_wait_event(self):
        return self._event_generator.async_wait_event()


def main():
    sensor = UltrasonicSensor(23, 24)
    sensor.set_sample_interval(0.1)

    for event in sensor.wait_event():
        current_time = str(datetime.now(timezone.utc).isoformat())
        print("Distance: ", event, " at ", current_time)


async def async_main():
    sensor = UltrasonicSensor(23, 24)
    sensor.set_sample_interval(0.1)

    async with contextlib.aclosing(sensor.async_wait_event()) as wait_event:
        async for event in wait_event:
            current_time = str(datetime.now(timezone.utc).isoformat())
            print("Distance: ", event, " at ", current_time)


if __name__ == "__main__":
    test = 2

    match test:
        case 1:
            print("Running main()")
            main()
        case 2:
            print("Running async_main()")
            asyncio.run(async_main())
