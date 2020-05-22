# Python-Screen-Stack-Manager - Help

**Read first**
- You should (and I may say you MUST) check the examples in the 'example' folder.  
It contains a few examples and useful comments. Make sure it works before testing anything else.
- Read the main file (pssm.py), it has a few helpful comments and you can read all the arguments each function expects here.



## Table of contents
1. Setup
2. Initializing PSSM
3. Basic functions
4. The ScreenStackManager class
5. The Element class
6. The Layout subclass





## 1. Setup
To install PSSM on your Kobo, I recommend you download this repo and put it here on your device :
> /mnt/onboard/.adds/mavireck/Python-Screen-Stack-Manager

If you have already used one of my apps, it should already be there (but it may be an older version)
Then, you only have to import my files at the beginning of your script :
```python
sys.path.append('/mnt/onboard/.adds/mavireck/Python-Screen-Stack-Manager') #To tell Python where to look for these files
import pssm  #The core logic
```




## 2. Initializing PSSM
###### Declaring the stack manager
```python
# Declare the Screen Stack Manager.
# "Kobo" points out to what kind of device to use. For the emulator, type "Emulator".
# Kindles should work well with "Kobo" too, thanks to FBInk, but I doubt touch input will work.
# 'Main' is the name of the screen manager (it is quite useless actually)
screen = pssm.ScreenStackManager("Kobo",'Main')
# Some interesting variables are available : width, height, offset, view_height...
# You should look at pssm.py for more.
screen.width
screen.height
```

###### Attaching the Touch listener
You can choose to start the touch listener as a separate thread with :
```python
# grabInput is a boolean, if set to True, PSSM will prevent any other software from
# registering touch events.
screen.startListenerThread(grabInput = False)  
```




## 3. Basic functions
```Python
screen.clear()        # Clears the screen
screen.refresh()      # Refreshes the screen
screen.addElt(myElement)          # Adds an element to the stack
screen.invertElt(myElement.id,5)  # Inverts an element for 5 seconds (Please do not edit that object in the meantime, it may break quite a few things)
screen.removeElt(myElement.id)    # Removes the element from the screen
screen.removeAllWithTag("MyTag")  # Removes all the objects which have the tag "MyTag"
```


## 4. The ScreenStackManager class
PSSM contains two different class of objects :
- The ScreenStackManager class  (usually, you have only 1 and call it 'screen' : screen = pssm.ScreenStackManager())
- The Element class
The first is the one which will perform most of the heavy operations.
The second is a GUI Element, something which is to be displayed on screen.
In short, everytime you may want to display something on screen (like a button), you will create it with the appropriate class.
Then, you will call:
```Python
screen.addElt(myElement)
```
The element will then be displayed on screen.
You can do quite a lot of operations, I will let you delve into pssm.py for more information.
As a quick note, through screen.device, you can do some other operations, like :
```Python
screen.device.setFrontlightLevel(50)
screen.device.readBatteryPercentage()
screen.device.readBatteryState()
screen.device.get_ip()
screen.device.wifiDown()
screen.device.wifiUp()
```



## 5. The Element class
>TODO



## 6. The Layout subclass
That is a subclass of the Element class.

It will be your best friend, but for more information, have a look at the examples.
Basically, you give it a layout like that :
```Python
layout_demo = [
      [30                                                                                         ],
      ["h*0.01", (None,"?/2"),        (pssm.Button("But1"),200),        (None,"?/2")              ],
      ["h*0.001"                                                                                  ],
      ["p*100", (None,"w*0.3"),       (pssm.Button("But2"),200),        (None,"w*0.3")            ],
      [30                                                                                         ],
      [100, (None,20), (pssm.Button("But3"),200), (None,20), (pssm.Button("nope"),300), (None,10) ],
      [40                                                                                         ]
  ]
# You can then add it to the screen:
area = screen.area   # That is the area where the Element will be displayed. PSSM areas are of the following shape : [(x,y),(w,h)]
myLayout = pssm.Layout(layout_demo,area)
screen.addElt(myLayout)
```
You may wonder what it all means. It is actually meant to be very visual.
Now **what you code is what you get** ;)

###### Every row in layout_demo represents a row on the screen.  
Rows always start with either an integer or a weird string like : "?", "p\*0.01", "h/2", "w/4" ,....  
This variable represents the height of the screen.  
**If it is an integer**, it represents an height in pixels.  
**If it starts with "p"**, then it also represents a number of pixels : "p\*100" means 100 pixels  
**If it starts with "w"**, then it is a fraction of the working area's width : "w/2" and "w\*0.5" mean half the width  
**If it starts with "h"**, then it is a fraction of the working area's height : "h/2" and "h\*0.5" mean half the height  
**If it starts with "?"**, then it means you leave the Layout to guess the size. In other terms, it means the Layout will calculate the remaining width (or height) available, and split it into equal parts. It also accounts differents proportions : for instance, if one of your row has height : "?\*1", and another "?\*2", then the second one will be twice as big as the first. But the sum of these two are made in such a way as to make them occupy all the remaining place.  

###### Then, every Tuple in a row represents an Element.
The first attribute of the Tuple being the Element itself.  
The second attribute is the width of the object, which obeys the same rules as the height as described before.  
A None Element is treated as a margin basically.
