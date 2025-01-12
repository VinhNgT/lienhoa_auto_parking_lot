# ruff: noqa: F401

import atexit
import time

from gpiozero import PWMOutputDevice, TonalBuzzer
from gpiozero.tones import Tone

from common import pi_gpio_factory

b = TonalBuzzer(21, pin_factory=pi_gpio_factory)
atexit.register(b.close)


if __name__ == "__main__":
    for midi_note in range(b.min_tone.midi, b.max_tone.midi + 1):
        tone = Tone(midi=midi_note)

        print(f"Playing {tone.midi} - fq: {tone.frequency} - note: {tone.note}")
        b.play(tone)
        time.sleep(0.5)
        b.stop()
        time.sleep(0.1)

    b.close()

    # c = PWMOutputDevice(21, pin_factory=pi_gpio_factory)
    # atexit.register(c.close)

    # for midi_note in range(57, 81 + 1):
    #     tone = Tone(midi=midi_note)
    #     print(f"Playing {tone.midi} - fq: {tone.frequency} - note: {tone.note}")

    #     c.frequency = tone.frequency
    #     c.value = 0.5
    #     time.sleep(0.5)

    #     c.value = 0
    #     time.sleep(0.1)

    # c.close()
