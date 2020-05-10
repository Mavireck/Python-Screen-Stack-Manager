#!/usr/bin/env python


import sys
# Load the wrapper module, it's linked against FBInk, so the dynamic loader will take care of pulling in the actual FBInk library
from _fbink import ffi, lib as FBInk
import KIP
import time


touchPath = "/dev/input/event1"
t = KIP.inputObject(touchPath, 600, 800)

while True:
	(x,y,err) = t.getInput()
	print("click - ",x,y)
