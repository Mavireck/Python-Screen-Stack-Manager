import sys
import os
import socket
import threading
from time import sleep
# Load the wrapper module, it's linked against FBInk, so the dynamic loader will take care of pulling in the actual FBInk library
from _fbink import ffi, lib as FBInk
# Load Pillow
from PIL import Image, ImageDraw, ImageFont
# Load Kobo-Input-Python
from PSSM.devices.kobo_tools import InputObject


PATH_TO_THIS_FILE       = os.path.dirname(os.path.abspath(__file__))
TOUCH_PATH 			    = "/dev/input/event1"
BATTERY_CAPACITY_PATH   = "/sys/devices/platform/pmic_battery.1/power_supply/mc13892_bat/capacity"
BATERY_STATUS_PATH      = "/sys/devices/platform/pmic_battery.1/power_supply/mc13892_bat/status"

TOOLS_PATH = os.path.join(PATH_TO_THIS_FILE, "kobo_tools")

# Init FBInk :
fbink_cfg = ffi.new("FBInkConfig *")
fbink_dumpcfg = ffi.new("FBInkDump *")
fbfd = FBInk.fbink_open()
FBInk.fbink_init(fbfd, fbink_cfg)
#Get screen infos
state = ffi.new("FBInkState *")
FBInk.fbink_get_state(fbink_cfg, state)
screen_width=state.screen_width
screen_height=state.screen_height
default_area = ((0, 0), (screen_width, screen_height))
view_width=state.view_width
view_height=state.view_height
h_offset = screen_height - view_height
w_offset = screen_width - view_width


class Screen:
    def __init__(self, onclick_handler, grab_input=True):
        self.onclick_handler = onclick_handler
        self.grab_input = grab_input
        self.width = view_width
        self.height = view_height
        self.area = [(0, 0), (view_width, view_height)]
        self.image = None   
        self.isInverted = False
        self.interaction_handler = InputObject(TOUCH_PATH, screen_width,
                                                  screen_height, 
                                                  grabInput=grab_input)
        pass

    def _start(self):
        # TODO : use a thread ?
        while True:
            try:
                deviceInput = self.interaction_handler.getInput()
                (x, y, err) = deviceInput
            except:
                # oops error, continnue anyway
                continue
            if self.interaction_handler.debounceAllow(x,y):
                # we got a click !
                self.onclick_handler(x, y)

    def _stop(self):
        self.interaction_handler.close()
    
    def print(self, img, x, y, inverted=False, fast_invertion=False):
        """
        Takes a PIL image and displays it

        Parameters:
            img : a PIL image
            x int: the x position
            y int: the y position
            inverted bool: whether to print the image inverted compared to the
                screen's inversion status
        """
        w = img.width
        h = img.height
        raw_data = img.tobytes("raw")
        length = len(raw_data)
        # FBInk.fbink_print_image(fbfd, str(path).encode('ascii'), x, y, fbink_cfg)
        FBInk.fbink_print_raw_data(fbfd, raw_data, w, h, length, x, y, fbink_cfg)
        if inverted == True:
            # Workaround : print_raw_data cannot print something inverted, so we print the thing
            # Then we invert-refresh the region
            # TODO: find a more elegant way (leave the inversion to PILLOW like the emulator ?)
            mode = bool(fbink_cfg.is_nightmode)
            # Set to A2 for faster invertion
            initial_waveform = fbink_cfg.wfm_mode
            if fast_invertion:
                self.set_waveform("A2")
            # Invert nightmode
            fbink_cfg.is_nightmode = not fbink_cfg.is_nightmode
            FBInk.fbink_refresh(fbfd, y+h_offset,x+w_offset,w,h, FBInk.HWD_PASSTHROUGH, fbink_cfg)
            # Then reset to default value
            fbink_cfg.is_nightmode = mode
            fbink_cfg.wfm_mode = initial_waveform
    
    def clear(self):
        """
        Clears the screen
        """
        FBInk.fbink_cls(fbfd, fbink_cfg)
    
    def refresh(self, area=None):
        """
        Refreshes the screen (useful for ereader)
        """
        # Save initial values
        initial_is_flashing = bool(fbink_cfg.is_flashing)
        # Prepare for the refresh
        fbink_cfg.is_flashing = True
        if area is None:
            area = default_area
        [(x,y),(w,h)] = area
        # Note : FBInk expects coordinates in a weird order : top(y), left(x), width, height
        # If given an empty area, it will perform a full screen refresh
        FBInk.fbink_refresh(
            fbfd,
            y + h_offset, x + w_offset, w, h,
            FBInk.HWD_PASSTHROUGH,
            fbink_cfg
        )
        # Then reset to previous value
        fbink_cfg.is_flashing = initial_is_flashing
    
    def invert(self):
        """
        Inverts the whole screen. 
        Then all the images will have to be displayed inverted
        """
        initial_is_flashing = bool(fbink_cfg.is_flashing)
        # Set config
        fbink_cfg.is_flashing = True
        fbink_cfg.is_nightmode = not fbink_cfg.is_nightmode
        FBInk.fbink_refresh(
            fbfd,
            y + h_offset, x + w_offset, w, h,
            FBInk.HWD_PASSTHROUGH,
            fbink_cfg
        )
        fbink_cfg.is_flashing = initial_is_flashing

    def set_waveform(self, mode):
        """
        Sets the waveform ("Auto", "A2", "DU", "DU4")
        """
        if mode == "AUTO":
            fbink_cfg.wfm_mode = FBInk.WFM_AUTO
        elif mode == "A2":
            fbink_cfg.wfm_mode = FBInk.WFM_A2
        elif mode == "DU":
            fbink_cfg.wfm_mode = FBInk.WFM_DU
        elif mode == "DU4":
            fbink_cfg.wfm_mode = FBInk.WFM_DU4
        else:
            fbink_cfg.wfm_mode = mode
    
    def capture(self, full=False):
        """
        Takes a screenshot and returns the corresponding image
        Args:
            full bool: whether to recalculate the image completely, 
                or simply send back self.image
        """
        print("SCREEN CAPTURE NOT IMPLEMENTED YET ON THE KOBO")

    def after(self, milliseconds, callback, args=[]):
        """
        Execute the callback function with args after a few milliseconds
        """
        def call_callback():
            sleep(milliseconds/1000)
            callback(*args)
        x = threading.Thread(target=call_callback)
        x.start()
        


class Hardware:
    def __init__(self):
        self.has_frontlight = True
        self.has_wifi = True
        self.wifi = True
    
    def wifi_up(self):
        try:
            os.system("sh " + TOOLS_PATH + "/enable-wifi.sh")
            # os.system("sh ./files/obtain-ip.sh")
            # os.system(". ./files/nickel-usbms.sh && enable_wifi")
            wait(1)
            self.wifi = True
        except:
            print(str(sys.exc_info()[0]),str(sys.exc_info()[1]))
    
    def wifi_down(self):
        try:
            os.system("sh " + TOOLS_PATH + "/disable-wifi.sh")
            self.wifi = False
        except:
            print("Failed to disabled Wifi")
    
    def get_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # self.wifi = True
            # doesn't even have to be reachable
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except:
            print("Error gettin IP")
        finally:
            s.close()
        return IP
    
    def get_battery(self):
        """
        Returns a (status, percentage) tuple
        """
        # First the percentage
        with open(BATTERY_CAPACITY_PATH) as state:
            state.seek(0)
            percentage = ""
            for line in state:
                percentage += str(line)
        percentage = int(percentage)
        # Then the status
        status = ""
        with open(BATERY_STATUS_PATH) as status_f:
            status_f.seek(0)
            for line in status_f:
                status += str(line).rstrip()
                # But we only read the first line
                break
        return (status, percentage)
    
    def set_frontlight(self, level):
        os.system(TOOLS_PATH + "/frontlight " + str(level))
        return True