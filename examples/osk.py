#!/usr/bin/env python
import sys
sys.path.append("../")
import pssm
import platform
if platform.machine() in ["x86","AMD64","i686","x86_64"]:
    device = "Emulator"
else:
    device = "Kobo"

######################### - Main logic - ##################################

#Declare the Screen Stack Manager
screen = pssm.PSSMScreen(device,'Main')
#Clear and refresh the screen
screen.clear()
screen.refresh()
# Now to initialize the keybaord
screen.OSKInit(area = None)
#Start Touch listener, as a separate thread
screen.startListenerThread(grabInput=True)



inputText = pssm.Input(
    outline_color   = "black",
    text_xPosition  = "left",
    text_yPosition  = "top"
)
mainLayout_array = [
    ["p*20"                                                   ],
    ["H*0.62", (None,"p*5"),    (inputText, "?"), (None,"p*5")     ]
]
mainLayout = pssm.Layout(mainLayout_array,screen.area)
screen.addElt(mainLayout)


if __name__ == "__main__":
    screen.device.startMainLoop()   # only necessary for the emulator, and must be the very last function of your code
