#!/usr/bin/env python
import sys
import os
import threading
import time
# Load the wrapper module, it's linked against FBInk, so the dynamic loader will take care of pulling in the actual FBInk library
from _fbink import ffi, lib as FBInk
# Load Pillow
from PIL import Image, ImageDraw, ImageFont
sys.path.append('../Kobo-Input-Python')
import KIP
# Import screenStack
import screenStack


img1 = Image.new('L', (200,800), color=255)
drawImg = ImageDraw.Draw(img1, 'L')
drawImg.rectangle([(0,0),(200,800)],fill=0,outline=50)
obj1 = screenStack.pillowImgToScreenObject(img1,0,0,"highObj")

img2 = Image.new('L', (800,200), color=255)
drawImg = ImageDraw.Draw(img2, 'L')
drawImg.rectangle([(0,0),(800,200)],fill=200,outline=50)
obj2 = screenStack.pillowImgToScreenObject(img2,0,0,"wideObj")

img3 = Image.new('L', (100,400), color=255)
drawImg = ImageDraw.Draw(img3, 'L')
drawImg.rectangle([(0,0),(100,400)],fill=100,outline=50)
obj3 = screenStack.pillowImgToScreenObject(img3,20,20,"middleObj")



##################################################################
touchPath = "/dev/input/event1"
touch = KIP.inputObject(touchPath, 1080, 1440)



screen = screenStack.ScreenStackManager(touch,'Main')
screen.clear()
screen.refresh()

screen.createCanvas()
print("just made canvas")
screen.addObj(obj1)
print("Just added highObj")
screen.addObj(obj2)
print("Just added wideObj")

# screen.invert()
# print("just inverted all the screen")
# time.sleep(2)

screen.addObj(obj3)
print("Just added middleObj")
time.sleep(5)

screen.invertObj(obj2,5)
print("Just inverted wideObj")
time.sleep(10)

screen.removeObj(obj1)
print("Just removed highObj")
time.sleep(5)

screen.addObj(obj1)
print("Just added highObj")

print("done")
