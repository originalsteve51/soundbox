import RPi.GPIO as GPIO
import time

from globaldefs import *
from platformdefs import *

class LEDFlasher(object):

    PAUSE_FLASH_DELAY = 0.25

    def __init__(self, led_id):
        self.__led_id = led_id
        self.__run_flag = True
        self.__flashing = False

    def stop_flashing(self):
        self.__run_flag = False

    def set_run_flag(self):
        self.__run_flag = True

    def is_flashing(self):
        return self.__flashing

    def flash_til_stopped(self):
        try:
            while self.__run_flag == True:
                self.__flashing = True
                GPIO.output(self.__led_id, GPIO.LOW)
                time.sleep(self.PAUSE_FLASH_DELAY)
                GPIO.output(self.__led_id, GPIO.HIGH)
                time.sleep(self.PAUSE_FLASH_DELAY)
                if self.__run_flag == False:
                    GPIO.output(self.__led_id, GPIO.LOW)
            self.__flashing = False

        except RuntimeError:
            print('Ignoring RuntimeError at shutdown (LEDFlasher)')


