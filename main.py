import signal
import os
import RPi.GPIO as GPIO

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import time

import ST7789


MENUPOS = 0
MESSAGE = ""
BUTTONS = [5, 6, 16, 20]
LABELS = ['A', 'B', 'X', 'Y']

GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTONS, GPIO.IN, pull_up_down=GPIO.PUD_UP)

os.system("mpc volume 10")
#os.system("mpc play")

# Create ST7789 LCD display class.
disp = ST7789.ST7789(
    port=0,
    cs=1,  			# BG_SPI_CS_BACK or BG_SPI_CS_FRONT, 1 to avoid clash with DAC
    dc=9,
    backlight=13,               # 18 for back BG slot, 19 for front BG slot, 13 to avoid clash with DAC.
    spi_speed_hz=80 * 1000 * 1000
)

WIDTH = disp.width
HEIGHT = disp.height



# Initialize display.
disp.begin()



image = Image.open('/home/pi/git/pirate/themes/streamline/images/home-ico.png');
image = image.resize((WIDTH,HEIGHT))
disp.display(image)




def handle_button(pin):
	label = LABELS[BUTTONS.index(pin)]
	global MENUPOS, MESSAGE, image
	if label == "Y":
		if MENUPOS < 11:
			MENUPOS = MENUPOS + 1
	elif label == "B":
		if MENUPOS > 0:
			MENUPOS = MENUPOS - 1


	#SHOW MENU BASED ON MENUPOS
	if MENUPOS == 0:
		print("Home")
        	image = Image.open('/home/pi/git/pirate/themes/streamline/images/home.png');

		if label == "X":
			os.system("mpc play & mpc next")
		elif label == "A":
			os.system("mpc update")
    	elif MENUPOS == 1:
		print("Volume")
        	image = Image.open('/home/pi/git/pirate/themes/streamline/images/volume.png');
        	if label == "X":
			os.system("mpc volume +5")
        	elif label == "A":
			os.system("mpc volume -5")
    	elif MENUPOS == 2:
		print("Playback: Next Prev")
        	image = Image.open('/home/pi/git/pirate/themes/streamline/images/skip.png');
        	if label == "X":
			os.system("mpc play & mpc next")
        	elif label == "A":
			os.system("mpc play & mpc prev")
    	elif MENUPOS == 3:
		print("Playback: Stop Start")
        	image = Image.open('/home/pi/git/pirate/themes/streamline/images/play.png');
        	if label == "X":
			os.system("mpc toggle")
        	elif label == "A":
			os.system("mpc stop")
    	elif MENUPOS == 4:
		print("Sysinfo: Data Temperature")
        	image = Image.open('/home/pi/git/pirate/themes/streamline/images/system.png');
    	elif MENUPOS == 5:
		print("Power: Reboot Poweroff")
        	image = Image.open('/home/pi/git/pirate/themes/streamline/images/power.png');
        	if label == "X":
			os.system("sudo reboot")
        	elif label == "A":
			os.system("sudo poweroff")

	print(MENUPOS)

	# CHANGE SCREEN
	image = image.resize((WIDTH, HEIGHT))
	disp.display(image)



# Loop through out buttons and attach the "handle_button" function to each
# We're watching the "FALLING" edge (transition from 3.3V to Ground) and
# picking a generous bouncetime of 100ms to smooth out button presses.
for pin in BUTTONS:
    GPIO.add_event_detect(pin, GPIO.FALLING, handle_button, bouncetime=100)

# Finally, since button handlers don't require a "while True" loop,
# we pause the script to prevent it exiting immediately.
signal.pause()
