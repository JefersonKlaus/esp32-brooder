from dht import DHT11, DHT22
from machine import Pin


class HygrothermographTypeOptions:
    WHITE = 1
    BLUE = 2


class Hygrothermograph:
    dht = None

    def __init__(self, data_pin=13, type=HygrothermographTypeOptions.BLUE):
        if type == HygrothermographTypeOptions.BLUE:
            self.dht = DHT11(Pin(data_pin))
        elif type == HygrothermographTypeOptions.WHITE:
            self.dht = DHT22(Pin(data_pin))
        else:
            TypeError("type needs to be WHITE or BLUE")

    def get_temperature(self):
        self.dht.measure()
        return self.dht.temperature()

    def get_humidity(self):
        self.dht.measure()
        return self.dht.humidity()

    def get_temperature_and_humidity(self):
        self.dht.measure()
        return self.dht.temperature(), self.dht.humidity()
