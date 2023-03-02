import time

from machine import Pin

from .utils import scale_value


class StepMotorDirectionOptions:
    CLOCKWISE = 1
    COUNTER_CLOCKWISE = 2


class Stepmotor(object):
    _out = 0x01

    def __init__(self, A: int = 14, B: int = 27, C: int = 26, D: int = 25):
        self._A = Pin(A, Pin.OUT, 0)
        self._B = Pin(B, Pin.OUT, 0)
        self._C = Pin(C, Pin.OUT, 0)
        self._D = Pin(D, Pin.OUT, 0)

    def _motor_control(self, data):
        if data == 0x08:
            self._A.on()
            self._B.off()
            self._C.off()
            self._D.off()
        if data == 0x04:
            self._A.off()
            self._B.on()
            self._C.off()
            self._D.off()
        if data == 0x02:
            self._A.off()
            self._B.off()
            self._C.on()
            self._D.off()
        if data == 0x01:
            self._A.off()
            self._B.off()
            self._C.off()
            self._D.on()
        if data == 0x00:
            self._A.off()
            self._B.off()
            self._C.off()
            self._D.off()

    def move_one_step(self, direction):
        if direction == StepMotorDirectionOptions.CLOCKWISE:
            if self._out != 0x08:
                self._out = self._out << 1
            else:
                self._out = 0x01
        else:
            if direction == StepMotorDirectionOptions.COUNTER_CLOCKWISE:
                if self._out != 0x01:
                    self._out = self._out >> 1
                else:
                    self._out = 0x08
        self._motor_control(self._out)

    def move_steps(self, direction, steps, us=2000):
        for i in range(steps):
            self.move_one_step(direction)
            time.sleep_us(us)

    def move_around(self, direction, turns, us=2000):
        for i in range(turns):
            self.move_steps(direction, 32 * 64, us)

    def move_degree(self, direction, degree, us=2000):
        steps = scale_value(
            value=degree, in_min=0, in_max=360, out_min=0, out_max=32 * 64
        )
        self.move_steps(direction, steps, us)

    def stop(self):
        self._motor_control(0x00)
