#!/usr/bin/env python
import sys
sys.path.append("../")
import pssm
import pssmElementsLibrairy as PEL
import pssmOSK

import platform
if platform.machine() in ["x86","AMD64","i686","x86_64"]:
    device = "Emulator"
else:
    device = "Kobo"


#Declare the Screen Stack Manager
screen = pssm.ScreenStackManager(device,'Main')
#Start Touch listener, as a separate thread
screen.startListenerThread(grabInput=True)
#Clear and refresh the screen
screen.clear()
screen.refresh()
# Create a blank canvas
screen.createCanvas()


keyboard_area = [(0,int(2*screen.view_height/3)),(screen.view_width,int(screen.view_height/3))]
myOSK = pssmOSK.OSK(area = keyboard_area)
screen.addElt(myOSK)
