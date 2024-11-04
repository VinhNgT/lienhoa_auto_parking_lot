from time import sleep
from typing import Final

import board
from adafruit_hcsr04 import HCSR04


class SonarDistance:
    MAX_DISTANCE_MM: Final = 2000

    def __init__(
        self,
        trigger_pin,
        echo_pin,
    ):
        self._sensor = HCSR04(trigger_pin=trigger_pin, echo_pin=echo_pin)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._sensor.__exit__(exc_type, exc_value, traceback)

    def get_distance(self) -> int:
        """
        Return the distance in mm
        """
        try:
            reading = int(self._sensor.distance * 10)
            return max(0, min(reading, self.MAX_DISTANCE_MM))

        except RuntimeError:
            # If the sensor can't get a reading.
            return self.MAX_DISTANCE_MM


def run_example():
    with SonarDistance(trigger_pin=board.D17, echo_pin=board.D27) as sonar:
        while True:
            print("Range: {0}mm".format(sonar.get_distance()))
            sleep(0.25)


if __name__ == "__main__":
    run_example()
