import atexit
import math
import os
import sys
import threading
import time

from gpiozero import AngularServo as GPIOAngularServo

# Add current script folder to Python path.
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from common import pi_gpio_factory
from request_queued_thread import RequestQueuedThread

SERVO_FREQUENCY_HZ = 50


class ServoMoveRequest:
    def __init__(self, angle: float, duration: float = 0):
        self.angle = angle
        self.duration = duration


class Servo:
    def __init__(
        self,
        pin: int,
        min_pulse_width: float,
        max_pulse_width=float,
        queue_size: int = 3,
        angle_offset: float = 0,
    ):
        self.gpio_servo = GPIOAngularServo(
            pin,
            pin_factory=pi_gpio_factory,
            min_pulse_width=min_pulse_width,
            max_pulse_width=max_pulse_width,
            min_angle=-45,
            max_angle=45,
        )
        # atexit.register(self.gpio_buzzer.close)

        self._angle_offset = angle_offset
        self._queue_size = queue_size
        self._move_queued_thread = self._setup_queued_thread()
        self._stop_flag_event = threading.Event()

    @property
    def max_angle(self) -> float:
        return self.gpio_servo.max_angle

    @property
    def min_angle(self) -> float:
        return self.gpio_servo.min_angle

    def ease_angle(self, angle: float, ease_seconds: float):
        if ease_seconds < 0:
            raise ValueError("ease_time must not be negative")
        if ease_seconds == 0:
            # Prevent division by zero.
            ease_seconds = sys.float_info.min

        # Skip if the requested angle is about the same as the current angle.
        # print(
        #     f"Current angle: {self.gpio_servo.angle}, Requested angle: {angle}"
        # )
        if angle == round(self.gpio_servo.angle, 0):
            return

        # The number of steps to finish the operation.
        # We multiply by 2 to make the movement smoother.
        steps = math.ceil(SERVO_FREQUENCY_HZ * ease_seconds * 2)

        # The time for each step.
        step_delay = ease_seconds / steps

        # The angle by which the servo needs to move in each step.
        step_size = (angle - self.gpio_servo.angle) / steps

        # Perform stepping
        initial_angle = self.gpio_servo.angle
        for i in range(steps):
            # User requested to stop the operation.
            if self._stop_flag_event.is_set():
                break

            target_angle = initial_angle + (step_size * (i + 1))

            # Normalize the angle to the servo's limits. Prevent situation like
            # moving to -45.00000000000001.
            target_angle = max(
                min(self.gpio_servo.max_angle, target_angle),
                self.gpio_servo.min_angle,
            )
            # print(f"Step {i + 1}/{steps}, moving to {target_angle}")
            # self.set_angle(target_angle)

            # print(f"Setting angle {target_angle}")
            self.gpio_servo.angle = target_angle
            time.sleep(step_delay)

    def _setup_queued_thread(self) -> RequestQueuedThread:
        def _serve_request(
            request: ServoMoveRequest, next_request_available: bool
        ):
            # self.gpio_servo.angle = request.angle
            self.ease_angle(
                request.angle + self._angle_offset, request.duration
            )

        def _cleanup():
            self.gpio_servo.close()

        return RequestQueuedThread(
            _serve_request,
            _cleanup,
            queue_size=self._queue_size,
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        self._stop_flag_event.set()
        self._move_queued_thread.close()
        # self.gpio_buzzer.close()

    def schedule(self, request: ServoMoveRequest, block=True):
        # print(f"Scheduling request: {request.angle}")
        self._move_queued_thread.schedule(request, block=block)

    def join_queue(self):
        self._move_queued_thread.join_queue()


def main():
    servo_1 = Servo(
        10,
        min_pulse_width=0.5475 / 1000,
        max_pulse_width=2.46 / 1000,
    )
    # atexit.register(servo_1.close)

    servo_2 = Servo(
        9,
        min_pulse_width=0.555 / 1000,
        max_pulse_width=2.49 / 1000,
    )
    # atexit.register(servo_2.close)

    move_duration = 1

    with servo_1, servo_2:
        while True:
            print("Min")
            servo_1.schedule(ServoMoveRequest(servo_1.min_angle, move_duration))
            servo_2.schedule(ServoMoveRequest(servo_2.min_angle, move_duration))
            servo_1.join_queue()
            servo_2.join_queue()
            # time.sleep(1)

            print("Mid")
            servo_1.schedule(ServoMoveRequest(0, move_duration))
            servo_2.schedule(ServoMoveRequest(0, move_duration))
            servo_1.join_queue()
            servo_2.join_queue()
            # time.sleep(1)

            print("Max")
            servo_1.schedule(ServoMoveRequest(servo_1.max_angle, move_duration))
            servo_2.schedule(ServoMoveRequest(servo_2.max_angle, move_duration))
            servo_1.join_queue()
            servo_2.join_queue()
            # time.sleep(1)


def calibrate_servo(pin_id: int):
    servo = GPIOAngularServo(
        pin_id,
        pin_factory=pi_gpio_factory,
        min_pulse_width=0.55 / 1000,
        max_pulse_width=2.485 / 1000,
        # min_pulse_width=0.555 / 1000,
        # max_pulse_width=2.49 / 1000,
        min_angle=-45,
        max_angle=45,
    )
    atexit.register(servo.close)

    while True:
        print("Min")
        servo.min()
        time.sleep(5)
        print("Max")
        servo.max()
        time.sleep(5)


if __name__ == "__main__":
    # calibrate_servo(9)
    main()
