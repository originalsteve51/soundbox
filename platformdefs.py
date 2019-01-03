import RPi.GPIO as GPIO


# depending on how the switches are wired, one of the following pairs of
# definitions should be used.

# if the button press connects to HIGH, use these
# pidevzero does this
BUTTON_ACTIVATED = GPIO.HIGH
BUTTON_PUD = GPIO.PUD_DOWN

# if the button press connects to LOW, use these
# fivebtns does this
#BUTTON_ACTIVATED = GPIO.HIGH
#BUTTON_PUD = GPIO.PUD_UP

# The ini file path name, this file must exist
SOUNDBOX_INI_FILE_PATH_NAME = '/home/pi/pizerodev/soundbox/soundbox.ini'

# Symbolic 'constants' for the Raspberry Pi pins where buttons are connected
BUTTON_WHITE    = 17 # ok
BUTTON_BLUE     = 27 # ok
BUTTON_GREEN    = 25 # ok
BUTTON_YELLOW   = 24 # ok
BUTTON_RED      = 5  # ok

# Symbolic 'constants' for the Raspberry Pi pins where LEDs are connected
LED_WHITE   = 20 # ok
LED_BLUE    = 16 # ok
LED_GREEN   = 12 # ok
LED_YELLOW  = 13 # ok
LED_RED     = 14 # ok

# Symbolic 'constants' for the Raspberry Pi pins used for the rotary switch
ROTARY_PIN_A        = 8  # CLK Pin   brown
ROTARY_PIN_B        = 15  # DT Pin   red
ROTARY_SWITCH_PIN   = 11 # Pushbutton Pin
