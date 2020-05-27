#!/usr/bin/env python
import sys
sys.path.append("../")
import pssm
import platform
if platform.machine() in ["x86","AMD64","i686","x86_64"]:
    device = "Emulator"
else:
    device = "Kobo"


########################## - TOOLS - ######################################
typed_text = ""

def keyPressFct(keyType,keyChar):
    """
    Example of an onKeyPress callback function, will be executed when the user press on a key.
    See demo here :
    ![Demo](https://raw.githubusercontent.com/Mavireck/Python-Screen-Stack-Manager/master/examples/screenshot-osk_advanced.jpg)
    """
    global isCaps
    global typed_text
    if keyType == pssm.KTstandardChar:
        typed_text += keyChar
    elif keyType == pssm.KTbackspace:
        typed_text = typed_text[:-1]
    elif keyType == pssm.KTcarriageReturn:
        typed_text += "\n"
    else:
        print("other keyType")
    # In this particular example, updating the button will lead in terrible performance
    # (a lot of funcitons will be called). So we update it without generating the parent layouts
    # Then, as we know this button is on top of the screeen, we candisplay it the most simple way, with simplePrintElt
    # The natural way to do it (without perforamcen concern) would be to run:
    #text.update(newAttributes={'text':typed_text})
    text.update(
        newAttributes={
            'text':typed_text
        },
        skipPrint = True
    )
    screen.simplePrintElt(text,skipGeneration=True)


######################### - Main logic - ##################################

#Declare the Screen Stack Manager
screen = pssm.PSSMScreen(device,'Main')
#Start Touch listener, as a separate thread
screen.startListenerThread(grabInput=True)
#Clear and refresh the screen
screen.clear()
screen.refresh()
# Now to initialize the keybaord
screen.OSKInit(area = None,onKeyPress = keyPressFct)



text = pssm.Button(
    text            = typed_text,
    outline_color   = "white",
    text_xPosition  = "left",
    text_yPosition  = "top"
)
mainLayout_array = [
    ["p*20"                                                   ],
    ["h*0.62", (None,"p*5"),    (text, "?"), (None,"p*5")     ]
]
mainLayout = pssm.Layout(mainLayout_array,screen.area)
screen.addElt(mainLayout)

# And to display the keyboard
screen.OSKShow()

# You can also hide it
#screen.device.wait(5)
#screen.OSKHide()

# And display it again
#screen.device.wait(5)
#screen.OSKShow()
