import os
import sys
from itertools import chain
from typing import Final

from RPLCD.i2c import CharLCD

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from fastapi_app.gpio_modules.utils.text_wrapper import TextWrapper


class LcdI2c:
    MAX_LINE_LENGTH: Final = 20
    MAX_LINE_COUNT: Final = 4

    def __init__(self, i2c_bus, i2c_addr=0x27):
        self._lcd = CharLCD(
            i2c_expander="PCF8574",
            address=i2c_addr,
            port=i2c_bus,
            cols=20,
            rows=4,
        )

        self._text_wrapper = TextWrapper(self.MAX_LINE_LENGTH)

    def close(self):
        self._lcd.close()

    def clear(self):
        self._lcd.clear()

    def write_string(self, text: str, clear=True):
        lines = text.rstrip().split("\n")
        lines = list(
            chain.from_iterable(
                [
                    self._text_wrapper.wrap(line) if line != "" else [""]
                    for line in lines
                ]
            )
        )

        if clear:
            self.clear()

        print(f"Sending text to LCD: {lines}")
        print("-" * self.MAX_LINE_LENGTH)

        for i, line in enumerate(lines):
            print(line)

            if i >= self.MAX_LINE_COUNT:
                raise ValueError(
                    f"Number of lines is greater than {self.MAX_LINE_COUNT}: {lines}"
                )

            self._lcd.write_string(line)
            self._lcd.crlf()

        print("-" * self.MAX_LINE_LENGTH)


def run_example():
    def get_multiline_input() -> str:
        print("Enter/Paste your content. Type #d to finish.")
        lines = []

        while True:
            line = input()

            if line != "#d":
                lines.append(line)
            else:
                break

        text = "\n".join(lines)
        return text

    lcd = LcdI2c(i2c_bus=1)
    lcd.write_string("Hello World!")

    while True:
        input_str = get_multiline_input()

        lcd.clear()
        lcd.write_string(input_str)


def run_example_print():
    lcd = LcdI2c(i2c_bus=8)
    lcd.write_string(("8" * 20 + "\n") * 4)


if __name__ == "__main__":
    # run_example()
    run_example_print()
