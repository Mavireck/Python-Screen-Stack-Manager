#!/usr/bin/env python
import sys
import os
import threading
from time import sleep
import matplotlib as mpl
mpl.use('TkAgg')
import matplotlib.pyplot as plt
# Load Pillow
from PIL import Image, ImageDraw, ImageFont
from random import random

screen_width=1080
screen_height=1440
view_width=screen_width
view_height=screen_height
h_offset = screen_height - view_height
w_offset = screen_width - view_width


def handlePyplotTouchEvent(event):
	global last_pyplot_x, last_pyplot_y
	last_pyplot_x, last_pyplot_y = event.xdata, event.ydata


def print_raw(raw_data,x,y,w,h,length=None,isInverted=False):
	img = Image.frombytes('L',(w,h),raw_data)
	img_rgba = img.convert('RGBA')
	plt.imshow(raw_data)
	plt.show()


def do_screen_refresh(isInverted=False,isPermanent=True):
	black = Image.new('L', (screen_width,screen_height),color=0)
	img_rgba = black.convert('RGBA')
	im.set_data(img_rgba)
	fig.canvas.draw()


def do_screen_clear(hey=False):
	black = Image.new('L', (screen_width,screen_height), color=int(random()*255))
	img_rgba = black.convert('RGBA')
	im.set_data(img_rgba)
	fig.canvas.draw()


def print_random_color(hey=False):
	global im
	global fig
	black = Image.new('L', (screen_width,screen_height), color=int(random()*255))
	img_rgba = black.convert('RGBA')
	im.set_data(img_rgba)
	fig.canvas.draw()


def initInteractionHandler():
	return True


def closeInteractionHandler():
	return True



"""
whiteBackground = Image.new('L', (screen_width,screen_height), color=255)
img_rgba = whiteBackground.convert('RGBA')
fig, ax = plt.subplots()
im = ax.imshow(img_rgba)
fig.canvas.mpl_connect('button_press_event', do_screen_clear)
plt.show()
"""

def toggleHasNewImg(hey=False):
	global hasNewImg
	hasNewImg = not hasNewImg

hasNewImg = False
def waitForPlotEvent():
	global hasNewImg
	global im
	global fig
	while True:
		if hasNewImg:
			print_random_color()
		else:
			plt.pause(0.01)

whiteBackground = Image.new('L', (screen_width,screen_height), color=255)
img_rgba = whiteBackground.convert('RGBA')
fig = plt.figure()
ax = fig.add_subplot(111)
im = ax.imshow(img_rgba)
plt.show(block=False)
fig.canvas.mpl_connect('button_press_event', toggleHasNewImg)
plt.pause(2)
black = Image.new('L', (screen_width,screen_height), color=100)
img_rgba = black.convert('RGBA')
im.set_data(img_rgba)
fig.canvas.draw()
plt.pause(10)

threading.Thread(target=waitForPlotEvent).start()