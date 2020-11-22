import sys
sys.path.append("../")
from PSSM import Stack
from PSSM.elements import Demo, Static, Rectangle, Margin
from time import sleep
from PSSM.styles import DEMO as DEMO_STYLE
from PSSM.layout import Layout


stack = Stack(style=DEMO_STYLE)

rectangle = Rectangle(width="?")

text = Rectangle(background_color=(0,255,0,255))
text.add_text("Hello there !")


my_layout = Layout([
    (80, ["80", rectangle, "80"]),
    (100, []),
    ("?", ["?/4", text, "?/4"]),
    ("200", [])
], area=stack.screen.area)


stack.add(my_layout)

stack.mainloop()