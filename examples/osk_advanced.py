#!/usr/bin/env python
import sys
sys.path.append("../")
import pssm
import pssmOSK
import platform
if platform.machine() in ["x86","AMD64","i686","x86_64"]:
    device = "Emulator"
else:
    device = "Kobo"


#Declare the Screen Stack Manager
screen = pssm.PSSMScreen(device,'Main')
#Start Touch listener, as a separate thread
screen.startListenerThread(grabInput=True)
#Clear and refresh the screen
screen.clear()
screen.refresh()

typed_text = ""

def onkeyPress(keyType,keyChar):
    global isCaps
    global typed_text
    if keyType == pssmOSK.KTstandardChar:
        typed_text += keyChar
    elif keyType == pssmOSK.KTbackspace:
        typed_text = typed_text[:-1]
    elif keyType == pssmOSK.KTcarriageReturn:
        typed_text += "\n"
    else:
        print("other keyType")
    # In this particular example, updating the button will lead in terrible performance
    # (a lot of funcitons will be called). So we update it without generating the parent layouts
    # Then, as we know this button is on top of the screeen, we candisplay it the most simple way, with simplePrintElt
    text.update(
        newAttributes={
            'text':typed_text
        },
        skipGeneration = True
    )
    screen.simplePrintElt(text)


text = pssm.Button(
    text            = typed_text,
    outline_color   = pssm.light_gray,
    text_xPosition  = "left",
    text_yPosition  = "top"
)
mainLayout_array = [
    ["p*20"                     ],
    ["h*0.62", (None,"p*5"),    (text, "?"), (None,"p*5")     ]
]
mainLayout = pssm.Layout(mainLayout_array,screen.area)
screen.addElt(mainLayout)

keyboard_area = [(0,int(2*screen.view_height/3)),(screen.view_width,int(screen.view_height/3))]
myOSK = pssmOSK.OSK(onkeyPress = onkeyPress, area = keyboard_area)
screen.addElt(myOSK)
