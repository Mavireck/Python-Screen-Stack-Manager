#!/usr/bin/env python
import sys
import os
import threading
from time import sleep
# Load Pillow
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import cv2

screen_width=768
screen_height=1024
view_width=768
view_height=1024
h_offset = screen_height - view_height
w_offset = screen_width - view_width
cv2.namedWindow("PSSM_Emulator")

last_printed_PIL = Image.new('RGB', (screen_width,screen_height), color=255)


def wait(time_seconds):
	cv2.waitKey(int(time_seconds*1000))

def closePrintHandler():
	#TODO
	print("Closed")

def print_raw(raw_data,x,y,w,h,length=None,isInverted=False):
	#TODO : honor is inverted
	if length==None:
		length = len(raw_data)
	pil_image = Image.frombytes('L',(w,h),raw_data).convert("RGB")
	last_printed_PIL.paste(pil_image,(x,y))
	opencvImage = np.array(last_printed_PIL)
	# Convert RGB to BGR
	opencvImage = opencvImage[:, :, ::-1].copy()
	cv2.imshow('PSSM_Emulator',opencvImage)

def do_screen_refresh(isInverted=False,isPermanent=True):
	#TODO:
	print("Screen refresh")

def do_screen_clear():
	pil_image = Image.new('L', (screen_width,screen_height), color=255).convert("RGB")
	opencvImage = np.array(pil_image)
	# Convert RGB to BGR
	opencvImage = opencvImage[:, :, ::-1].copy()
	cv2.imshow('PSSM_Emulator',opencvImage)


interactionHandler = None
def initInteractionHandler():
	print("initInteractionHandler started")
	global interactionHandler
	interactionHandler = inputObject()
	cv2.setMouseCallback("PSSM_Emulator", interactionHandler.cv2Link)

def closeInteractionHandler():
	#TODO: is there anything to do?
	print("Closed interactionHandler")


class inputObject():
	"""
	Input object
	"""
	def __init__(self):
		self.lastClick_wasSent = True
		self.lastClick = (-1,-1)

	def close(self):
		""" Closes the input event file """
		self.devFile.close()
		return True

	def cv2Link(self,event, x, y, flags, param):
		if event == cv2.EVENT_LBUTTONUP:
			self.lastClick = (x, y)
			self.lastClick_wasSent = False

	def getInput(self):
		"""
		Returns the rotated x,y coordinates of where the user last touched
		returns None if the last touch coordinates have already been sent
		"""
		err = None
		if self.lastClick_wasSent == False:
			(x,y) = self.lastClick
			self.lastClick_wasSent = True
			return (x, y, None)
		else:
			return None

	def debounceAllow(self,x,y):
		return True
