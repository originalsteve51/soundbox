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


# Following are used only by SoundPlayer
import subprocess
import alsaaudio


# The ini file must exist
SOUNDBOX_INI_FILE_PATH_NAME = '/home/pi/soundbox/soundbox.ini'

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

# Symbolic 'constants' for the Raspberry Pi pins used for the rotary switch
ROTARY_PIN_A        = 20     # CLK Pin
ROTARY_PIN_B        = 6      # DT Pin
ROTARY_SWITCH_PIN   = 5 # Button Pin

# Values used when command line overrides are not supplied and
# soundbox.ini values are not present
OMX_VOL_SETTING_DEFAULT = '0'
OMX_AMP_SETTING_DEFAULT = '2500'

VOLUME_DELTA = 5


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


class VolumeControl(object):

    terminate = False

    def __init__(self, sound_player):
        self.__sound_player = sound_player
        self.globalCounter = 0
        self.flag = 0
        self.Last_RoB_Status = 0
        self.Current_RoB_Status = 0

        # alsa /etc/asound.conf defines the name 'Master'
        self.__mixer = alsaaudio.Mixer('Master')

    def close(self):
        if self.__mixer is not None:
            rc = self.__mixer.close()
            print ('ALSA Master mixer closed with rc =', rc)

    def rotate(self):

        self.Last_RoB_Status = GPIO.input(ROTARY_PIN_B)

        while(not GPIO.input(ROTARY_PIN_A)):
            self.Current_RoB_Status = GPIO.input(ROTARY_PIN_B)
            self.flag = 1

        if self.flag == 1:
            self.flag = 0
            if (self.Last_RoB_Status == 0) and (self.Current_RoB_Status == 1):
                self.globalCounter = self.globalCounter + 1
            if (self.Last_RoB_Status == 1) and (self.Current_RoB_Status == 0):
                self.globalCounter = self.globalCounter - 1

    def loop(self):
        tmp = 0
        try:
            while not VolumeControl.terminate:
                self.rotate()
                if tmp != self.globalCounter:
                    current_volume = self.__mixer.getvolume()[0]
                    print('current volume = ', current_volume)
                    if tmp > self.globalCounter:
                        # increase volume up to 100 max
                        new_volume = current_volume + VOLUME_DELTA
                        if new_volume > 100:
                            new_volume = 100
                        print('increase to ', new_volume)
                        self.__mixer.setvolume(new_volume)
                    else:
                        # decrease volume down to 0 min
                        new_volume = current_volume - VOLUME_DELTA
                        if new_volume < 0:
                            new_volume = 0
                        print('decrease to ', new_volume)
                        self.__mixer.setvolume(new_volume)
                    tmp = self.globalCounter
        except RuntimeError:
            print('Ignoring RuntimeError at shutdown (VolumeControl)')

class CommandSwitch(object):

    terminate = False

    def __init__(self, prompts_dir, termination_event):
        self.__command_underway = False
        self.__prompts_dir = prompts_dir
        self.__termination_event = termination_event

    def process_switch_events(self):
        try:
            while not CommandSwitch.terminate:
                GPIO.wait_for_edge(ROTARY_SWITCH_PIN, GPIO.FALLING)
                print('control button pressed')

                if sound_player.is_active():
                    # sound player is active, meaning a sound is playing

                    if sound_player.is_paused():
                        # if paused and the button remains pressed...
                        time.sleep(1.0)
                        if GPIO.input(ROTARY_SWITCH_PIN) == GPIO.LOW:
                            # button was held down while playing/paused,
                            # stop this sound file and resume scanning
                            # awaiting a new sound choice
                            # sound player is paused, quit playing
                            sound_player.quit_playing()
                        else:
                            p = sound_player.toggle_playback()
                    else:
                        # sound playing, not paused
                        p = sound_player.toggle_playback()
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
                        led_scanner.stop_scanning()
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
                                        '-o','alsa:hifiberry',
                                        self.__prompts_dir+'shutdown-admin-resume.wav'],
                                        stdin=subprocess.PIPE,
                                        stdout=None,stderr=None)

                        button_monitor = ButtonMonitor(1)
                        button_pattern = button_monitor.get_button_presses()
                        if button_pattern[0] == BUTTON_GREEN:
                            print('restarting in config mode')
                            sound_player.close()
                            os.system('sudo /etc/init.d/soundbox restart')

                        else:
                            if button_pattern[0] == BUTTON_RED:
                                print('shutting down in 2 seconds')
                                time.sleep(2.0)
                                os.system('sudo shutdown now')

                            else:
                                print('neither red or green picked. carry on')
                                os.system('sudo /etc/init.d/soundbox restart2')



#

                # sleep just a bit in case of switch bounce. this is because
                # we are using edge detection here, and if the switch bounces,
                # one press could cause two or more detectable edges.
                time.sleep(0.2)
        except:
            print('Ignoring Exception probably due to KeyboardInterrupt')


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



# Class definition encapsulating the metadata for the sound being played.
# This class  manages a sub-process to play sounds asynchronously while
# the process that started the player continues to run on its own.
class SoundPlayer(object):

    def __init__(self, omx_vol_setting, omx_amp_setting):
        self.__player_process = None
        self.__omx_vol_setting = omx_vol_setting
        self.__omx_amp_setting = omx_amp_setting
        self.__playing_event = None
        self.__playing_led_id = None
        self.__paused = False
        self.__volume_control = VolumeControl(self)
        self.__flasher = None
        vol_ctl_Thread = Thread(target=self.__volume_control.loop)
        vol_ctl_Thread.start()

    def is_active(self):
        if self.__player_process is None:
            return False
        else:
            return True

    def is_paused(self):
        return self.__paused

    def close(self):
        self.__volume_control.close()

    def toggle_playback(self):
        if self.__player_process is not None:
            if self.__paused == False:
                self.__player_process.stdin.write(b'p')
                self.__player_process.stdin.flush()
                self.__paused = True

                # Flash the playing led
                self.__flasher = LEDFlasher(self.__playing_led_id)
                flash_thread = Thread(target=self.__flasher.flash_til_stopped)
                flash_thread.start()
            else:
                self.__player_process.stdin.write(b' ')
                self.__player_process.stdin.flush()
                self.__paused = False
                self.__flasher.stop_flashing()

                # get the led on now to minimize flickering
                GPIO.output(self.__playing_led_id, GPIO.HIGH)
                # Wait for the flashing to cease
                while self.__flasher.is_flashing():
                    continue
                # make sure that when the flasher is done, the led is on
                GPIO.output(self.__playing_led_id, GPIO.HIGH)

        return self.__player_process

    def close_player_process(self):
        self.__player_process = None

    def quit_playing(self):
        if self.__player_process is not None:
            if self.__flasher is not None:
                self.__flasher.stop_flashing()
                while self.__flasher.is_flashing():
                    continue
                self.__flasher.set_run_flag()
            print('writing q to omxplayer to make it stop')
            self.__player_process.stdin.write(b'q')
            self.__player_process.stdin.flush()
            self.__player_process.terminate()
            self.__player_process = None
            self.__playing_event.set()
            self.__paused = False
            GPIO.output(self.__playing_led_id, GPIO.LOW)


    def play_sound_file(self, sound_file_path_name, event, led_id):
        # When a sound is already playing and a new sound is requested,
        # stop the current sound before starting the new one.
        self.quit_playing()

        # Remember how this sound was selected so the leds stop scanning
        # and the led for the selection is lit up.
        self.__playing_event = event
        self.__playing_led_id = led_id
        GPIO.output(self.__playing_led_id, GPIO.HIGH)
        self.__playing_event.clear()

        # Play the sound in a sub-process. This allows the sound to play
        # while we continue scanning the buttons in case our user presses
        # a button while the sound plays.
        p = self.__player_process = subprocess.Popen(['omxplayer',
                        '--vol', self.__omx_vol_setting,
                        '--amp', self.__omx_amp_setting,
                        '-o','alsa:hifiberry',
                        sound_file_path_name],
                        stdin=subprocess.PIPE,
                        stdout=None,stderr=None)
        return p



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

    # Let there NOT be light.
    def turnoff_all_leds():
        GPIO.output(LED_WHITE, GPIO.LOW)
        GPIO.output(LED_BLUE, GPIO.LOW)
        GPIO.output(LED_GREEN, GPIO.LOW)
        GPIO.output(LED_YELLOW, GPIO.LOW)
        GPIO.output(LED_RED, GPIO.LOW)

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
            config.read('/home/pi/soundbox/soundbox.ini')

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

    # For convenience, make tuples for buttons and LEDs
    buttons = (BUTTON_WHITE, BUTTON_BLUE, BUTTON_GREEN, BUTTON_YELLOW, BUTTON_RED)
    leds = (LED_WHITE, LED_BLUE, LED_GREEN, LED_YELLOW, LED_RED)


    # Initialize button input pins as GPIO.HIGH when buttons are not pressed
    # The buttons are tied to ground, so input pins go GPIO.LOW when buttons
    # are pressed
    GPIO.setup(buttons, GPIO.IN, pull_up_down=GPIO.PUD_UP)

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
                                   termination_event)
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
            if GPIO.input(BUTTON_WHITE) == GPIO.LOW:
                termination_event.wait()
                print(sounds[0])
                p = process_button_press(sound_player, LED_WHITE, led_scanner, white_e,
                    sound_base_dir+selected_dir+'/'+sounds[0])
            if GPIO.input(BUTTON_BLUE) == GPIO.LOW:
                termination_event.wait()
                print(sounds[1])
                p = process_button_press(sound_player, LED_BLUE, led_scanner, blue_e,
                    sound_base_dir+selected_dir+'/'+sounds[1])
            if GPIO.input(BUTTON_GREEN) == GPIO.LOW:
                termination_event.wait()
                print(sounds[2])
                p = process_button_press(sound_player, LED_GREEN, led_scanner,green_e,
                    sound_base_dir+selected_dir+'/'+sounds[2])
            if GPIO.input(BUTTON_YELLOW) == GPIO.LOW:
                termination_event.wait()
                print(sounds[3])
                p = process_button_press(sound_player, LED_YELLOW, led_scanner,yellow_e,
                    sound_base_dir+selected_dir+'/'+sounds[3])
            if GPIO.input(BUTTON_RED) == GPIO.LOW:
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


