import _thread
import time

import utime
from machine import Pin

from esp_libs.hygrothermograph import Hygrothermograph
from esp_libs.lcd import I2cLcd
from esp_libs.servo import Servo
from esp_libs.stepmotor import Stepmotor, StepMotorDirectionOptions
from esp_libs.thermistor import Thermistor

# CONSTANTS
START_DATE = utime.localtime()

# GLOBAL VARIABLES
temperature = None
last_10_temperatures = []
humidity = None
current_date = None
final_date = 24

# DEVICES
# step motor to move the eggs
egg_movement_step_motor = Stepmotor(A=33, B=25, C=26, D=27)
# servo to open and close the extractor fan
extractor_fan_servo = Servo(pin_number=12, max_degree=180, freq=50, init_duty=0)
extractor_fan_servo.set_degree(degree=20)
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


def get_temperature(thermistor):
    try:
        temperature = thermistor.get_temperature()
        if isinstance(temperature, float):
            return temperature  
        else:
            # Log if temperature sensor is not found
            print("GET_TEMPERATURE: Value is not float: {}".format(temperature))
            return None
    except:
        # Log if temperature sensor is not found
        print("GET_TEMPERATURE: Temperature sensor not found")
        return None


def get_humidity(hygrothermograph):
    try:
        return hygrothermograph.get_humidity()
    except:
        # Log if hygrothermograph sensor is not found
        print("GET_HUMIDITY: Humidity sensor not found")
        return None


def run_get_temperature_and_humidity(thermistor, hygrothermograph):
    """
    Get the temperature and humidity from the sensors.

    Args:
        thermistor (Thermistor): The thermistor for temperature measurement.
        hygrothermograph (Hygrothermograph): The hygrothermograph for humidity measurement.

    Returns:
        None
    """
    global current_date, temperature, humidity, last_10_temperatures

    while True:
        lock.acquire()

        current_date = utime.localtime()

        temperature = get_temperature(thermistor)
        humidity = get_humidity(hygrothermograph)

        if temperature is not None:
            last_10_temperatures.append(temperature)

        # Keep only the last 10 temperatures
        if len(last_10_temperatures) > 10:
            last_10_temperatures.pop(0)
        
        lock.release()
        time.sleep(1)


def run_config_temperature(relay, temp_min=37, temp_max=38):
    """
    Control lights to maintain the temperature within a specified range.

    Args:
        relay (Pin): The relay pin for controlling the lights.
        temp_min (float): The minimum temperature threshold.
        temp_max (float): The maximum temperature threshold.

    Returns:
        None
    """
    global last_10_temperatures

    while True:
        lock.acquire()

        if len(last_10_temperatures) > 0:
            current_average_temp = (sum(last_10_temperatures) / len(last_10_temperatures))

            if current_average_temp < temp_min:
                # Turn off relay to use NC state, TURNING ON the lights
                print("RUN_CONFIG_TEMPERATURE: Turn on lights")
                relay.value(0)

            elif current_average_temp > temp_max:
                # Turn on relay to use NO state, TURNING OFF the lights
                print("RUN_CONFIG_TEMPERATURE: Turn off lights")
                relay.value(1)

        lock.release()
        time.sleep(1)


def run_config_extractor_fan(servo, min_humidity=60, max_humidity=70):
    """
    Control the extractor fan to maintain the humidity within a specified range.

    Args:
        servo (Servo): The servo for controlling the extractor fan.
        min_humidity (float): The minimum humidity threshold.
        max_humidity (float): The maximum humidity threshold.

    Returns:
        None
    """
    global humidity

    while True:
        time.sleep(10)
        lock.acquire()

        if humidity is not None:
            # open the exaustor fan proportionally to the humidity
            servo_position = int(
                ((humidity - min_humidity) / (max_humidity - min_humidity)) * (0 - 50)
                + 50
            )

            if servo_position < 0:
                # full open
                servo_position = 0
            elif servo_position > 50:
                # full close
                servo_position = 50

            servo.set_degree(degree=servo_position)
            print(
                f"RUN_CONFIG_EXTRACTOR_FAN: Servo position: {servo_position}, humidity: {humidity}"
            )
        
        else:
            servo.set_degree(degree=50)
            print(
                f"RUN_CONFIG_EXTRACTOR_FAN: Servo position: 50, humidity: Not Found"
            )

        lock.release()        


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
    global START_DATE, current_date, final_date

    while True:        
        time.sleep(3600)
        lock.acquire()

        count_day, *_ = time_diff(START_DATE, current_date)

        if count_day + 3 < final_date:
            step_motor.move_degree(StepMotorDirectionOptions.CLOCKWISE, 180)
        else:
            break

        lock.release()

    lock.release()


def run_show_basic_lcd_informations(lcd):
    """
    Display basic information on the LCD.

    Args:
        lcd (Lcd): The LCD display.

    Returns:
        None
    """
    global current_date, last_10_temperatures, humidity, temperature, final_date

    while True:
        lock.acquire()

        if current_date is None:
            lock.release()
            time.sleep(2)
            continue

        count_day, count_hour, count_minute = time_diff(START_DATE, current_date)

        # Display
        if temperature is None:
            temperature_str = "--.--"
        else:
            if temperature >= 100:
                temperature_str = "{:.1f}".format(temperature)
            elif temperature < 100 and temperature >= 10:
                temperature_str = "{:.2f}".format(temperature)
            else:
                temperature_str = "0{:.2f}".format(temperature)

        if humidity is None:
            humidity_str = "--.--"
        else:
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
            % (
                count_day,
                count_hour,
                count_minute,
                final_date - count_day,
            )
        )

        lock.release()
        time.sleep(10)


def main():
    """
    Main function.
    """
    _thread.start_new_thread(
        run_get_temperature_and_humidity, (thermistor_device, hygrothermograph_device)
    )
    _thread.start_new_thread(run_config_temperature, (lamp_relay,))
    _thread.start_new_thread(
        run_config_extractor_fan, (extractor_fan_servo, hygrothermograph_device)
    )
    _thread.start_new_thread(run_input_lcd_light, (lcd_light_button, lcd_device))
    _thread.start_new_thread(run_move_eggs, (egg_movement_step_motor,))
    _thread.start_new_thread(
        run_show_basic_lcd_informations,
        (lcd_device,),
    )

    # TEST
    # run_config_extractor_fan(servo=extractor_fan_servo)
    # run_show_basic_lcd_informations(lcd=lcd_device )
    # run_move_eggs(step_motor=egg_movement_step_motor)

    while True:
        pass


lock = _thread.allocate_lock()
if __name__ == "__main__":
    main()
