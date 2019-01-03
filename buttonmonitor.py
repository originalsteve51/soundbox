import RPi.GPIO as GPIO
import time

from globaldefs import *
from platformdefs import *

class ButtonMonitor(object):

    def __init__ (self, num_to_get):
        self.__num_to_get = num_to_get
        self.__count = 0
        self.__button_presses = []

    def button_event(self, button_id):

        print("button ", button_id, " pressed")

        if button_id==BUTTON_WHITE:
            led_id = LED_WHITE
        if button_id==BUTTON_BLUE:
            led_id = LED_BLUE
        if button_id==BUTTON_GREEN:
            led_id = LED_GREEN
        if button_id==BUTTON_YELLOW:
            led_id = LED_YELLOW
        if button_id==BUTTON_RED:
            led_id = LED_RED

        GPIO.output(led_id, GPIO.HIGH)
        time.sleep(1.0)

        self.__count = self.__count + 1
        self.__button_presses.append(button_id)

    def get_button_presses(self):
        for button in buttons:
            GPIO.add_event_detect (button, GPIO.FALLING,
                                   self.button_event, 300)

        while self.__count < self.__num_to_get:
            continue

        time.sleep(1.0)

        for button in buttons:
            GPIO.remove_event_detect (button)

        turnoff_all_leds()

        return self.__button_presses

