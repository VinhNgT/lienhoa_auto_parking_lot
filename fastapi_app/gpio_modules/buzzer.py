import os
import sys
import time

from gpiozero import TonalBuzzer as GPIOTonalBuzzer
from gpiozero.tones import Tone

# Add current script folder to Python path.
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from common import pi_gpio_factory

from fastapi_app.gpio_modules.request_queued_thread import RequestQueuedThread


class BuzzerPlayRequest:
    def __init__(self, tone: Tone, duration: float):
        self.tone = tone
        self.duration = duration


class Buzzer:
    def __init__(self, pin: int, queue_size: int = 3):
        self.gpio_buzzer = GPIOTonalBuzzer(
            pin, pin_factory=pi_gpio_factory, octaves=2
        )
        # atexit.register(self.gpio_buzzer.close)

        self._queue_size = queue_size
        self._play_queued_thread = self._setup_queued_thread()

    def _setup_queued_thread(self) -> RequestQueuedThread:
        def _serve_request(
            request: BuzzerPlayRequest, next_request_available: bool
        ):
            self.gpio_buzzer.play(request.tone)
            time.sleep(request.duration)

            if not next_request_available:
                self.gpio_buzzer.stop()

        def _cleanup():
            self.gpio_buzzer.stop()

        return RequestQueuedThread(
            _serve_request,
            _cleanup,
            queue_size=self._queue_size,
        )

    @property
    def max_frequency(self) -> float:
        return self.gpio_buzzer.max_tone.frequency

    @property
    def min_frequency(self) -> float:
        return self.gpio_buzzer.min_tone.frequency

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        self._play_queued_thread.close()
        # self.gpio_buzzer.close()

    def schedule(self, request: BuzzerPlayRequest, block=True):
        self._play_queued_thread.schedule(request, block=block)

    def join_queue(self):
        self._play_queued_thread.join_queue()


def main():
    with Buzzer(21) as buzzer:
        for midi_note in range(
            buzzer.gpio_buzzer.mid_tone.midi - 15,
            buzzer.gpio_buzzer.mid_tone.midi + 15,
            5,
        ):
            tone = Tone(midi=midi_note)

            buzzer.schedule(BuzzerPlayRequest(tone, 2))
            print(
                f"Added {tone.midi} - fq: {tone.frequency} - note: {tone.note}"
            )
            time.sleep(0.1)

        buzzer.join_queue()


if __name__ == "__main__":
    main()
