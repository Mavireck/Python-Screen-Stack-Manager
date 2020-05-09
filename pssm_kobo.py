#!/usr/bin/env python
import sys
import os
import threading
from time import sleep
# Load the wrapper module, it's linked against FBInk, so the dynamic loader will take care of pulling in the actual FBInk library
from _fbink import ffi, lib as FBInk
# Load Pillow
from PIL import Image, ImageDraw, ImageFont
sys.path.append('/mnt/onboard/.adds/mavireck/Kobo-Input-Python')
import KIP



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
isEmulator=False


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


def do_screen_refresh(isInverted=False,isPermanent=True,area=[[0,0],[0,0]]):
	mode = bool(fbink_cfg.is_flashing)
	mode2 = bool(fbink_cfg.is_nightmode)
	fbink_cfg.is_flashing = True
	fbink_cfg.is_nightmode = isInverted
	# Note : FBInk expects coordinates in a weird order : top(y), left(x), width, height
	# If given an empty area, it will perform a full screen refresh
	FBInk.fbink_refresh(
		fbfd,
		area[0][1], area[0][0], area[1][0]-area[0][0], area[1][1]-area[0][1],
		FBInk.HWD_PASSTHROUGH,
		fbink_cfg
	)
	fbink_cfg.is_flashing = mode
	if not isPermanent:
		fbink_cfg.is_nightmode = mode2

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
	touchPath = "/dev/input/event1"
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
