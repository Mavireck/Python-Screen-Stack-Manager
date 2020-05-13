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
white = 255
light_gray = 230
gray = 128
black = 0
Merri_regular = os.path.join(path_to_pssm,"fonts", "Merriweather-Regular.ttf")
Merri_bold = os.path.join(path_to_pssm,"fonts", "Merriweather-Bold.ttf")
standard_font_size = 30


def returnFalse(*args):
	return False


############################# - StackManager 	- ##############################
class ScreenStackManager:
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
		> area : a [(x,y),(w,h)] array
		"""
		#TODO : Must be retought to work with the new nested structure
		# for now it will just reprint the whole stack
		placeholder = Image.new('L', (self.width, self.height), color=255)
		for elt in self.stack:
			[(x,y),(w,h)] = elt.area
			placeholder.paste(elt.imgData, (x,y))
		[(x,y),(w,h)] = self.area
		self.device.print_pil(placeholder,x, y, w, h, isInverted=self.isInverted)

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

	def simplePrintElt(self,myElement,skipGeneration = False):
		"""
		Prints the Element without adding it to the stack
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

	def createCanvas(self,color=255):
		"""
		Creates a white Element at the bottom of the stack, displays it while refreshing the screen
		"""
		img = Image.new('L', (self.width,self.height), color=255)
		background = Static(img,0,0,name="Canvas")
		self.addElt(background)

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
				# We append the element to the stack
				myElement.parentStackManager = self
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
					if elt.isLayout:
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


############################# - Core Element	- ##############################
class Element:
	def __init__(
			self,
			area 			= None,
			imgData 		= None,
			onclickInside 	= returnFalse,
			isInverted 		= False,
			data 			= [],
			tags 			= set(),
			invertOnClick 	= False,
			invertDuration 	= 0.2
		):
		"""
		If onclickInside == None, then the stack will keep searching for another Element under this one.
		Use onclickInside == returnFalse if you want the stack to do nothing when touhching the Element.
		OnclickInside and onclickOutside will be given as argument : x,y,data
		"""
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
		self.parentStackManager = None

	def __hash__(self):
		return hash(self.id)

	def __eq__(self, other):
		if isinstance(other, self.__class__):
			return self.id == other.id
		return NotImplemented

	def update(self,newAttributes,skipGeneration=False):
		"""
		Pass a dict as argument, and it will update the Element's attributes accordingly
		"""
		# First, we set the attributes
		for param in newAttributes:
			setattr(self, param, newAttributes[param])
		if not skipGeneration:
			# Then we recreate the pillow image of this particular object
			self.generator()
			if len(self.parentLayouts) > 0:
				# We recreate the pillow image of the oldest parent
				# And it is not needed to regenerate standard objects, since
				oldest_parent = self.parentLayouts[0]
				oldest_parent.generator(skipNonLayoutEltGeneration=True)
			#then, let's reprint the stack
			self.parentStackManager.printStack(area=self.area)
		return True

	def generator(self):
		"""
		A basic Element has no generator
		"""
		return NotImplemented

	def setInverted(self,mode):
		self.isInverted = mode


############################# - Layout Elements	- ##############################
class Layout(Element):
	"""
	A layout is a quite general kind of Element :
	If must be given the working area, and a layout, and will generate every element of the layout
	"""
	def __init__(self,layout,area=None,background_color=white,**kwargs):
		super().__init__(area=area)
		self.layout      = layout
		self.background_color = background_color
		self.areaMatrix = None
		self.imgMatrix  = None
		self.borders    = None
		self.isLayout   = True
		for param in kwargs:
			setattr(self, param, kwargs[param])

	def generator(self,min_height=-1,min_width=-1,max_height=-1,max_width=-1,area=None):
		"""
		Builds one img out of all the Elements it is being given
		"""
		if area != None:
			self.area = area
		self.createAreaMatrix(min_height=min_height,min_width=min_width,max_height=max_height,max_width=max_width)
		self.createImgMatrix()
		[(x,y),(w,h)] = self.area
		placeholder = Image.new('L', (w,h), color=self.background_color)
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

	def createImgMatrix(self):
		matrix = []
		if not self.areaMatrix:
			print("Error, areaMatrix has to be defined first")
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
					myElement_img   = myElement.generator(area=myElement_area)
				row.append(myElement_img)
			matrix.append(row)
		self.imgMatrix = matrix

	def createAreaMatrix(self,min_height=-1,min_width=-1,max_height=-1,max_width=-1):
		# TODO : must honor min and max
		matrix = []
		n_rows = len(self.layout)
		[(x,y),(w,h)] = self.area[:]
		x0,y0=x,y
		for i in range(len(self.layout)):     # Lets loop through the rows
			row = self.layout[i]
			row_cols = []           # All the columns of this particular row
			row_height = row[0]
			converted_height = self.parentStackManager.convertDimension(row_height)
			if isinstance(converted_height,int):
				true_row_height = converted_height
			else:
				remaining_height = self.calculate_remainingHeight()
				true_row_height = int(eval(str(remaining_height) + converted_height[1:]))
			n_cols = len(row)     # Do not forget that the first item of each row is an int indicating the row height
			for j in range(1,n_cols):
				(element,element_width) = row[j]
				converted_width = self.parentStackManager.convertDimension(element_width)
				if element != None:
					self.layout[i][j][0].parentStackManager = self.parentStackManager
				if not isinstance(converted_width,int):
					remaining_width = self.calculate_remainingWidth(i)
					true_element_width = int(eval(str(remaining_width) + converted_width[1:]))
					self.layout[i][j] = (self.layout[i][j][0], true_element_width)
				else:
					true_element_width = converted_width
				element_area = [(x0,y0),(true_element_width,true_row_height)]
				x0 += true_element_width
				row_cols.append(element_area)
			y0 += true_row_height
			x0 = x
			matrix.append(row_cols)
		self.areaMatrix = matrix

	def calculate_remainingHeight(self):
		rows = self.extract_rowsHeight()
		total_questionMarks_weight = 0
		total_height = 0
		for dimension in rows:
			converted_dimension = self.parentStackManager.convertDimension(dimension)
			if isinstance(converted_dimension,int):
				total_height += converted_dimension
			else:
				weight = eval("1" + converted_dimension[1:])
				total_questionMarks_weight += weight
		layout_height = self.area[1][1]
		print(layout_height,total_height,total_questionMarks_weight)
		return int((layout_height - total_height)/total_questionMarks_weight)

	def calculate_remainingWidth(self,rowIndex):
		cols = self.extract_colsWidth(rowIndex)
		total_width = 0
		total_questionMarks_weight = 0
		for dimension in cols:
			converted_dimension = self.parentStackManager.convertDimension(dimension)
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
		# TODO : use dichotomy search instead of linear search with extract_rowsHeight and extract_colsWidth
		click_x,click_y = coords
		[(x,y),(w,h)] = self.area[:]
		is_found = False
		for i in range(len(self.areaMatrix)):
			for j in range(len(self.areaMatrix[i])):
				if coordsInArea(click_x,click_y,self.areaMatrix[i][j]):
					row,col=i,j
					is_found = True
					break
			if is_found:
				break
		if is_found:
			elt,_ = self.layout[row][col+1]
			if elt != None and elt.onclickInside != None:
				if elt.isLayout:
					if elt.onclickInside != None:
						elt.onclickInside(elt,coords)
					if elt.invertOnClick:
						elt.parentStackManager.invertArea(elt.area,elt.default_invertDuration)
					elt.dispatchClick(coords)
				else:
					if elt.invertOnClick:
						elt.parentStackManager.invertArea(elt.area,elt.default_invertDuration)
					elt.onclickInside(elt,coords)
			return True
		else:
			return False

class ButtonList(Layout):
	def __init__(self,buttons, margins=[0,0,0,0],spacing=0,**kwargs):
		"""
		Generates a Layout with one item per row, all the same type (buttons) and same height and width
		:button : a [{"text":"my text","onclickInside":onclickInside},someOtherDict,someOtherDict] array
		:borders : a [top,bottom,left,right]
		"""
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
	def __init__(self,background_color=255,outline=50):
		super().__init__()
		self.background_color = background_color
		self.outline = outline

	def generator(self,area):
		[(x,y),(w,h)] = area
		self.area = area
		img = Image.new('L', (w+1,h+1), color=white)
		rect = ImageDraw.Draw(img, 'L')
		rect.rectangle([(0,0),(w,h)],fill=self.background_color,outline=self.outline)
		self.imgData = img
		return self.imgData

class RectangleRounded(Element):
	def __init__(self,radius=20,background_color=255,outline=0):
		super().__init__()
		self.radius = radius
		self.background_color = background_color
		self.outline = outline

	def generator(self,area):
		[(x,y),(w,h)] = area
		self.area = area
		rectangle = Image.new('L', (w,h), white)
		draw = ImageDraw.Draw(rectangle)
		draw.rectangle([(0,0),(w,h)],fill=self.background_color,outline=self.outline)
		draw.line([(self.radius,h-1),(w-self.radius,h-1)],fill=self.outline,width=1)
		draw.line([(w-1,self.radius),(w-1,h-self.radius)],fill=self.outline,width=1)
		corner = roundedCorner(self.radius, self.background_color,self.outline)
		rectangle.paste(corner, (0, 0))
		rectangle.paste(corner.rotate(90), (0, h - self.radius)) # Rotate the corner and paste it
		rectangle.paste(corner.rotate(180), (w - self.radius, h - self.radius))
		rectangle.paste(corner.rotate(270), (w - self.radius, 0))
		self.imgData = rectangle
		return self.imgData

class Button(Element):
	def __init__(
			self,
			text,
			font=Merri_regular,
			font_size=standard_font_size,
			background_color=255,
			outline=0,
			radius=0,
			text_color=0,
			**kwargs
		):
		super().__init__()
		self.background_color   = background_color
		self.outline    = outline
		self.text       = text
		self.font       = font
		self.font_size  = font_size
		self.radius     = radius
		self.text_color = text_color
		for param in kwargs:
			setattr(self, param, kwargs[param])

	def generator(self,area=None):
		loaded_font = ImageFont.truetype(self.font, self.font_size)
		if area==None:
			area = self.area
		[(x,y),(w,h)] = area
		self.area = area
		if self.radius>0:
			rect = RectangleRounded(radius=self.radius,background_color=self.background_color,outline=self.outline)
		else:
			rect = Rectangle(background_color=self.background_color,outline=self.outline)
		rect_img = rect.generator(self.area)
		imgDraw = ImageDraw.Draw(rect_img, 'L')
		text_w,text_h = imgDraw.textsize(self.text, font=loaded_font)
		x = tools_convertXArgsToPX("center",w,text_w)
		y = tools_convertYArgsToPX("center",h,text_h)
		imgDraw.text((x,y),self.text,font=loaded_font,fill=self.text_color)
		self.imgData = rect_img
		return self.imgData

class Icon(Element):
	def __init__(self,file):
		super().__init__()
		self.file = file

	def generator(self,area):
		"""
		Returns a  PIL image with the icon corresponding to the path you give as argument.
		If you pass "back", "delete" or another known image, it will fetch the integrated icons
		"""
		path_to_file = tools_parseKnownImageFile(file)
		iconImg = Image.open(path_to_file).convert("L").resize((icon_size,icon_size))
		self.imgData = iconImg
		return iconImg

class Static(Element):
	def __init__(self,pil_image,x,y,**kwargs):
		super().__init__()
		self.imgData = pil_image
		self.area = [(x,y),(pil_image.width,pil_image.height)]
		for param in kwargs:
			setattr(self, param, kwargs[param])



############################# - 	Tools 		- ##############################
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

def roundedCorner(radius, fill=255,outline=50):
	"""
	Draw a round corner
	"""
	corner = Image.new('L', (radius, radius), white)
	draw = ImageDraw.Draw(corner)
	draw.pieslice((0, 0, radius * 2, radius * 2), 180, 270, fill=fill,outline=outline)
	return corner

def tools_convertXArgsToPX(xPosition,objw,textw):
	"""
	Converts xPosition string arguments to numerical values
	"""
	if xPosition == "left":
		x = 0
	elif xPosition == "center":
		x = int(0.5*objw-0.5*textw)
	elif xPosition == "right":
		x = int(objw-textw)
	else:
		try:
			x = int(xPosition)
		except:
			print("[PSSMOL] Invalid input for xPosition")
			return False
	return x

def tools_convertYArgsToPX(yPosition,objh,texth):
	"""
	Converts yPosition string arguments to numerical values
	"""
	if yPosition == "top":
		y = 0
	elif yPosition == "center":
		y = int(0.5*objh-0.5*texth)
	elif yPosition == "bottom":
		y = int(objh-texth)
	else:
		try:
			y = int(yPosition)
		except:
			print("[PSSMOL] Invalid input for yPosition")
			return False
	return y

def tools_parseKnownImageFile(file):
	if file=="back":
		return path_to_pssm + "/icons/back.png"
	elif file=="delete":
		return path_to_pssm + "/icons/delete.jpg"
	elif file=="frontlight-down":
		return path_to_pssm + "/icons/frontlight-down.jpg"
	elif file=="frontlight-up":
		return path_to_pssm + "/icons/frontlight-up.jpg"
	elif file=="invert":
		return path_to_pssm + "/icons/invert.jpg"
	elif file=="reboot":
		return path_to_pssm + "/icons/reboot.jpg"
	elif file=="save":
		return path_to_pssm + "/icons/save.png"
	elif file=="touch-off":
		return path_to_pssm + "/icons/touch-off.png"
	elif file=="touch-on":
		return path_to_pssm + "/icons/touch-on.png"
	elif file=="wifi-lock":
		return path_to_pssm + "/icons/wifi-lock.jpg"
	elif file=="wifi-on":
		return path_to_pssm + "/icons/wifi-on.jpg"
	elif file=="wifi-off":
		return path_to_pssm + "/icons/wifi-off.jpg"
	else:
		return file
