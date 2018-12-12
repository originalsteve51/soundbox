# Soundbox
The Soundbox is a Raspberry Pi based sound player intended for use by young people in a supervised learning environment.

The Soundbox hardware includes a Raspberry Pi Zero W, an Adafruit I2S sound card, six push buttons, a rotary encoder w push button, and five leds. 

The OS is Raspbian/stretch.

Two Python 3 programs provide control panel functionality using five of the push buttons. Additional control is provided by the rotary encoder (volume control) and its push button (command button). There is no text display, however to clarify user responses in some situations recorded audio prompts are used.

ALSA (Advanced Linux Sound Architecture) configuration along with a hifiberry sound driver enables the Adafruit sound card to play sounds. Python 3 calls omxplayer, a commonly used Raspberry Pi sound application, to play mp3, wav, and similar audio files. 

Part of the ALSA configuration enables a software volume control to be implemented by the Python Soundbox application. The rotary encoder is read by the Soundbox application to manipulate the volume while sounds are played.

Two Python programs are used:
1. **soundbox.py** - This application starts automatically when the R-Pi is powered up. It provides a five-button interface to play five preloaded sound files. It is multi-threaded for responsiveness as it manages four parts of the system:
  - *The button panel*: This comprises five colored buttons. Typically, selecting a button causes an audio file to play.
  - *The led panel*: Five colored leds are associated with the five buttons. These are turned on and off to help the user understand what the Soundbox is doing. Hopefully the on/off patterns are easily interpreted by users. 
  
    For example, when the Soundbox starts and no sound is playing, the leds are lit in a scanning pattern signifying (I hope) 'push a button'. When a button is pressed, the associated led is lit. But when a playing sound is paused (see the command switch), the associated led is flashed on and off.
  - *The volume control*: This is a rotary encoder which, when turned clockwise/counter-clockwise, increases/decreases the volume of a sound when played.
  - *The command switch*: This is a push button incorporated on the volume control shaft. When pressed, it performs different functions depending on what the Soundbox is doing. 
  
    For example, when a sound is playing, pressing the command switch toggles between pause/resume play of the sound. But when no sound is playing, a long press on this button triggers shutdown options to be audibly presented to the user. 

2. **soundbox-config.py** - This application is optionally launched when Soundbox is in user mode not playing a sound and the user presses and holds the command switch. Doing so allows the user to exit Soundbox and launch soundbox-config.py. (Two other options are also possible, these are described elsewhere.)

    The configuration options are not for the typical Soundbox user. Configuration should be done by a teacher, not by a student. That is why a passcode-sequence of three buttons has to be entered in the correct order before any configuration can be done.
    
    After authentication, audible menus are presented. For example the user might be told to 'Press the red button to configure xxx, or press the green button to configure yyy'.
    
    
