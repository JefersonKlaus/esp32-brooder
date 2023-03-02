import math

from machine import ADC, Pin

from .utils import scale_value

"""
Thermistor
from thermistor import Thermistor
thermistor = Thermistor(pin=36)
print(thermistor.get_temperature())
"""


class Thermistor:
    adc = None

    def __init__(self, pin: int):
        self.adc = ADC(Pin(pin))
        self.adc.atten(ADC.ATTN_11DB)
        self.adc.width(ADC.WIDTH_12BIT)

    def get_temperature(self):
        adc_value = self.adc.read()
        voltage = adc_value / 4095 * 3.3
        rt = 10 * voltage / (3.3 - voltage)
        temp_k = 1 / (1 / (273.15 + 25) + (math.log(rt / 10)) / 3950)
        temp_c = temp_k - 273.15
        return temp_c
