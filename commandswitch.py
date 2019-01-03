import RPi.GPIO as GPIO

import os

from globaldefs import *
from platformdefs import *

from ledscanner import *
from ledcontroller import *
from buttonmonitor import *

import time
import subprocess
from threading import Thread

class CommandSwitch(object):

    terminate = False

    def __init__(self, prompts_dir, termination_event, sound_player, led_scanner):
        self.__command_underway = False
        self.__prompts_dir = prompts_dir
        self.__termination_event = termination_event
        self.__sound_player = sound_player
        self.__led_scanner = led_scanner


    def process_switch_events(self):
        try:
            while not CommandSwitch.terminate:
                GPIO.wait_for_edge(ROTARY_SWITCH_PIN, GPIO.FALLING)
                print('control button pressed')

                if self.__sound_player.is_active():
                    # sound player is active, meaning a sound is playing

                    if self.__sound_player.is_paused():
                        # if paused and the button remains pressed...
                        time.sleep(1.0)
                        if GPIO.input(ROTARY_SWITCH_PIN) == GPIO.LOW:
                            # button was held down while playing/paused,
                            # stop this sound file and resume scanning
                            # awaiting a new sound choice
                            # sound player is paused, quit playing
                            self.__sound_player.quit_playing()
                        else:
                            p = self.__sound_player.toggle_playback()
                    else:
                        # sound playing, not paused
                        p = self.__sound_player.toggle_playback()
                else:
                    # Player is not active (leds are scanning)...
                    # Wait 2 seconds to see if command button remains pressed
                    time.sleep(2.0)
                    if GPIO.input(ROTARY_SWITCH_PIN) == GPIO.LOW:
                        # we are ending one way or another.
                        # prevent the main thread from starting a sound
                        self.__termination_event.clear()

                        # command button held down for 2 sec
                        # see if we shut down or go to configuration restart
                        turnoff_all_leds()
                        self.__led_scanner.stop_scanning()
                        turnoff_all_leds()

                        # shutdown-admin-resume.wav
                        #
                        # Soundbox is shutting down.
                        # Choose one of the three following options
                        # Press the red button to power down.
                        # or
                        # Press the green button to configure Soundbox and
                        # restart it
                        # or
                        # Press any other button to restart Soundbox
                        subprocess.Popen(['omxplayer',
                                        '-o','alsa:'+ALSA_DEVICE_NAME,
                                        self.__prompts_dir+'shutdown-admin-resume.wav'],
                                        stdin=subprocess.PIPE,
                                        stdout=None,stderr=None)

                        led_controller = LEDController(1000, (LED_GREEN, LED_RED))
                        led_thread = Thread(target=led_controller.run)
                        led_thread.start()


                        button_monitor = ButtonMonitor(1)
                        button_pattern = button_monitor.get_button_presses()

                        led_controller.go_dark()

                        if button_pattern[0] == BUTTON_GREEN:

                            led_controller.light_up(BUTTON_GREEN)
                            time.sleep(1.0)
                            print('restarting in config mode')
                            self.__sound_player.close()
                            os.system('sudo /etc/init.d/soundbox restart')

                        else:
                            if button_pattern[0] == BUTTON_RED:

                                print('shutting down now')
                                led_controller.light_up(BUTTON_RED)
                                time.sleep(1.0)
                                os.system('sudo shutdown now')

                            else:
                                os.system('sudo /etc/init.d/soundbox restart2')



#

                # sleep just a bit in case of switch bounce. this is because
                # we are using edge detection here, and if the switch bounces,
                # one press could cause two or more detectable edges.
                time.sleep(0.2)
        except Exception as ex:
            print('CommandSwitch: exception: ', ex)
