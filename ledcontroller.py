import RPi.GPIO as GPIO
import time

from globaldefs import *
from platformdefs import *

class LEDController(object):

    def __init__(self, num_dimming_cycles, led_ids):
        self.__led_ids = led_ids
        self.__keep_running = True
        # Store the number of dark-->light-->dark cycles before
        # five second countdown to termination
        self.__num_dimming_cycles = num_dimming_cycles

        # Pulse-width modulation @ 50 Hz for dimming effect
        if LED_WHITE in self.__led_ids:
            self.__pwm_white   = GPIO.PWM(LED_WHITE, 50)
            self.__pwm_white.start(0)
        if LED_BLUE in self.__led_ids:
            self.__pwm_blue    = GPIO.PWM(LED_BLUE, 50)
            self.__pwm_blue.start(0)
        if LED_GREEN in self.__led_ids:
            self.__pwm_green   = GPIO.PWM(LED_GREEN, 50)
            self.__pwm_green.start(0)
        if LED_YELLOW in self.__led_ids:
            self.__pwm_yellow  = GPIO.PWM(LED_YELLOW, 50)
            self.__pwm_yellow.start(0)
        if LED_RED in self.__led_ids:
            self.__pwm_red     = GPIO.PWM(LED_RED, 50)
            self.__pwm_red.start(0)

        # LEDs fully dimmed to start

    def flash(self, button_id, count):

        self.go_dark()

        duty_cycle = 100

        for counter in range(0, count*2):
            counter += 1
            if button_id == BUTTON_WHITE and LED_WHITE in self.__led_ids:
                self.__pwm_white.ChangeDutyCycle(duty_cycle)
            if button_id == BUTTON_BLUE  and LED_BLUE in self.__led_ids:
                self.__pwm_blue.ChangeDutyCycle(duty_cycle)
            if button_id == BUTTON_GREEN and LED_GREEN in self.__led_ids:
                self.__pwm_green.ChangeDutyCycle(duty_cycle)
            if button_id == BUTTON_YELLOW and LED_YELLOW in self.__led_ids:
                self.__pwm_yellow.ChangeDutyCycle(duty_cycle)
            if button_id == BUTTON_RED and LED_RED in self.__led_ids:
                self.__pwm_red.ChangeDutyCycle(duty_cycle)
            if duty_cycle == 0:
                duty_cycle = 100
            else:
                duty_cycle = 0
            time.sleep(0.5)


    def light_up(self, button_id):
        if button_id == BUTTON_WHITE and LED_WHITE in self.__led_ids:
            self.__pwm_white.ChangeDutyCycle(100)
        if button_id == BUTTON_BLUE and LED_BLUE in self.__led_ids:
            self.__pwm_blue.ChangeDutyCycle(100)
        if button_id == BUTTON_GREEN and LED_GREEN in self.__led_ids:
            self.__pwm_green.ChangeDutyCycle(100)
        if button_id == BUTTON_YELLOW and LED_YELLOW in self.__led_ids:
            self.__pwm_yellow.ChangeDutyCycle(100)
        if button_id == BUTTON_RED and LED_RED in self.__led_ids:
            self.__pwm_red.ChangeDutyCycle(100)

    def change_duty_cycle(self, time_on, pwm_obj):
        if pwm_obj is None:
            # Change all of them
            if LED_WHITE in self.__led_ids:
                self.__pwm_white.ChangeDutyCycle(time_on)
            if LED_BLUE in self.__led_ids:
                self.__pwm_blue.ChangeDutyCycle(time_on)
            if LED_GREEN in self.__led_ids:
                self.__pwm_green.ChangeDutyCycle(time_on)
            if LED_YELLOW in self.__led_ids:
                self.__pwm_yellow.ChangeDutyCycle(time_on)
            if LED_RED in self.__led_ids:
                self.__pwm_red.ChangeDutyCycle(time_on)
        else:
            # Change the specific pwm that was passed
            pwm_obj.ChangeDutyCycle(time_on)

    def go_dark(self):
        time_on = 0
        self.stop_cycling()
        if LED_WHITE in self.__led_ids:
            self.__pwm_white.ChangeDutyCycle(time_on)
        if LED_BLUE in self.__led_ids:
            self.__pwm_blue.ChangeDutyCycle(time_on)
        if LED_GREEN in self.__led_ids:
            self.__pwm_green.ChangeDutyCycle(time_on)
        if LED_YELLOW in self.__led_ids:
            self.__pwm_yellow.ChangeDutyCycle(time_on)
        if LED_RED in self.__led_ids:
            self.__pwm_red.ChangeDutyCycle(time_on)

    def stop_cycling(self):
        self.__keep_running = False


    def close(self):

        if LED_WHITE in self.__led_ids:
            self.__pwm_white.stop()
        if LED_BLUE in self.__led_ids:
            self.__pwm_blue.stop()
        if LED_GREEN in self.__led_ids:
            self.__pwm_green.stop()
        if LED_YELLOW in self.__led_ids:
            self.__pwm_yellow.stop()
        if LED_RED in self.__led_ids:
            self.__pwm_red.stop()
        self.__keep_running = False


    def run(self):
        for cycle_count in range(self.__num_dimming_cycles):
            if not self.__keep_running:
                break
            for on_time in range(100):
                if not self.__keep_running:
                    break
                self.change_duty_cycle(on_time, ALL)
                time.sleep(0.01)

            for on_time in range(100,0,-1):
                if not self.__keep_running:
                    break
                self.change_duty_cycle(on_time, ALL)
                time.sleep(0.01)
        # Done with dimming cycles. Now countdown...
        # First bring up the lights again...
        for on_time in range(100):
            if not self.__keep_running:
                break
            self.change_duty_cycle(on_time, ALL)
            time.sleep(0.01)

        # All are fully lit now...
        # Shut them off one by one, on one second intervals
        if self.__keep_running and LED_WHITE in self.__led_ids:
            time.sleep(1.0)
            self.change_duty_cycle(0, self.__pwm_white)
        if self.__keep_running and LED_BLUE in self.__led_ids:
            time.sleep(1.0)
            self.change_duty_cycle(0, self.__pwm_blue)
        if self.__keep_running and LED_GREEN in self.__led_ids:
            time.sleep(1.0)
            self.change_duty_cycle(0, self.__pwm_green)
        if self.__keep_running and LED_YELLOW in self.__led_ids:
            time.sleep(1.0)
            self.change_duty_cycle(0, self.__pwm_yellow)
        if self.__keep_running and LED_RED in self.__led_ids:
            time.sleep(1.0)
            self.change_duty_cycle(0, self.__pwm_red)

        if self.__keep_running:
            # Countdown is completed without correct button-press
            # combination being detected. Exit now...
            os.kill(os.getpid(), signal.SIGINT)
