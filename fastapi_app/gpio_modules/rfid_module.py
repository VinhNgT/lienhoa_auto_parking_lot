import asyncio
import contextlib
import os
import queue
import sys
import threading
import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Callable

from adafruit_extended_bus import ExtendedI2C as I2C
from adafruit_pn532.i2c import PN532_I2C
from gpiozero.tones import Tone

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from buzzer import Buzzer, BuzzerPlayRequest
from event_generator import SingleSourceEventGenerator

PN532_RESTART_EXCEPTIONS = [
    "Did not receive expected ACK from PN532!",
    "Response frame preamble does not contain 0x00FF!",
]


class RfidModule:
    def __init__(self, i2c, buzzer: Buzzer | None = None):
        self._i2c = i2c
        self._buzzer = buzzer

        self._event_thread: threading.Thread | None = None
        self._stop_event_flag = threading.Event()

        self._event_generator = self._setup_event_generator()

        self._pn532 = self._init_pn532()
        ic, ver, rev, support = self._pn532.firmware_version
        print("Found PN532 with firmware version: {0}.{1}".format(ver, rev))

    def _init_pn532(self) -> PN532_I2C:
        init_attempts = 10
        for i in range(init_attempts):
            try:
                pn532 = PN532_I2C(self._i2c, debug=False)
                pn532.SAM_configuration()
                break
            except RuntimeError as e:
                if (
                    str(e) not in PN532_RESTART_EXCEPTIONS
                    or i == init_attempts - 1
                ):
                    raise

                print(
                    f"Failed to init PN532, retrying... ({i + 1}/{init_attempts})"
                )
                time.sleep(1)

        return pn532

    def _read_uid(self) -> str | None:
        read_attempts = 3
        for i in range(read_attempts):
            try:
                uid = self._pn532.read_passive_target(timeout=0.5)
                break
            except RuntimeError as e:
                if (
                    str(e) not in PN532_RESTART_EXCEPTIONS
                    or i == read_attempts - 1
                ):
                    raise

                print(
                    f"Failed to read PN532, reinit... ({i + 1}/{read_attempts})"
                )
                self._pn532 = self._init_pn532()

        if uid is None:
            return None

        return "".join(f"{x:02x}" for x in uid)

    def _setup_event_generator(self) -> SingleSourceEventGenerator[str]:
        def _live_thread_loop(
            on_event: Callable[[str], None], stop_event_flag: threading.Event
        ):
            scan_time_history: dict[str, float] = defaultdict(lambda: 0)

            while True:
                if stop_event_flag.is_set():
                    break

                uid = self._read_uid()

                if uid is not None:
                    current_time = time.time()
                    scan_delta_time_uid = current_time - scan_time_history[uid]
                    scan_time_history[uid] = current_time

                    # print("Scan delta time:", scan_delta_time)

                    # Debounce
                    if scan_delta_time_uid < 0.5:
                        continue

                    on_event(uid)
                    if self._buzzer is not None:
                        self._buzzer.schedule(
                            BuzzerPlayRequest(Tone(frequency=800), duration=0.1)
                        )

        def _setup_gpio(queue: queue.Queue[str]):
            def on_event(uid: str):
                queue.put(uid)

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
    with Buzzer(21) as buzzer:
        rfid = RfidModule(I2C(6), buzzer)

        print("Waiting for RFID/NFC card")
        for event in rfid.wait_event():
            current_time = str(datetime.now(timezone.utc).isoformat())
            print("Card: ", event, " at ", current_time)


async def async_main():
    with Buzzer(21) as buzzer:
        rfid = RfidModule(I2C(6), buzzer)

        print("Waiting for RFID/NFC card")
        async with contextlib.aclosing(rfid.async_wait_event()) as wait_event:
            async for event in wait_event:
                current_time = str(datetime.now(timezone.utc).isoformat())
                print("Card: ", event, " at ", current_time)


if __name__ == "__main__":
    test = 2

    match test:
        case 1:
            print("Running main()")
            main()
        case 2:
            print("Running async_main()")
            asyncio.run(async_main())


# servo_1 = Servo(
#     10,
#     pin_factory=pi_gpio_factory,
#     min_pulse_width=0.5475 / 1000,
#     max_pulse_width=2.46 / 1000,
# )
# atexit.register(servo_1.close)
# servo_1.detach()

# servo_2 = Servo(
#     9,
#     pin_factory=pi_gpio_factory,
#     min_pulse_width=0.555 / 1000,
#     max_pulse_width=2.49 / 1000,
# )
# atexit.register(servo_2.close)
# servo_2.detach()
