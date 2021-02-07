import signal, os, re, sys, time, subprocess
import RPi.GPIO as GPIO
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
    cs=1,           # 1 to avoid clash with DAC
    dc=9,
    backlight=13,   # 13 to avoid clash with DAC
    spi_speed_hz=80 * 1000 * 1000
)

WIDTH = disp.width
HEIGHT = disp.height



# Initialize display.
disp.begin()





image = Image.open('/home/pi/git/pirate/themes/streamline/images/home-ico.png');
image = image.resize((WIDTH,HEIGHT))
disp.display(image)

def get_station():
    # EXTRACT STATION NAME FROM AMENDED RADIO URL
    # EXAMPLE: http://ice6.somafm.com/lush-128-aac?station_name=SomaFM_Lush
    station_url     = subprocess.check_output("mpc -f %file% current", stderr=subprocess.STDOUT, shell=True)
    info_station    = re.findall(r'\?station_name=(.*)', station_url)
    info_station_name = info_station[0].replace('_', ' ')

    return(info_station_name)

def screen_update(file, text_center, text_top):
    font_top                = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
    font_center_top         = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
    font_center_bottom      = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
    file        = "/home/pi/git/pirate/themes/streamline/images/" + file + ".png"
    image       = Image.open(file)
    
    # CENTER TEXT
    if text_center != "none":
        image           = image.convert('RGB')
        draw            = ImageDraw.Draw(image)

        if text_center.find("-") > -1:
            text_split      = text_center.split("-")
            text_artist     = text_split[0]
            text_song       = text_split[1][1:]
            
            if text_top != "none":
                draw.text((0, 15), text_top, font=font_top, fill=(255, 255, 255))
            
            draw.text((0, 100), text_artist, font=font_center_top, fill=(255, 255, 255))
            draw.text((0, 125), text_song, font=font_center_bottom, fill=(255, 255, 255))
        else:
            draw.text((0, 100), text_center, font=font_center_top, fill=(255, 255, 255))
        
        
        image   = image.resize((WIDTH, HEIGHT))
        disp.display(image)
    else:    
        image   = image.resize((WIDTH, HEIGHT))
        disp.display(image)


def handle_button(pin):   
    global MENUPOS, MESSAGE, image
    
    label  = LABELS[BUTTONS.index(pin)]
    print(label)
    
    if label == "Y":
        if MENUPOS < 11:
            MENUPOS = MENUPOS + 1
    elif label == "B":
        if MENUPOS > 0:
            MENUPOS = MENUPOS - 1
    # MPD Fetch
    client = MPDConnect()
    client.connect()
    
    # EXTRACT METADATA FROM Python-MPD
    info        = client.fetch()
    state       = info['state']
    eltime      = info['eltime']
    vol         = info['volume']
    artist      = info['artist']
    title       = info['title']
    audio       = info['audio_info']
    station     = get_station()
    
    client.disconnect()

	#SHOW MENU BASED ON MENUPOS
    if MENUPOS == 0:
		print("Home")
		screen_update("home", title, "none")
		if label == "X":
			os.system("mpc play & mpc next")
			screen_update("home", title, "none")
		elif label == "A":
			os.system("mpc update")
			screen_update("home", "DB Update", "none")
    
    elif MENUPOS == 1:
        print("Volume: " + str(vol))
        screen_update("volume", str(vol), "none")
        if label == "X":
            screen_update("volume", str(vol+5), "none")
            os.system("mpc volume +5")
        elif label == "A":
            os.system("mpc volume -5")
            screen_update("volume", str(vol-5), "none")

    
    elif MENUPOS == 2:
        print("Playback: Next Prev - " + station + ": " + title)
        screen_update("skip", title, station)
        
        client.connect()
        if label == "X":
            screen_update("skip", "Tuning ...", "none")
            os.system("mpc play & mpc next")

            info	= client.fetch()
            title	= info['title']
            station = get_station()
            screen_update("skip", title, station)
        elif label == "A":
            screen_update("skip", "Tuning ...", "none")
            os.system("mpc play & mpc prev")
            
            info	= client.fetch()
            title	= info['title']
            station = get_station()
            screen_update("skip", title, station)
        client.disconnect()
    
    elif MENUPOS == 3:
        print("Playback: Stop Start - " + title)
        if state == "play":
            screen_update("play-playing", "none", "none")
        elif state == "pause":
            screen_update("play-paused", "none", "none")
        elif state == "stop":
            screen_update("play-stopped", "none", "none")
        else:
            screen_update("play", "none", "none")
        
        client.connect()
        if label == "X":
            os.system("mpc toggle")
            info        = client.fetch()
            state       = info['state']

            if state == "pause":
                screen_update("play-paused", "none", "none")
            else:
                screen_update("play-playing", "none", "none")
        elif label == "A":
            os.system("mpc stop")
            info        = client.fetch()
            state       = info['state']
            
            if state == "stop":
                screen_update("play-stopped", "none", "none")
        client.disconnect()
    
    
    elif MENUPOS == 4:
        print("Sysinfo: Data Temperature")
        image = "blank"
    
    
    elif MENUPOS == 5:
        print("Power: Reboot Poweroff")
        if label == "X":
            os.system("sudo reboot")
        elif label == "A":
            os.system("sudo poweroff")

	print(MENUPOS)




# Loop through out buttons and attach the "handle_button" function to each
# We're watching the "FALLING" edge (transition from 3.3V to Ground) and
# picking a generous bouncetime of 100ms to smooth out button presses.
for pin in BUTTONS:
    GPIO.add_event_detect(pin, GPIO.FALLING, handle_button, bouncetime=500)

# Finally, since button handlers don't require a "while True" loop,
# we pause the script to prevent it exiting immediately.
signal.pause()
