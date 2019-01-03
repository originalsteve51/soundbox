import time
import sys
import os
from os import listdir
import atexit
import signal

import configparser

import RPi.GPIO as GPIO
from threading import Thread
from threading import Event

from globaldefs import *
from platformdefs import *
from commandswitch import *
from ledflasher import *
from ledscanner import *
from buttonmonitor import *
from ledcontroller import *
from soundplayer import *

# main execution block starts here
if __name__ == '__main__':

    # Define functions used by main execution block

    # Convenience function to create and set an event
    def create_event_and_set():
        new_event = Event()
        new_event.set()
        return new_event

    # List all files (presumably sound files) alphabetically that are
    # in a specified directory
    def get_sound_file_list(from_dir_name):
        file_list = sorted(os.listdir(from_dir_name))

        # we have 5 buttons, so we need 5 things in this list or problems
        # ensue! it's ok to try to play a file with no name, but its not ok
        # to access the 4th element of a list with only three elements.
        while len(file_list)<5:
            file_list.append(' ')
        print(file_list)
        return file_list


    # Button press function to turn an LED on, signal the LEDScanner that
    # it should stop scanning (and not turn this particular LED off),
    # play the sound, turn off the LED after the sound plays, and signal
    # the LEDScanner to resume. The sound plays in an asynchronously
    # running subprocess, a handle to which is returned so we can interact
    # with it.
    def process_button_press(sound_player, led_id, led_scanner, event, sound_file):

        # a sound file can either be a real sound file, e.g. mp3, or it
        # can contain a url for an internet audio stream. the file extension
        # tells us which it is...
        if sound_file.endswith('.url'):
            url_file = open(sound_file, 'r')
            sound_file = url_file.read().rstrip()
            url_file.close()
            print('url from the sound file: ', sound_file)


        led_scanner.set_resume_led(led_id)
        GPIO.output(led_id, GPIO.HIGH)
        event.clear()
        p = sound_player.play_sound_file(sound_file, event, led_id)
        # sleep in case the user is holding the button down. this
        # prevents repeated button presses for the amount of time that we
        # sleep here. there must be a better way, but for now this will do.
        time.sleep(1.5)
        return p

    # When the program terminates in an orderly manner, reset the hardware so
    # it works properly if another program tries to use the GPIO.
    def reset_gpio():
        GPIO.cleanup()

    # When ending the program via ctrl-c (or other means) no threads should be
    # blocked so they can terminate. Otherwise they hang around.
    def release_all_threads():
        white_e.set()
        blue_e.set()
        green_e.set()
        yellow_e.set()
        red_e.set()

    def handle_exit():
        print('handle_exit called to assure GPIO cleanup')
        reset_gpio()


    # Create a map of the sections and options found in the ini file
    def config_section_map(config_parser, section):
        dict1 = {}
        options = config_parser.options(section)
        for option in options:
            try:
                dict1[option] = config_parser.get(section, option)
                if dict1[option] == -1:
                    DebugPrint("skip: %s" % option)
            except:
                print('exception on %s' % option)
                dict1[option] = None
        return dict1

    #-----------------------------------------------------------
    # Entry point, where execution begins...main execution block
    #-----------------------------------------------------------

    # at the very beginning, set up what happens at the very end.
    # we want to be sure the GPIO stuff is reset in the event the
    # program stops after a system kill process occurrence.
    atexit.register(handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)
    signal.signal(signal.SIGINT, handle_exit)

    # Obtain configuration options from the ini file.
    # Note that the soundbox-config program obtains a selection of
    # one out of five possible sound collections. This choice is written by
    # that program to the ini file that is read here. The 'selected_sound_dir'
    # in the ini file determines the sound collection used by the soundbox.
    #
    # Configurable roperties in the ini file are:
    #   sound_file_base_dir : the parent directory of the five sound
    #                         collection directories
    #   selected_sound_dir : the dir with the sound collection that is used
    #                        this is a dir named based on button colors, i.e.
    #                        the button pushed during soundbox-config
    #                        determines the directory used to get sounds
    #   vol_setting: value passed to omxplayer for initial volume
    #                 note--too high a volume causes distortion
    #   amp_setting: value passed to omxplayer that tries to deal with
    #                playback distortion. this is magic I don't really
    #                understand. type 'man omxplayer' and prepare to be
    #                amazed.
    if os.path.isfile(SOUNDBOX_INI_FILE_PATH_NAME):

        try:
            config = configparser.ConfigParser()
            config.read(SOUNDBOX_INI_FILE_PATH_NAME)


            # get configuration values related to file system usage
            lookup_map = config_section_map(config,'file_locations')
            sound_base_dir = lookup_map['sound_file_base_dir']
            selected_dir = lookup_map['selected_sound_dir']

            # get configuration values related to omxplayer usage
            lookup_map = config_section_map(config,'omxplayer_configuration')
            omx_ini_vol = lookup_map['vol_setting']
            omx_ini_amp = lookup_map['amp_setting']

        except Exception as ex:
            print('soundbox.ini file problem: ', ex)
            print('exiting now...')
            sys.exit(3)
    else:
        # if the ini file is missing, just stop. it is necessary.
        print('The soundbox.ini file is missing. exiting now...')
        sys.exit(2)


    # Volume and Amp settings used by omxplayer can optionally be passed
    # on the command line. Cmd line overrides any ini file settings.
    if len(sys.argv)==3:
        omx_vol_setting = sys.argv[1]
        omx_amp_setting = sys.argv[2]
        print('sound player settings from cmd line')
    else:
        if omx_ini_vol is not None and omx_ini_amp is not None:
            omx_vol_setting = omx_ini_vol
            omx_amp_setting = omx_ini_amp
            print('sound player settings from ini file')
        else:
            omx_vol_setting = OMX_VOL_SETTING_DEFAULT
            omx_amp_setting = OMX_AMP_SETTING_DEFAULT
            print('sound player default settings')
    print("--vol ",omx_vol_setting,"--amp ",omx_amp_setting)

    # Tell the GPIO subsystem we are using BCM numbering for the pins
    GPIO.setmode(GPIO.BCM)

    # Initialize button input pins as GPIO.HIGH when buttons are not pressed
    # The buttons are tied to ground, so input pins go GPIO.LOW when buttons
    # are pressed
    GPIO.setup(buttons, GPIO.IN, pull_up_down=BUTTON_PUD)

    # Initialize pins connected to LEDs as output pins
    GPIO.setup(leds, GPIO.OUT)


    # There are pull up resistors already in place on the rotary switch
    # assembly, so the two pins for it are simply configured as GPIO.IN
    GPIO.setup(ROTARY_PIN_A, GPIO.IN)
    GPIO.setup(ROTARY_PIN_B, GPIO.IN)

    # The push switch of the rotary switch assembly requires pull up
    # configuration as it does not have a built-in pull-up resistor
    GPIO.setup(ROTARY_SWITCH_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    # Create a set of events that will be signaled when buttons are pressed.
    # These are used to stop led scanning when a sound is played.
    white_e = create_event_and_set()
    blue_e = create_event_and_set()
    green_e = create_event_and_set()
    yellow_e = create_event_and_set()
    red_e = create_event_and_set()

    # Termination is triggered by the CommandSwitch. When terminating, the
    # scan of buttons in the main thread has to be blocked lest the
    # button press that ends things in command switch be acted on
    # by the main thread also.
    termination_event = create_event_and_set()

    # Create the sound_player, which plays one sound at a time. So if
    # a sound is being played and another sound is requested, playback
    # of the first sound is stopped and playback of the second one is started.
    sound_player = SoundPlayer(omx_vol_setting, omx_amp_setting)

    # Create the led scanner and start it on its own thread.
    # The button press events are passed to it so the main thread can
    # stop the led scan when a button is pressed.
    led_scanner = LEDScanner(white_e, blue_e, green_e, yellow_e, red_e)
    scannerThread = Thread(target=led_scanner.run)
    scannerThread.start()

    # Monitor the command switch (push button function of volume control)
    # on a separate thread.
    command_switch = CommandSwitch(sound_base_dir+'prompts/',
                                   termination_event,
                                   sound_player,
                                   led_scanner)
    command_thread = Thread(target=command_switch.process_switch_events)
    command_thread.start()

    sounds = get_sound_file_list(sound_base_dir+selected_dir)

    try:
        p = None
        terminate = False
        while not terminate:
            # Loop, scanning the five buttons awaiting a button press. When
            # a button is pressed, process it. The processing starts a
            # subprocess in which the sound plays. As it is a subprocess,
            # it runs asynchronously and we can immediately resume this
            # button scanning as the sound plays.
            if GPIO.input(BUTTON_WHITE) == BUTTON_ACTIVATED:
                termination_event.wait()
                print(sounds[0])
                p = process_button_press(sound_player, LED_WHITE, led_scanner, white_e,
                    sound_base_dir+selected_dir+'/'+sounds[0])
            if GPIO.input(BUTTON_BLUE) == BUTTON_ACTIVATED:
                termination_event.wait()
                print(sounds[1])
                p = process_button_press(sound_player, LED_BLUE, led_scanner, blue_e,
                    sound_base_dir+selected_dir+'/'+sounds[1])
            if GPIO.input(BUTTON_GREEN) == BUTTON_ACTIVATED:
                termination_event.wait()
                print(sounds[2])
                p = process_button_press(sound_player, LED_GREEN, led_scanner,green_e,
                    sound_base_dir+selected_dir+'/'+sounds[2])
            if GPIO.input(BUTTON_YELLOW) == BUTTON_ACTIVATED:
                termination_event.wait()
                print(sounds[3])
                p = process_button_press(sound_player, LED_YELLOW, led_scanner,yellow_e,
                    sound_base_dir+selected_dir+'/'+sounds[3])
            if GPIO.input(BUTTON_RED) == BUTTON_ACTIVATED:
                termination_event.wait()
                print(sounds[4])
                p = process_button_press(sound_player, LED_RED, led_scanner,red_e,
                    sound_base_dir+selected_dir+'/'+sounds[4])

            # While a sound is playing after a button press, we call
            # p.poll() each pass through the loop. This returns None as
            # long as the player subprocess continues running. When it
            # finally returns a value, the player subprocess is finished.
            # At that time we resume flashing the leds in sequence, which
            # the user will interpret to mean that a new sound can be
            # selected.
            if p is not None:
                rc = p.poll()
                if rc is not None:
                    print("Sound player has finished with rc: ", rc)
                    sound_player.close_player_process()
                    p = None
                    turnoff_all_leds()
                    release_all_threads()

            time.sleep(0.1)
    except IOError:
        print("An IOError occurred")
    except KeyboardInterrupt:
        print("Program ending after ctrl-c")
        terminate = True
        led_scanner.stop_scanning()
        VolumeControl.terminate = True
        CommandSwitch.terminate = True
#        release_all_threads()
    finally:
        if sound_player is not None:
            print("Closing the sound player")
            sound_player.close()
        print("Releasing any blocked threads...")
        print("Resetting GPIO buttons and LEDs...")

        reset_gpio()


