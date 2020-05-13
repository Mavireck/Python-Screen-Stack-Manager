#!/usr/bin/env python
import sys
import os
import socket
import threading
from time import sleep
# Load the wrapper module, it's linked against FBInk, so the dynamic loader will take care of pulling in the actual FBInk library
from _fbink import ffi, lib as FBInk
# Load Pillow
from PIL import Image, ImageDraw, ImageFont
import devices.kobo.KIP as KIP

path_to_pssm_device = os.path.dirname(os.path.abspath(__file__))
isEmulator= False
isRGB     = False
isEreader = True
isWifiOn  = True
touchPath 			= "/dev/input/event1"
batteryCapacityFile = "/sys/devices/platform/pmic_battery.1/power_supply/mc13892_bat/capacity"
batteryStatusFile   = "/sys/devices/platform/pmic_battery.1/power_supply/mc13892_bat/status"


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
view_width=state.view_width
view_height=state.view_height
h_offset = screen_height - view_height
w_offset = screen_width - view_width

def setFrontlightLevel(level):
	"""
	:level (int) : A frontlight level between 0 (off) and 100 (maximum)
	"""
	os.system(path_to_pssm_device + "/frontlight " + str(level))

def readBatteryPercentage():
	with open(batteryCapacityFile) as state:
		state.seek(0)
		res = ""
		for line in state:
			res += str(line)
	return res

def readBatteryState():
	res=""
	with open(batteryStatusFile) as percentage:
		percentage.seek(0)
		isFirst = True
		for line in percentage:
			if isFirst:
				res += str(line).rstrip()
				isFirst=False
	return res

def get_ip():
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	try:
		# isWifiOn = True
		# doesn't even have to be reachable
		s.connect(('10.255.255.255', 1))
		IP = s.getsockname()[0]
	except:
		print("Error gettin IP")
	finally:
		s.close()
	return IP

def wifiDown():
	try:
		os.system("sh " + path_to_pssm_device + "/disable-wifi.sh")
		isWifiOn = False
	except:
		print("Failed to disabled Wifi")

def wifiUp():
	try:
		os.system("sh " + path_to_pssm_device + "/enable-wifi.sh")
		# os.system("sh ./files/obtain-ip.sh")
		# os.system(". ./files/nickel-usbms.sh && enable_wifi")
		wait(1)
		isWifiOn = True
	except:
		print(str(sys.exc_info()[0]),str(sys.exc_info()[1]))


def wait(time_seconds):
	sleep(time_seconds)

def closePrintHandler():
	FBInk.fbink_close(fbfd)

def print_pil(imgData,x,y,w,h,length=None,isInverted=False):
	raw_data = imgData.tobytes("raw")
	length = len(raw_data)
	# FBInk.fbink_print_image(fbfd, str(path).encode('ascii'), x, y, fbink_cfg)
	FBInk.fbink_print_raw_data(fbfd, raw_data, w, h, length, x, y, fbink_cfg)
	if isInverted == True:
		# Workaround : print_raw_data cannot print something inverted, so we print the thing
		# Then we invert-refresh the region
		mode = bool(fbink_cfg.is_nightmode)
		fbink_cfg.is_nightmode = not fbink_cfg.is_nightmode
		FBInk.fbink_refresh(fbfd, y+h_offset,x+w_offset,w,h, FBInk.HWD_PASSTHROUGH, fbink_cfg)
		fbink_cfg.is_nightmode = mode


def do_screen_refresh(isInverted=False, isFlashing=True, isPermanent=True,area=[(0,0),(0,0)],w_offset=0,h_offset=0):
	initial_is_flashing = bool(fbink_cfg.is_flashing)
	initial_is_nigthmode = bool(fbink_cfg.is_nightmode)
	if isFlashing:
		fbink_cfg.is_flashing = True
	if isInverted:
		fbink_cfg.is_nightmode = not initial_is_nigthmode
	[(x,y),(w,h)] = area
	# Note : FBInk expects coordinates in a weird order : top(y), left(x), width, height
	# If given an empty area, it will perform a full screen refresh
	FBInk.fbink_refresh(
		fbfd,
		y+h_offset, x+w_offset, w, h,
		FBInk.HWD_PASSTHROUGH,
		fbink_cfg
	)
	fbink_cfg.is_flashing = initial_is_flashing
	if not isPermanent and isInverted:
		fbink_cfg.is_nightmode = initial_is_nigthmode

def do_screenDump():
	d = FBInk.fbink_dump(fbfd,fbink_dumpcfg)
	return True

def do_screenDump_restore():
	FBInk.fbink_restore(fbfd,fbink_cfg,fbink_dumpcfg)
	return True

def do_screen_clear():
	FBInk.fbink_cls(fbfd, fbink_cfg)


interactionHandler = None
isInputThreadStarted = False
def initInteractionHandler(grabInput=False):
	print("initInteractionHandler started")
	global interactionHandler
	interactionHandler = KIP.inputObject(touchPath, screen_width, screen_height,grabInput=grabInput)

def eventBindings(callbackFct, isThread=False,grabInput=False):
	"""
	This function is started as another thread, and calls 'callbackFct(x,y)'
	When a click or touch event is recorded
	"""
	print("[PSSM_Kobo - Touch handler] : Let's do this")
	global interactionHandler
	initInteractionHandler(grabInput=grabInput)
	while True:
		try:
			deviceInput = interactionHandler.getInput()
			(x, y, err) = deviceInput
			print(deviceInput)
		except:
			continue
		if isThread and not isInputThreadStarted:
			break
		if interactionHandler.debounceAllow(x,y):
			callbackFct(x,y)

def closeInteractionHandler():
	global interactionHandler
	interactionHandler.close()
