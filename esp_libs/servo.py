import time

from machine import PWM, Pin

from .utils import scale_value

"""
from servo import Servo
servo = Servo(pin_number=15, max_degree=180, freq=50, nit_duty=0)
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

    def set_degree(self, degree):
        """
        Set degree position
        :param degree: int
        :return:
        """
        duty = int(
            scale_value(
                value=degree, in_min=0, in_max=self.max_degree, out_min=26, out_max=128
            )
        )
        self.pwm.duty(duty)
