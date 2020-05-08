#!/usr/bin/env python

import pssm
import pssmObjectsLibrairy as POL

## Import pssm_device
import platform
if platform.machine() in ["x86","AMD64","i686","x86_64"]:
	# If it is a non-ARM device, it is likely to be used on a computer -> emulator
	# TODO : make a better test (get the device's precise name for instance or something like that)
	import pssm_opencv as pssm_device
else:
	import pssm_kobo as pssm_device



################################################################################

def printObjData(obj,coords):
	"""
	Will be executed on touch
	"""
	# A better behaviour would be to use the obj.data structure to pass whatever
	# you want to be passed
	# Therefore you do not need to iterate to find the object
	print(obj.id, " - ", obj.data, coords)


################################################################################

#Declare the Screen Stack Manager
screen = pssm.ScreenStackManager(pssm_device,'Main')
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

def demo():
	"""
	A simple demo to show how to add, invert and remove objects
	"""
	# Create rectangle from the PSSM objecs library
	obj1 = POL.rectangle(0,0,400,1000,fill=0,outline=50)
	obj2 = POL.rectangle(0,0,1000,400,fill=200,outline=50)
	obj3 = POL.rectangle(0,0,500,500,fill=100,outline=50)

	# There are a few ways to edit an object's attribute
	# Here are some : depending on the context, one may be simpler than the other
	obj1.updateAttributes({
		'data' : "highObj",
		'onclickInside' : printObjData
	})

	obj2.data = "wideObj"
	obj2.onclickInside = printObjData

	obj3.data = "middleObj"
	obj3.onclickInside = printObjData

	# Here is how to add them to the screen :
	screen.addObj(obj1)
	screen.addObj(obj2)
	screen.addObj(obj3)
	print("Waiting 5 seconds")
	pssm_device.wait(5)

	screen.removeObj(obj1.id)
	print("Waiting 5 seconds")
	pssm_device.wait(5)

	screen.addObj(obj1)
	print("All done")


def makeAMatrix():
	"""
	How to use POL to make a simple matrix with buttons
	"""
	# Let's choose an area on the screen where to display our table
	area = [(0,0),(screen.width,screen.height)]
	# Let's choose the size of each borders
	# borders is a [(border_left,border_top),(border_right,border_bottom)] list
	borders = [(20,10),(20,10)]
	# Now let's use a built-in function to get all the coordinates for our table:
	table = POL.tools_createTable(area,rows=8,cols=2,borders=borders)
	i=0
	for col in table:
		for row_item in col:
			# Then, let's create one button per table entry
			# Note :  row_item is a [(x,y),(w,h)] list
			i+=1
			text = "This is some text - " + str(i)
			item = POL.button(row_item,text)
			screen.addObj(item)

demo()
pssm_device.wait(10)
makeAMatrix()
