import asyncio
import contextlib
import os
import queue
import sys
import threading
import time
from datetime import datetime, timezone
from typing import Callable

from adafruit_hcsr04 import HCSR04

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import board
from event_generator import SingleSourceEventGenerator

MAX_DISTANCE = 300


class UltrasonicSensor:
    def __init__(
        self, trigger_pin: int, echo_pin: int, sample_interval: float = 1
    ):
        self.trigger_pin = trigger_pin
        self.echo_pin = echo_pin
        self.sample_interval = sample_interval

        self._event_thread: threading.Thread | None = None
        self._stop_event_flag = threading.Event()
        self._event_generator = self._setup_event_generator()

    def _setup_event_generator(self) -> SingleSourceEventGenerator[float]:
        def _live_thread_loop(
            on_event: Callable[[float], None], stop_event_flag: threading.Event
        ):
            with HCSR04(
                trigger_pin=self.trigger_pin, echo_pin=self.echo_pin
            ) as sonar:
                while True:
                    if stop_event_flag.is_set():
                        break

                    if sonar._echo._process.poll() == 0:
                        # print("CircuitPython PulseIn subprocess was closed!")
                        break

                    try:
                        current_value = sonar.distance
                    except RuntimeError as e:
                        if str(e) == "Timed out":
                            current_value = MAX_DISTANCE
                        else:
                            raise

                    on_event(round(min(current_value, MAX_DISTANCE), 3))
                    time.sleep(self.sample_interval)

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
    sensor = UltrasonicSensor(board.D23, board.D24)
    for event in sensor.wait_event():
        current_time = str(datetime.now(timezone.utc).isoformat())
        print("Distance: ", event, " at ", current_time)


async def async_main():
    sensor = UltrasonicSensor(board.D23, board.D24, sample_interval=0.1)

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
