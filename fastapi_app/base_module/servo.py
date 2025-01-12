# ruff: noqa: F401

import atexit
from time import sleep

from gpiozero import Servo

from common import pi_gpio_factory

servo_1 = Servo(
    10,
    pin_factory=pi_gpio_factory,
    min_pulse_width=0.5475 / 1000,
    max_pulse_width=2.46 / 1000,
)
atexit.register(servo_1.close)

servo_2 = Servo(
    9,
    pin_factory=pi_gpio_factory,
    min_pulse_width=0.555 / 1000,
    max_pulse_width=2.49 / 1000,
)
atexit.register(servo_2.close)


# def calibrate_servo(pin_id: int):
#     servo = Servo(
#         pin_id,
#         pin_factory=pi_gpio_factory,
#         min_pulse_width=0.555 / 1000,
#         max_pulse_width=2.49 / 1000,
#     )
#     atexit.register(servo.close)

#     while True:
#         print("Min")
#         servo.min()
#         sleep(5)
#         print("Max")
#         servo.max()
#         sleep(5)


if __name__ == "__main__":
    # calibrate_servo(9)

    while True:
        print("Min")
        servo_1.min()
        servo_2.min()
        sleep(1)

        print("Mid")
        servo_1.mid()
        servo_2.mid()
        sleep(1)

        print("Max")
        servo_1.max()
        servo_2.max()
        sleep(1)
