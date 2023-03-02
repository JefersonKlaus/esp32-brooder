import _thread
import time

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


def get_air_flow_correction(list_last_temperatures, current_correction):
    """
    Args:
        list_last_temperatures (list):
        current_correction (int):
    Returns:
        int: return the new air flow correction
    """
    _CORRETION_VALUE = 5
    if (sum(list_last_temperatures) / len(list_last_temperatures)) > 38:
        return current_correction + _CORRETION_VALUE
    elif (sum(list_last_temperatures) / len(list_last_temperatures)) < 37:
        return current_correction - _CORRETION_VALUE
    else:
        return current_correction


def config_air_outlet_opening(servo, temperature, correction=0):
    """
    Change the position of the servo motor to control the temperature
    Args:
        servo (Servo):
        temperature (float):
        correction (int):
    Returns:
        None
    """
    if temperature < 37.7:
        servo.set_degree(degree=(correction if correction >= 0 else 0))
    elif temperature >= 37.7 and temperature < 37.9:
        _degree = 15 + correction
        _degree = max(0, _degree)
        servo.set_degree(degree=_degree if _degree <= 90 else 90)
    elif temperature >= 37.9 and temperature < 38.1:
        _degree = 30 + correction
        _degree = max(0, _degree)
        servo.set_degree(degree=_degree if _degree <= 90 else 90)
    elif temperature >= 38.1 and temperature < 39:
        _degree = 45 + correction
        _degree = max(0, _degree)
        servo.set_degree(degree=_degree if _degree <= 90 else 90)
    elif temperature >= 39:
        servo.set_degree(degree=90 + (correction if correction <= 0 else 0))


def show_basic_lcd_information(
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
# servo to temperature control
servo = Servo(pin_number=12)
servo.set_degree(degree=0)
# step motor to move the eggs
step_motor = Stepmotor(A=32, B=33, C=25, D=26)
# device to get temperature and humidity
hygrothermograph = Hygrothermograph(data_pin=18)
# display to show temperatura, humidity and time
lcd = I2cLcd(scl_pin=14, sda_pin=13)
# thermistor
thermistor = Thermistor(pin=36)
# lcd.backlight_off()
lcd.backlight_on()


def main():
    # _thread.start_new_thread(get_temperature, (hygrothermograph,))
    # _thread.start_new_thread(get_humidity, (hygrothermograph,))
    DATE_CONTROL = {"INIT_AIR_FLOW": 0, "STOP_SPINNING": 21, "FINAL_DATE": 24}
    started_date = utime.localtime()
    control_eggs_moved = False

    list_last_temperatures = list()
    air_flow_correction = 0
    last_minute_checked_air_flow_correction = 0

    while True:
        # calculate how long it's been working
        current_date = utime.localtime()
        count_day, count_hour, count_minute = time_diff(started_date, current_date)

        # get data from sensors
        try:
            humidity = hygrothermograph.get_humidity()
        except:
            humidity = -1

        try:
            temperature = thermistor.get_temperature()
            list_last_temperatures.append(temperature)

            # keep only the last 30 temps
            if len(list_last_temperatures) > 30:
                list_last_temperatures.pop(0)

        except:
            temperature = -1

        # get the correction to air flow
        if last_minute_checked_air_flow_correction != count_minute:
            air_flow_correction = get_air_flow_correction(
                list_last_temperatures=list_last_temperatures,
                current_correction=air_flow_correction,
            )
            last_minute_checked_air_flow_correction = count_minute

        # AIR FLOW
        if count_day >= DATE_CONTROL.get("INIT_AIR_FLOW"):
            config_air_outlet_opening(
                servo=servo, temperature=temperature, correction=air_flow_correction
            )

        # TODO: implement when the engine for moving the eggs is ready
        # # EGGS MOVIMENT CONTROL
        # if (count_minute == 0 or count_minute == 30) and count_day <= DATE_CONTROL.get(
        #     "STOP_SPINNING"
        # ):
        #     if control_eggs_moved == False:
        #         step_motor.move_degree(
        #             direction=StepMotorDirectionOptions.CLOCKWISE, degree=180
        #         )
        #         step_motor.stop()
        #         control_eggs_moved = True
        # else:
        #     # set to False for next hour to be moved
        #     control_eggs_moved = False

        # DISPLAY
        show_basic_lcd_information(
            lcd=lcd,
            temperature=temperature,
            humidity=humidity,
            count_day=count_day,
            count_hour=count_hour,
            count_minute=count_minute,
            day_to_finish=DATE_CONTROL.get("FINAL_DATE") - count_day,
        )

        time.sleep(1)


# lock = _thread.allocate_lock()
if __name__ == "__main__":
    main()
