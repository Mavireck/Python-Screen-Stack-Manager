#!/usr/bin/env python
import sys
import os
import threading
from time import sleep
# Load Pillow
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import cv2

screen_width=600
screen_height=800
view_width=screen_width
view_height=screen_height
h_offset = screen_height - view_height
w_offset = screen_width - view_width
isEmulator=True
cv2.namedWindow("PSSM_Emulator")

last_printed_PIL = Image.new('RGB', (screen_width,screen_height), color=255)


def wait(time_seconds):
	#Reminder : When using 'wait' in the emulator, you can skip the wait by pressing any keyboard key
	cv2.waitKey(int(time_seconds*1000))


def closePrintHandler():
	#TODO : is there anything to do?
	print("Closed")

def print_raw(raw_data,x,y,w,h,length=None,isInverted=False):
	#TODO : honor is inverted
	global last_printed_PIL
	if length==None:
		length = len(raw_data)
	pil_image = Image.frombytes('L',(w,h),raw_data).convert("RGB")
	last_printed_PIL.paste(pil_image,(x,y))
	opencvImage = np.array(last_printed_PIL)
	# Convert RGB to BGR
	opencvImage = opencvImage[:, :, ::-1].copy()
	cv2.imshow('PSSM_Emulator',opencvImage)
	cv2.waitKey(1)

def do_screen_refresh(isInverted=False,isPermanent=True,area=[[0,0],[0,0]]):
	#TODO: Honor inversion 
	print("Screen refresh - Inversion (partial and full) are not yet supported on the emulator")

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
