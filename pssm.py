#!/usr/bin/env python
import sys
import os
import threading
# Load Pillow
from PIL import Image, ImageDraw, ImageFont
from PIL.ImageOps import invert as PILInvert
from copy import deepcopy

lastUsedId=0

def coordsInArea(click_x,click_y,area):
	[(x,y),(w,h)] = area
	if click_x>=x and click_x<x+w and click_y>=y and click_y<y+h:
		return True
	else:
		return False

def getRectanglesIntersection(area1,area2):
	(x1,y1),(w1,h1) = area1
	(x2,y2),(w2,h2) = area2
	x0a = max(x1,x2)
	x0b = min(x1+w1,x2+w2)
	y0a = max(y1,y2)
	y0b = min(y1+h1,y2+h2)
	w0 = x0b-x0a
	h0 = y0b-y0a
	if  w0 > 0 and h0 > 0:
		return [(x0a,y0a),(w0,h0)]
	else:
		return None

def returnFalse(*args):
	return False

def pillowImgToElement(img,x,y,name="noname",onclickInside=returnFalse,isInverted=False,data=[],tags=set()):
	area = [(x,y),(img.width,img.height)]
	elt =  Element(area=area,imgData=img, onclickInside=onclickInside,isInverted=isInverted,data=data,tags=tags)
	return elt


class Element:
	def __init__(
			self,
			area=None,
			imgData=None,
			onclickInside=returnFalse,
			isInverted=False,
			data=[],
			tags=set(),
			invertOnClick = False,
			invertDuration = 0.5
		):
		"""
		If onclickInside == None, then the stack will keep searching for another Element under this one.
		Use onclickInside == returnFalse if you want the stack to do nothing when touhching the Element.
		OnclickInside and onclickOutside will be given as argument : x,y,data
		"""
		global lastUsedId
		self.id = lastUsedId
		lastUsedId += 1
		self.subclass = None
		self.imgData = imgData
		self.area = area
		self.onclickInside = onclickInside
		self.isInverted = isInverted
		self.user_data = data
		self.invertOnClick = invertOnClick
		self.tags=tags
		self.default_invertDuration = invertDuration
		self.parentStackManager = None

	def __hash__(self):
		return hash(self.id)

	def __eq__(self, other):
		if isinstance(other, self.__class__):
			return self.id == other.id
		return NotImplemented

	def updateAttributes(self,newParams):
		"""
		Pass a dict as argument, and it will update the Element's attributes accordingly
		"""
		for param in newParams:
			setattr(self, param, newParams[param])
		return True

	def generator(self):
		"""
		A basic Element has no generator
		"""
		return NotImplemented

	def setInverted(self,mode):
		self.isInverted = mode


class ScreenStackManager:
	def __init__(
			self,
			deviceName,
			name="screen",
			stack=[],
			isInverted=False
		):
		if deviceName == "Kobo":
			import pssm_kobo as pssm_device
		else:
			import pssm_opencv as pssm_device
		self.device = pssm_device
		self.width = self.device.screen_width
		self.height = self.device.screen_height
		self.view_width = self.device.view_width
		self.view_height = self.device.view_height
		self.w_offset = self.device.w_offset
		self.h_offset = self.device.h_offset
		self.area = [(0,0),(self.view_width,self.view_height)]
		self.name = name
		self.stack = stack
		self.isInverted = isInverted
		self.isPrintLocked = False
		self.isInputThreadStarted = False
		self.lastX = -1
		self.lastY = -1

	def findEltWithId(self,myElementId):
		for elt in self.stack:
			if elt.id == myElementId:
				return elt
		return None

	def printStack(self,skipEltId=None,area=None):
		"""
		Prints the stack Elements in the stack order
		If a skipElt is specified, then the function will not display the skipElt.
		If a area is set, then, we only display
		the part of the stack which is in this area
		> skipEltId : The ID of a PSSM Element
		> area : a [(x,y),(w,h)] array
		"""
		if self.isPrintLocked:
			return False
		[(x,y),(w,h)] = area
		mainIntersectionArea = [(x,y),(w,h)] if area else [(0,0),(self.width,self.height)]
		placeholder = Image.new('L', (mainIntersectionArea[1][0]-mainIntersectionArea[0][0],mainIntersectionArea[1][1]-mainIntersectionArea[0][1]), color=255)
		for elt in self.stack:
			if (not skipEltId) or (skipEltId and elt.id != skipEltId):
				# We loop through the Elements behind the Element we are working on
				rectIntersection = getRectanglesIntersection(mainIntersectionArea,elt.area)
				if rectIntersection != None:
					# The elt we are looking at is behind the myElement
					intersectionImg = self.getPartialEltImg(elt,rectIntersection)
					placeholder.paste(intersectionImg,(rectIntersection[0][0],rectIntersection[0][1]))
		raw_data=placeholder
		self.device.print_pil(raw_data,mainIntersectionArea[0][0], mainIntersectionArea[0][1],placeholder.width,placeholder.height,isInverted=self.isInverted)

	def getPartialEltImg(self,elt,rectIntersection):
		"""
		Returns a PIL image of the the interesection of the Element image and the
		rectangle coordinated given as parameter.
		> elt : a PSSM Element
		> rectIntersection : a [[x1,y1],[x2,y2]] array
		"""
		#TODO : MUST HONOR INVERSION
		# We crop and print a part of the Element
		# First, lets make a PILLOW Element:
		[(x,y),(w,h)] = elt.area
		img = deepcopy(elt.imgData)
		# Then, lets crop it:
		img = img.crop((rectIntersection[0][0]-x, rectIntersection[0][1]-y, rectIntersection[1][0]-x, rectIntersection[1][1]-y))
		if elt.isInverted:
			inverted_img = PILInvert(img)
			return inverted_img
		else:
			return img

	def simplePrintElt(self,myElement):
		"""
		Prints the Element without adding it to the stack
		"""
		# First, the element must be generated
		myElement.generator()
		if not self.isPrintLocked:
			[(x,y),(w,h)] = myElement.area
			self.device.print_pil(myElement.imgData,x, y, w, h, isInverted=myElement.isInverted)
		else:
			print("[PSSM] Print is locked, no image was updated")

	def createCanvas(self,color=255):
		"""
		Creates a white Element at the bottom of the stack, displays it while refreshing the screen
		"""
		img = Image.new('L', (self.width,self.height), color=255)
		background = pillowImgToElement(img,0,0,name="Canvas")
		background.tags.add("Canvas")
		self.addElt(background)
		return True

	def addElt(self,myElement,skipPrint=False,skipRegistration=False):
		"""
		Adds Element to the stack and prints it
		> myElement : (PSSM Element)
		> skipPrint : (boolean) True if you don't want to update the screen
		> skipRegistration : (boolean) True if you don't want to add the Element to the stack
		"""
		for i in range(len(self.stack)):
			elt=self.stack[i]
			if elt.id == myElement.id:
				# There is already an Element in the stack with the same ID.
				# Let's update the Element in the stack
				if not skipPrint:
					self.stack[i] = myElement
					self.updateArea(myElement.area)
				break	#The Element is already in the stack
		else:
			# the Element is not already in the stack
			if not skipRegistration:
				self.forceAddElt(myElement)

	def forceAddElt(self,myElement):
		"""
		Adds Element to the stack and prints it, without checking if it is already here
		"""
		myElement.parentStackManager = self
		self.stack.append(myElement)
		self.simplePrintElt(myElement)

	def updateArea(self,area=None):
		"""
		Updates the Element : updates the stack and prints the Element and all the stack above it
		while keeping the stack position
		"""
		self.printStack(area=area)

	def removeElt(self,myElementId,skipPrint=False,weAlreadyHaveTheElt=None):
		"""
		Removes the Element from the stack and hides it from the screen
		"""
		# First, we print the stack where the Element useed to stand
		if not skipPrint:
			myElement=self.findEltWithId(myElementId)
			self.printStack(skipEltId=myElementId,area=myElement.area)
		# Then it can be removed from the stack
		if weAlreadyHaveTheElt:
			self.stack.remove(weAlreadyHaveTheElt)
		else :
			elt = self.findEltWithId(myElementId)
			if elt:
				self.stack.remove(elt)

	def getTagList(self):
		"""
		Returns the set of all tags from all Elements in the stack
		"""
		tags={}
		for elt in self.stack:
			tags.update(elt.tags)
		return tags

	def removeAllWithTag(self,tag):
		"""
		Removes every Element from the stack which have the specified tag
		"""
		stackCopy = deepcopy(self.stack) #It is unsage to loop through a mutable list which is being edited afterwards : some items are skipped
		for elt in stackCopy:
			if tag in elt.tags:
				self.removeElt(elt.id,skipPrint=True,weAlreadyHaveTheElt=elt)
		#Then we reprint the whole screen (yeah, the *whole* screen... Performance is not our goal)
		self.printStack()

	def invertAllWithTag(self,tag,invertDuration=-1):
		"""
		Removes all the Element which have a specific tag
		"""
		stackCopy = deepcopy(self.stack) #It is unsage to loop through a mutable list which is being edited afterwards : some items are skipped
		for elt in stackCopy:
			if tag in elt.tags:
				self.invertElt(myElementId=elt.id,invertDuration=-1,skipPrint=True)
		#Then we reprint the whole screen (yeah, the *whole* screen... Performance is not our goal)
		self.printStack()
		# If an invert duration is given, then start a timer to go back to the original state
		if invertDuration>0:
			threading.Timer(invertDuration,self.invertAllWithTag,[tag,-1]).start()

	def getStackLevel(self,myElementId):
		elt = self.findEltWithId(myElementId)
		return self.stack.index(elt)

	def setStackLevel(self,myElementId,stackLevel="last"):
		"""
		Set the position of said Element
		Then prints every Element above it (including itself)
		"""
		#TODO : Must be able to accept another stackLevel
		if stackLevel=="last" or stackLevel==-1:
			stackLevel=len(self.stack)
			elt = self.findEltWithId(myElementId)
			self.removeElt(myElementId,skipPrint=True)
			self.stack.insert(stackLevel,elt)
			self.printStack(area=[elt.xy,elt.xy2])
			return True

	def invertElt(self,myElementId,invertDuration=-1,skipPrint=False):
		"""
		Inverts an Element
		> myElementId
		> invertDuration (int) : -1 or 0 if permanent, else an integer
		"""
		myElement = self.findEltWithId(myElementId)
		if myElement==None:
			return False
		# First, let's get the Element's initial inverted state
		Element_initial_state = bool(myElement.isInverted)
		# Then, we change the Element's state
		myElement.setInverted(not Element_initial_state)
		if not skipPrint:
			# Then we print the inverted version
			self.printStack(skipEltId=None, area=myElement.area)
		# Then, if an invertDuration is given, we setup a timer to go back to the original state
		if invertDuration and invertDuration>0:
			#Then, we start a timer to set it back to its intial state
			threading.Timer(invertDuration,myElement.setInverted,[Element_initial_state]).start()
			threading.Timer(invertDuration,self.invertElt,[myElementId,-1]).start()

	def invertArea(self,area,invertDuration,isInverted=False):
		"""
		Inverts an area
		"""
		# TODO: To be tested
		initial_mode = isInverted
		print("invertArea called ", isInverted)
		self.device.do_screen_refresh(
			isInverted	= not isInverted,
			area		= area,
			isPermanent	= False,
			isFlashing 	= False,
			w_offset	= self.w_offset,
			h_offset	= self.h_offset
		)
		if invertDuration>0:
			# Now we call this funcion, without starting a timer
			# And the screen is now in an opposite state as the initial one
			threading.Timer(invertDuration,self.invertArea,[area,-1,not initial_mode]).start()
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

	def startListenerThread(self,grabInput=False):
		"""
		Starts the touch listener as a separate thread
		> grabInput : (boolean) Whether to do an EVIOCGRAB IOCTL call to prevent
			another software from registering touch events
		"""
		self.isInputThreadStarted = True
		self.device.isInputThreadStarted = True
		print("[PSSM - Touch handler] : Input thread started")
		threading.Thread(target=self.device.eventBindings,args=[self.clickHandler,True,grabInput]).start()

	def clickHandler(self,x,y):
		n = len(self.stack)
		for i in range(n):
			j = n-1-i 	# We go through the stack in descending order
			elt = self.stack[j]
			if elt.area == None:
				# An object without area, it should not happen, but if it does,
				# it can be skipped
				continue
			if coordsInArea(x,y,elt.area):
				if elt.onclickInside != None:
					self.lastX = x
					self.lastY = y
					if elt.subclass == "Layout":
						if elt.onclickInside != None:
							elt.onclickInside(elt,(x,y))
						if elt.invertOnClick:
							self.invertArea(elt.area,elt.default_invertDuration)
						elt.dispatchClick((x,y))
					else:
						if elt.invertOnClick:
							self.invertArea(elt.area,elt.default_invertDuration)
						elt.onclickInside(elt,(x,y))
					break 		# we quit the for loop

	def stopListenerThread(self):
		self.isInputThreadStarted = False
		self.device.isInputThreadStarted = False
		print("[PSSM - Touch handler] : Input thread stopped")
