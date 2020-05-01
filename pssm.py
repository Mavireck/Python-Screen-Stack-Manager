#!/usr/bin/env python
import sys
import os
import threading
from time import sleep
# Load Pillow
from PIL import Image, ImageDraw, ImageFont
from PIL.ImageOps import invert as PILInvert
from copy import deepcopy

lastUsedId=0

def coordsInArea(x,y,area):
	if len(area)>2:
		if x>=area[0] and x<area[2] and y>=area[1] and y<area[3]:
			return True
		else:
			return False
	else:
		if x>=area[0][0] and x<area[1][0] and y>=area[0][1] and y<area[1][1]:
			return True
		else:
			return False

def getRectanglesIntersection(area1,area2):
	x1 = max(area1[0][0],area2[0][0])
	x2 = min(area1[1][0],area2[1][0])
	y1 = max(area1[0][1],area2[0][1])
	y2 = min(area1[1][1],area2[1][1])
	if x2-x1>0 and y2-y1>0:
		return [[x1,y1],[x2,y2]]
	else:
		return None

def returnFalse(*args):
	return False

def pillowImgToScreenObject(img,x,y,name="noname",onclickInside=returnFalse,onclickOutside=None,isInverted=False,data=[],tags=set()):
	raw_data = img.tobytes("raw")
	obj =  ScreenObject(raw_data,(x,y),(x + img.width, y + img.height),name, onclickInside, onclickOutside,isInverted,data,tags)
	return obj


class ScreenObject:
	def __init__(self,imgData,xy1,xy2,name="noname",onclickInside=returnFalse,onclickOutside=None,isInverted=False,data=[],tags=set()):
		"""
		If onclickInside == None, then the stack will keep searching for another object under this one.
		Use onclickInside == returnFalse if you want the stack to do nothing when touhching the object.
		OnclickInside and onclickOutside will be given as argument : x,y,data
		"""
		self.objType = "obj"
		global lastUsedId
		lastUsedId += 1
		self.id = lastUsedId
		self.imgData = imgData
		self.name = name
		self.xy1 = xy1
		self.x = xy1[0]
		self.y = xy1[1]
		self.xy2 = xy2
		self.x2 = xy2[0]
		self.y2 = xy2[1]
		self.w = self.x2-self.x
		self.h = self.y2-self.y
		self.onclickInside = onclickInside
		self.onclickOutside = onclickOutside
		self.isInverted = isInverted
		self.data = data
		self.tags=tags
		self.parents = []

	def __hash__(self):
		return hash(self.id)

	def __eq__(self, other):
		if isinstance(other, self.__class__):
			return self.id == other.id
		return NotImplemented

	def addTag(self,tag):
		self.tags.add(tag)

	def removeTag(self,tag):
		self.tags.discard(tag)

	def setInverted(self,mode):
		self.isInverted = mode

	def updateImg(self,newImg,xy1,xy2):
		"""
		Updates the object without displaying it.
		"""
		self.imgData = imgData
		self.xy1 = xy1
		self.x = xy1[0]
		self.y = xy1[1]
		self.xy2 = xy2
		self.x2 = xy2[0]
		self.y2 = xy2[1]
		self.w = x2-x
		self.h = y2-y

class ScreenStackManager:
	def __init__(self,device,name="screen",stack=[],isInverted=False):
		self.device = device
		self.width = device.screen_width
		self.height = device.screen_height
		self.view_width = device.view_width
		self.view_height = device.view_height
		self.w_offset = device.w_offset
		self.h_offset = device.h_offset
		self.name = name
		self.stack = stack
		self.isInverted = isInverted
		self.isInputThreadStarted = False
		self.lastX = -1
		self.lastY = -1

	def findObjWithId(self,screenObjId):
		for obj in self.stack:
			if obj.id == screenObjId:
				return obj
		return None

	def printStack(self,skipObjId=None,area=None):
		"""
		Prints the stack elements in the stack order
		If a skipObj is specified, then the function will not display the skipObj.
		If a area is set, then, we only display
			the part of the stack which is in this area
		"""
		mainIntersectionArea = [(area[0][0],area[0][1]),(area[1][0],area[1][1])] if area else [(0,0),(self.width,self.height)]
		placeholder = Image.new('L', (mainIntersectionArea[1][0]-mainIntersectionArea[0][0],mainIntersectionArea[1][1]-mainIntersectionArea[0][1]), color=255)
		for obj in self.stack:
			if (not skipObjId) or (skipObjId and obj.id != skipObjId):
				# We loop through the objects behind the screenObject we are working on
				objArea = [(obj.x,obj.y),(obj.x2,obj.y2)]
				rectIntersection = getRectanglesIntersection(mainIntersectionArea,objArea)
				if rectIntersection != None:
					# The obj we are looking at is behind the screenObj
					intersectionImg = self.getPartialObjImg(obj,rectIntersection)
					placeholder.paste(intersectionImg,(rectIntersection[0][0],rectIntersection[0][1]))
		raw_data=placeholder.tobytes("raw")
		self.device.print_raw(raw_data,mainIntersectionArea[0][0], mainIntersectionArea[0][1],placeholder.width,placeholder.height,isInverted=self.isInverted)

	def getPartialObjImg(self,obj,rectIntersection):
		#TODO : MUST HONOR INVERSION
		# We crop and print a part of the object
		# First, lets make a PILLOW object:
		img = Image.frombytes('L',(obj.w,obj.h),obj.imgData)
		# Then, lets crop it:
		img = img.crop((rectIntersection[0][0]-obj.x, rectIntersection[0][1]-obj.y, rectIntersection[1][0]-obj.x, rectIntersection[1][1]-obj.y))
		if obj.isInverted:
			inverted_img = PILInvert(img)
			return inverted_img
		else:
			return img

	def simplePrintObj(self,screenObj):
		"""
		Prints the object without adding it to the stack
		"""
		self.device.print_raw(screenObj.imgData,screenObj.x, screenObj.y, screenObj.w, screenObj.h,isInverted=screenObj.isInverted)

	def addObj(self,screenObj,skipPrint=False,skipRegistration=False):
		"""
		Adds object to the stack and prints it
		"""
		for obj in self.stack:
			if obj.id == screenObj.id:
				if not skipPrint:
					self.updateArea(screenObj)
				break	#The object is already in the stack
		else:
			# the object is not already in the stack
			if not skipRegistration:
				self.forceAddObj(screenObj)

	def forceAddObj(self,screenObj):
		"""
		Adds object to the stack and prints it, without checking if it is already here
		"""
		self.stack.append(screenObj)
		self.simplePrintObj(screenObj)

	def updateArea(self,area = None):
		"""
		Updates the object : updates the stack and prints the object and all the stack above it
		while keeping the stack position
		"""
		self.printStack(area=area)

	def removeObj(self,screenObjId,skipPrint=False,weAlreadyHaveTheObj=None):
		"""
		Removes the object from the stack and hides it from the screen
		"""
		# We print the stack, but only the area where screenObj was
		if not skipPrint:
			screenObj=self.findObjWithId(screenObjId)
			self.printStack(screenObjId,[screenObj.xy1,screenObj.xy2])
		if weAlreadyHaveTheObj:
			self.stack.remove(weAlreadyHaveTheObj)
		else :
			obj = self.findObjWithId(screenObjId)
			if obj:
				self.stack.remove(obj)

	def getTagList(self):
		"""
		Returns the set of all tags from all objects in the stack
		"""
		tags={}
		for obj in self.stack:
			tags.update(obj.tags)
		return tags

	def removeAllWithTag(self,tag):
		"""
		Removes every object from the stack which have the specified tag
		"""
		stackCopy = deepcopy(self.stack) #It is unsage to loop through a mutable list which is being edited afterwards : some items are skipped
		for obj in stackCopy:
			if tag in obj.tags:
				self.removeObj(obj.id,skipPrint=True,weAlreadyHaveTheObj=obj)
		#Then we reprint the whole screen (yeah, the *whole* screen... Performance is not our goal)
		self.printStack()

	def getStackLevel(self,screenObjId):
		obj = self.findObjWithId(screenObjId)
		return self.stack.index(obj)

	def setStackLevel(self,screenObjId,stackLevel="last"):
		"""
		Set the position of said object
		Then prints every object above it (including itself)
		"""
		if stackLevel=="last" or stackLevel==-1:
			stackLevel=len(self.stack)
			obj = self.findObjWithId(screenObjId)
			self.removeObj(screenObjId,skipPrint=True)
			self.stack.insert(stackLevel,obj)
			self.printStack(area=[obj.xy,obj.xy2])
			return True

	def printInvertedObj(self,invertDuration,screenObjId):
		screenObj = self.findObjWithId(screenObjId)
		if screenObj==None:
			return False
		mode = bool(screenObj.isInverted)
		screenObj.setInverted(not screenObj.isInverted)
		self.simplePrintObj(screenObj)
		if invertDuration and invertDuration>0:
			#Then, we start a timer to set it back to a non inverted state
			threading.Timer(invertDuration,screenObj.setInverted,[mode]).start()
			threading.Timer(invertDuration,self.simplePrintObj,[screenObj]).start()

	def invertObj(self, screenObjId,invertDuration):
		"""
		Shortcut (or longcut, it depends on the point of view) to invert the screen object
		"""
		screenObj = self.findObjWithId(screenObjId)
		self.printInvertedObj(invertDuration,screenObj)
		area = [screenObj.xy1,screenObj.xy2]
		self.printStack(skipObjId=None, area=area)
		threading.Timer(invertDuration,self.printStack,[None,area]).start()
		return True

	def invert(self):
		"""
		Inverts the whole screen
		"""
		self.isInverted = not self.isInverted
		self.device.do_screen_refresh(self.isInverted)
		return True

	def refresh(self):
		"""
		Refreshes the screeen
		"""
		self.device.do_screen_refresh()
		return True

	def clear(self):
		"""
		Clears the screen
		"""
		self.device.do_screen_clear()
		return True

	def createCanvas(self,color=255):
		"""
		Creates a white object at the bottom of the stack, displays it while refreshing the screen
		"""
		img = Image.new('L', (self.width,self.height), color=255)
		background = pillowImgToScreenObject(img,0,0,name="Canvas")
		self.addObj(background)
		return True

	def startListenerThread(self,grabInput=False):
		"""
		Starts the touch listener as a separate thread
		"""
		self.isInputThreadStarted = True
		self.device.isInputThreadStarted = True
		print("[PSSM - Touch handler] : Input thread started")
		threading.Thread(target=self.device.eventBindings,args=[self.clickHandler,True,grabInput]).start()

	def clickHandler(self,x,y):
		n = len(self.stack)
		for i in range(n):
			j = n-1-i 	# We go through the stack in descending order
			obj = self.stack[j]
			if coordsInArea(x,y,[obj.xy1,obj.xy2]):
				if obj.onclickInside != None:
					self.lastX = x
					self.lastY = y
					obj.onclickInside(obj.id, obj.data)
					break 		# we quit the for loop
			elif obj.onclickOutside != None:
				self.lastX = x
				self.lastY = y
				obj.onclickOutside(obj.id, obj.data)
				break 			# we quit the for loop


	def stopListenerThread(self):
		self.isInputThreadStarted = False
		self.device.isInputThreadStarted = False
		print("[PSSM - Touch handler] : Input thread stopped")
