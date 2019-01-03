import alsaaudio
import RPi.GPIO as GPIO

from globaldefs import *
from platformdefs import *

VOLUME_DELTA = 5


class VolumeControl(object):

    terminate = False

    def __init__(self, sound_player):
        self.__sound_player = sound_player
        self.globalCounter = 0
        self.flag = 0
        self.Last_RoB_Status = 0
        self.Current_RoB_Status = 0

        # alsa /etc/asound.conf defines the mixer name
        self.__mixer = alsaaudio.Mixer(ALSA_MIXER_NAME)

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
