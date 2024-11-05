from time import sleep
from typing import Final

from adafruit_extended_bus import ExtendedI2C as I2C
from adafruit_pcf8574 import PCF8574


class LedsI2c:
    PCF8574_PIN_COUNT: Final = 8

    def __init__(self, i2c_bus: int, i2c_addr=0x20, led_count=PCF8574_PIN_COUNT):
        self.led_count: Final = led_count

        self._i2c = I2C(i2c_bus)
        self._pcf = PCF8574(self._i2c, i2c_addr)
        self._setup_pins(self._pcf)

    def __del__(self):
        self._pcf.write_gpio(0xFF)

    def _setup_pins(self, pcf: PCF8574):
        for i in range(self.PCF8574_PIN_COUNT):
            pcf.get_pin(i).switch_to_output(True)

    def _reverse_bits(self, bits: int) -> int:
        result = 0
        for i in range(self.led_count):
            # Move the result one bit to the left and add the least significant
            # bit of byte to it.
            #
            # (result << 1): Move the result one bit to the left.
            #
            # (byte & 1): Get the least significant bit of byte.
            #
            # (result << 1) | (byte & 1): Combine the two results.
            result = (result << 1) | (bits & 1)

            # Shift the byte one bit to the right. Prepare for the next
            # iteration.
            bits >>= 1

        return result

    def set_leds_bits(self, bits: int, is_reversed=False):
        if bits > (1 << self.led_count + 1) - 1:
            raise ValueError(
                f"The amount of bits should be smaller or equal to {self.led_count} bits"
            )

        adjusted_bits = self._reverse_bits(bits) if is_reversed else bits

        # The LEDs use 'active low' logic, so we need to flip the bits.
        flipped = ~adjusted_bits & 0xFF
        self._pcf.write_gpio(flipped)

    def set_led(self, led_pin: int, state: bool):
        if led_pin >= self.led_count:
            raise ValueError(
                f"LED pin should be smaller than {self.led_count} but was {led_pin}"
            )

        self._pcf.get_pin(led_pin).value = not state

    def get_led(self, led_pin: int) -> bool:
        if led_pin >= self.led_count:
            raise ValueError(
                f"LED pin should be smaller than {self.led_count} but was {led_pin}"
            )

        return not self._pcf.get_pin(led_pin).value


def run_example():
    leds = LedsI2c(i2c_bus=1, led_count=4)

    bit_pattern = 0b1100
    while True:
        leds.set_leds_bits(bit_pattern, is_reversed=True)
        sleep(0.25)

        # Rotate the bit pattern to the right
        bit_pattern = ((bit_pattern >> 1) | (bit_pattern << 3)) & 0xF
        print(f"{bit_pattern:04b}")


if __name__ == "__main__":
    run_example()
