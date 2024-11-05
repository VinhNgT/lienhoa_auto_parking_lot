import math
from time import sleep
from typing import Final

from rpi_hardware_pwm import HardwarePWM

SERVO_DEFAULT_SLEEP_DURATION = 0.5


class PercentHardwarePWM:
    def __init__(
        self, pwm_channel, hz=50, min_duty=2.85, max_duty=12.425, duty_offset=0
    ):
        self._pwm: Final = HardwarePWM(pwm_channel=pwm_channel, hz=hz, chip=0)
        self.min_duty: Final = min_duty + duty_offset
        self.max_duty: Final = max_duty + duty_offset
        self.ratio: Final = (max_duty - min_duty) / 100

    def _duty_to_percent(self, duty: float) -> float:
        if duty < self.min_duty or duty > self.max_duty:
            print(f"Duty not in range {self.min_duty}-{self.max_duty}")
            # Warn: Setting the duty too high or too low will confused the servo.
            # Fix by unplug and plug the servo in again or the power source.
            duty = max(self.min_duty, min(duty, self.max_duty))

        return (duty - self.min_duty) / self.ratio

    def _percent_to_duty(self, percent: float) -> float:
        if percent < 0 or percent > 100:
            print("Percent value not in range 0-100")
            percent = max(0, min(percent, 100))

        return (percent * self.ratio) + self.min_duty

    def start(self, duty_percent=0):
        self._pwm.start(self._percent_to_duty(duty_percent))

    def stop(self):
        self._pwm.stop()

    def set_percent(self, percent: float):
        self._pwm.change_duty_cycle(self._percent_to_duty(percent))


class ServoHwPwm:
    SERVO_MIN_ANGLE: Final = 0
    SERVO_MAX_ANGLE: Final = 180
    SERVO_FREQUENCY_HZ = 50

    # Round numbers to 13 decimal places to prevent situation like
    # 7.63750000000001 or 6.87149999999999
    ROUNDING_DIGITS: Final = 13

    # Flag to stop the servo
    is_stopping_flag: bool = False

    def __init__(
        self,
        pwm_channel,
        initial_angle=0,
        angle_offset=0,
    ):
        # 1% = 1.8 degree
        self.percent_angle_ratio: Final = self.SERVO_MAX_ANGLE / 100  # 1.8
        self.initial_angle: Final = round(initial_angle, self.ROUNDING_DIGITS)

        # Variables
        self.current_angle = self.initial_angle

        # Initialize the servo
        self._pwm: Final = PercentHardwarePWM(
            pwm_channel=pwm_channel,
            hz=self.SERVO_FREQUENCY_HZ,
            duty_offset=round(
                self._angle_to_percent(angle_offset), self.ROUNDING_DIGITS
            ),
        )
        self._pwm.start(
            round(self._angle_to_percent(initial_angle), self.ROUNDING_DIGITS)
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._cleanup()

    def _cleanup(self):
        self.is_stopping_flag = True
        # self.ease_angle(self.initial_angle, 0.5)
        # sleep(SERVO_DEFAULT_SLEEP_DURATION)
        self._pwm.stop()

    def _angle_to_percent(self, angle: float) -> float:
        return angle / self.percent_angle_ratio

    def _percent_to_angle(self, percent: float) -> float:
        return percent * self.percent_angle_ratio

    def set_angle(self, angle: float):
        self.current_angle = round(angle, self.ROUNDING_DIGITS)
        self._pwm.set_percent(
            round(self._angle_to_percent(angle), self.ROUNDING_DIGITS)
        )

    def ease_angle(self, angle: float, ease_seconds: float):
        if ease_seconds <= 0:
            raise ValueError("ease_time must be greater than 0")

        # Skip if the requested angle is the same as the current angle.
        print(f"Current angle: {self.current_angle}, Requested angle: {angle}")
        if angle == self.current_angle:
            return

        # The number of steps to finish the operation.
        # We multiply by 2 to make the movement smoother.
        steps = math.ceil(self.SERVO_FREQUENCY_HZ * ease_seconds * 2)

        # The time for each step.
        step_delay = ease_seconds / steps

        # The angle by which the servo needs to move in each step.
        step_size = (angle - self.current_angle) / steps

        # Perform stepping
        raw_current_angle = self.current_angle
        for i in range(steps):
            if self.is_stopping_flag:
                break

            target_angle = raw_current_angle + (step_size * (i + 1))
            # print(f"Step {i + 1}/{steps}, moving to {target_angle}")
            # self.set_angle(target_angle)

            self.set_angle(target_angle)
            # print(f"Set angle {target_angle}")
            sleep(step_delay)


def run_example_1():
    try:
        with ServoHwPwm(pwm_channel=0) as servo:
            while True:
                for i in [0, 90, 180, 90]:
                    # for i in [0, 90, 180]:
                    servo.set_angle(i)
                    print(f"Angle: {i}")
                    sleep(SERVO_DEFAULT_SLEEP_DURATION)

    except KeyboardInterrupt:
        pass


def run_example_2():
    with ServoHwPwm(pwm_channel=0) as servo:
        while True:
            input_angle = float(input("Enter angle: "))
            servo.ease_angle(input_angle, ease_seconds=1)


def run_example_3():
    with ServoHwPwm(pwm_channel=0, initial_angle=180, angle_offset=0.3) as servo:
        is_90 = False

        while True:
            input("Waiting for trigger")
            is_90 = not is_90
            servo.ease_angle(90 if is_90 else 180, ease_seconds=0.5)


def servo_calibrator():
    """
    A method to find the max and min duty of a servo.
    """
    pwm: Final = HardwarePWM(pwm_channel=0, hz=50, chip=0)
    pwm.start(0)

    while True:
        input_duty = float(input("Enter duty: "))
        pwm.change_duty_cycle(input_duty)


if __name__ == "__main__":
    # servo_calibrator()

    # run_example_1()
    run_example_3()
