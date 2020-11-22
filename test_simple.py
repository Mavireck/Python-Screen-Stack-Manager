import sys
sys.path.append("../")
from PSSM import Stack
from PSSM.elements import Demo, Static, Rectangle
from time import sleep
from PSSM.styles import DEMO as DEMO_STYLE
from PSSM.styles import DEFAULT as DEFAULT_STYLE


def say_hello(*args):
    print("USER CLICKED ON THE DEMO RECTANGLE")
    #stack.screen.invert()


stack = Stack(style=DEMO_STYLE)

# Create the Demo
demoElt = Demo()        # Demo is a orange rectangle on the top left corner
demoElt.onclick = say_hello
demoElt.onclick_invert = True

# Show the image
imgElt = Static("./demo.jpg", centered=True, resize=True, rotation=0, 
                area=[(150, 0), (300, 300)])

# Show the rectangle
rectImg = Rectangle(area=[(0, 300), (200, 50)])
rectImg.add_text('Blabla')

# Displays the image
stack.add(demoElt)
stack.add(imgElt)
stack.add(rectImg)


# Remove the image after 5 seconds
stack.screen.after(6000, lambda:[
    print("Removing"),
    stack.remove(demoElt)
])

# Start the main loop : actually display it all
stack.mainloop()