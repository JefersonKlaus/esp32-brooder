import time

from machine import Pin

from .utils import scale_value


class StepMotorDirectionOptions:
    CLOCKWISE = 1
    COUNTER_CLOCKWISE = 2


class Stepmotor(object):
    """
    The stator in the Stepper Motor we have supplied has 32 magnetic poles. Therefore, to complete one full
    revolution requires 32 full steps. The rotor (or output shaft) of the Stepper Motor is connected to a speed
    reduction set of gears and the reduction ratio is 1:64. Therefore, the final output shaft (exiting the Stepper
    Motor’s housing) requires 32 X 64 = 2048 steps to make one full revolution."""

    _out = 0x01

    def __init__(self, A: int = 14, B: int = 27, C: int = 26, D: int = 25):
        """
        Initializes the Stepmotor class.

        Args:
            A (int): Pin for motor A (default: 14).
            B (int): Pin for motor B (default: 27).
            C (int): Pin for motor C (default: 26).
            D (int): Pin for motor D (default: 25).
        """
        self._A = Pin(A, Pin.OUT, 0)
        self._B = Pin(B, Pin.OUT, 0)
        self._C = Pin(C, Pin.OUT, 0)
        self._D = Pin(D, Pin.OUT, 0)

    def _motor_control(self, data):
        """
        Controls the stepper motor based on the provided data.

        Args:
            data: Motor control data.
        """
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
        """
        Moves the stepper motor one step in the specified direction.

        Args:
            direction: Direction of movement (StepMotorDirectionOptions.CLOCKWISE or StepMotorDirectionOptions.COUNTER_CLOCKWISE).
        """
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
        """
        Moves the stepper motor a specific number of steps in the specified direction.

        Args:
            direction: Direction of movement (StepMotorDirectionOptions.CLOCKWISE or StepMotorDirectionOptions.COUNTER_CLOCKWISE).
            steps: Number of steps to move.
            us: Delay in microseconds between each step. From 2k to 40k (default: 2000).
        """
        for i in range(steps):
            self.move_one_step(direction)
            time.sleep_us(us)

    def move_around(self, direction, turns, us=2000):
        """
        Moves the stepper motor a specific number of full turns in the specified direction.

        Args:
            direction: Direction of movement (StepMotorDirectionOptions.CLOCKWISE or StepMotorDirectionOptions.COUNTER_CLOCKWISE).
            turns: Number of full turns to move.
            us: Delay in microseconds between each step. From 2k to 40k (default: 2000).
        """
        for i in range(turns):
            self.move_steps(direction, 32 * 64, us)

    def move_degree(self, direction, degree, us=2000):
        """
        Moves the stepper motor to a specific angle in the specified direction.

        Args:
            direction: Direction of movement (StepMotorDirectionOptions.CLOCKWISE or StepMotorDirectionOptions.COUNTER_CLOCKWISE).
            degree: Angle to move the motor to (0 to 360 degrees).
            us: Delay in microseconds between each step. From 2k to 40k (default: 2000).
        """
        steps = scale_value(
            value=degree, in_min=0, in_max=360, out_min=0, out_max=32 * 64
        )
        self.move_steps(direction, steps, us)

    def stop(self):
        "After all moviments use this method to turn off the step motor"
        self._motor_control(0x00)
