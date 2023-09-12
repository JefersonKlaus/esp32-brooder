import time

from machine import PWM, Pin

from .utils import scale_value

"""
from servo import Servo
servo = Servo(pin_number=15, max_degree=180, freq=50, init_duty=0)
servo.set_degree(degree=180)
"""


class Servo:
    pwm = None
    pin = None
    max_degree = 0

    def __init__(self, pin_number=15, max_degree=180, freq=50, init_duty=0):
        self.pin = Pin(pin_number, Pin.OUT)
        self.pwm = PWM(self.pin)
        self.pwm.init()
        self.pwm.freq(freq)
        self.pwm.duty(init_duty)

        self.max_degree = max_degree

    def __del__(self):
        self.pwm.deinit()

    def set_degree(self, degree, speed=100):
        """
        Set degree position with speed control
        Args:
            degree (int): Desired position in degrees
            speed (int): Speed percentage (0-100)
        Returns:
            None
        """
        speed = max(min(speed, 100), 1)  # Ensure speed is between 1 and 100
        speed_factor = speed / 100.0  # Calculate the speed factor as a float

        current_degree = self.get_degree()
        steps = int(abs(degree - current_degree) * speed_factor)

        if degree > current_degree:
            for _ in range(steps):
                current_degree += 1
                self._move_servo(current_degree)
                time.sleep(0.01)
        elif degree < current_degree:
            for _ in range(steps):
                current_degree -= 1
                self._move_servo(current_degree)
                time.sleep(0.01)

    def _move_servo(self, degree):
        """
        Set degree position
        Args:
            degree (int):
        Returns:
            None
        """
        duty = int(
            scale_value(
                value=degree, in_min=0, in_max=self.max_degree, out_min=26, out_max=128
            )
        )
        self.pwm.duty(duty)

    def get_degree(self):
        """
        Get degree position
        Returns:
            Int: Position in degrees
        """
        _duty = self.pwm.duty()
        degree = int(
            scale_value(
                value=_duty, in_min=26, in_max=128, out_min=0, out_max=self.max_degree
            )
        )
        return degree
