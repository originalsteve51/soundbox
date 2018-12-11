import time
import sys
import os
import signal
from os import listdir

import configparser

import RPi.GPIO as GPIO
from threading import Thread
from threading import Event


# Symbolic 'constants' for the Raspberry Pi pins where buttons are connected
BUTTON_WHITE    = 4
BUTTON_BLUE     = 17
BUTTON_GREEN    = 22
BUTTON_YELLOW   = 23
BUTTON_RED      = 27

# Symbolic 'constants' for the Raspberry Pi pins where LEDs are connected
LED_WHITE   = 16
LED_BLUE    = 25
LED_GREEN   = 13
LED_YELLOW  = 12
LED_RED     = 24

# Command param signifying that a command pertains to ALL eligible entities
ALL = None

SOUND_HOME_DIR = "/home/pi/soundbox/drop_zone"

DIR_WHITE   = SOUND_HOME_DIR + "/white"
DIR_BLUE    = SOUND_HOME_DIR + "/blue"
DIR_GREEN   = SOUND_HOME_DIR + "/green"
DIR_YELLOW  = SOUND_HOME_DIR + "/yellow"
DIR_RED     = SOUND_HOME_DIR + "/red"

DIR_PROMPTS = SOUND_HOME_DIR + "/prompts/"

# Lists that are handy when setting and changing things
buttons = (BUTTON_WHITE, BUTTON_BLUE, BUTTON_GREEN, BUTTON_YELLOW, BUTTON_RED)
leds = (LED_WHITE, LED_BLUE, LED_GREEN, LED_YELLOW, LED_RED)

def create_event_and_set():
    new_event = Event()
    new_event.set()
    return new_event

def authenticate(entered_list, accepted_list):
    return entered_list == accepted_list

class LEDController(object):

    def __init__(self, num_dimming_cycles):
        self.__keep_running = True
        # Store the number of dark-->light-->dark cycles before
        # five second countdown to termination
        self.__num_dimming_cycles = num_dimming_cycles

        # Pulse-width modulation @ 100 Hz for dimming effect
        self.__pwm_white   = GPIO.PWM(LED_WHITE, 100)
        self.__pwm_blue    = GPIO.PWM(LED_BLUE, 100)
        self.__pwm_green   = GPIO.PWM(LED_GREEN, 100)
        self.__pwm_yellow  = GPIO.PWM(LED_YELLOW, 100)
        self.__pwm_red     = GPIO.PWM(LED_RED, 100)

        # LEDs fully dimmed to start
        self.__pwm_white.start(0)
        self.__pwm_blue.start(0)
        self.__pwm_green.start(0)
        self.__pwm_yellow.start(0)
        self.__pwm_red.start(0)

    def flash(self, button_id, count):
        self.go_dark()

        duty_cycle = 100

        for counter in range(0, count*2):
            counter += 1
            if (button_id == BUTTON_WHITE):
                self.__pwm_white.ChangeDutyCycle(duty_cycle)
            if (button_id == BUTTON_BLUE):
                self.__pwm_blue.ChangeDutyCycle(duty_cycle)
            if (button_id == BUTTON_GREEN):
                self.__pwm_green.ChangeDutyCycle(duty_cycle)
            if (button_id == BUTTON_YELLOW):
                self.__pwm_yellow.ChangeDutyCycle(duty_cycle)
            if (button_id == BUTTON_RED):
                self.__pwm_red.ChangeDutyCycle(duty_cycle)
            if duty_cycle == 0:
                duty_cycle = 100
            else:
                duty_cycle = 0
            time.sleep(0.5)


    def light_up(self, button_id):
        if (button_id == BUTTON_WHITE):
            self.__pwm_white.ChangeDutyCycle(100)
        if (button_id == BUTTON_BLUE):
            self.__pwm_blue.ChangeDutyCycle(100)
        if (button_id == BUTTON_GREEN):
            self.__pwm_green.ChangeDutyCycle(100)
        if (button_id == BUTTON_YELLOW):
            self.__pwm_yellow.ChangeDutyCycle(100)
        if (button_id == BUTTON_RED):
            self.__pwm_red.ChangeDutyCycle(100)

    def change_duty_cycle(self, time_on, pwm_obj):
        if pwm_obj is None:
            # Change all of them
            self.__pwm_white.ChangeDutyCycle(time_on)
            self.__pwm_blue.ChangeDutyCycle(time_on)
            self.__pwm_green.ChangeDutyCycle(time_on)
            self.__pwm_yellow.ChangeDutyCycle(time_on)
            self.__pwm_red.ChangeDutyCycle(time_on)
        else:
            # Change the specific pwm that was passed
            pwm_obj.ChangeDutyCycle(time_on)

    def go_dark(self):
        time_on = 0
        self.__pwm_white.ChangeDutyCycle(time_on)
        self.__pwm_blue.ChangeDutyCycle(time_on)
        self.__pwm_green.ChangeDutyCycle(time_on)
        self.__pwm_yellow.ChangeDutyCycle(time_on)
        self.__pwm_red.ChangeDutyCycle(time_on)

    def stop_cycling(self):
        self.__keep_running = False


    def close(self):
        self.__pwm_white.stop()
        self.__pwm_blue.stop()
        self.__pwm_green.stop()
        self.__pwm_yellow.stop()
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
        if self.__keep_running:
            time.sleep(1.0)
            self.change_duty_cycle(0, self.__pwm_white)
        if self.__keep_running:
            time.sleep(1.0)
            self.change_duty_cycle(0, self.__pwm_blue)
        if self.__keep_running:
            time.sleep(1.0)
            self.change_duty_cycle(0, self.__pwm_green)
        if self.__keep_running:
            time.sleep(1.0)
            self.change_duty_cycle(0, self.__pwm_yellow)
        if self.__keep_running:
            time.sleep(1.0)
            self.change_duty_cycle(0, self.__pwm_red)

        if self.__keep_running:
            # Countdown is completed without correct button-press
            # combination being detected. Exit now...
            os.kill(os.getpid(), signal.SIGINT)

class ButtonMonitor(object):

    def __init__ (self, num_to_get, led_controller):
        self.__num_to_get = num_to_get
        self.__count = 0
        self.__button_presses = []
        self.__led_controller = led_controller
        print('press ', num_to_get, ' buttons')

    # flash the led corresponding to the button color
    # start flag signifies whether to start or stop flashing
    def flash(self, button_id, count):
        self.__led_controller.flash(button_id, count)

    def button_event(self, button_id):

        if len(self.__button_presses) == 0:
            self.__led_controller.go_dark()
            self.__led_controller.stop_cycling()

        print("button ", button_id, " pressed")

        if button_id==BUTTON_WHITE:
            led_controller.light_up(BUTTON_WHITE)
        if button_id==BUTTON_BLUE:
            led_controller.light_up(BUTTON_BLUE)
        if button_id==BUTTON_GREEN:
            led_controller.light_up(BUTTON_GREEN)
        if button_id==BUTTON_YELLOW:
            led_controller.light_up(BUTTON_YELLOW)
        if button_id==BUTTON_RED:
            led_controller.light_up(BUTTON_RED)


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


        return self.__button_presses





if __name__ == '__main__':


    try:

        GPIO.setmode(GPIO.BCM)
        for button in buttons:
            GPIO.setup(button, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # Initialize pins connected to LEDs as output pins
        GPIO.setup(leds, GPIO.OUT)

        # Run the LEDs through their paces. They provide a countdown for
        # the user so s/he knows how long they have to enter a button pattern
        # that lets them do some configuration.
        # Example: Authorized user has to enter pattern red-white-blue in
        # that order to configure system. If this is not entered in time, the
        # soundbox starts in user mode.
        os.system('omxplayer -o alsa:hifiberry --vol 300 '+DIR_PROMPTS+'enter-passcode-pattern.wav')

        led_controller = LEDController(5)
        led_thread = Thread(target=led_controller.run)
        led_thread.start()

        button_monitor = ButtonMonitor(3, led_controller)
        button_pattern = button_monitor.get_button_presses()

        accept_pattern = [BUTTON_RED, BUTTON_WHITE, BUTTON_BLUE]

        if authenticate(button_pattern, accept_pattern):

            os.system('omxplayer -o alsa:hifiberry --vol 300 '+DIR_PROMPTS+'choose-sound-group.wav')

            print ('proper buttons were pressed')
            time.sleep(1.0)
            led_controller.go_dark()

            button_monitor = ButtonMonitor(1, led_controller)
            buttons_pressed = button_monitor.get_button_presses()

            if buttons_pressed[0]==BUTTON_WHITE:
                selected_dir = 'white'
            if buttons_pressed[0]==BUTTON_BLUE:
                selected_dir = 'blue'
            if buttons_pressed[0]==BUTTON_GREEN:
                selected_dir = 'green'
            if buttons_pressed[0]==BUTTON_YELLOW:
                selected_dir = 'yellow'
            if buttons_pressed[0]==BUTTON_RED:
                selected_dir = 'red'

            print('selection made by user: ', selected_dir)

            config = configparser.ConfigParser()
            config.read('/home/pi/soundbox/soundbox.ini')
            cfgfile = open('/home/pi/soundbox/soundbox.ini', 'w')
            config.set('file_locations', 'selected_sound_dir', selected_dir)
            config.write(cfgfile)
            cfgfile.close()


            os.system('omxplayer -o alsa:hifiberry --vol 300 '+DIR_PROMPTS+'wifi-or-access-pt.wav')
            button_monitor = ButtonMonitor(1, led_controller)
            buttons_pressed = button_monitor.get_button_presses()

            if buttons_pressed[0]==BUTTON_GREEN:
                # call start_ap.sh to configure soundbox as an access point

                os.system('omxplayer -o alsa:hifiberry --vol 300 '+DIR_PROMPTS+'access-point-enabled.wav')
                os.system('cd /home/pi/soundbox')
                os.system('sudo ./start_ap.sh')
                os.system('sudo reboot')
            else:
                if buttons_pressed[0]==BUTTON_RED:
                    print('call stopap to configure soundbox to use available WiFi')
                    os.system('omxplayer -o alsa:hifiberry --vol 300 '+DIR_PROMPTS+'wifi-enabled.wav')
                    os.system('cd /home/pi/soundbox')
                    os.system('sudo ./stop_ap.sh')
                    os.system('sudo reboot')
                else:
                    os.system('omxplayer -o alsa:hifiberry --vol 300 '+DIR_PROMPTS+'connection-mode-unchanged.wav')
        else:
            os.system('omxplayer -o alsa:hifiberry --vol 300 '+DIR_PROMPTS+'invalid-passcode.wav')

    # If keyboard Interrupt (CTRL-C) is pressed
    except KeyboardInterrupt:
        print('Program terminated')
    finally:
        print('Freeing up system resources')
        GPIO.cleanup()
