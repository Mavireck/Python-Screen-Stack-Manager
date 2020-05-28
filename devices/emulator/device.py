#!/usr/bin/env python
import sys
import os
import threading
from time import sleep
# Load Pillow
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import cv2

delay_emulateEInk_Sluggishness = 0.001
screen_width=600
screen_height=800
view_width=screen_width
view_height=screen_height
h_offset = screen_height - view_height
w_offset = screen_width - view_width
isEmulator= True
isRGB 	  = True
colorType = "L"
cv2.namedWindow("PSSM_Emulator")

last_printed_PIL = Image.new('RGB', (screen_width,screen_height), color=255)

def setFrontlightLevel(level):
	print("setFrontlightLevel -  Not supported on the emulator")

def readBatteryPercentage():
	print(" readBatteryPercentage - Not supported on the emulator")

def readBatteryState():
	print("readBatteryState - Not supported on the emulator")

def get_ip():
	print("get_ip - Not supported on the emulator")

def wifiDown():
	print("wifiDown - Not supported on the emulator")

def wifiUp():
	print("wifiUp - Not supported on the emulator")

def wait(time_seconds):
	#Reminder : When using 'wait' in the emulator, you can skip the wait by pressing any keyboard key
	cv2.waitKey(int(time_seconds*1000))


def closePrintHandler():
	#TODO : is there anything to do?
	print("Closed")

def print_pil(imgData,x,y,w,h,length=None,isInverted=False):
	sleep(delay_emulateEInk_Sluggishness)
	#TODO : honor is inverted
	global last_printed_PIL
	raw_data = imgData.tobytes("raw")
	length = len(raw_data)
	pil_image = Image.frombytes(colorType,(w,h),raw_data).convert("RGB")
	last_printed_PIL.paste(pil_image,(x,y))
	opencvImage = np.array(last_printed_PIL)
	# Convert RGB to BGR
	opencvImage = opencvImage[:, :, ::-1].copy()
	cv2.imshow('PSSM_Emulator',opencvImage)
	cv2.waitKey(1)

def do_screen_refresh(isInverted=False,isFlashing=True,isPermanent=True,area=[[0,0],[0,0]],w_offset=0,h_offset=0):
	#TODO: Honor inversion
	#print("Screen refresh and Inversion (partial and full) are not yet supported on the emulator")
	pass

def do_screen_clear():
	pil_image = Image.new('L', (screen_width,screen_height), color=255).convert("RGB")
	last_printed_PIL = pil_image
	opencvImage = np.array(pil_image)
	# Convert RGB to BGR
	opencvImage = opencvImage[:, :, ::-1].copy()
	cv2.imshow('PSSM_Emulator',opencvImage)
	cv2.waitKey(1)


################################# - Click - ####################################
eventCallbackFct = None
isInputThreadStarted = False
def eventBindings(callbackFct, isThread=False,grabInput=False):
	"""
	This function is started as another thread, and calls 'callbackFct(x,y)'
	When a click or touch event is recorded
	"""
	print("[PSSM_OpenCV - Click handler] : Let's do this")
	global eventCallbackFct
	if grabInput:
		print('Using an emulator - nothing to be grabbed')
	eventCallbackFct = callbackFct
	cv2.setMouseCallback("PSSM_Emulator", cv2Link)

def closeInteractionHandler():
	#TODO
	print("Closed interactionHandler")

def cv2Link(event, x, y, flags, param):
	global eventCallbackFct
	if event == cv2.EVENT_LBUTTONUP:
		eventCallbackFct(x,y)
