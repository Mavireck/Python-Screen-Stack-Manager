#!/usr/bin/env python
import os
import json
import threading
# Load Pillow
from PIL import Image, ImageDraw, ImageFont, ImageOps
from copy import deepcopy
# Load some useful functions
from tools import returnFalse, coordsInArea, insertStr, getPartialEltImg, \
    getRectanglesIntersection, tools_convertXArgsToPX, tools_convertYArgsToPX,\
    tools_parseKnownImageFile, tools_parseKnownFonts, get_Color, debug, timer


# ########################## - VARIABLES - ####################################
lastUsedId = 0

# GENERAL
PATH_TO_PSSM = os.path.dirname(os.path.abspath(__file__))
DEFAULT_FONT = "default"
DEFAULT_FONTBOLD = "default-Bold"
DEFAULT_FONT_SIZE = "H*0.036"
CURSOR_CHAR = "|"
DEFAULT_INVERT_DURATION = 0.2


# OSK CONSTANTS
DEFAULT_KEYMAP_PATH_STANDARD = os.path.join(PATH_TO_PSSM,
                                            "config",
                                            "default-keymap-en_us.json")
DEFAULT_KEYMAP_PATH_CAPS = os.path.join(PATH_TO_PSSM,
                                        "config",
                                        "default-keymap-en_us_CAPS.json")
DEFAULT_KEYMAP_PATH_ALT = os.path.join(PATH_TO_PSSM,
                                       "config",
                                       "default-keymap-en_us_ALT.json")
DEFAULT_KEYMAP_PATH = {
    'standard': DEFAULT_KEYMAP_PATH_STANDARD,
    'caps': DEFAULT_KEYMAP_PATH_CAPS,
    'alt': DEFAULT_KEYMAP_PATH_ALT
}

KTstandardChar = 0
KTcarriageReturn = 1
KTbackspace = 2
KTdelete = 3
KTcapsLock = 4
KTcontrol = 5
KTalt = 6


# ########################## - StackManager    - ##############################
class PSSMScreen:
    """
    This is the class which handles most of the logic.

    Args:
        deviceName (str): "Kobo" for Kobo ereaders
            (and probably all FBInk supported devices)
        name (str): The name of the class instance
            (deprecated, I will eventually remove it)
        stack (list): Do not use it unless you know what you are doing.
            The list of all the pssm Elements which are on the screen.
        isInverted (bool): ...

    Attributes:
        device: the device.py module.
            You can with it access a few useful functions like
            `self.device.readBatteryPercentage()`
        colorType: "L" for grayscale devices, "RGBA" for others
        width: The screen width
        height : The screen height
        view_width: The width of the screen portion not hidden behind bezels
        view_height: ...
        name: ...
        isInverted: ...

    Example of usage:
        screen = pssm.PSSMScreen("Kobo","Main"))
    """
    def __init__(self, deviceName, name="screen", stack=[], isInverted=False):
        self.name = name
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
        self.area = [(0, 0), (self.view_width, self.view_height)]
        self.stack = stack
        self.isInverted = isInverted
        self.isInputThreadStarted = False
        self.lastX = -1
        self.lastY = -1
        self.osk = None
        self.numberEltOnTop = 0
        self.isOSKShown = False
        self.isBatch = False

    def findEltWithId(self, myElementId, stack=None):
        """
        (Deprecated)
        Returns the element which has such an ID.
        Avoid using this function as much as possible:
        it has terrible performance.
        (Recursive search through all the elements of the stack)
        And anyway there is no reason why you should use it.
        """
        if stack is None:
            stack = self.stack
        for elt in stack:
            if elt.id == myElementId:
                return elt
            elif elt.isLayout:
                layoutEltList = elt.createEltList()
                search = self.findEltWithId(myElementId, stack=layoutEltList)
                if search is not None:
                    return search
        return None

    def printStack(self, area=None, forceLayoutGen=False):
        """
        Prints the stack Elements in the stack order
        If a area is set, then, we only display
        the part of the stack which is in this area
        """
        if self.isBatch:
            # Do not do anything during batch mode
            return None
        pil_image = self.capture(area=area, forceLayoutGen=forceLayoutGen)
        if area:
            [(x, y), (w, h)] = area
        else:
            [(x, y), (w, h)] = self.area
        self.device.print_pil(pil_image, x, y, isInverted=self.isInverted)

    def capture(self,area=None, forceLayoutGen=False):
        """
        Returns a screen capture of the current stack state.
        """
        white = get_Color("white", self.colorType)
        dim = (self.width, self.height)
        img = Image.new(self.colorType, dim, color=white)
        for elt in self.stack:
            [(x, y), (w, h)] = elt.area
            if elt.isLayout and forceLayoutGen:
                elt.generator(area=elt.area, skipNonLayoutGen=True)
            if elt.isInverted:
                pil_image = ImageOps.invert(elt.imgData)
            else:
                pil_image = elt.imgData
            img.paste(pil_image, (x, y))
        if area:
            [(x, y), (w, h)] = area
            box = (x, y, x+w, y+h)
            return img.crop(box=box)
        else:
            return img

    def simplePrintElt(self, myElement, skipGen=False):
        """
        Prints the Element without adding it to the stack.
        Does not honor isBatch (you can simplePrint even during batch mode)
        Args:
            myElement (PSSM Element): The element you want to display
            skipGen (bool): Do you want to regenerate the image?
        """
        if not skipGen:
            # First, the element must be generated
            myElement.generator()
        # Then, we print it
        [(x, y), (w, h)] = myElement.area
        # What follows is a Workaround :
        self.device.print_pil(
            myElement.imgData,
            x, y,
            isInverted=myElement.isInverted
        )

    def startBatchWriting(self):
        """
        Toggle batch writing: nothing will be displayed on the screen until
        you use screen.stopBatchWriting()
        """
        self.isBatch = True

    def stopBatchWriting(self):
        """
        Updates the screen after batch writing
        """
        self.isBatch = False
        self.printStack(area=self.area, forceLayoutGen=True)

    def addElt(self, myElement, skipPrint=False, skipRegistration=False):
        """
        Adds Element to the stack and prints it
            myElement (PSSM Element): The Element you want to add
            skipPrint (bool): True if you don't want to update the screen
            skipRegistration (bool): True if you don't want to add the Element
                to the stack
        """
        for i in range(len(self.stack)):
            elt = self.stack[i]
            if elt.id == myElement.id:
                # There is already an Element in the stack with the same ID.
                # Let's update the Element in the stack
                if not skipPrint:
                    self.stack[i] = myElement
                    self.printStack(area=myElement.area)
                break   # The Element is already in the stack
        else:
            # the Element is not already in the stack
            if not skipRegistration:
                # We append the element to the stack
                myElement.parentPSSMScreen = self
                if self.numberEltOnTop > 0:
                    # There is something on top, addnig it at position -2
                    # (before the last one)
                    pos = - 1 - self.numberEltOnTop
                    self.stack.insert(pos, myElement)
                else:
                    self.stack.append(myElement)
                if not skipPrint :
                    if self.numberEltOnTop > 0 and not self.forcePrintOnTop:
                        # TODO : make it faster, we only need to display the
                        # image behind the keyboard, not reprint everything
                        myElement.generator()
                        self.printStack(area=myElement.area)
                    else:
                        # No keyboard on the horizon, let's do it
                        if self.isBatch:
                            # Then we only generate
                            myElement.generator()
                        else:
                            myElement.generator()
                            self.simplePrintElt(myElement, skipGen=True)

    def removeElt(self, elt=None, eltid=None, skipPrint=False):
        """
        Removes the Element from the stack and hides it from the screen
        """
        if elt:
            self.stack.remove(elt)
            if not skipPrint:
                self.printStack(area=elt.area)
        elif eltid:
            elt = self.findEltWithId(eltid)
            if elt:
                self.stack.remove(elt)
                if not skipPrint:
                    self.printStack(area=elt.area)
        else:
            print('No element given')

    def getStackLevel(self, myElementId):
        elt = self.findEltWithId(myElementId)
        return self.stack.index(elt)

    def setStackLevel(self, elt, stackLevel="last"):
        """
        Set the position of said Element
        Then prints every Element above it (including itself)
        """
        # TODO : Must be able to accept another stackLevel
        if stackLevel == "last" or stackLevel == -1:
            stackLevel = len(self.stack)
            self.removeElt(elt, skipPrint=True)
            self.stack.insert(stackLevel, elt)
            self.printStack(area=[elt.xy, elt.xy2])
            return True

    def invertElt(self, elt, invertDuration=-1,
                  useFastPrint=True, skipPrint=False):
        """
        Inverts an Element

        Args:
            elt (Element): The PSSM Element to invert
            invertDuration (int) : -1 or 0 if permanent, else an integer
            skipPrint (bool): Save only or save + print?
            useFastPrint (bool): Use FBInk's partial refresh with nightmode
                (much faster) instead of printing the whole stack.
        """
        if elt is None:
            print("No element given")
            return False
        # First, let's get the Element's initial inverted state
        Element_initial_state = bool(elt.isInverted)
        elt.isInverted = not Element_initial_state
        if not skipPrint:
            if useFastPrint:
                # Run as thread to make things a bit faster
                args = [
                    elt.area,
                    invertDuration,
                    not Element_initial_state
                ]
                invertThread = threading.Thread(
                    target=self._invertArea_helper,
                    args=args
                )
                invertThread.start()
                # self._invertArea_helper(elt.area, invertDuration, True)
            else:
                elt.update()
        elt.isInverted = Element_initial_state

    def _invertArea_helper(self, area, invertDuration, isInverted=False):
        """
        Helper function to properly setup the timer.
        """
        # TODO: To be tested
        initial_mode = isInverted
        isTemporaryinvertion = bool(invertDuration > 0)
        self.device.do_screen_refresh(
            isInverted=isInverted,
            area=area,
            isInvertionPermanent=False,
            isFlashing=False,
            useFastInvertion=True
        )
        if isTemporaryinvertion:
            # Now we call this funcion, without starting a timer
            # And the screen is now in an opposite state as the initial one
            myTimer = threading.Timer(
                interval=invertDuration,
                function=self._invertArea_helper,
                args=[area, -1, not initial_mode]
            )
            myTimer.start()
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

    def OSKInit(self, onKeyPress=None, area=None, keymapPath=None):
        if not area:
            x = 0
            y = int(2*self.view_height/3)
            w = self.view_width
            h = int(self.view_height/3)
            area = [(x, y), (w, h)]
        self.osk = OSK(onKeyPress=onKeyPress, area=area, keymapPath=keymapPath)

    def OSKShow(self, onKeyPress=None):
        if not self.osk:
            print("OSK not initialized, it can't be shown")
            return None
        if onKeyPress:
            self.osk.onKeyPress = onKeyPress
        self.addElt(self.osk)   # It has already been generated
        self.numberEltOnTop += 1
        self.isOSKShown = True

    def OSKHide(self):
        if self.isOSKShown:
            self.removeElt(elt=self.osk)
            self.numberEltOnTop -= 1
            self.isOSKShown = False

    def startListenerThread(self, grabInput=False):
        """
        Starts the touch listener as a separate thread
        Args:
            grabInput (boolean): Do an EVIOCGRAB IOCTL call to prevent
                any other software from registering touch events
        """
        self.isInputThreadStarted = True
        self.device.isInputThreadStarted = True
        print("[PSSM - Touch handler] : Input thread started")
        args = [self._clickHandler, True, grabInput]
        inputThread = threading.Thread(
            target=self.device.eventBindings,
            args=args
        )
        inputThread.start()

    def _clickHandler(self, x, y):
        n = len(self.stack)
        for i in range(n):
            j = n-1-i   # We go through the stack in descending order
            elt = self.stack[j]
            if elt.area is None:
                # An object without area, it should not happen, but if it does,
                # it can be skipped
                continue
            if coordsInArea(x, y, elt.area):
                if elt.onclickInside is not None:
                    self.lastX = x
                    self.lastY = y
                    if elt is not None:
                        self._dispatchClickToElt((x, y), elt)
                break

    def _dispatchClickToElt(self, coords, elt):
        """
        Once given an object on which the user clicked, this function calls the
        appropriate function on the object
        (ie elt.onclickInside or elt._dispatchClick)
        It also handles invertion.
        """
        if elt.isLayout:
            if elt.onclickInside is not None:
                elt.onclickInside(elt, coords)
            if elt.invertOnClick:
                self.invertElt(elt, elt.invertDuration)
            elt._dispatchClick(coords)
        else:
            if elt.invertOnClick:
                self.invertElt(elt, elt.invertDuration)
            # Execute PSSM action on click
            elt.pssmOnClickInside(coords)
            # Execute user action attached to it too
            elt.onclickInside(elt, coords)

    def stopListenerThread(self):
        self.isInputThreadStarted = False
        self.device.isInputThreadStarted = False
        print("[PSSM - Touch handler] : Input thread stopped")


# ########################## - Core Element    - ##############################
class Element:
    """
    Everything which is going to be displayed on the screen is an Element.

    Args:
        isInverted (bool): Is the element inverted
        data (dict, or any): A parameter for you to store whatever you want
        area (list): a [(x, y), (w, h)] list. If used in a Layout, the layout
            will take care of calculating the area.
        imgData (PILImage): the PIL image of the object (None by default, the
            generator function takes care of generating one)
        onclickInside (function): A function to be executed when the user
            clicks on the Element
        invertOnClick (bool): Invert the element when a click is registered ?
        invertDuration (int): Duration in seconds of the element invertion
            after a click is registered (use 0 for infinite)
        forcePrintOnTop (bool): Force the element to be printed on top of the
            stack, even if there is an on-screen keyboard or a popup
    """
    def __init__(self, area=None, imgData=None, onclickInside=returnFalse,
                 isInverted=False, data={}, invertOnClick=False,
                 invertDuration=DEFAULT_INVERT_DURATION, forcePrintOnTop=False
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
        self.invertDuration = invertDuration
        self.forcePrintOnTop = forcePrintOnTop
        self.parentLayouts = []
        self.parentPSSMScreen = None

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.id == other.id
        return NotImplemented

    def update(self, newAttributes={}, skipGen=False, skipPrint=False,
               reprintOnTop=False):
        """
        Pass a dict as argument, and it will update the Element's attributes
        accordingly (both its attribute and then the screen).
        Note:
            Updating an element can be very slow ! It depends on every specific
            cases, but know there are a few ways to make it faster:
            - Use `screen.startBatchWriting()` and `screen.stopBatchWriting()`
            - If you know this specific element is on top of the screen, use:
                `elt.update(newAttributes=myDict, reprintOnTop=True)`
                Which will do the same, except it won't rebuild the whole stack
                image, it will just print this object on top. (On my tests, I
                could spare up to 0.5s !)

        Args :
            newAttributes (dict): The element's new attributes
            skipGen (bool): Just update the element's attribute, but do
                not do any generation or printing
            reprintOnTop (bool): Do not reprint the whole stack, but do print
                this element on top of the screen. (much faster when possible)
            skipPrint (bool): Do not update the screen, but do regenerate.
        """
        # First, we set the attributes
        for param in newAttributes:
            setattr(self, param, newAttributes[param])
        if not skipGen:
            # we recreate the pillow image of this particular object
            self.generator()
        if (not skipPrint) and (not skipGen):  # No need to update if no regen
            isBatch = self.parentPSSMScreen.isBatch
            if reprintOnTop:
                self.parentPSSMScreen.simplePrintElt(self)
            elif not isBatch:
                hasParent = len(self.parentLayouts) > 0
                # We don't want unncesseray generation when printing batch
                if hasParent:
                    # We recreate the pillow image of the oldest parent
                    # And it is not needed to regenerate standard objects, since
                    oldest_parent = self.parentLayouts[0]
                    oldest_parent.generator(skipNonLayoutGen=True)
                # Then, let's reprint the stack
                self.parentPSSMScreen.printStack(area=self.area)
        return True

    def generator(self):
        """
        The generator is the function which is called when the container layout
        wants to build an image. It therefore returns a pillow image.
        """
        return NotImplemented

    def convertDimension(self, dimension):
        """
        Converts the user dimension input (like "h*0.1") to to proper integer
        amount of pixels.
        Basically, you give it a string. And it will change a few characters to
        their corresponding value, then return the evaluated string.

        Examples:
            I HIGHLY recommend doing only simple operation, like "H*0.1", or
            "W/10", always starting with the corresponding variable.
            But you can if you want do more complicated things:
            elt.convertDimension("H+W")
                    ->  screen_height + screen_width
            elt.convertDimension("p*300+max(w, h)")
                    -> 300 + max(element_width, screen_height)

        Note:
            When using question mark dimension (like "?*2"), the question mark
            MUST be at the beginning of the string
        """
        if isinstance(dimension, int):
            return dimension
        elif isinstance(dimension, str):
            nd = ""
            W = self.parentPSSMScreen.width
            H = self.parentPSSMScreen.height
            if self.area:
                (x, y), (w, h) = self.area
            else:
                # area not defined. Instead of being stuck, let's assume the
                # screen height and width are a decent alternative
                w, h = W, H
            for c in dimension:
                if c == 'p' or c == 'P':
                    nd += '1'
                elif c == 'W':      # screen width
                    nd += str(W)
                elif c == 'H':      # screen height
                    nd += str(H)
                elif c == 'w':      # element width
                    nd += str(w)
                elif c == 'h':      # element height
                    nd += str(h)
                else:           # A standard character
                    nd += c
            if dimension[0] == '?':
                # We return the string, another function will take care of
                # evaluating it
                return nd
            else:
                return int(eval(nd))        # Then we can evaluate the input
        else:
            print("[PSSM] Could not parse the dimension")
            return dimension

    def pssmOnClickInside(self, coords=None):
        """
        Each Element can also have a pssm function implemented on click.
        By default, it does nothing.
        """
        return None


# ########################## - Layout Elements - ##############################
class Layout(Element):
    """
    A layout is a quite general kind of Element :
    If must be given the working area, and a layout, and will generate every
    element of the layout

    Args:
        layout (list): The given layout (see example below). It is basically a
        list of rows. Each row is a list containing : the height of the row,
        then as many tuples as you want, each tuple being a
        (pssm.Element, width) instance
        background_color
        area
        ... all other arguments from the pssm.Element class

    Example of usage:
        See [examples](examples/index.html)
    """
    def __init__(self, layout, area=None, background_color="white", **kwargs):
        super().__init__()
        self.area = area
        self.layout = layout
        self.isValid = self.isLayoutValid()
        self.background_color = background_color
        self.areaMatrix = None
        self.imgMatrix = None
        self.borders = None
        self.isLayout = True
        for param in kwargs:
            setattr(self, param, kwargs[param])

    def isLayoutValid(self):
        # TODO : to be tested
        layout = self.layout
        if not isinstance(layout, list):
            raise Exception("Layout Element is supposed to be a list")
        for row in layout:
            if not isinstance(row, list):
                raise Exception("A layout row is supposed to be a list")
            elif len(row) == 0:
                raise Exception("A layout row cannot be empty")
            elif not isinstance(row[0], str) and not isinstance(row[0], int):
                raise Exception(
                    "The first element of a row (its height) should be a " +
                    "string or an integer"
                )
            for j in range(1, len(row)):
                eltTuple = row[j]
                isTuple = isinstance(eltTuple, tuple)
                isList = isinstance(eltTuple, list)
                if not (isTuple or isList):
                    raise Exception(
                        "A layout row should be a list of Tuple " +
                        "(except for its first element)"
                    )
                if len(eltTuple) != 2:
                    raise Exception(
                        "A layout element should be a Tuple : " +
                        "(Element, elementWidth)"
                    )
                isStr = isinstance(eltTuple[1], str)
                isInt = isinstance(eltTuple[1], int)
                if not (isInt or isStr):
                    raise Exception(
                        "An element width should be a string or an integer"
                    )
                isElement = isinstance(eltTuple[0], Element)
                if not (isElement or eltTuple[0] is None):
                    raise Exception(
                        "A layout element should be a Tuple : " +
                        "(Element, elementWidth), with Element designating " +
                        " a PSSM Element"
                    )
        return True

    def generator(self, area=None, skipNonLayoutGen=False):
        """
        Builds one img out of all the Elements it is being given
        """
        if area is not None:
            self.area = area
        self.createAreaMatrix()
        self.createImgMatrix(skipNonLayoutGen=skipNonLayoutGen)
        [(x, y), (w, h)] = self.area
        colorType = self.parentPSSMScreen.colorType
        color = get_Color(self.background_color, colorType)
        placeholder = Image.new(colorType, (w, h), color=color)
        for i in range(len(self.areaMatrix)):
            for j in range(len(self.areaMatrix[i])):
                [(elt_x, elt_y), (elt_w, elt_h)] = self.areaMatrix[i][j]
                relative_x = elt_x - x
                relative_y = elt_y - y
                elt_img = self.imgMatrix[i][j]
                if elt_img is not None:
                    pos = (relative_x, relative_y)
                    placeholder.paste(self.imgMatrix[i][j], pos)
        self.imgData = placeholder
        return self.imgData

    def createImgMatrix(self, skipNonLayoutGen=False):
        matrix = []
        if not self.areaMatrix:
            print("[PSSM Layout] Error, areaMatrix has to be defined first")
            return None
        for i in range(len(self.layout)):
            row = []
            for j in range(1, len(self.layout[i])):
                elt, _ = self.layout[i][j]
                if elt is None:
                    elt_area = self.areaMatrix[i][j-1]
                    elt_img = None
                else:
                    elt_area = self.areaMatrix[i][j-1]
                    if not elt.isLayout and skipNonLayoutGen:
                        elt_img = elt.imgData
                    else:
                        elt_img = elt.generator(area=elt_area)
                row.append(elt_img)
            matrix.append(row)
        self.imgMatrix = matrix

    def createAreaMatrix(self):
        # TODO : must honor min and max
        matrix = []
        n_rows = len(self.layout)
        [(x, y), (w, h)] = self.area[:]
        x0, y0 = x, y
        for i in range(n_rows):     # Lets loop through the rows
            row = self.layout[i]
            row_cols = []           # All the columns of this particular row
            row_height = row[0]
            converted_height = self.convertDimension(row_height)
            if isinstance(converted_height, int):
                true_row_height = converted_height
            else:
                remaining_height = self.calculate_remainingHeight()
                dim = str(remaining_height) + converted_height[1:]
                true_row_height = int(eval(dim))
            for j in range(1, len(row)):
                (element, element_width) = row[j]
                converted_width = self.convertDimension(element_width)
                if element is not None:
                    for parent in self.parentLayouts:
                        self.layout[i][j][0].parentLayouts.append(parent)
                    self.layout[i][j][0].parentLayouts.append(self)
                    self.layout[i][j][0].parentPSSMScreen = \
                        self.parentPSSMScreen
                if isinstance(converted_width, int):
                    true_elt_width = converted_width
                else:
                    remaining_width = self.calculate_remainingWidth(i)
                    dim = str(remaining_width) + converted_width[1:]
                    true_elt_width = int(eval(dim))
                    self.layout[i][j] = (self.layout[i][j][0], true_elt_width)
                element_area = [(x0, y0), (true_elt_width, true_row_height)]
                x0 += true_elt_width
                row_cols.append(element_area)
            y0 += true_row_height
            x0 = x
            matrix.append(row_cols)
        self.areaMatrix = matrix

    def createEltList(self):
        """
        Returns a list of all the elements the Layout Element contains
        """
        eltList = []
        for row in self.layout:
            for i in range(1, len(row)):
                elt, _ = row[i]
                if elt is not None:
                    eltList.append(elt)
        return eltList

    def calculate_remainingHeight(self):
        rows = self.extract_rowsHeight()
        total_questionMarks_weight = 0
        total_height = 0
        for dimension in rows:
            converted_dimension = self.convertDimension(dimension)
            if isinstance(converted_dimension, int):
                total_height += converted_dimension
            else:
                weight = eval("1" + converted_dimension[1:])
                total_questionMarks_weight += weight
        layout_height = self.area[1][1]
        return int((layout_height - total_height)/total_questionMarks_weight)

    def calculate_remainingWidth(self, rowIndex):
        cols = self.extract_colsWidth(rowIndex)
        total_width = 0
        total_questionMarks_weight = 0
        for dimension in cols:
            converted_dimension = self.convertDimension(dimension)
            if isinstance(converted_dimension, int):
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

    def extract_colsWidth(self, rowIndex):
        cols = []
        for col in self.layout[rowIndex]:
            if isinstance(col, tuple):
                cols.append(col[1])
        return cols

    def _dispatchClick(self, coords):
        """
        Finds the element on which the user clicked
        """
        self._dispatchClick_LINEAR(coords)

    def _dispatchClick_LINEAR(self, coords):
        """
        Linear search throuh both the rows and the columns
        """
        click_x, click_y = coords
        # Linear search though the rows
        for i in range(len(self.areaMatrix)):
            if len(self.areaMatrix[i]) == 0:
                # That's a fake row (a margin row)
                continue
            first_row_elt = self.areaMatrix[i][0]
            last_row_elt = self.areaMatrix[i][-1]
            x = first_row_elt[0][0]
            y = first_row_elt[0][1]
            w = last_row_elt[0][0] + last_row_elt[1][0] - first_row_elt[0][0]
            h = last_row_elt[0][1] + last_row_elt[1][1] - first_row_elt[0][1]
            if coordsInArea(click_x, click_y, [(x, y), (w, h)]):
                # CLick was in that row
                for j in range(len(self.areaMatrix[i])):
                    # Linear search through the columns
                    if coordsInArea(click_x, click_y, self.areaMatrix[i][j]):
                        # Click was on that element
                        elt, _ = self.layout[i][j+1]
                        if elt is not None and elt.onclickInside is not None:
                            self.parentPSSMScreen._dispatchClickToElt(
                                coords, elt
                            )
                        return True
        return False

    def _dispatchClick_DICHOTOMY_colsOnly(self, coords):
        """
        Linear search through the rows, dichotomy for the columns
        (Because of the empty rows, a dichotomy for the rows doesn't work)
        NEEDS TO BE FIXED TOO (example : two buttons in a row)
        """
        click_x, click_y = coords
        row_A = -1
        for i in range(len(self.areaMatrix)):
            # Linear search though the rows
            if len(self.areaMatrix[i]) == 0:
                # That's a fake row (a margin row)
                continue
            first_row_elt = self.areaMatrix[i][0]
            last_row_elt = self.areaMatrix[i][-1]
            x = first_row_elt[0][0]
            y = first_row_elt[0][1]
            w = last_row_elt[0][0] + last_row_elt[1][0] - first_row_elt[0][0]
            h = last_row_elt[0][1] + last_row_elt[1][1] - first_row_elt[0][1]
            if coordsInArea(click_x, click_y, [(x, y), (w, h)]):
                # CLick was in that row
                row_A = i
                break
        if row_A == -1:
            return None
        col_A = 0
        col_C = max(len(self.areaMatrix[row_A]) - 1, 0)
        xA = self.areaMatrix[row_A][col_A][0][0]
        xC = self.areaMatrix[row_A][col_C][0][0]
        if click_x < xA:
            return None
        if click_x > xC + self.areaMatrix[row_A][col_C][1][0]:
            return None
        while col_C > col_A + 1:
            col_B = int(0.5*(col_A+col_C))      # The average of the two
            xB = self.areaMatrix[row_A][col_B][0][0]
            if click_x >= xB or col_B == col_C:
                col_A = col_B
                xA = xB
            else:
                col_C = col_B
                xC = xB
        # Element is at indexes row_A, col_A
        elt, _ = self.layout[row_A][col_A+1]
        if elt is not None and elt.onclickInside is not None:
            self.parentPSSMScreen._dispatchClickToElt(coords, elt)
        return True

    def _dispatchClick_DICHOTOMY_Full_ToBeFixed(self, coords):
        """
        Finds the element on which the user clicked
        Implemented with dichotomy search (with the hope of making things
        faster, especially the integrated keyboard)
        """
        # TODO : To be fixed
        # For now it does not work, because there are empty rows which
        # break the loop
        click_x, click_y = coords
        row_A = 0
        row_C = max(len(self.areaMatrix) - 1, 0)
        print(self.areaMatrix[row_C])
        while len(self.areaMatrix[row_A]) == 0:
            row_A += 1
        while len(self.areaMatrix[row_C]) == 0:
            row_C -= 1
        # First column THEN first row , [(x, y), (w, h)] THUS first tuple of
        # list THEN second coordinate of tuple
        yA = self.areaMatrix[row_A][0][0][1]
        yC = self.areaMatrix[row_C][0][0][1]
        if click_y < yA:
            return None
        if click_y > yC + self.areaMatrix[row_C][0][1][1]:
            return None
        while row_C > row_A+1:
            row_B = int(0.5*(row_A+row_C))      # The average of the two
            while len(self.areaMatrix[row_B]) == 0:
                row_B += 1
            yB = self.areaMatrix[row_B][0][0][1]
            if click_y >= yB or row_B == row_C:
                row_A = row_B
                yA = yB
            else:
                row_C = row_B
                yC = yB
        # User clicked on element ar row of index row_A
        # Let's do the same for the column
        col_A = 0
        col_C = max(len(self.areaMatrix[row_A]) - 1, 0)
        xA = self.areaMatrix[row_A][col_A][0][0]
        xC = self.areaMatrix[row_A][col_C][0][0]
        if click_x < xA:
            return None
        if click_x > xC + self.areaMatrix[row_A][col_C][1][0]:
            return None
        while col_C > col_A + 1:
            col_B = int(0.5*(col_A+col_C))      # The average of the two
            xB = self.areaMatrix[row_A][col_B][0][0]
            if click_x >= xB or col_B == col_C:
                col_A = col_B
                xA = xB
            else:
                col_C = col_B
                xC = xB
        # Element is at indexes row_A, col_A
        elt, _ = self.layout[row_A-2][col_A+1]
        if elt is not None and elt.onclickInside is not None:
            self.parentPSSMScreen._dispatchClickToElt(coords, elt)
        return True


class ButtonList(Layout):
    """
    Generates a Layout with only one item per row, all the same type (buttons)
    and same height and width
    Args:
        button (list): a [{"text":"my text","onclickInside":onclickInside},
            someOtherDict, someOtherDict] array. Each dict will contain the
            parameters of each button of the button list
        borders (list): a [top, bottom,left,right] array
    """
    def __init__(self, buttons, margins=[0, 0, 0, 0], spacing=0, **kwargs):
        self.buttons = buttons
        self.margins = margins
        self.spacing = spacing
        layout = self.build_layoutFromButtons()
        super().__init__(layout)
        for param in kwargs:
            setattr(self, param, kwargs[param])

    def build_layoutFromButtons(self):
        # TODO : must honor min_width,max_width etc
        [top, bottom, left, right] = self.margins
        buttonLayout = [[top-self.spacing]]
        for button in self.buttons:
            buttonElt = Button(text=button['text'])
            for param in button:
                setattr(buttonElt, param, button[param])
            row_height = "?"
            buttonLayout.append([self.spacing])
            row = [row_height, (None, left), (buttonElt, "?"), (None, right)]
            buttonLayout.append(row)
        buttonLayout.append([bottom])
        return buttonLayout


class OSK(Layout):
    """
    A PSSM Layout element which builds an on-screen keyboard
    Args:
        keymapPath (str): a path to a PSSMOSK keymap (like the one included)
        onKeyPress (function): A callback function. Will be given keyType and
            keyChar as argument
    """
    def __init__(self, keymapPath=DEFAULT_KEYMAP_PATH, onKeyPress=None,
                 area=None, **kwargs):
        if not keymapPath:
            keymapPath = DEFAULT_KEYMAP_PATH
        self.keymapPaths = keymapPath
        self.keymap = {'standard': None, 'caps': None, 'alt': None}
        self.keymap_layouts = {'standard': None, 'caps': None, 'alt': None}
        self.keymap_imgs = {'standard': None, 'caps': None, 'alt': None}
        with open(self.keymapPaths['standard']) as json_file:
            self.keymap['standard'] = json.load(json_file)
        with open(self.keymapPaths['caps']) as json_file:
            self.keymap['caps'] = json.load(json_file)
        with open(self.keymapPaths['alt']) as json_file:
            self.keymap['alt'] = json.load(json_file)
        self.lang = self.keymap['standard']["lang"]
        self.onKeyPress = onKeyPress
        for param in kwargs:
            setattr(self, param, kwargs[param])
        self.view = 'standard'
        self.keymap_layouts['standard'] = self.build_layout(
                                               self.keymap['standard'])
        self.keymap_layouts['caps'] = self.build_layout(self.keymap['caps'])
        self.keymap_layouts['alt'] = self.build_layout(self.keymap['alt'])
        # Initialize layout with standard view
        self.layout = self.keymap_layouts['standard']
        super().__init__(self.layout)
        self.area = area

    def generator(self, area=None, forceRegenerate=False,
                  skipNonLayoutGen=False):
        """
        This generator is a bit special : we don't want it to regenerate
        everything everytime we change view. So we will generate all the views
        at once the first time. Then, unless asked to, we will only return the
        appropriate image.
        """
        isStDefined = self.keymap_imgs['standard']
        isCaDefined = self.keymap_imgs['caps']
        isAlDefined = self.keymap_imgs['alt']
        areAllDefined = isStDefined and isCaDefined and isAlDefined
        if forceRegenerate or (not areAllDefined):
            print("[PSSM OSK] Regenration started")
            # Let's create all the Images
            # Standard view is created last, because it is the one which is to
            # be displayed
            def generateLayout(name):
                self.layout = self.keymap_layouts[name]
                self.keymap_imgs[name] = super(OSK, self).generator(area=area)
            generateLayout("caps")
            generateLayout("alt")
            generateLayout("standard")
        self.imgData = self.keymap_imgs[self.view]
        return self.keymap_imgs[self.view]

    def build_layout(self, keymap):
        oskLayout = []
        spacing = keymap["spacing"]
        for row in keymap["rows"]:
            buttonRow = ["?", (None, spacing)]
            for key in row:
                label = self.getKeyLabel(key)
                color_condition = key["keyType"] != KTstandardChar
                background_color = "gray12" if color_condition else "white"
                outline_color = "white" if key["isPadding"] else "black"
                willChangeLayout = key["keyType"] in [
                    KTcapsLock, KTalt, KTcarriageReturn
                ]
                invertOnClick = False if willChangeLayout else True
                buttonElt = Button(
                    text=label,
                    font_size="H*0.02",
                    background_color=background_color,
                    outline_color=outline_color,
                    onclickInside=self.handleKeyPress,
                    user_data=key,
                    wrap_textOverflow=False,
                    invertOnClick=invertOnClick
                )
                key_width = key["keyWidth"]
                buttonRow.append((buttonElt, key_width))
                buttonRow.append((None, spacing))
            oskLayout.append(buttonRow)
            oskLayout.append([spacing])
        return oskLayout

    def handleKeyPress(self, elt, coords):
        keyType = elt.user_data["keyType"]
        keyChar = elt.user_data["char"]
        if keyType == KTcapsLock:
            # In this particular case, we can assume the keyboard will always
            # be on top.
            # Therefore, no need to print everything
            self.view = 'caps' if self.view != 'caps' else 'standard'
            self.layout = self.keymap_layouts[self.view]
            self.imgData = self.keymap_imgs[self.view]
            self.parentPSSMScreen.simplePrintElt(self)
        elif keyType == KTalt:
            # In this particular case, we can assume the keyboard will always
            # be on top
            # Therefore, no need to print everything
            self.view = 'alt' if self.view != 'alt' else 'standard'
            self.layout = self.keymap_layouts[self.view]
            self.imgData = self.keymap_imgs[self.view]
            self.parentPSSMScreen.simplePrintElt(self)
        if self.onKeyPress:
            self.onKeyPress(keyType, keyChar)

    def getKeyLabel(self, key):
        kt = key["keyType"]
        if kt == KTstandardChar:
            return key["char"]
        elif kt == KTalt:
            return "ALT"
        elif kt == KTbackspace:
            return "BACK"
        elif kt == KTcapsLock:
            return "CAPS"
        elif kt == KTcarriageReturn:
            return "RET"
        elif kt == KTcontrol:
            return "CTRL"
        elif kt == KTdelete:
            return "DEL"
        return ""


class Popup(Layout):
    """
    A popup to be displayed above everything else, to simple ask a question
    Args:
        layout (list): The list of PSSMElements to be displayed. cf Layout
        width (str): The width of the popup
        height (str): The height of the popup
        xPos (float): Relative position on the x axis of the center point
        yPos (float): Relative position on the y axis of the center point
    """
    def __init__(self, layout=[], width="W*0.8", height="H*0.5",
                 xPos=0.5, yPos=0.3, **kwargs):
        super().__init__(layout=layout)
        self.width = width
        self.height = height
        self.xPos = xPos
        self.yPos = yPos
        for param in kwargs:
            setattr(self, param, kwargs[param])

    def make_area(self):
        w = self.convertDimension(self.width)
        h = self.convertDimension(self.height)
        x = self.convertDimension("W*" + str(self.xPos)) - int(0.5*w)
        y = self.convertDimension("H*" + str(self.yPos)) - int(0.5*h)
        self.area = [(x, y), (w, h)]
        return self.area


class PoputInput(Popup):
    def __init__(self, titleText="", mainText="", confirmText="OK",
                 titleFont=DEFAULT_FONT, titleFontSize=DEFAULT_FONT_SIZE,
                 mainFont=DEFAULT_FONT, mainFontSize=DEFAULT_FONT_SIZE,
                 inputFont=DEFAULT_FONT, inputFontSize=DEFAULT_FONT_SIZE,
                 confirmFont=DEFAULT_FONT, confirmFontSize=DEFAULT_FONT_SIZE,
                 titleFontColor="black", mainFontColor="black",
                 inputFontColor="black", confirmFontColor="black",
                 mainTextXPos="center", mainTextYPos="center",
                 isMultiline=False, **kwargs):
        super().__init__()
        self.titleText = titleText
        self.mainText = mainText
        self.confirmText = confirmText
        self.isMultiline = isMultiline
        self.titleFont = titleFont
        self.mainFont = mainFont
        self.inputFont = inputFont
        self.confirmFont = confirmFont
        self.titleFontSize = titleFontSize
        self.mainFontSize = mainFontSize
        self.inputFontSize = inputFontSize
        self.confirmFontSize = confirmFontSize
        self.titleFontColor = titleFontColor
        self.mainFontColor = mainFontColor
        self.inputFontColor = inputFontColor
        self.confirmFontColor = confirmFontColor
        self.mainTextXPos = mainTextXPos
        self.mainTextYPos = mainTextYPos
        self.userConfirmed = False
        self.inputBtn = None
        self.okBtn = None
        for param in kwargs:
            setattr(self, param, kwargs[param])
        self.build_layout()

    def generator(self,**kwargs):
        self.make_area()
        super().generator(**kwargs)

    def build_layout(self):
        titleBtn = Button(
            text=self.titleText,
            font=self.titleFont,
            font_size=self.titleFontSize,
            font_color=self.titleFontColor
        )
        mainBtn = Button(
            text=self.mainText,
            font=self.mainFont,
            font_size=self.mainFontSize,
            font_color=self.mainFontColor,
            text_xPosition=self.mainTextXPos,
            text_yPosition=self.mainTextYPos
        )
        if self.isMultiline:
            onReturn = returnFalse
        else:
            onReturn = self.toggleConfirmation
        inputBtn = Input(
            font=self.inputFont,
            font_size=self.inputFontSize,
            font_color=self.inputFontColor,
            isMultiline=self.isMultiline,
            onReturn=onReturn
        )
        okBtn = Button(
            text=self.confirmText,
            font=self.confirmFont,
            font_size=self.confirmFontSize,
            font_color=self.confirmFontColor,
            onclickInside=self.toggleConfirmation
        )
        self.inputBtn = inputBtn
        lM = (None,1)
        layout = [
            ["?*1.5", (titleBtn, "?"), lM],
            ["?*3", (mainBtn, "?"), lM],
            ["?*2", (inputBtn, "?"), lM],
            ["?*1", (okBtn, "?"), lM]
        ]
        self.layout = layout
        return layout

    def toggleConfirmation(self, elt=None, coords=None):
            print("Toggling confirmation")
            self.userConfirmed = True

    def waitForResponse(self):
        while not self.userConfirmed:
            self.parentPSSMScreen.device.wait(0.01)
        self.parentPSSMScreen.OSKHide()
        input = self.inputBtn.getInput()
        self.userConfirmed = False  # Reset the state
        self.parentPSSMScreen.removeElt(self)
        return input


class PopupConfirm(Popup):
    def __init__(self, titleText="", mainText="", confirmText="OK",
                 cancelText="Cancel",
                 titleFont=DEFAULT_FONT, titleFontSize=DEFAULT_FONT_SIZE,
                 mainFont=DEFAULT_FONT, mainFontSize=DEFAULT_FONT_SIZE,
                 confirmFont=DEFAULT_FONT, confirmFontSize=DEFAULT_FONT_SIZE,
                 titleFontColor="black", mainFontColor="black",
                 confirmFontColor="black",
                 mainTextXPos="center", mainTextYPos="center",
                 **kwargs):
        super().__init__()
        self.titleText = titleText
        self.mainText = mainText
        self.confirmText = confirmText
        self.cancelText = cancelText
        self.titleFont = titleFont
        self.mainFont = mainFont
        self.confirmFont = confirmFont
        self.titleFontSize = titleFontSize
        self.mainFontSize = mainFontSize
        self.confirmFontSize = confirmFontSize
        self.titleFontColor = titleFontColor
        self.mainFontColor = mainFontColor
        self.confirmFontColor = confirmFontColor
        self.mainTextXPos = mainTextXPos
        self.mainTextYPos = mainTextYPos
        self.userAction = 0
        self.okBtn = None
        self.cancelBtn = None
        for param in kwargs:
            setattr(self, param, kwargs[param])
        self.build_layout()

    def generator(self,**kwargs):
        self.make_area()
        super().generator(**kwargs)

    def build_layout(self):
        titleBtn = Button(
            text=self.titleText,
            font=self.titleFont,
            font_size=self.titleFontSize,
            font_color=self.titleFontColor
        )
        mainBtn = Button(
            text=self.mainText,
            font=self.mainFont,
            font_size=self.mainFontSize,
            font_color=self.mainFontColor,
            text_xPosition=self.mainTextXPos,
            text_yPosition=self.mainTextYPos
        )
        okBtn = Button(
            text=self.confirmText,
            font=self.confirmFont,
            font_size=self.confirmFontSize,
            font_color=self.confirmFontColor,
            onclickInside=self.confirm
        )
        cancelBtn = Button(
            text=self.cancelText,
            font=self.confirmFont,
            font_size=self.confirmFontSize,
            font_color=self.confirmFontColor,
            onclickInside=self.cancel
        )
        lM = (None,1)
        layout = [
            ["?*1.5", (titleBtn, "?"), lM],
            ["?*3", (mainBtn, "?"), lM],
            ["?*1", (okBtn, "?"), (cancelBtn, "?"), lM]
        ]
        self.layout = layout
        return layout

    def confirm(self, elt=None, coords=None):
            self.userAction = 1

    def cancel(self,elt=None, coords=None):
            self.userAction = 2

    def waitForResponse(self):
        while self.userAction == 0:
            self.parentPSSMScreen.device.wait(0.01)
        self.parentPSSMScreen.OSKHide()
        hasConfirmed = self.userAction == 1
        self.userAction = 0  # Reset the state
        self.parentPSSMScreen.removeElt(self)
        return hasConfirmed




# ########################## - Simple Elements - ##############################
class Rectangle(Element):
    """
    A rectangle
    Args:
        background_color (str): The background color
        outline_color (str): The border color
    """
    def __init__(self, background_color="white", outline_color="gray3",
                 parentPSSMScreen=None):
        super().__init__()
        self.background_color = background_color
        self.outline_color = outline_color
        self.parentPSSMScreen = parentPSSMScreen

    def generator(self, area):
        [(x, y), (w, h)] = area
        self.area = area
        colorType = self.parentPSSMScreen.colorType
        img = Image.new(
            colorType,
            (w, h),
            color=get_Color("white", colorType)
        )
        rect = ImageDraw.Draw(img, colorType)
        fill_color = get_Color(self.background_color, colorType)
        outline_color = get_Color(self.outline_color, colorType)
        rect.rectangle(
            [(0, 0), (w-1, h-1)],
            fill=fill_color,
            outline=outline_color
        )
        self.imgData = img
        return self.imgData


class RectangleRounded(Element):
    """
    A rectangle, but with rounded corners
    """
    def __init__(self, radius=20, background_color="white",
                 outline_color="gray3", parentPSSMScreen=None):
        super().__init__()
        self.radius = radius
        self.background_color = background_color
        self.outline_color = outline_color
        self.parentPSSMScreen = parentPSSMScreen

    def generator(self, area):
        [(x, y), (w, h)] = area
        self.area = area
        colorType = self.parentPSSMScreen.colorType
        rectangle = Image.new(
            colorType,
            (w, h),
            color=get_Color("white", colorType)
        )
        draw = ImageDraw.Draw(rectangle)
        draw.rectangle(
            [(0, 0), (w, h)],
            fill=get_Color(self.background_color, colorType),
            outline=get_Color(self.outline_color, colorType)
        )
        draw.line(
            [(self.radius, h-1), (w-self.radius, h-1)],
            fill=get_Color(self.outline_color, colorType),
            width=1
        )
        draw.line(
            [(w-1, self.radius), (w-1, h-self.radius)],
            fill=get_Color(self.outline_color, colorType),
            width=1
        )
        corner = roundedCorner(
            self.radius,
            self.background_color,
            self.outline_color,
            self.parentPSSMScreen.colorType
        )
        rectangle.paste(corner, (0, 0))
        # Rotate the corner and paste it
        rectangle.paste(corner.rotate(90), (0, h - self.radius))
        rectangle.paste(corner.rotate(180), (w - self.radius, h - self.radius))
        rectangle.paste(corner.rotate(270), (w - self.radius, 0))
        self.imgData = rectangle
        return self.imgData


class Button(Element):
    """
    Basically a rectangle (or rounded rectangle) with text printed on it
    Args:
        text (str): The main text to be written on it
        font (str): Path to a font file (ttf file), or one of PSSM built-in
            fonts (e.g. "Merriweather-Bold", "default", "Merriweather-Regular",
            ...) (see the font folder for the complete list)
        font_size (int): The font size
        font_color (str): The color of the font : "white", "black", "gray0" to
            "gray15" or a (red, green, blue, transparency) tuple
        wrap_textOverflow (bool): (True by default) Wrap text in order to avoid
         it overflowing. The cuts are made between words.
        text_xPosition (str or int): can be left, center, right, or an integer
            value, or a pssm string dimension
        text_yPosition (str or int): can be left, center, right, or an integer
            value, or a pssm string dimension
        background_color (str): The background color
        outline_color (str): The border color
        radius (int): If not 0, then add rounded corners of this radius
    """
    def __init__(self, text="", font=DEFAULT_FONT, font_size=DEFAULT_FONT_SIZE,
                 background_color="white", outline_color="black", radius=0,
                 font_color="black", text_xPosition="center",
                 text_yPosition="center", wrap_textOverflow=True, **kwargs):
        super().__init__()
        self.background_color = background_color
        self.outline_color = outline_color
        self.text = text
        self.font = tools_parseKnownFonts(font)
        self.font_size = font_size
        self.radius = radius
        self.font_color = font_color
        self.text_xPosition = text_xPosition
        self.text_yPosition = text_yPosition
        self.wrap_textOverflow = wrap_textOverflow
        for param in kwargs:
            setattr(self, param, kwargs[param])
        self.loaded_font = None
        self.convertedText = None
        self.imgDraw = None

    def generator(self, area=None):
        if area is None:
            area = self.area
        [(x, y), (w, h)] = area
        self.area = area
        if not isinstance(self.font_size, int):
            self.font_size = self.convertDimension(self.font_size)
            if not isinstance(self.font_size, int):
                # That's a question mark dimension, or an invalid dimension.
                # Rollback to default font size
                self.font_size = self.convertDimension(DEFAULT_FONT_SIZE)
        loaded_font = ImageFont.truetype(self.font, self.font_size)
        self.loaded_font = loaded_font
        if self.radius > 0:
            rect = RectangleRounded(
                radius=self.radius,
                background_color=self.background_color,
                outline_color=self.outline_color,
                parentPSSMScreen=self.parentPSSMScreen
            )
        else:
            rect = Rectangle(
                background_color=self.background_color,
                outline_color=self.outline_color,
                parentPSSMScreen=self.parentPSSMScreen
            )
        rect_img = rect.generator(self.area)
        imgDraw = ImageDraw.Draw(rect_img, self.parentPSSMScreen.colorType)
        self.imgDraw = imgDraw
        if self.wrap_textOverflow:
            myText = self.wrapText(self.text, loaded_font, imgDraw)
        else:
            myText = self.text
        self.convertedText = myText
        text_w, text_h = imgDraw.textsize(myText, font=loaded_font)
        x = tools_convertXArgsToPX(self.text_xPosition, w, text_w, myElt=self)
        y = tools_convertYArgsToPX(self.text_yPosition, h, text_h, myElt=self)
        imgDraw.text(
            (x, y),
            myText,
            font=loaded_font,
            fill=get_Color(self.font_color, self.parentPSSMScreen.colorType)
        )
        self.imgData = rect_img
        return self.imgData

    def wrapText(self, text, loaded_font, imgDraw):
        def get_text_width(text):
            return imgDraw.textsize(text=text, font=loaded_font)[0]

        [(x, y), (max_width, h)] = self.area
        text_lines = [
            ' '.join([w.strip() for w in line.split(' ') if w])
            for line in text.split('\n')
            if line
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
        file (str): Path to a file, or one of the integrated image (see the
            icon folder for the name of each image). 'reboot' for instance
            points to the integrated reboot image.
        centered (bool): Center the icon?
    """
    def __init__(self, file, centered=True, **kwargs):
        super().__init__()
        self.file = file
        self.centered = centered
        self.path_to_file = tools_parseKnownImageFile(self.file)
        for param in kwargs:
            setattr(self, param, kwargs[param])

    def generator(self, area):
        self.area = area
        [(x, y), (w, h)] = area
        colorType = self.parentPSSMScreen.colorType
        icon_size = min(area[1][0], area[1][1])
        loadedImg = Image.open(self.path_to_file)
        convImg = loadedImg.convert(colorType)
        iconImg = convImg.resize((icon_size, icon_size))
        if not self.centered:
            self.imgData = iconImg
            return iconImg
        else:
            img = Image.new(
                colorType,
                (w+1, h+1),
                color=get_Color("white", colorType)
            )
            x = int(0.5*w-0.5*icon_size)
            y = int(0.5*h-0.5*icon_size)
            img.paste(iconImg, (x, y))
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
        background_color (str): "white", "black", "gray0" to "gray15" or a
            (red, green, blue, transparency) tuple
    """
    def __init__(self, pil_image, centered=True, resize=True,
                 background_color="white", rotation=0, **kwargs):
        super().__init__()
        if isinstance(pil_image, str):
            self.pil_image = Image.open(pil_image)
        else:
            self.pil_image = pil_image
        self.background_color = background_color
        self.centered = centered
        self.resize = resize
        self.rotation = rotation
        for param in kwargs:
            setattr(self, param, kwargs[param])

    def generator(self, area=None):
        # TODO : crop or resize the image to make it fit the area
        (x, y), (w, h) = area
        colorType = self.parentPSSMScreen.colorType
        pil_image = self.pil_image.convert(colorType)
        if self.resize:
            r = min(w/pil_image.width, h/pil_image.height)
            size = (int(pil_image.width*r), int(pil_image.height*r))
            pil_image = self.pil_image.resize(size)
        if self.rotation != 0:
            pil_image = pil_image.rotate(self.rotation,
                                         fillcolor=self.background_color)
        if not self.centered:
            return pil_image
        else:
            img = Image.new(
                colorType,
                (w+1, h+1),
                color=get_Color(self.background_color, colorType)
            )
            x = int(0.5*w-0.5*pil_image.width)
            y = int(0.5*h-0.5*pil_image.height)
            img.paste(pil_image, (x, y))
            self.imgData = img
            return img


class Line(Element):
    """
    Draws a simple line
    Args:
        color (str or tuple): "white", "black", "gray0" to "gray15" or a
            (red, green, blue, transparency) tuple
        width (int): The width of the line
        type (str): can be "horizontal", "vertical", "diagonal1" (top-left to
            bottom right) or "diagonal2" (top-right to bottom-left)
    """
    def __init__(self, color="black", width=1, type="horizontal"):
        super().__init__()
        self.color = color
        self.width = width
        self.type = type

    def generator(self, area):
        (x, y), (w, h) = area
        self.area = area
        colorType = self.parentPSSMScreen.colorType
        if self.type == "horizontal":
            coo = [(0, 0), (w, 0)]
        elif self.type == "vertical":
            coo = [(0, 0), (0, h)]
        elif self.type == "diagonal1":
            coo = [(0, 0), (w, h)]
        else:               # Assuming diagonal2
            coo = [(w, 0), (0, h)]
        rectangle = Image.new(
            colorType,
            (w, h),
            color=get_Color("white", colorType)
        )
        draw = ImageDraw.Draw(rectangle)
        draw.line(
            coo,
            fill=get_Color(self.color, colorType),
            width=self.width
        )
        self.imgData = rectangle
        return self.imgData


class Input(Button):
    """
    Basically a button, except when you click on it, it displays the keyboard.
    It handles typing things for you. so when you click on this element, the
    keyboard shows up, and you can start typing.
    The main thing it does is that it is able to detect between which
    characters the user typed to be able to insert a character between two
    others (and that was no easy task)
    It has a method to retrieve what was typed :
    Input.getInput()
    Args:
        isMultiline (bool): Allow carriage return
        onReturn (function): Function to be executed on carriage return
    """
    def __init__(self, isMultiline=True, onReturn=returnFalse, **kwargs):
        super().__init__()
        self.hideCursorWhenLast = True
        self.isMultiline = isMultiline
        self.onReturn = onReturn
        self.allowSetCursorPos = False
        self.isOnTop = True  # Let's assume an input elt is always on top
        for param in kwargs:
            setattr(self, param, kwargs[param])
        if 'font' in kwargs:
            self.font = tools_parseKnownFonts(kwargs["font"])
        self.cursorPosition = len(self.text)
        self.typedText = self.text[:]
        self.text = self.typedText

    def getInput(self):
        """
        Returns the text currently written on the Input box.
        """
        return self.typedText

    def pssmOnClickInside(self, coords):
        if not self.parentPSSMScreen.osk:
            print(
                "[PSSM] Keyboard not initialized, Input element cannot be " +
                "properly handled"
            )
            return None
        # Set the callback function to our own
        self.parentPSSMScreen.osk.onKeyPress = self.onKeyPress
        if not self.parentPSSMScreen.isOSKShown:
            # Let's print the on screen keyboard as it is not already here
            self.parentPSSMScreen.OSKShow()
        elif self.allowSetCursorPos:
            cx, cy = coords
            [(sx, sy), (w, h)] = self.area
            loaded_font = self.loaded_font
            myText = self.convertedText
            imgDraw = self.imgDraw
            text_w, text_h = imgDraw.textsize(myText, font=loaded_font)
            x = tools_convertXArgsToPX(self.text_xPosition, w, text_w,
                                       myElt=self)
            y = tools_convertYArgsToPX(self.text_yPosition, h, text_h,
                                       myElt=self)
            # Then let's linear search
            wasFound = False
            olines = myText[:].split("\n")
            if len(olines) > 0:
                lines = [olines[0]]
            else:
                lines = []
            for i in range(len(olines)):
                lines.append("\n")
            linesBefore = ""
            for i in range(len(lines)):
                tw1, th1 = imgDraw.textsize(linesBefore, font=loaded_font)
                linesBefore += lines[i]
                tw2, th2 = imgDraw.textsize(linesBefore, font=loaded_font)
                b_correct_y = cy > sy + x + th1 and cy <= sy + y + th2
                if b_correct_y:
                    for j in range(len(linesBefore)):
                        tw1, th1 = imgDraw.textsize(linesBefore[:j],
                                                    font=loaded_font)
                        tw2, th2 = imgDraw.textsize(linesBefore[:j+1],
                                                    font=loaded_font)
                        b_correct_x = cx > sx + x + tw1 and cx <= sx + x + tw2
                        if b_correct_x:
                            pos = j
                            for line in lines[:i]:
                                pos += len(line)
                            self.setCursorPosition(pos+1)
                            wasFound = True
                    if not wasFound:    # Let's put it at the end of the row
                        pos = 0
                        for line in lines[:i+1]:
                            pos += len(line)
                        self.setCursorPosition(pos)
                        wasFound = True
            if not wasFound:
                self.setCursorPosition(None)
            pass

    def onKeyPress(self, keyType, keyChar):
        """
        Handles each key press.
        By default, it will re-display the input element on each keypress ON
        TOP OF THE SCREEN (not honoring stack position). This allow for a 30%
        speed increase on my basic test. You can change this behaviour by
        setting `InputElt.isOnTop = False`
        """
        c = self.cursorPosition
        if keyType == KTstandardChar:
            self.typedText = insertStr(self.typedText, keyChar, c)
            self.setCursorPosition(self.cursorPosition+1, skipPrint=True)
        elif keyType == KTcarriageReturn:
            if self.isMultiline:
                self.typedText = insertStr(self.typedText, "\n", c)
                self.setCursorPosition(self.cursorPosition+1, skipPrint=True)
            else:
                self.onReturn()
        elif keyType == KTbackspace:
            self.typedText = self.typedText[:c-1] + self.typedText[c:]
            self.setCursorPosition(self.cursorPosition-1, skipPrint=True)
        if self.hideCursorWhenLast:
            if self.cursorPosition >= len(self.typedText):
                # Don't display the cursor when it is at the last position
                self.text = self.typedText[:]
        else:
            self.text = insertStr(self.typedText, CURSOR_CHAR,
                                  self.cursorPosition)
        if self.isOnTop:
            self.update(reprintOnTop=True)
        else:
            self.update()

    def setCursorPosition(self, pos, skipPrint=False):
        if pos is None:
            pos = len(self.typedText)
        self.cursorPosition = pos
        self.text = insertStr(self.typedText, CURSOR_CHAR, self.cursorPosition)
        if not skipPrint:
            self.update()


# ########################## -     Tools       - ##############################
def roundedCorner(radius, fill="white", outline_color="gray3", colorType='L'):
    """
    Draw a round corner
    """
    corner = Image.new(colorType, (radius, radius), "white")
    draw = ImageDraw.Draw(corner)
    draw.pieslice(
        (0, 0, radius * 2, radius * 2),
        180,
        270,
        fill=get_Color(fill, colorType),
        outline=get_Color(outline_color, colorType)
    )
    return corner


# ############################# - DOCUMENTATION - #############################
__pdoc__ = {}           # For the documentation
ignoreList = [
    'returnFalse',
    'coordsInArea',
    'getRectanglesIntersection',
    'roundedCorner',
    'tools_convertXArgsToPX',
    'tools_convertYArgsToPX',
    'tools_parseKnownImageFile',
    'get_Color',
    'PSSMScreen.convertDimension',
    'Layout.generator',
    'Layout.createImgMatrix',
    'Layout.createAreaMatrix',
    'Layout.calculate_remainingHeight',
    'Layout.calculate_remainingWidth',
    'Layout.extract_rowsHeight',
    'Layout.extract_colsWidth',
    'Layout._dispatchClick',
    'Layout._dispatchClick_LINEAR',
    'Layout._dispatchClick_DICHOTOMY_colsOnly',
    'Layout._dispatchClick_DICHOTOMY_Full_ToBeFixed'
]
for f in ignoreList:
    __pdoc__[f] = False
