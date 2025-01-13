# ruff: noqa: F401

import asyncio
import atexit
import concurrent.futures
import os
import sys
import threading
import time

from gpiozero import PWMOutputDevice
from gpiozero import TonalBuzzer as GPIOTonalBuzzer
from gpiozero.tones import Tone

# Add current script folder to Python path.
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from common import pi_gpio_factory
from utils import helper_done_callback


class BuzzerPlayRequest:
    def __init__(self, tone: Tone, duration: float):
        self.tone = tone
        self.duration = duration


class Buzzer:
    def __init__(self, pin: int):
        self.gpio_buzzer = GPIOTonalBuzzer(pin, pin_factory=pi_gpio_factory)

        self._play_queue: asyncio.Queue[BuzzerPlayRequest] = asyncio.Queue(1)

        # asyncio.to_thread

        atexit.register(self.gpio_buzzer.close)

        self._stop_event = threading.Event()
        self._main_loop_task = asyncio.create_task(
            self._main_thread_loop(
                self._play_queue, self.gpio_buzzer, self._stop_event
            )
        )
        self._main_loop_task.add_done_callback(helper_done_callback)

        # loop = asyncio.get_running_loop()
        # with concurrent.futures.ThreadPoolExecutor() as pool:
        #     result = await loop.run_in_executor(
        #         pool, blocking_io)
        #     print('custom thread pool', result)

        # self._speaker_thread = threading.Thread(
        #     target=asyncio.run,
        #     args=[self._main_thread_loop(self._play_queue, self.gpio_buzzer)],
        #     kwargs={"debug": True},
        # )
        # self._speaker_thread.start()

        # loop = asyncio.get_running_loop()
        # self._main_future = asyncio.run_coroutine_threadsafe(
        #     self._main_thread_loop(self._play_queue, self.gpio_buzzer), loop
        # )

        # self._speaker_thread.

        # atexit.register(self.gpio_buzzer.close)

    @staticmethod
    async def _main_thread_loop(
        queue: asyncio.Queue[BuzzerPlayRequest],
        gpio_buzzer: GPIOTonalBuzzer,
        stop_event: threading.Event,
    ):
        while not stop_event.is_set():
            request = await queue.get()

            if stop_event.is_set():
                gpio_buzzer.stop()
                queue.task_done()
                break

            gpio_buzzer.play(request.tone)
            await asyncio.sleep(request.duration)

            if queue.empty():
                gpio_buzzer.stop()

            queue.task_done()

        print("Exiting main thread loop")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close()

    async def close(self):
        # self._main_loop_task.cancel()
        # self._speaker_thread.
        # await self._play_queue.put(None)
        # print("Put None")

        # print("Waiting")
        # await self._main_future

        print("Closing")

        self._clear_queue()
        # await self._play_queue.join()

        self._stop_event.set()
        self._play_queue.put_nowait(Tone(0))

        await self._main_loop_task
        # self._main_loop_task.cancel()
        self.gpio_buzzer.close()

    def _clear_queue(self):
        while not self._play_queue.empty():
            self._play_queue.get_nowait()
            self._play_queue.task_done()

    async def add_request(self, tone: Tone, duration: float):
        await self._play_queue.put(BuzzerPlayRequest(tone, duration))


async def main():
    # buzzer = Buzzer(21)
    # atexit.register(buzzer.close)

    async with Buzzer(21) as buzzer:
        try:
            for midi_note in [57, 60, 70]:
                tone = Tone(midi=midi_note)
                # print(
                #     f"Playing {tone.midi} - fq: {tone.frequency} - note: {tone.note}"
                # )

                await buzzer.add_request(tone, 1)
                print("Add request", tone.midi)
                # await asyncio.sleep(1)
        except asyncio.exceptions.CancelledError:
            # pass
            raise

    # async with contextlib.aclosing(button.wait_event()) as wait_event:
    #     try:
    #         async for event in wait_event:
    #             current_time = str(datetime.now())

    #             match event:
    #                 case ButtonEvent.PRESSED:
    #                     print("Button pressed! at ", current_time)
    #                 case ButtonEvent.RELEASED:
    #                     print("Button released! at ", current_time)
    #     except asyncio.exceptions.CancelledError:
    #         pass


if __name__ == "__main__":
    asyncio.run(main(), debug=True)


# if __name__ == "__main__":
#     for midi_note in range(b.min_tone.midi, b.max_tone.midi + 1):
#         tone = Tone(midi=midi_note)

#         print(f"Playing {tone.midi} - fq: {tone.frequency} - note: {tone.note}")
#         b.play(tone)
#         time.sleep(0.5)
#         b.stop()
#         time.sleep(0.1)

#     b.close()

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
