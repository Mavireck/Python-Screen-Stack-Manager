#!/usr/bin/env python
import sys
import os
import threading
# Load Pillow
from PIL import Image, ImageDraw, ImageFont
from PIL.ImageOps import invert as PILInvert
from copy import deepcopy


############################ - VARIABLES - #####################################
lastUsedId=0

path_to_pssm = os.path.dirname(os.path.abspath(__file__))
DEFAULT_FONT = os.path.join(path_to_pssm,"fonts", "Merriweather-Regular.ttf")
Merri_bold = os.path.join(path_to_pssm,"fonts", "Merriweather-Bold.ttf")
STANDARD_FONT_SIZE = "h*0.036"

def returnFalse(*args):
	return False

############################# - StackManager 	- ##############################
class PSSMScreen:
	"""
	This is the class which handles most of the logic.

	Args:
		deviceName (str): "Kobo" for Kobo ereaders (and probably all FBInk supported devices)
		name (str): The name of the class instance (deprecated, I will eventually remove it)
		stack (list): Do not use it unless you know what you are doing. It is the list of all the pssm Elements which are on the screen
		isInverted (bool)

	Example of usage:
		screen = pssm.PSSMScreen("Kobo","Main"))

	"""
	def __init__(
			self,
			deviceName,
			name="screen",
			stack=[],
			isInverted=False
		):
		if deviceName == "Kobo":
			import devices.kobo.device as pssm_device
		else:
			import devices.emulator.device as pssm_device
		self.device = pssm_device
		self.colorType = self.device.colorType
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

	def findEltWithId(self,myElementId,stack=None):
		"""
		Returns the element which has such an ID.
		Avoid using this function as much as possible, as it is really not Performance-friendly
		(Recursive search through all the elements of the stack)
		And anyway there is no reason why you should use it.
		"""
		if stack == None:
			stack = self.stack
		for elt in stack:
			if elt.id == myElementId:
				return elt
			elif elt.isLayout:
				layoutEltList = elt.createEltList()
				search = self.findEltWithId(myElementId,stack=layoutEltList)
				if search != None:
					return search
		return None

	def printStack(self,area=None):
		"""
		Prints the stack Elements in the stack order
		If a area is set, then, we only display
		the part of the stack which is in this area
		"""
		#TODO : Must be retought to work with the new nested structure
		# for now it will just reprint the whole stack
		white = get_Color("white",self.colorType)
		placeholder = Image.new(self.colorType, (self.width, self.height), color=white)
		for elt in self.stack:
			[(x,y),(w,h)] = elt.area
			placeholder.paste(elt.imgData, (x,y))
		[(x,y),(w,h)] = self.area
		self.device.print_pil(placeholder,x, y, w, h, isInverted=self.isInverted)

	def getPartialEltImg(self,elt,rectIntersection):
		"""
		Returns a PIL image of the the interesection of the Element image and the
		rectangle coordinated given as parameter.
			elt : a PSSM Element
			rectIntersection : a [[x1,y1],[x2,y2]] array
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

	def simplePrintElt(self,myElement,skipGeneration = False):
		"""
		Prints the Element without adding it to the stack.
		Args:
			myElement (PSSM Element): The element you want to display
			skipGeneration (bool): Do you want to regenerate the image?
		"""
		if not skipGeneration:
			# First, the element must be generated
			myElement.generator()
		# Then, we print it
		if not self.isPrintLocked:
			[(x,y),(w,h)] = myElement.area
			# What follows is a Workaround :
			# TODO : this Workaround must be investigated
			if not myElement.isLayout:
				w += 1
				h += 1
			self.device.print_pil(myElement.imgData,x, y, w, h, isInverted=myElement.isInverted)
		else:
			print("[PSSM] Print is locked, no image was updated")

	def createCanvas(self,color="white"):
		"""
		(Deprecated)
		Creates a white Element at the bottom of the stack, displays it while refreshing the screen.
		"""
		color = get_Color(color,self.colorType)
		img = Image.new(self.colorType, (self.width,self.height), color=color)
		background = Static(img,0,0,name="Canvas")
		self.addElt(background)

	def addElt(self,myElement,skipPrint=False,skipRegistration=False):
		"""
		Adds Element to the stack and prints it
			myElement (PSSM Element): The Element you want to add
			skipPrint (bool): True if you don't want to update the screen
			skipRegistration (bool): True if you don't want to add the Element to the stack
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
				# We append the element to the stack
				myElement.parentPSSMScreen = self
				self.stack.append(myElement)
				self.simplePrintElt(myElement)

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

	def convertDimension(self,dimension):
		if isinstance(dimension,int):
			return dimension
		else:
			t  = dimension[0]
			op = dimension[1:]
			if t == "p":
				return int(eval("1" + op))
			elif t== "w":
				return int(eval(str(self.width) + op))
			elif t== "h":
				return int(eval(str(self.height) + op))
			else:
				return dimension

	def startListenerThread(self,grabInput=False):
		"""
		Starts the touch listener as a separate thread
		> grabInput : (boolean) Whether to do an EVIOCGRAB IOCTL call to prevent
			another software from registering touch events
		"""
		self.isInputThreadStarted = True
		self.device.isInputThreadStarted = True
		print("[PSSM - Touch handler] : Input thread started")
		args = [self.clickHandler,True,grabInput]
		inputThread = threading.Thread(target=self.device.eventBindings,args=args)
		inputThread.start()

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
					if elt != None:
						self.dispatchClickToElt((x,y),elt)
				break 		# we quit the for loop

	def dispatchClickToElt(self,coords,elt):
		"""
		Once given an object on which the user clicked, this function calls the
		appropriate function on the object (ie elt.onclickInside or elt.dispatchClick)
		It also handles inversion.
		"""
		if elt.isLayout:
			if elt.onclickInside != None:
				elt.onclickInside(elt,coords)
			if elt.invertOnClick:
				self.invertArea(elt.area,elt.default_invertDuration)
			elt.dispatchClick(coords)
		else:
			if elt.invertOnClick:
				self.invertArea(elt.area,elt.default_invertDuration)
			elt.onclickInside(elt,coords)

	def stopListenerThread(self):
		self.isInputThreadStarted = False
		self.device.isInputThreadStarted = False
		print("[PSSM - Touch handler] : Input thread stopped")


############################# - Core Element	- ##############################
class Element:
	"""
	Everything which is going to be displayed on the screen is an Element.

	Args:
		isInverted (bool): Is the element inverted
		data (dict, or whatever): A parameter for you to store whatever you want
		area (list): a [(x,y),(w,h)] list. If used in a Layout, the layout will take care of calculating the area.
		imgData (PILImage): the PIL image of the object (None by default, the generator function takes care of generating one on supported Elements)
		onclickInside (function): A function to be executed when the user clicks on the Element
		tags (set): A set of tags the element has. (deprecated)
		invertOnClick (bool): Invert the element when a click is registered ?
		invertDuration (int): Duration in seconds of the element invertion after a click is registered (use 0 for infinite)
	"""
	def __init__(
			self,
			area 			= None,
			imgData 		= None,
			onclickInside 	= returnFalse,
			isInverted 		= False,
			data 			= {},
			tags 			= set(),
			invertOnClick 	= False,
			invertDuration 	= 0.2
		):
		global lastUsedId
		self.id = lastUsedId
		lastUsedId += 1
		self.isLayout = False
		self.imgData = imgData
		self.area = area
		self.onclickInside = onclickInside
		self.isInverted = isInverted
		self.user_data = data
		self.invertOnClick = invertOnClick
		self.tags=tags
		self.default_invertDuration = invertDuration
		self.parentLayouts = []
		self.parentPSSMScreen = None

	def __hash__(self):
		return hash(self.id)

	def __eq__(self, other):
		if isinstance(other, self.__class__):
			return self.id == other.id
		return NotImplemented

	def update(self,newAttributes,skipGeneration=False,skipThisEltGeneration=False,skipPrint=False):
		"""
		Pass a dict as argument, and it will update the Element's attributes accordingly
		Args :
			newAttributes (dict): The element's new attributes
			skipGeneration (bool): Just update the element's attribute, but do not do any generation or printing
			skipThisEltGeneration (bool): Do not regenerate this element but do update the parent layouts
			skipPrint (bool): Do not update the screen, but do regenerate.
		"""
		# First, we set the attributes
		for param in newAttributes:
			setattr(self, param, newAttributes[param])
		if not skipGeneration:
			# Then we recreate the pillow image of this particular object
			if not skipThisEltGeneration:
				self.generator()
			if len(self.parentLayouts) > 0:
				# We recreate the pillow image of the oldest parent
				# And it is not needed to regenerate standard objects, since
				oldest_parent = self.parentLayouts[0]
				oldest_parent.generator(skipNonLayoutEltGeneration=True)
			#then, let's reprint the stack
			if not skipPrint:
				self.parentPSSMScreen.printStack(area=self.area)
		return True

	def generator(self):
		"""
		The generator is the function which is called when the container layout wants to
		build an image. It therefore returns a pillow image.
		"""
		return NotImplemented

	def setInverted(self,mode):
		# TODO : actually invert it ? or delete this function
		self.isInverted = mode


############################# - Layout Elements	- ##############################
class Layout(Element):
	"""
	A layout is a quite general kind of Element :
	If must be given the working area, and a layout, and will generate every element of the layout

	Args:
		layout (list): The given layout (see example below). It is basically a list of rows. Each row is a list containing : the height of the row, then as many tuples as you want, each tuple being a (pssm.Element, width) instance
		background_color
		area
		... all other arguments from the pssm.Element class

	Example of usage:
		layout_demo = [
	        [30                                                                                         ],
	        ["h*0.1", (None,"?/2"),        (pssm.Button("But1"),200),        (None,"?/2")               ],
	        ["?"                                                                                        ],
	        ["p*100", (None,"w*0.3"),       (pssm.Button("But2"),200),        (None,"w*0.3")            ],
	        [30                                                                                         ],
	        [100, (None,20), (pssm.Button("But3"),200), (None,20), (pssm.Button("nope"),300), (None,10) ],
	        [40                                                                                         ]
	    ]
	    myLayout = pssm.Layout(layout_demo,screen.area)
	    screen.addElt(myLayout)
	"""
	def __init__(self,layout,area=None,background_color="white",**kwargs):
		super().__init__(area=area)
		self.layout      = layout
		self.isValid = self.isLayoutValid()
		self.background_color = background_color
		self.areaMatrix = None
		self.imgMatrix  = None
		self.borders    = None
		self.isLayout   = True
		for param in kwargs:
			setattr(self, param, kwargs[param])

	def isLayoutValid(self):
		# TODO : to be tested
		l = self.layout
		if not isinstance(l,list):
			raise Exception("Layout Element is supposed to be a list")
		for row in l:
			if not isinstance(row,list):
				raise Exception("A layout row is supposed to be a list")
			elif len(row) == 0:
				raise Exception("A layout row cannot be empty")
			elif not isinstance(row[0],str) and not isinstance(row[0],int):
				raise Exception("The first element of a row (its height) should be a string or an integer")
			for j in range(1,len(row)):
				eltTuple = row[j]
				if not (isinstance(eltTuple,tuple) or isinstance(eltTuple,list)):
					raise Exception("A layout row should be a list of Tuple (except for its first element)")
				if len(eltTuple) != 2:
					raise Exception("A layout element should be a Tuple : (Element, elementWidth)")
				if not (isinstance(eltTuple[1],str) or isinstance(eltTuple[1],int)):
					raise Exception("An element width should be a string or an integer")
				if not (isinstance(eltTuple[0],Element) or eltTuple[0] == None):
					raise Exception("A layout element should be a Tuple : (Element, elementWidth), with Element designating a PSSM Element")
		return True

	def generator(self,area=None, skipNonLayoutEltGeneration=False):
		"""
		Builds one img out of all the Elements it is being given
		"""
		if area != None:
			self.area = area
		self.createAreaMatrix()
		self.createImgMatrix(skipNonLayoutEltGeneration=skipNonLayoutEltGeneration)
		[(x,y),(w,h)] = self.area
		placeholder = Image.new(
			self.parentPSSMScreen.colorType,
			(w,h),
			color=get_Color(self.background_color,self.parentPSSMScreen.colorType)
		)
		for i in range(len(self.areaMatrix)):
			for j in range(len(self.areaMatrix[i])):
				[(elt_x,elt_y),(elt_w,elt_h)] = self.areaMatrix[i][j]
				relative_x = elt_x - x
				relative_y = elt_y - y
				elt_img = self.imgMatrix[i][j]
				if elt_img != None:
					placeholder.paste(self.imgMatrix[i][j],(relative_x,relative_y))
		self.imgData = placeholder
		return self.imgData

	def createImgMatrix(self,skipNonLayoutEltGeneration=False):
		matrix = []
		if not self.areaMatrix:
			print("[PSSM Layout Element] Error, areaMatrix has to be defined first")
			return None
		for i in range(len(self.layout)):
			row = []
			for j in range(1,len(self.layout[i])):
				myElement,_   = self.layout[i][j]
				if myElement == None:
					myElement_area  = self.areaMatrix[i][j-1]
					myElement_img   = None
				else:
					myElement_area  = self.areaMatrix[i][j-1]
					if not myElement.isLayout and skipNonLayoutEltGeneration:
						myElement_img = myElement.imgData
					else:
						myElement_img   = myElement.generator(area=myElement_area)
				row.append(myElement_img)
			matrix.append(row)
		self.imgMatrix = matrix

	def createAreaMatrix(self):
		# TODO : must honor min and max
		matrix = []
		n_rows = len(self.layout)
		[(x,y),(w,h)] = self.area[:]
		x0,y0=x,y
		for i in range(len(self.layout)):     # Lets loop through the rows
			row = self.layout[i]
			row_cols = []           # All the columns of this particular row
			row_height = row[0]
			converted_height = self.parentPSSMScreen.convertDimension(row_height)
			if isinstance(converted_height,int):
				true_row_height = converted_height
			else:
				remaining_height = self.calculate_remainingHeight()
				true_row_height = int(eval(str(remaining_height) + converted_height[1:]))
			for j in range(1,len(row)):
				(element,element_width) = row[j]
				converted_width = self.parentPSSMScreen.convertDimension(element_width)
				if element != None:
					for parent in self.parentLayouts:
						self.layout[i][j][0].parentLayouts.append(parent)
					self.layout[i][j][0].parentLayouts.append(self)
					self.layout[i][j][0].parentPSSMScreen = self.parentPSSMScreen
				if isinstance(converted_width,int):
					true_element_width = converted_width
				else:
					remaining_width = self.calculate_remainingWidth(i)
					true_element_width = int(eval(str(remaining_width) + converted_width[1:]))
					self.layout[i][j] = (self.layout[i][j][0], true_element_width)
				element_area = [(x0,y0),(true_element_width,true_row_height)]
				x0 += true_element_width
				row_cols.append(element_area)
			y0 += true_row_height
			x0 = x
			matrix.append(row_cols)
		self.areaMatrix = matrix

	def createEltList(self):
		"""
		Returns a list of all the elements the Layout Element contains
		"""
		eltList=[]
		for row in self.layout:
			for i in range(1,len(row)):
				elt,_ = row[i]
				if elt != None:
					eltList.append(elt)
		return eltList

	def calculate_remainingHeight(self):
		rows = self.extract_rowsHeight()
		total_questionMarks_weight = 0
		total_height = 0
		for dimension in rows:
			converted_dimension = self.parentPSSMScreen.convertDimension(dimension)
			if isinstance(converted_dimension,int):
				total_height += converted_dimension
			else:
				weight = eval("1" + converted_dimension[1:])
				total_questionMarks_weight += weight
		layout_height = self.area[1][1]
		return int((layout_height - total_height)/total_questionMarks_weight)

	def calculate_remainingWidth(self,rowIndex):
		cols = self.extract_colsWidth(rowIndex)
		total_width = 0
		total_questionMarks_weight = 0
		for dimension in cols:
			converted_dimension = self.parentPSSMScreen.convertDimension(dimension)
			if isinstance(converted_dimension,int):
				total_width += converted_dimension
			else:
				weight = eval("1" + converted_dimension[1:])
				total_questionMarks_weight += weight
		layout_width = self.area[1][0]
		return int((layout_width - total_width)/total_questionMarks_weight)

	def extract_rowsHeight(self):
		rows = []
		for row in self.layout:
			rows.append(row[0])
		return rows

	def extract_colsWidth(self,rowIndex):
		cols = []
		for col in self.layout[rowIndex]:
			if isinstance(col,tuple):
				cols.append(col[1])
		return cols

	def dispatchClick(self,coords):
		"""
		Finds the element on which the user clicked
		"""
		self.dispatchClick_DICHOTOMY_colsOnly(coords)

	def dispatchClick_LINEAR(self,coords):
		"""
		Linear search throuh both the rows and the columns
		"""
		click_x,click_y = coords
		for i in range(len(self.areaMatrix)):			# Linear search though the rows
			if len(self.areaMatrix[i]) == 0:
				# That's a fake row (a margin row)
				continue
			first_row_elt = self.areaMatrix[i][0]
			last_row_elt = self.areaMatrix[i][-1]
			x = first_row_elt[0][0]
			y = first_row_elt[0][1]
			w = last_row_elt[0][0] + last_row_elt[1][0] - first_row_elt[0][0]
			h = last_row_elt[0][1] + last_row_elt[1][1] - first_row_elt[0][1]
			if coordsInArea(click_x, click_y, [(x,y),(w,h)]):		# CLick was in that row
				for j in range(len(self.areaMatrix[i])):			# Linear search through the columns
					if coordsInArea(click_x,click_y,self.areaMatrix[i][j]):
						# Click was on that element
						elt,_ = self.layout[i][j+1]
						if elt != None and elt.onclickInside != None:
							self.parentPSSMScreen.dispatchClickToElt(coords,elt)
						return True
		return False

	def dispatchClick_DICHOTOMY_colsOnly(self,coords):
		"""
		Linear search through the rows, dichotomy for the columns
		(Because of the empty rows, a dichotomy for the rows doesn't work)
		"""
		click_x,click_y = coords
		row_A = -1
		for i in range(len(self.areaMatrix)):						# Linear search though the rows
			if len(self.areaMatrix[i]) == 0:
				# That's a fake row (a margin row)
				continue
			first_row_elt = self.areaMatrix[i][0]
			last_row_elt = self.areaMatrix[i][-1]
			x = first_row_elt[0][0]
			y = first_row_elt[0][1]
			w = last_row_elt[0][0] + last_row_elt[1][0] - first_row_elt[0][0]
			h = last_row_elt[0][1] + last_row_elt[1][1] - first_row_elt[0][1]
			if coordsInArea(click_x, click_y, [(x,y),(w,h)]):		# CLick was in that row
				row_A = i
				break
		if row_A ==-1:
			return None
		col_A = 0
		col_C = max(len(self.areaMatrix[row_A]) - 1,0)
		xA = self.areaMatrix[row_A][col_A][0][0]
		xC = self.areaMatrix[row_A][col_C][0][0]
		if click_x < xA:
			return None
		if click_x > xC + self.areaMatrix[row_A][col_C][1][0]:
			return None
		while col_C > col_A +1:
			col_B = int(0.5*(col_A+col_C))  	# The average of the two
			xB = self.areaMatrix[row_A][col_B][0][0]
			if click_x >= xB or col_B==col_C:
				col_A = col_B
				xA = xB
			else:
				col_C = col_B
				xC = xB
		## Element is at indexes row_A, col_A
		elt,_ = self.layout[row_A][col_A+1]
		if elt != None and elt.onclickInside != None:
			self.parentPSSMScreen.dispatchClickToElt(coords,elt)
		return True

	def dispatchClick_DICHOTOMY_Full_ToBeFixed(self,coords):
		"""
		Finds the element on which the user clicked
		Implemented with dichotomy search (with the hope of making things faster,
		especially the integrated keyboard)
		"""
		# TODO : To be fixed
		# For now it does not work, because there are empty rows which break the loop
		click_x,click_y = coords
		row_A = 0
		row_C = max(len(self.areaMatrix) - 1,0)
		print(self.areaMatrix[row_C])
		while len(self.areaMatrix[row_A])==0:
			row_A += 1
		while len(self.areaMatrix[row_C])==0:
			row_C -= 1
		yA = self.areaMatrix[row_A][0][0][1]  # First column THEN first row , [(x,y),(w,h)] THUS first tuple of list THEN second coordinate of tuple
		yC = self.areaMatrix[row_C][0][0][1]
		if click_y < yA:
			return None
		if click_y > yC + self.areaMatrix[row_C][0][1][1]:
			return None
		while row_C > row_A+1:
			row_B = int(0.5*(row_A+row_C))  	# The average of the two
			while len(self.areaMatrix[row_B])==0:
				row_B += 1
			yB = self.areaMatrix[row_B][0][0][1]
			if click_y >= yB or row_B==row_C:
				row_A = row_B
				yA = yB
			else:
				row_C = row_B
				yC = yB
		# User clicked on element ar row of index row_A
		# Let's do the same for the column
		col_A = 0
		col_C = max(len(self.areaMatrix[row_A]) - 1,0)
		xA = self.areaMatrix[row_A][col_A][0][0]
		xC = self.areaMatrix[row_A][col_C][0][0]
		if click_x < xA:
			return None
		if click_x > xC + self.areaMatrix[row_A][col_C][1][0]:
			return None
		while col_C > col_A +1:
			col_B = int(0.5*(col_A+col_C))  	# The average of the two
			xB = self.areaMatrix[row_A][col_B][0][0]
			if click_x >= xB or col_B==col_C:
				col_A = col_B
				xA = xB
			else:
				col_C = col_B
				xC = xB
		## Element is at indexes row_A, col_A
		elt,_ = self.layout[row_A-2][col_A+1]
		if elt != None and elt.onclickInside != None:
			self.parentPSSMScreen.dispatchClickToElt(coords,elt)
		return True


class ButtonList(Layout):
	"""
	Generates a Layout with only one item per row, all the same type (buttons) and same height and width
	Args:
		button (list): a [{"text":"my text","onclickInside":onclickInside},someOtherDict,someOtherDict] array. Each dict will contain the parameters of each button of the button list
		borders (list): a [top,bottom,left,right] array
	"""
	def __init__(self,buttons, margins=[0,0,0,0],spacing=0,**kwargs):
		self.buttons = buttons
		self.margins = margins
		self.spacing = spacing
		layout = self.build_layoutFromButtons()
		super().__init__(layout)
		for param in kwargs:
			setattr(self, param, kwargs[param])

	def build_layoutFromButtons(self):
		#TODO : must honor min_width,max_width etc
		[top,bottom,left,right] = self.margins
		buttonLayout = [[top-self.spacing]]
		for button in self.buttons:
			buttonElt = Button(text=button['text'])
			for param in button:
				setattr(buttonElt, param, button[param])
			row_height = "?"
			buttonLayout.append([self.spacing])
			row = [row_height,(None,left),(buttonElt,"?"),(None,right)]
			buttonLayout.append(row)
		buttonLayout.append([bottom])
		return buttonLayout


############################# - Simple Elements	- ##############################
class Rectangle(Element):
	"""
	A rectangle
	Args:
		background_color (str): The background color
		outline_color (str): The border color
	"""
	def __init__(self,background_color="white",outline_color="gray3",parentPSSMScreen=None):
		super().__init__()
		self.background_color = background_color
		self.outline_color = outline_color
		self.parentPSSMScreen = parentPSSMScreen

	def generator(self,area):
		[(x,y),(w,h)] = area
		self.area = area
		img = Image.new(
			self.parentPSSMScreen.colorType,
			(w+1,h+1),
			color=get_Color("white",self.parentPSSMScreen.colorType)
		)
		rect = ImageDraw.Draw(img, self.parentPSSMScreen.colorType)
		rect.rectangle(
			[(0,0),(w,h)],
			fill=get_Color(self.background_color,self.parentPSSMScreen.colorType),
			outline=get_Color(self.outline_color,self.parentPSSMScreen.colorType)
		)
		self.imgData = img
		return self.imgData

class RectangleRounded(Element):
	"""
	A rectangle, but with rounded corners
	"""
	def __init__(
			self,
			radius=20,
			background_color="white",
			outline_color="gray3",
			parentPSSMScreen=None
		):
		super().__init__()
		self.radius = radius
		self.background_color = background_color
		self.outline_color = outline_color
		self.parentPSSMScreen = parentPSSMScreen

	def generator(self,area):
		[(x,y),(w,h)] = area
		self.area = area
		rectangle = Image.new(
			self.parentPSSMScreen.colorType,
			(w,h),
			color=get_Color("white",self.parentPSSMScreen.colorType)
		)
		draw = ImageDraw.Draw(rectangle)
		draw.rectangle(
			[(0,0),(w,h)],
			fill=get_Color(self.background_color,self.parentPSSMScreen.colorType),
			outline=get_Color(self.outline_color,self.parentPSSMScreen.colorType)
		)
		draw.line(
			[(self.radius,h-1),(w-self.radius,h-1)],
			fill  = get_Color(self.outline_color, self.parentPSSMScreen.colorType),
			width = 1
		)
		draw.line(
			[(w-1,self.radius),(w-1,h-self.radius)],
			fill  = get_Color(self.outline_color, self.parentPSSMScreen.colorType),
			width = 1
		)
		corner = roundedCorner(
			self.radius,
			self.background_color,
			self.outline_color,
			self.parentPSSMScreen.colorType
		)
		rectangle.paste(corner, (0, 0))
		rectangle.paste(corner.rotate(90), (0, h - self.radius)) # Rotate the corner and paste it
		rectangle.paste(corner.rotate(180), (w - self.radius, h - self.radius))
		rectangle.paste(corner.rotate(270), (w - self.radius, 0))
		self.imgData = rectangle
		return self.imgData

class Button(Element):
	"""
	Basically a rectangle (or rounded rectangle) with text printed on it
	Args:
		font (str): Path to a font file
		font_size (int): The font size
		font_color (str): The color of the font : "white", "black", "gray0" to "gray15" or a (red, green, blue, transparency) tuple
		wrap_textOverflow (bool): (True by default) Wrap text in order to avoid it overflowing. The cuts are made between words.
		text_xPosition (str or int): can be left, center, right, or an integer value, or a pssm string dimension
		text_yPosition (str or int): can be left, center, right, or an integer value, or a pssm string dimension
		background_color (str): The background color
		outline_color (str): The border color
		radius (int): If not 0, then add rounded corners of this radius
	"""
	def __init__(
			self,
			text,
			font=DEFAULT_FONT,
			font_size=STANDARD_FONT_SIZE,
			background_color="white",
			outline_color="black",
			radius=0,
			font_color="black",
			text_xPosition="center",
			text_yPosition="center",
			wrap_textOverflow = True,
			**kwargs
		):
		super().__init__()
		self.background_color   = background_color
		self.outline_color    	= outline_color
		self.text       		= text
		self.font       		= font
		self.font_size  		= font_size
		self.radius     		= radius
		self.font_color 		= font_color
		self.text_xPosition 	= text_xPosition
		self.text_yPosition 	= text_yPosition
		self.wrap_textOverflow 	= wrap_textOverflow
		for param in kwargs:
			setattr(self, param, kwargs[param])

	def generator(self,area=None):
		if area==None:
			area = self.area
		[(x,y),(w,h)] = area
		self.area = area
		if not isinstance(self.font_size,int):
			self.font_size = self.parentPSSMScreen.convertDimension(self.font_size)
			if not isinstance(self.font_size,int):
				# That's a question mark dimension, or an invalid dimension. Rollback to default font size
				self.font_size = self.parentPSSMScreen.convertDimension(STANDARD_FONT_SIZE)
		loaded_font = ImageFont.truetype(self.font, self.font_size)
		if self.radius>0:
			rect = RectangleRounded(
				radius=self.radius,
				background_color 	= self.background_color,
				outline_color 		= self.outline_color,
				parentPSSMScreen 	= self.parentPSSMScreen
			)
		else:
			rect = Rectangle(
				background_color	= self.background_color,
				outline_color		= self.outline_color,
				parentPSSMScreen 	= self.parentPSSMScreen
			)
		rect_img = rect.generator(self.area)
		imgDraw  = ImageDraw.Draw(rect_img, self.parentPSSMScreen.colorType)
		myText 	 = self.wrapText(self.text,loaded_font,imgDraw) if self.wrap_textOverflow else self.text
		text_w,text_h = imgDraw.textsize(self.text, font=loaded_font)
		x = tools_convertXArgsToPX(self.text_xPosition, w,text_w , parentPSSMScreen = self.parentPSSMScreen)
		y = tools_convertYArgsToPX(self.text_yPosition,h ,text_h , parentPSSMScreen = self.parentPSSMScreen)
		imgDraw.text(
			(x,y),
			myText,
			font=loaded_font,
			fill=get_Color(self.font_color, self.parentPSSMScreen.colorType)
		)
		self.imgData = rect_img
		return self.imgData

	def wrapText(self,text,loaded_font,imgDraw):
		def get_text_width(text):
			return imgDraw.textsize(text=text,font=loaded_font)[0]

		[(x,y),(max_width,h)] = self.area
		text_lines = [
			' '.join([w.strip() for w in l.split(' ') if w])
			for l in text.split('\n')
			if l
		]
		space_width = get_text_width(" ")
		wrapped_lines = []
		buf = []
		buf_width = 0

		for line in text_lines:
			for word in line.split(' '):
				word_width = get_text_width(word)

				expected_width = word_width if not buf else \
					buf_width + space_width + word_width

				if expected_width <= max_width:
					# word fits in line
					buf_width = expected_width
					buf.append(word)
				else:
					# word doesn't fit in line
					wrapped_lines.append(' '.join(buf))
					buf = [word]
					buf_width = word_width
			if buf:
				wrapped_lines.append(' '.join(buf))
				buf = []
				buf_width = 0
		return '\n'.join(wrapped_lines)

class Icon(Element):
	"""
	An icon, built from an image
	Args:
		file (str): Path to a file, or one of the integrated image (see the icon folder for the name of each image). 'reboot' for instance points to the integrated reboot image.
		centered (bool): Center the icon?
	"""
	def __init__(self,file,centered=True,**kwargs):
		super().__init__()
		self.file = file
		self.centered = centered
		self.path_to_file = tools_parseKnownImageFile(self.file)
		for param in kwargs:
			setattr(self, param, kwargs[param])

	def generator(self,area):
		self.area = area
		[(x,y),(w,h)] = area
		icon_size = min(area[1][0],area[1][1])
		iconImg = Image.open(self.path_to_file).convert(self.parentPSSMScreen.colorType).resize((icon_size,icon_size))
		if not self.centered:
			self.imgData = iconImg
			return iconImg
		else:
			img = Image.new(
				self.parentPSSMScreen.colorType,
				(w+1,h+1),
				color=get_Color("white",self.parentPSSMScreen.colorType)
			)
			img.paste(iconImg, (int(0.5*w-0.5*icon_size), int(0.5*h-0.5*icon_size)))
			self.imgData = img
			return img

class Static(Element):
	"""
	A very simple element which only displays a pillow image
	Args:
		pil_image (str or pil image): path to an image or a pillow image
		centered (bool): Center the image ?
		resize (bool): Make it fit the area ? (proportions are respected)
		rotation (int): an integer rotation angle
		background_color (str): "white", "black", "gray0" to "gray15" or a (red, green, blue, transparency) tuple
	"""
	def __init__(self,pil_image,centered=True,resize=True,background_color="white",rotation=0,**kwargs):
		super().__init__()
		if isinstance(pil_image,str):
			self.pil_image = Image.open(pil_image)
		else:
			self.pil_image = pil_image
		self.background_color = background_color
		self.centered = centered
		self.resize   = resize
		self.rotation = rotation
		for param in kwargs:
			setattr(self, param, kwargs[param])

	def generator(self,area=None):
		# TODO : crop or resize the image to make it fit the area
		(x,y),(w,h) = area
		pil_image = self.pil_image.convert(self.parentPSSMScreen.colorType)
		if self.resize:
			r = min(w/pil_image.width, h/pil_image.height)
			size = (int(pil_image.width*r), int(pil_image.height*r))
			pil_image = self.pil_image.resize(size)
		if self.rotation != 0:
			pil_image = pil_image.rotate(self.rotation,fillcolor=self.background_color)
		if not self.centered:
			return pil_image
		else:
			img = Image.new(
				self.parentPSSMScreen.colorType,
				(w+1,h+1),
				color=get_Color(self.background_color,self.parentPSSMScreen.colorType)
			)
			img.paste(pil_image, (int(0.5*w-0.5*pil_image.width), int(0.5*h-0.5*pil_image.height)))
			self.imgData = img
			return img

class Line(Element):
	"""
    Draws a simple line
    Args:
        color (str or tuple): "white", "black", "gray0" to "gray15" or a (red, green, blue, transparency) tuple
        width (int): The width of the line
        type (str): can be "horizontal", "vertical", "diagonal1" (top-left to bottom right) or "diagonal2" (top-right to bottom-left)
    """
	def __init__(self,color="black",width=1,type="horizontal"):
		super().__init__()
		self.color = color
		self.width = width
		self.type  = type

	def generator(self,area):
		(x,y),(w,h) = area
		self.area = area
		if self.type == "horizontal":
			coo = [(0,0),(w,0)]
		elif self.type == "vertical":
			coo = [(0,0),(0,h)]
		elif self.type == "diagonal1":
			coo = [(0,0),(w,h)]
		else: # Assuming diagonal2
			coo = [(w,0),(0,h)]
		rectangle = Image.new(
			self.parentPSSMScreen.colorType,
			(w,h),
			color=get_Color("white",self.parentPSSMScreen.colorType)
		)
		draw = ImageDraw.Draw(rectangle)
		draw.line(
			coo,
			fill  = get_Color(self.color, self.parentPSSMScreen.colorType),
			width = self.width
		)
		self.imgData = rectangle
		return self.imgData


############################# - 	Tools 		- ##############################
def coordsInArea(click_x,click_y,area):
    """
    Returns a boolean indicating if the click was in the given area
    Args:
        click_x (str): The x coordinate of the click
        click_y (str): The y coordinate of the click
        area (list): The area (of shape : [(x,y),(w,h)])
    """
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

def roundedCorner(radius, fill="white",outline_color="gray3",colorType='L'):
	"""
	Draw a round corner
	"""
	corner = Image.new(colorType, (radius, radius), "white")
	draw = ImageDraw.Draw(corner)
	draw.pieslice(
		(0, 0, radius * 2, radius * 2),
		180,
		270,
		fill=get_Color(fill,colorType),
		outline=get_Color(outline_color,colorType)
	)
	return corner

def tools_convertXArgsToPX(xPosition,objw,textw,parentPSSMScreen=None):
	"""
	Converts xPosition string arguments to numerical values
	"""
	xPosition = xPosition.lower()
	if xPosition == "left":
		x = 0
	elif xPosition == "center":
		x = int(0.5*objw-0.5*textw)
	elif xPosition == "right":
		x = int(objw-textw)
	else:
		try:
			converted = parentPSSMScreen.convertDimension(xPosition)
			x = int(converted)
		except:
			print("[PSSM] Invalid input for xPosition")
			return False
	return x

def tools_convertYArgsToPX(yPosition,objh,texth,parentPSSMScreen=None):
	"""
	Converts yPosition string arguments to numerical values
	"""
	yPosition = yPosition.lower()
	if yPosition == "top":
		y = 0
	elif yPosition == "center":
		y = int(0.5*objh-0.5*texth)
	elif yPosition == "bottom":
		y = int(objh-texth)
	else:
		try:
			converted = parentPSSMScreen.convertDimension(xPosition)
			y = int(converted)
		except:
			print("[PSSM] Invalid input for yPosition")
			return False
	return y

def tools_parseKnownImageFile(file):
	files={
		'back' 		: path_to_pssm + "/icons/back.png",
		'delete' 	: path_to_pssm + "/icons/delete.jpg",
		"frontlight-down"	: path_to_pssm + "/icons/frontlight-down.jpg",
		"frontlight-up"		: path_to_pssm + "/icons/frontlight-up.jpg",
		"invert"	: path_to_pssm + "/icons/invert.jpg",
		"reboot"	: path_to_pssm + "/icons/reboot.jpg",
		"save"		: path_to_pssm + "/icons/save.png",
		"touch-off"	: path_to_pssm + "/icons/touch-off.png",
		"touch-on"	: path_to_pssm + "/icons/touch-on.png",
		"wifi-lock"	: path_to_pssm + "/icons/wifi-lock.jpg",
		"wifi-on"	: path_to_pssm + "/icons/wifi-on.jpg",
		"wifi-off"	: path_to_pssm + "/icons/wifi-off.jpg"
	}
	if file in files:
		return files[file]
	else:
		return file


colorsL = {'black':0,'white':255}
colorsRGBA = {'black':(0,0,0,0),'white':(255,255,255,1)}
for i in range(16):
	s = int(i*255/15)
	colorsL['gray' + str(i)] 	= s
	colorsRGBA['gray' + str(i)] = (s,s,s,1)

def get_Color(color,deviceColorType):
	if isinstance(color,str):
		if deviceColorType == "L":
			try:
				return colorsL[color]
			except:
				print("Invalid color, ",color)
				return color
		elif deviceColorType == "RGBA":
			try:
				return colorsRGBA[color]
			except:
				print("Invalid color, ",color)
				return color
	elif isinstance(color,list) or isinstance(color,tuple):
		if deviceColorType == "RGBA":
			if len(color) == 4:
				return color
			else:
				#That's probably RGB
				try:
					return color + [1]
				except:
					return color + (1)
		else:
			r, g, b = color[0], color[1], color[2]
			gray = 0.2989 * r + 0.5870 * g + 0.1140 * b
			return gray


################################ - DOCUMENTATION - #############################
__pdoc__ = {} 			# For the documentation
ignoreList  =[
	'returnFalse',
	'coordsInArea',
	'getRectanglesIntersection',
	'roundedCorner',
	'tools_convertXArgsToPX',
	'tools_convertYArgsToPX',
	'tools_parseKnownImageFile',
	'get_Color',
	'PSSMScreen.getPartialEltImg',
	'PSSMScreen.convertDimension',
	'Layout.generator',
	'Layout.createImgMatrix',
	'Layout.createAreaMatrix',
	'Layout.calculate_remainingHeight',
	'Layout.calculate_remainingWidth',
	'Layout.extract_rowsHeight',
	'Layout.extract_colsWidth',
	'Layout.dispatchClick',
	'Layout.dispatchClick_LINEAR',
	'Layout.dispatchClick_DICHOTOMY_colsOnly',
	'Layout.dispatchClick_DICHOTOMY_Full_ToBeFixed'
]
for f in ignoreList:
	__pdoc__[f] = False
