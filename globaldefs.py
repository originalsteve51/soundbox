import RPi.GPIO as GPIO
from platformdefs import *

# Command param signifying that a command pertains to ALL eligible entities
ALL = None

# ALSA sound device to use (see /etc/asound.conf)
# ALSA_DEVICE_NAME = 'speakerbonnet'
ALSA_DEVICE_NAME = 'default'

# ALSA mixer name
ALSA_MIXER_NAME = 'PCM'

# For convenience, make tuples for buttons and LEDs
buttons = (BUTTON_WHITE, BUTTON_BLUE, BUTTON_GREEN, BUTTON_YELLOW, BUTTON_RED)
leds = (LED_WHITE, LED_BLUE, LED_GREEN, LED_YELLOW, LED_RED)

# Let there NOT be light.
def turnoff_all_leds():
    GPIO.output(LED_WHITE, GPIO.LOW)
    GPIO.output(LED_BLUE, GPIO.LOW)
    GPIO.output(LED_GREEN, GPIO.LOW)
    GPIO.output(LED_YELLOW, GPIO.LOW)
    GPIO.output(LED_RED, GPIO.LOW)



