import signal
import os
import sys
import RPi.GPIO as GPIO
import time
import ST7789


from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from socket import error as socket_error
from mpd import MPDClient, MPDError, CommandError, ConnectionError



# System UTF-8
reload(sys)
sys.setdefaultencoding('utf-8')


MENUPOS = 0
MESSAGE = ""
BUTTONS = [5, 6, 16, 20]
LABELS = ['A', 'B', 'X', 'Y']

GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTONS, GPIO.IN, pull_up_down=GPIO.PUD_UP)

os.system("mpc volume 10")
#os.system("mpc play")



# MPD Client
class MPDConnect(object):
    def __init__(self, host='localhost', port=6600):
        self._mpd_client = MPDClient()
        self._mpd_client.timeout = 10
        self._mpd_connected = False

        self._host = host
        self._port = port

    def connect(self):
        if not self._mpd_connected:
            try:
                self._mpd_client.ping()
            except(socket_error, ConnectionError):
                try:
                    self._mpd_client.connect(self._host, self._port)
                    self._mpd_connected = True
                except(socket_error, ConnectionError, CommandError):
                    self._mpd_connected = False

    def disconnect(self):
        self._mpd_client.close()
        self._mpd_client.disconnect()

    def _play_pause(self):
        self._mpd_client.pause()
        #return False

    def _next_track(self):
        self._mpd_client.next()
        #return False

    def _prev_track(self):
        self._mpd_client.previous()
        #return False

    def fetch(self):
        # MPD current song
        song_info = self._mpd_client.currentsong()

        # Artist Name
        if 'artist' in song_info:
            artist = song_info['artist']
        else:
            artist = 'Unknown Artist'
        # Song Name
        if 'title' in song_info:
            title = song_info['title']
        else:
            title = 'Unknown Title'

        # MPD Status
        song_stats = self._mpd_client.status()
        # State
        state = song_stats['state']

        # Song time
        if 'elapsed' in song_stats:
            elapsed = song_stats['elapsed']
            m,s = divmod(float(elapsed), 60)
            h,m = divmod(m, 60)
            eltime = "%d:%02d:%02d" % (h, m, s)
        else:
            eltime ="0:00:00"

        # Audio
        if 'audio' in song_stats:
            bit = song_stats['audio'].split(':')[1]
            frequency = song_stats['audio'].split(':')[0]
            z, f = divmod( int(frequency), 1000 )
            if ( f == 0 ):
                frequency = str(z)
            else:
                frequency = str( float(frequency) / 1000 )
            bitrate = song_stats['bitrate']

            audio_info =  bit + "bit " + frequency + "kHz " + bitrate + "kbps"
        else:
            audio_info = ""

        # Volume
        vol = song_stats['volume']

        return({'state':state, 'artist':artist, 'title':title, 'eltime':eltime, 'volume':int(vol), 'audio_info':audio_info})








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

# MPD Fetch
client = MPDConnect()
client.connect()



image = Image.open('/home/pi/git/pirate/themes/streamline/images/home-ico.png');
image = image.resize((WIDTH,HEIGHT))
disp.display(image)




def handle_button(pin):
	label  = LABELS[BUTTONS.index(pin)]
    	font   = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)

    	global MENUPOS, MESSAGE, image

	info        = client.fetch()
	state       = info['state']
	eltime      = info['eltime']
   	vol         = info['volume']
	artist      = info['artist']
	title       = info['title']
	audio       = info['audio_info']

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
		print("Volume: " + str(vol+5))
        	image = Image.open('/home/pi/git/pirate/themes/streamline/images/volume.png');
        	if label == "X":
			os.system("mpc volume +5")
                	MESSAGE = str(vol+5)
        	elif label == "A":
			os.system("mpc volume -5")
                	MESSAGE = str(vol-5)
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
    
    	image          = image.convert('RGB')
    	draw           = ImageDraw.Draw(image)
    	draw.text((0, 100), MESSAGE, font=font, fill=(255, 255, 255))
    	disp.display(image)

    	image   = image.resize((WIDTH, HEIGHT))
	disp.display(image)



# Loop through out buttons and attach the "handle_button" function to each
# We're watching the "FALLING" edge (transition from 3.3V to Ground) and
# picking a generous bouncetime of 100ms to smooth out button presses.
for pin in BUTTONS:
    GPIO.add_event_detect(pin, GPIO.FALLING, handle_button, bouncetime=250)

# Finally, since button handlers don't require a "while True" loop,
# we pause the script to prevent it exiting immediately.
signal.pause()
