# ruff: noqa: F401

import asyncio
import atexit
import random
import time
from datetime import datetime

import board
import busio
from adafruit_extended_bus import ExtendedI2C as I2C
from adafruit_pn532.i2c import PN532_I2C
from gpiozero import PWMOutputDevice, Servo
from gpiozero.tones import Tone

from common import pi_gpio_factory

# i2c = busio.I2C(board.SCL, board.SDA)
i2c = I2C(6)
buzzer_ctl = PWMOutputDevice(21, pin_factory=pi_gpio_factory)
atexit.register(buzzer_ctl.close)


servo_1 = Servo(
    10,
    pin_factory=pi_gpio_factory,
    min_pulse_width=0.5475 / 1000,
    max_pulse_width=2.46 / 1000,
)
atexit.register(servo_1.close)
servo_1.detach()

servo_2 = Servo(
    9,
    pin_factory=pi_gpio_factory,
    min_pulse_width=0.555 / 1000,
    max_pulse_width=2.49 / 1000,
)
atexit.register(servo_2.close)
servo_2.detach()


# Try to init pn532 10 times
for i in range(10):
    try:
        pn532 = PN532_I2C(i2c, debug=False)
        break
    except RuntimeError as e:
        if str(e) not in [
            "Did not receive expected ACK from PN532!",
            "Response frame preamble does not contain 0x00FF!",
        ]:
            raise

        print(f"Failed to communicate PN532, retrying... ({i + 1}/10)")
        time.sleep(1)


def startup():
    ic, ver, rev, support = pn532.firmware_version
    print("Found PN532 with firmware version: {0}.{1}".format(ver, rev))

    pn532.SAM_configuration()


async def beep_consumer(beep_queue: asyncio.Queue) -> None:
    while True:
        tone: Tone = await beep_queue.get()
        buzzer_ctl.frequency = tone.frequency

        buzzer_ctl.value = 0.5
        await asyncio.sleep(0.1)
        buzzer_ctl.value = 0
        beep_queue.task_done()


async def get_rfid_card() -> str:
    def read_loop() -> bytearray:
        while True:
            uid = pn532.read_passive_target()

            if uid is not None:
                return uid

    uid = await asyncio.to_thread(read_loop)
    return "".join(f"{x:02x}" for x in uid)


async def main_loop(beep_queue: asyncio.Queue):
    startup()
    print("Waiting for RFID/NFC card")

    previous_uid: bytearray | None = None
    previous_scan_time = 0

    while True:
        uid = await get_rfid_card()

        if uid is not None:
            current_time = time.time()
            scan_delta_time = current_time - previous_scan_time
            previous_scan_time = current_time

            # print("Scan delta time:", scan_delta_time)

            # Debounce
            if previous_uid == uid and scan_delta_time < 0.5:
                continue

            print(f"Found card with UID: {uid}")
            previous_uid = uid

            if not beep_queue.full():
                beep_queue.put_nowait(Tone(frequency=1000))


async def main():
    beep_queue = asyncio.Queue(3)

    beep_task = asyncio.create_task(beep_consumer(beep_queue))
    main_task = asyncio.create_task(main_loop(beep_queue))

    atexit.register(beep_task.cancel)
    atexit.register(main_task.cancel)

    await asyncio.gather(beep_task, main_task)


if __name__ == "__main__":
    asyncio.run(main())
