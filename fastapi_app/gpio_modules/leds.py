import os
import sys
import time

from adafruit_extended_bus import ExtendedI2C as I2C
from adafruit_pcf8574 import PCF8574

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


class LedsPcf8574:
    # Note: If you get OSError: [Errno 5] Input/output error, these's probably
    # too much current flowing to the PCF8574. Try to increase the resistor
    # value or reduce the number of LEDs running at the same time.

    def __init__(
        self,
        i2c,
        address=0x20,
        led_count=8,
        reverse_layout=False,
    ):
        if led_count < 1 or led_count > 8:
            raise ValueError("led_count must be between 1 and 8")

        self.pcf = PCF8574(i2c, address)
        self.led_count = led_count
        self.reverse_layout = reverse_layout

        # Init pins turn off be default. LEDs are active low so we set the pins
        # high.
        # for i in range(8):
        #     self.pcf.get_pin(i).switch_to_output(value=True)
        self.pcf.write_gpio(0xFF)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        # Turn off all LEDs.
        self.pcf.write_gpio(0xFF)

    def set_led(self, led_id: int, state: bool):
        if led_id < 0 or led_id > self.led_count - 1:
            raise ValueError(
                f"led_id must be between 0 and {self.led_count - 1}"
            )

        self.pcf.write_pin(
            led_id if not self.reverse_layout else 7 - led_id,
            not state,
        )

    def set_leds_byte(self, byte: int, reverse_byte=False):
        if byte < 0 or byte > self.max_byte:
            raise ValueError(
                f"byte must be between 0x00 and {hex(self.max_byte)}"
            )

        # Flip bits because LEDs are active low.
        byte = ~byte & 0xFF

        if reverse_byte:
            byte = self._reverse_bits(byte, self.led_count)

        if self.reverse_layout:
            byte = self._reverse_bits(byte, 8)

        self.pcf.write_gpio(byte)

    @property
    def max_byte(self):
        """
        Return the maximum byte value that can be written to the PCF8574 to
        turn on all LEDs.
        """
        return (1 << self.led_count) - 1

    def _reverse_bits(self, n, length):
        result = 0

        for _ in range(length):
            # Create space for the next bit.
            result <<= 1
            # Add the rightmost bit of n to result.
            result |= n & 1
            # Shift n to the right. So the next bit can be added.
            n >>= 1

        return result


def main():
    with LedsPcf8574(I2C(7), reverse_layout=True, led_count=4) as led_ctl:
        print("Turning on LEDs.")

        while True:
            # for i in range(led_ctl.led_count):
            #     led_ctl.set_led(i, True)
            #     time.sleep(0.5)
            #     led_ctl.set_led(i, False)

            # led_ctl.set_leds_byte(0b00001011)
            led_ctl.set_leds_byte(0b1000)
            time.sleep(0.5)
            led_ctl.set_leds_byte(0)
            time.sleep(0.5)


if __name__ == "__main__":
    main()
