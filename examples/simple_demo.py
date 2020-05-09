#!/usr/bin/env python
import sys
sys.path.append("../")
import pssm
import pssmElementsLibrairy as PEL

import platform
if platform.machine() in ["x86","AMD64","i686","x86_64"]:
    device = "Emulator"
else:
    device = "Kobo"


#Declare the Screen Stack Manager
screen = pssm.ScreenStackManager(device,'Main')
#Start Touch listener, as a separate thread
screen.startListenerThread()
#Clear and refresh the screen
screen.clear()
screen.refresh()
# Create a blank canvas
screen.createCanvas()
print("just made canvas")





def demo1():
    def reactFctn(elt,coords):
        print(coords," - ",elt.text)

    button1 = PEL.Button("Hey", onclickInside=reactFctn)
    button2 = PEL.Button("Hey2",onclickInside=reactFctn)
    button3 = PEL.Button("Hey3",onclickInside=reactFctn)
    layout_demo = [
        [30                                                                             ],
        [100, (None,20), (button1,200), (None,20)                                       ],
        [30                                                                             ],
        [100, (None,20), (button2,200), (None,20)                                       ],
        [30                                                                             ],
        [100, (None,20), (button3,200), (None,20), (PEL.Button("nope"),300), (None,10)  ],
        [40]
    ]
    myLayout = PEL.Layout(layout_demo,screen.area)
    myLayout.tags.add("layout")
    screen.addElt(myLayout)


def demo2():
    reactFctn = lambda elt,coords : print(coords," - ",elt.text)
    myButtonList = PEL.ButtonList(
        buttons = [
            {'text':'Yup1','onclickInside':reactFctn},
            {'text':'Yup2','onclickInside':reactFctn},
            {'text':'Yup3','onclickInside':reactFctn},
            {'text':'Yup4','onclickInside':reactFctn},
            {'text':'Yup5','onclickInside':reactFctn}
        ],
        margins = [200,200,100,100],
        spacing = 30,
        area = screen.area
    )
    screen.addElt(myButtonList)


def demo3():
    reactFctn   = lambda elt,coords : print(coords," - ",elt.text)
    buttons     = [{'text':'This is button number : ' + str(n), 'onclickInside':reactFctn} for n in range(8)]
    buttonList  = PEL.ButtonList(buttons=buttons, margins=[30,30,100,100], spacing=10)
    button_welcome  = PEL.Button(text="Welcome !",radius=20, background_color = 220, font=PEL.Merri_bold, font_size = 35)
    button_previous = PEL.Button("Previous",onclickInside = reactFctn)
    button_reboot   = PEL.Button("Reboot")
    button_next     = PEL.Button("Next")
    menu = [
        [30                                                                                                             ],
        [100,            (None,80),                       (button_welcome,"?"),                    (None,80)            ],
        ["?",                                               (buttonList,"?")                                            ],
        [100,(None,30), (button_previous,"?"), (None,30), (button_reboot,"?"), (None,30), (button_next,"?"), (None,30)  ],
        [30                                                                                                             ]
    ]
    myLayout = PEL.Layout(menu,screen.area)
    screen.addElt(myLayout)

demo3()