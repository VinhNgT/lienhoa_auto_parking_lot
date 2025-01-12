import time

import board
from adafruit_hcsr04 import HCSR04

MAX_DISTANCE = 300

with HCSR04(trigger_pin=board.D23, echo_pin=board.D24) as sonar:
    try:
        while True:
            try:
                print(
                    round(min(sonar.distance, MAX_DISTANCE), 3)
                )  # Round to 14 decimal places to remove noise

            except RuntimeError:
                print(MAX_DISTANCE)

            time.sleep(1)

    except KeyboardInterrupt:
        pass
