import _thread
import time

import utime
from machine import Pin

from esp_libs.hygrothermograph import Hygrothermograph
from esp_libs.lcd import I2cLcd
from esp_libs.servo import Servo
from esp_libs.stepmotor import Stepmotor, StepMotorDirectionOptions
from esp_libs.thermistor import Thermistor

FINAL_DATE = 24
START_DATE = utime.localtime()


def time_diff(first_date, second_date):
    """
    Calculate the time difference between two dates in days, hours, and minutes.

    Args:
        first_date (int): The first date in seconds.
        second_date (int): The second date in seconds.

    Returns:
        tuple: A tuple containing the difference in days, hours, and minutes.
    """
    # Ensure both dates have a time past midnight
    second_date += (1,) + (0,) * (8 - len(second_date))
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


def run_config_temperature(relay, thermistor, temp_min=37, temp_max=38):
    """
    Control lights to maintain the temperature within a specified range.

    Args:
        relay (Pin): The relay pin for controlling the lights.
        thermistor (Thermistor): The thermistor for temperature measurement.
        temp_min (float): The minimum temperature threshold.
        temp_max (float): The maximum temperature threshold.

    Returns:
        None
    """
    list_last_temperatures = []

    while True:
        lock.acquire()

        try:
            temperature = thermistor.get_temperature()
            list_last_temperatures.append(temperature)

            # Keep only the last 10 temperatures
            if len(list_last_temperatures) > 10:
                list_last_temperatures.pop(0)

        except:
            # Log if temperature sensor is not found
            print("Temperature sensor not found")

        current_average_temp = sum(list_last_temperatures) / len(list_last_temperatures)

        if current_average_temp < temp_min:
            # Turn off relay to use NC state, turning on the lights
            relay.value(0)

        elif current_average_temp > temp_max:
            # Turn on relay to use NO state, turning off the lights
            relay.value(1)

        lock.release()
        time.sleep(1)


def run_config_extractor_fan(servo, hygrothermograph, min_humidity=60, max_humidity=70):
    """
    Control the extractor fan to maintain the humidity within a specified range.

    Args:
        servo (Servo): The servo for controlling the extractor fan.
        hygrothermograph (Hygrothermograph): The hygrothermograph for humidity measurement.
        min_humidity (float): The minimum humidity threshold.
        max_humidity (float): The maximum humidity threshold.

    Returns:
        None
    """
    while True:
        lock.acquire()

        try:
            humidity = hygrothermograph.get_humidity()
        except:
            # Log if humidity sensor is not found
            print("Humidity sensor not found")

        # open the exaustor fan proportionally to the humidity
        servo_position = int(
            ((humidity - min_humidity) / (max_humidity - min_humidity)) * (0 - 50) + 50
        )

        if servo_position < 0:
            # full open
            servo_position = 0
        elif servo_position > 50:
            # full close
            servo_position = 50

        servo.set_degree(degree=servo_position)

        lock.release()
        time.sleep(1)


def run_input_lcd_light(button, lcd):
    """
    Turn on the LCD backlight when the button is pressed.

    Args:
        button (Pin): The button pin.
        lcd (LCD): The LCD display.

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
            current_time = utime.localtime()
            _, _, count_minute = time_diff(started_light, current_time)

            if count_minute >= 1:
                started_light = None
                lcd.backlight_off()


def run_move_eggs(step_motor):
    """
    Move the eggs hourly.

    Args:
        step_motor (Stepmotor): The step motor.

    Returns:
        None
    """

    while True:
        lock.acquire()

        current_date = utime.localtime()
        count_day, *_ = time_diff(START_DATE, current_date)

        if count_day + 3 < FINAL_DATE:
            step_motor.move_degree(StepMotorDirectionOptions.CLOCKWISE, 180)
        else:
            break

        lock.release()
        time.sleep(3600)

    lock.release()


def run_show_basic_lcd_informations(hygrothermograph, thermistor, lcd):
    """
    Display basic information on the LCD.

    Args:
        hygrothermograph (Hygrothermograph): The hygrothermograph for humidity measurement.
        thermistor (Thermistor): The thermistor for temperature measurement.
        lcd (Lcd): The LCD display.

    Returns:
        None
    """
    while True:
        lock.acquire()

        current_date = utime.localtime()
        count_day, count_hour, count_minute = time_diff(START_DATE, current_date)

        try:
            humidity = hygrothermograph.get_humidity()
        except:
            humidity = -1

        try:
            temperature = thermistor.get_temperature()
        except:
            temperature = -1

        # Display
        _print_basic_lcd_information(
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


def _print_basic_lcd_information(
    lcd, temperature, humidity, count_day, count_hour, count_minute, day_to_finish
):
    """
    Format and show the informations on the LCD.

    Args:
        lcd (Lcd): The LCD display.
        temperature (float): The temperature.
        humidity (float): The humidity.
        count_day (int): The number of days.
        count_hour (int): The number of hours.
        count_minute (int): The number of minutes.
        day_to_finish (int): The number of days to finish.

    Returns:
        None
    """

    if temperature >= 100:
        temperature_str = "{:.1f}".format(temperature)
    elif temperature < 100 and temperature >= 10:
        temperature_str = "{:.2f}".format(temperature)
    else:
        temperature_str = "0{:.2f}".format(temperature)

    if humidity >= 100:
        humidity_str = "{:.1f}".format(humidity)
    elif humidity < 100 and humidity >= 10:
        humidity_str = "{:.2f}".format(humidity)
    else:
        humidity_str = "0{:.2f}".format(humidity)

    lcd.move_to(0, 0)
    lcd.put_str("T:{}  U:{}".format(temperature_str, humidity_str))

    lcd.move_to(0, 1)
    lcd.put_str(
        "D:%.2d T%.2d:%.2d F:%.2d"
        % (count_day, count_hour, count_minute, day_to_finish)
    )


# DEVICES
# step motor to move the eggs
egg_movement_step_motor = Stepmotor(A=33, B=25, C=26, D=27)
# servo to open and close the extractor fan
extractor_fan_servo = Servo(pin_number=12, max_degree=180, freq=50, init_duty=0)
extractor_fan_servo.set_degree(degree=0)
# device to get temperature and humidity
hygrothermograph_device = Hygrothermograph(data_pin=18)
# display to show temperatura, humidity and time
lcd_device = I2cLcd(scl_pin=14, sda_pin=13)
# thermistor
thermistor_device = Thermistor(pin=36)
# relay to control the lights
lamp_relay = Pin(2, Pin.OUT)
# lcd button
lcd_light_button = Pin(15, Pin.IN, Pin.PULL_UP)


def main():
    _thread.start_new_thread(run_input_lcd_light, (lcd_light_button, lcd_device))
    _thread.start_new_thread(run_config_temperature, (lamp_relay, thermistor_device))
    _thread.start_new_thread(
        run_config_extractor_fan, (extractor_fan_servo, hygrothermograph_device)
    )
    _thread.start_new_thread(
        run_show_basic_lcd_informations,
        (hygrothermograph_device, thermistor_device, lcd_device),
    )
    _thread.start_new_thread(run_move_eggs, (egg_movement_step_motor,))

    while True:
        pass


lock = _thread.allocate_lock()
if __name__ == "__main__":
    main()
