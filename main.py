import _thread
import time
from machine import Pin

import utime

from esp_libs.hygrothermograph import Hygrothermograph
from esp_libs.lcd import I2cLcd
from esp_libs.servo import Servo
from esp_libs.stepmotor import Stepmotor, StepMotorDirectionOptions
from esp_libs.thermistor import Thermistor


def time_diff(first_date, second_date):
    """
    get the difference time between first and second data

    Args:
        first_date (int): First date int seconds, utime.localtime() is a example of method that return seconds
        second_date (int): Second date int seconds, utime.localtime() is a example of method that return seconds

    Returns:
        tuple: diff day, diff hour, diff minute
    """
    second_date += (1,) + (0,) * (8 - len(second_date))  # ensure a time past midnight
    first_date += (1,) + (0,) * (8 - len(first_date))

    _date_1 = utime.mktime(second_date)
    _date_2 = utime.mktime(first_date)

    _day_1 = _date_1 // (24 * 3600)
    _day_2 = _date_2 // (24 * 3600)
    diff_day = _day_1 - _day_2

    _hour_1 = (_date_1 - _day_1 * (24 * 3600)) // 3600
    _hour_2 = (_date_2 - _day_2 * (24 * 3600)) // 3600
    diff_hour = _hour_1 - _hour_2

    _min_1 = (_date_1 - (_day_1 * (24 * 3600) + _hour_1 * 3600)) // 60
    _min_2 = (_date_2 - (_day_2 * (24 * 3600) + _hour_2 * 3600)) // 60
    diff_min = _min_1 - _min_2

    return diff_day, diff_hour, diff_min


def run_config_temperature(relay, thermistor):
    """
    Turns the lights on or off to control the temperature
    Works seccond by seccond
    Args:
        relay (Pin):
        thermistor (Thermistor):
    Returns:
        None
    """
    list_last_temperatures = list()
    TEMP_MIN = 37
    TEMP_MAX = 38

    while True:
        lock.acquire()

        try:
            temperature = thermistor.get_temperature()
            list_last_temperatures.append(temperature)

            # keep only the last 3 temps
            if len(list_last_temperatures) > 10:
                list_last_temperatures.pop(0)

        except:
            pass

        _current_average_temp = sum(list_last_temperatures) / len(
            list_last_temperatures
        )

        if _current_average_temp < TEMP_MIN:
            # Turn off relay to use state NC turning on the lights
            relay.value(0)

        elif _current_average_temp > TEMP_MAX:
            # Turn on relay to use state NO turning off the lights
            relay.value(1)

        lock.release()
        time.sleep(1)


def run_input_lcd_light(button, lcd):
    """
    Turns the LCD lights on when the button is pressed
    Args:
        button (Pin):
        lcd (LCD):
    Returns:
        None
    """
    started_light = utime.localtime()
    lcd.backlight_on()

    while True:
        if not button.value():
            started_light = utime.localtime()
            lcd.backlight_on()

        if started_light is not None:
            _current_time = utime.localtime()
            _, _, count_minute = time_diff(started_light, _current_time)

            if count_minute >= 1:
                started_light = None
                lcd.backlight_off()


def run_show_basic_lcd_informations(hygrothermograph, thermistor, lcd):
    """
    Shows the LCD informations
    Args:
        hygrothermograph (Hygrothermograph):
        thermistor (Thermistor):
        lcd (Lcd):
    Returns:
        None
    """
    FINAL_DATE = 24
    started_date = utime.localtime()

    while True:
        lock.acquire()

        current_date = utime.localtime()
        count_day, count_hour, count_minute = time_diff(started_date, current_date)

        try:
            humidity = hygrothermograph.get_humidity()
        except:
            humidity = -1

        try:
            temperature = thermistor.get_temperature()
        except:
            temperature = -1

        # DISPLAY
        print_basic_lcd_information(
            lcd=lcd,
            temperature=temperature,
            humidity=humidity,
            count_day=count_day,
            count_hour=count_hour,
            count_minute=count_minute,
            day_to_finish=FINAL_DATE - count_day,
        )

        lock.release()
        time.sleep(1)


def print_basic_lcd_information(
    lcd, temperature, humidity, count_day, count_hour, count_minute, day_to_finish
):
    lcd.move_to(0, 0)
    lcd.put_str("T:%.2f  U:%.2f" % (temperature, humidity))

    lcd.move_to(0, 1)
    lcd.put_str(
        "D:%.2d T%.2d:%.2d F:%.2d"
        % (count_day, count_hour, count_minute, day_to_finish)
    )


# DEVICES
# step motor to move the eggs
# step_motor = Stepmotor(A=32, B=33, C=25, D=26)
# device to get temperature and humidity
hygrothermograph = Hygrothermograph(data_pin=18)
# display to show temperatura, humidity and time
lcd = I2cLcd(scl_pin=14, sda_pin=13)
# thermistor
thermistor = Thermistor(pin=36)
# relay
relay = Pin(2, Pin.OUT)
# lcd button
button = Pin(15, Pin.IN, Pin.PULL_UP)


def main():
    _thread.start_new_thread(run_input_lcd_light, (button, lcd))
    _thread.start_new_thread(run_config_temperature, (relay, thermistor))
    _thread.start_new_thread(
        run_show_basic_lcd_informations, (hygrothermograph, thermistor, lcd)
    )

    while True:
        pass


lock = _thread.allocate_lock()
if __name__ == "__main__":
    main()
