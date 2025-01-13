import os
import queue
import sys
import threading
import time
from contextlib import contextmanager

from gpiozero import TonalBuzzer as GPIOTonalBuzzer
from gpiozero.tones import Tone

# Add current script folder to Python path.
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from common import pi_gpio_factory


class BuzzerPlayRequest:
    def __init__(self, tone: Tone, duration: float):
        self.tone = tone
        self.duration = duration


class Buzzer:
    def __init__(self, pin: int):
        self.gpio_buzzer = GPIOTonalBuzzer(
            pin, pin_factory=pi_gpio_factory, octaves=2
        )
        # atexit.register(self.gpio_buzzer.close)

        self._play_queue: queue.Queue[BuzzerPlayRequest] = queue.Queue()
        self._buzzer_thread = threading.Thread(
            target=self._buzzer_thread_loop,
            args=(self._play_queue, self.gpio_buzzer),
        )
        self._buzzer_thread.start()

    @staticmethod
    def _buzzer_thread_loop(
        queue: queue.Queue[BuzzerPlayRequest],
        gpio_buzzer: GPIOTonalBuzzer,
    ):
        @contextmanager
        def _get_request():
            request = queue.get()
            yield request
            if queue.empty():
                gpio_buzzer.stop()
            queue.task_done()

        while True:
            with _get_request() as request:
                if request is None:
                    break

                gpio_buzzer.play(request.tone)
                time.sleep(request.duration)

        # print("Exiting main thread loop")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        # print("Closing")

        try:
            self._clear_queue()
            self._play_queue.put_nowait(None)
            self._buzzer_thread.join()
        finally:
            # Must run this to ensure the buzzer is stopped.
            self.gpio_buzzer.close()

    def _clear_queue(self):
        while not self._play_queue.empty():
            self._play_queue.get_nowait()
            self._play_queue.task_done()

    def schedule(self, request: BuzzerPlayRequest):
        if request is None:
            raise ValueError("Request cannot be None")

        self._play_queue.put(request)

    def join_queue(self):
        self._play_queue.join()


def main():
    with Buzzer(21) as buzzer:
        for midi_note in range(
            buzzer.gpio_buzzer.mid_tone.midi,
            buzzer.gpio_buzzer.mid_tone.midi + 15,
            5,
        ):
            tone = Tone(midi_note)
            print(f"Add {tone.midi} - fq: {tone.frequency} - note: {tone.note}")

            buzzer.schedule(BuzzerPlayRequest(tone, 1))
            time.sleep(0.1)

        buzzer.join_queue()


if __name__ == "__main__":
    main()
