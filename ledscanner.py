import RPi.GPIO as GPIO
import time

from globaldefs import *
from platformdefs import *


# Class definition containing code to flash the LEDs in sequence. The run()
# function is executed on its own thread so the LEDs operate at the same time
# buttons are monitored by the main execution thread. Events corresponding to
# button presses are used to stop scanning when sounds are played.
class LEDScanner(object):

    # Time each LED remains on during the scanning
    FLASH_DELAY = 0.5

    def set_resume_led(self, led_id):
        self.resume_led = led_id

# Initialize button events that are signaled by the main thread
#    __white_button_event = None
#    __blue_button_event = None
#    __green_button_event = None
#    __yellow_button_event = None
#    __red_button_event = None
    # Initialize an instance of an LEDScanner
    def __init__(self, white_button_event, blue_button_event, green_button_event, yellow_button_event, red_button_event):
        self.__white_button_event = white_button_event
        self.__blue_button_event = blue_button_event
        self.__green_button_event = green_button_event
        self.__yellow_button_event = yellow_button_event
        self.__red_button_event = red_button_event
        self.resume_led = None
        self.__scanning = True

    def stop_scanning(self):
        self.__scanning = False

    # Function to flash an LED on and off. LEDs are not turned off when the
    # button event corresponding to the LED is cleared (i.e. unset). That's
    # because when the user presses a button, its light is supposed to stay
    # on until the button's action completes.
    def flash(self, led_code):
        if self.__scanning:
            if self.resume_led is None:
                GPIO.output(led_code, GPIO.HIGH)
                time.sleep(self.FLASH_DELAY)
            else:
                if self.resume_led == led_code:
                    GPIO.output(led_code, GPIO.HIGH)
                    self.resume_led = None
                    time.sleep(self.FLASH_DELAY)
            if led_code == LED_WHITE and self.__white_button_event.isSet():
                GPIO.output(led_code, GPIO.LOW)
            if led_code == LED_BLUE and self.__blue_button_event.isSet():
                GPIO.output(led_code, GPIO.LOW)
            if led_code == LED_GREEN and self.__green_button_event.isSet():
                GPIO.output(led_code, GPIO.LOW)
            if led_code == LED_YELLOW and self.__yellow_button_event.isSet():
                GPIO.output(led_code, GPIO.LOW)
            if led_code == LED_RED and self.__red_button_event.isSet():
                GPIO.output(led_code, GPIO.LOW)

    # Function to block execution whenever a button's event is in the clear
    # state, which signifies that the button was pressed and its action is not
    # yet finished.
    def check_buttons(self):
        self.__white_button_event.wait()
        self.__blue_button_event.wait()
        self.__green_button_event.wait()
        self.__yellow_button_event.wait()
        self.__red_button_event.wait()

    # Function where the scanner thread started by the main thread runs.
    def run(self):
        try:
            # Run forever, blinking the LEDs in sequence. Check after each
            # flash whether the sequential blinking should stop because
            # the user has pressed a button.
            while self.__scanning:
                self.check_buttons()
                self.flash(LED_WHITE)
                self.check_buttons()
                self.flash(LED_BLUE)
                self.check_buttons()
                self.flash(LED_GREEN)
                self.check_buttons()
                self.flash(LED_YELLOW)
                self.check_buttons()
                self.flash(LED_RED)
                self.check_buttons()
                self.flash(LED_YELLOW)
                self.check_buttons()
                self.flash(LED_GREEN)
                self.check_buttons()
                self.flash(LED_BLUE)
        except RuntimeError:
            print("Ignoring RuntimeError after terminating program")
