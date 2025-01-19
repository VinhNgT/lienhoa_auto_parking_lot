import re
import threading
import time
from itertools import chain
from typing import Final

from more_itertools import batched
from RPLCD.i2c import CharLCD


class StringObject:
    def __init__(self, content: str):
        self._content = content

    def __len__(self) -> int:
        return len(self._content)

    def __str__(self) -> str:
        return self._content


class Word(StringObject):
    def __init__(self, content: str):
        super().__init__(content)


class Spaces(StringObject):
    def __init__(self, content: str):
        super().__init__(content)


class TextWrapper:
    def __init__(self, max_line_length: int):
        self.max_line_length: Final = max_line_length

    def _convert_to_str_objs(self, text: str) -> list[StringObject]:
        split: list[str] = re.findall(r"\S+|\s+", text)
        return [
            Spaces(item) if item.isspace() else Word(item) for item in split
        ]

    def _get_remaining_space(self, line: str) -> int:
        return self.max_line_length - len(line)

    def wrap(self, text: str) -> list[str]:
        if len(text) == 0:
            return []

        str_objs: list[StringObject] = self._convert_to_str_objs(text)
        lines: list[str] = [""]

        for obj in str_objs:
            if self._get_remaining_space(lines[-1]) >= len(obj):
                lines[-1] += str(obj)
                continue

            match obj:
                case Spaces():
                    # The number of spaces that we need to remove because they are
                    # considered "newline".
                    space_to_newline_num = (len(lines[-1]) + len(obj)) // (
                        self.max_line_length + 1
                    )
                    compound_line = lines[-1] + str(obj)[:-space_to_newline_num]
                    lines_to_be_added = [
                        "".join(str_tuple)
                        for str_tuple in batched(
                            compound_line, self.max_line_length
                        )
                    ]

                    lines.pop()
                    lines.extend(lines_to_be_added)

                case Word():
                    lines_to_be_added = [
                        "".join(str_tuple)
                        for str_tuple in batched(str(obj), self.max_line_length)
                    ]

                    if len(lines[-1]) == 0:
                        lines.pop()

                    lines.extend(lines_to_be_added)

        return [line.rstrip() for line in lines]


class LcdI2c:
    MAX_LINE_LENGTH: Final = 20
    MAX_LINE_COUNT: Final = 4

    def __init__(self, i2c_bus, i2c_addr=0x27):
        self._i2c_bus = i2c_bus
        self._i2c_addr = i2c_addr
        self._lcd = self._init_lcd()

        self._text_wrapper = TextWrapper(self.MAX_LINE_LENGTH)
        self._write_lock = threading.Lock()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def _init_lcd(self):
        attempts = 0
        while True:
            try:
                lcd = CharLCD(
                    i2c_expander="PCF8574",
                    address=self._i2c_addr,
                    port=self._i2c_bus,
                    cols=20,
                    rows=4,
                )
                break
            except IOError as e:
                attempts += 1

                print(e)
                print(f"Failed to init LCD, retrying... (attempt {attempts})")
                time.sleep(1)

        return lcd

    def close(self):
        self._lcd.close()

    def clear(self):
        self._lcd.clear()

    def write_string(self, text: str, clear=True):
        attempts = 0
        with self._write_lock:
            while True:
                try:
                    lines = text.rstrip().split("\n")
                    lines = list(
                        chain.from_iterable(
                            [
                                self._text_wrapper.wrap(line)
                                if line != ""
                                else [""]
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
                    break

                except IOError as e:
                    attempts += 1

                    print(e)
                    # print(
                    #     f"Failed to write text to LCD, reinit... (attempt {attempts})"
                    # )
                    # self._lcd = self._init_lcd()

                    print(
                        f"Failed to write text to LCD, retry... (attempt {attempts})"
                    )


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

    lcd = LcdI2c(i2c_bus=8)
    lcd.write_string("Hello World!")

    while True:
        input_str = get_multiline_input()

        lcd.clear()
        lcd.write_string(input_str)


def run_example_print():
    lcd = LcdI2c(i2c_bus=8)
    lcd.write_string(("8" * 20 + "\n") * 4)


def run_example_wrap():
    formatter = TextWrapper(20)
    text = "Hello, World!        888888"

    result = formatter.wrap(text)
    for line in result:
        print(line)


def stress_test_lcd():
    ascii_chars = "\n".join(
        [
            "".join(
                chr(65 + (i * 20 + j) % 26)
                if (i * 20 + j) < 26
                else chr(48 + (i * 20 + j - 26) % 10)
                for j in range(20)
            )
            for i in range(4)
        ]
    )
    for _ in range(100):
        with LcdI2c(i2c_bus=8) as lcd:
            lcd.write_string(ascii_chars)
            # lcd.write_string(("8" * 20 + "\n") * 4)

        time.sleep(0.5)


if __name__ == "__main__":
    # run_example()
    # run_example_print()
    stress_test_lcd()
