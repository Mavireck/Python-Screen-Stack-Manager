#!/usr/bin/env python
#Import the time module for demonstration purposes
import time
# Import pssm
import pssm
import pssm_kobo
import pssmObjectsLibrairy as POL

################################################################################

def printObjData(objId,objData):
	"""
	Will be executed on touch
	"""
	# A better behaviour would be to use the obj.data structure to pass whatever
	# you want to be passed
	# Therefore you do not need to iterate to find the object
	obj = screen.findObjWithId(objId)
	print(obj.name, objId)

# Create rectangle from the PSSM objecs library
obj1 = POL.rectangle(0,0,400,1000,fill=0,outline=50)
obj1.name = "highObj"
obj1.onclickInside = printObjData

obj2 = POL.rectangle(0,0,1000,400,fill=200,outline=50)
obj2.name = "wideObj"
obj2.onclickInside = printObjData

obj3 = POL.rectangle(0,0,500,500,fill=100,outline=50)
obj3.name = "middleObj"
obj3.onclickInside = printObjData


################################################################################

#Declare the Screen Stack Manager
screen = pssm.ScreenStackManager(pssm_kobo,'Main')
screenWidth = screen.width
screenHeight = screen.height
#Start Touch listener, as a separate thread
screen.startListenerThread()
#Clear and refresh the screen
screen.clear()
screen.refresh()

# Create a blank canvas
screen.createCanvas()
print("just made canvas")

screen.addObj(obj1)
print("Just added highObj")

screen.addObj(obj2)
print("Just added wideObj")

screen.addObj(obj3)
print("Just added middleObj")

print("Waiting 5 seconds")
time.sleep(5)

screen.invertObj(obj2.id,5)
print("Just inverted wideObj for 5 seconds, waiting 5 seconds after that")
time.sleep(10)

screen.removeObj(obj1.id)
print("Just removed highObj")
time.sleep(5)

screen.addObj(obj1)
print("Just added highObj")

print("All done")
