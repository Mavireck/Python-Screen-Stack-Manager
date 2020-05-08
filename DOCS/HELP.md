# Python-Screen-Stack-Manager - Help


You should (and I may say you MUST) check the file named screenStackTest.py.
It contains a few examples and useful comments. Make sure it works before testing anything else.



## Table of contents
1. Setup
2. Initializing PSSM
3. Basic functions
4. The EMULATOR :)
5. POL - PSSM Objects Librairy
6. Advanced functions : The ScreenStackManager object
7. Advanced functions : The ScreenObject object

## 1. Setup
To install PSSM on your Kobo, I recommend you install all my packages in :
> .adds/mavireck/

For instance :

> /mnt/onboard/.adds/mavireck/Python-Screen-Stack-Manager

Then, you only have to import my files at the beginning of your script :

```python
sys.path.append('/mnt/onboard/.adds/mavireck/Python-Screen-Stack-Manager') #To tell Python where to look for these files
import pssm  #The core logic
import pssm_kobo  #The Kobo-specific things
import pssmObjectsLibrairy as POL  # A librairy of pre-made objects (rectangles, buttons...)
```
**Note** : You should also have a look at myKobo-Python-OSKandUtils repo on github, there are a few intersting things there.


## 2. Initializing PSSM
###### Declaring the stack manager
```python
# Declare the Screen Stack Manager.
#pssm_kobo is a link to the imported pssm_kobo librairy. 'Main' is the name of the screen manager (useless actually)
screen = pssm.ScreenStackManager(pssm_kobo,'Main')
# Some interesting variables are available : width, height, offset, view_height...
# You should look at pssm.py for more.
screenWidth = screen.width
screenHeight = screen.height
```
Every time you add an object, you can attach an onclick event on it, which is a function which is going to be executed when the Touch Listener detects a touch event on the area of the given object.

###### Attaching the Touch listener
You can choose to start the touch listener as a separate thread or not, with :
```python
screen.listenForTouch()       #Standalone, will prevent any loop from running
screen.startListenerThread()  #As a separate thread
```

## 3. Basic functions
```Python
screen.clear()    # Clears the screen
screen.refresh()  # Refreshes the screen
screen.createCanvas() # Create a white canvas
screen.addObj(screenObj)  # Adds an object to the stack
screen.invertObj(screenObj.id,5) # Inverts an object for 5 seconds (Please do not edit that object in the meantime, it may break quite a few things)
screen.removeObj(screenObj.id)   # Removes the object from the screen
screen.removeAllWithTag("MyTag")  # Removes all the objects which have the tag "MyTag"
```
More information on tags, etc below.

## 4. The EMULATOR :) :)
>**TODO**

You can use : import pssm_opencv as pssm_device to use the emulator, instead of pssm_kobo. Then run your script on your computer.

## 5. POL - PSSM Objects Librairy
>**TODO**

Example :
```Python
obj = POL.rectangle(0,0,400,1000,fill=0,outline=50)
obj.name = "highObj"                #Give a specific name to the object (useful for debug purposes)
obj.onclickInside = printObjData    #Attach a function to be executed onclick
```
Non-exhaustive list of functions :
````Python
POL.rectangle(x,y,w,h,fill=255,outline=50)  #Create a simple rectangle
POL.roundedRectangle(x,y,w,h, radius=20, fill=255,outline=50)  # Create a rectangle with round corners
POL.button(x,y,w,h,text,font,fill=255,outline=50,text_fill=0)  # Create a button
POL.add_text(obj,text,font,xPosition="left",yPosition="top",fill=0)
POL.add_centeredText(obj,text,font,fill=0)
````

## 6. Advanced functions : The ScreenStackManager object
A PSSM ScreenStackManager has these attributes :
````Python
screen.device = device
screen.width = device.screen_width
screen.height = device.screen_height
screen.view_width = device.view_width
screen.view_height = device.view_height
screen.w_offset = device.w_offset
screen.h_offset = device.h_offset
screen.name = name
screen.stack = stack
screen.isInverted = isInverted
screen.isInputThreadStarted = False

screen.findObjWithId(screenObjId)

screen.printStack(skipObjId=None,area=None):
"""
Prints the stack elements in the stack order
If a skipObj is specified, then the function will not display the skipObj.
If a area is set, then, we only display the part of the stack which is in this area
"""

screen.simplePrintObj(screenObj):
""" Prints the object without adding it to the stack """

screen.addObj(screenObj,skipPrint=False,skipRegistration=False)
""" Adds object to the stack and prints it """

screen.forceAddObj(screenObj)
""" Adds object to the stack and prints it, without checking if it is already here """

screen.updateArea(area = None)

screen.removeObj(screenObjId,skipPrint=False)
""" Removes an object from the screen"""

screen.getTagList()
""" Returns a list of tags"""

screen.removeAllWithTag("tag")
""" Removes all the object with this tag"""

screen.invertAllWithTag("tag")
""" Inverts all the object with this tag"""

screen.getStackLevel(screenObjId)
""" Returns the index of the object """

screen.setStackLevel(screenObjId,stackLevel="last")
""" Set the position of said object
Then prints every object above it (including itself) """

screen.invertObj(screenObjId,invertDuration)
""" Inverts an object """

screen.invert():
""" Inverts the whole screen"""
screen.refresh()
screen.clear()
screen.createCanvas(color=255)

screen.startListenerThread()
screen.stopListenerThread()
````

## 7. Advanced functions : The ScreenObject object
A PSSM Object has these attributes :
````Python
screenObj.id         # A specific ID - do not edit
screenObj.imgData    # The raw image file associated with it (can be made with PILLOW for instance)
screenObj.name       # A name, for debug purposes
screenObj.xy1        # The top-left coordinates of the image [x,y]
screenObj.x
screenObj.y
screenObj.xy2        # The bottom-right coordinates of the image [x2,y2]
screenObj.x2
screenObj.y2
screenObj.w          # The width of the image
screenObj.h          # The height of the image
screenObj.onclickInside   # A function to be executed on a touch event on the object (should accept as paramater the object and a (x,y) coordinate tuple)
screenObj.onclickOutside  # A function to be executed on a touch event not on the object (should accept as paramater the object and a (x,y) coordinate tuple)
screenObj.isInverted  # Boolean (Do not edit - use screen.invertObj(objId,duration))
screenObj.data        # Some data you can attach to the object, as you wish
screenObj.tags        # A set of tags the object has. Useful to remove a lot of objects at the same time
screenObj.addTag("MyTag")
screenObj.removeTag("MyTag")
screenObj.updateImg(newImg,xy1,xy2)  #Updates the image attached to the object. you must add the object to the stack once again afterwards in order to display the changes
````
