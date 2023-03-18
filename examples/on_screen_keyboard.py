#!/usr/bin/env python
import sys
sys.path.append("../")
from PSSM import Stack
from PSSM.elements import Rectangle
from PSSM.styles import DEFAULT as DEFAULT_STYLE
from PSSM.layouts import Collection
from PSSM.layouts import OSK, KTstandardChar,KTcarriageReturn,KTbackspace, KTdelete, KTcapsLock, KTcontrol, KTalt


import platform
if platform.machine() in ["x86", "AMD64", "i686", "x86_64"]:
    device = "Emulator"
else:
    device = "Kobo"



typed_text = "Lorem ipsum dolor sit amet, ..."


# ########################### - Main logic - ##################################
if __name__ == "__main__":

    def onkeypressfct(keyType, keyChar):
        global typed_text
        # Update text
        if keyType == KTstandardChar:
            typed_text += keyChar
        elif keyType == KTbackspace:
            typed_text = typed_text[:-1]
        elif keyType == KTcarriageReturn:
            typed_text += "\n"
        else:
            print("other keyType")
        # Debug
        print(f"Pressed keytype={keyType} and keychar={keyChar} ")
        # We use on_top=True here because we know the text is on top of the screen,
        # therefore it is faster to just tell PSSM to print it again on top of everything
        text.update(attr={'text':typed_text}, on_top=True)


    def say_hello(*args):
        print("User clicked on the demo rectangle")


    # Declare the Screen Stack Manager
    stack = Stack(style=DEFAULT_STYLE)
    
    # Clear and refresh the screen
    stack.screen.clear()
    stack.screen.refresh()

    # Initialize the OSK 
    osk = OSK(on_key_press=onkeypressfct)

    # Initialize the input rectangle
    text = Rectangle(outline_color="black")
    text.add_text(typed_text)
    text.onclick = say_hello

    # Define layout
    demo = Collection(axis="y", area=stack.screen.area, coll=[
        Collection([], height=50),
        Collection(["p*5", text, "p*5"], height="h/3")
    ])

    # Add elements on the screen
    stack.add(demo)
    stack.add(osk)

    if device == "Emulator":
        # only necessary for the emulator, and must be at the very end
        stack.mainloop()