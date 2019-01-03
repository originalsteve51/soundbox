from threading import Thread
from threading import Event


# Following are used only by SoundPlayer
import subprocess
import alsaaudio

from volumecontrol import *
from ledflasher import *
from globaldefs import *

# Values used when command line overrides are not supplied and
# soundbox.ini values are not present
OMX_VOL_SETTING_DEFAULT = '0'
OMX_AMP_SETTING_DEFAULT = '2500'


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
        pass
#        self.__volume_control.close()

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
        print('playing: ', sound_file_path_name)
        p = self.__player_process = subprocess.Popen(['omxplayer',
                        '--vol', self.__omx_vol_setting,
                        '--amp', self.__omx_amp_setting,
                        '-o','alsa:'+ALSA_DEVICE_NAME,
                        sound_file_path_name],
                        stdin=subprocess.PIPE,
                        stdout=None,stderr=None)
        return p


