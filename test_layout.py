import sys
sys.path.append("../")
from PSSM import Stack
from PSSM.elements import Demo, Static, Rectangle, Margin
from time import sleep
from PSSM.styles import DEMO as DEMO_STYLE
from PSSM.styles import DEFAULT as DEFAULT_STYLE
from PSSM.layout import Layout


def say_hello(*args):
    print("HELLO ", args)


stack = Stack(style=DEMO_STYLE)

rectangle = Rectangle(width="?", style=DEFAULT_STYLE["Rectangle"])

text = Rectangle(background_color=(0,255,0,255), width="?")
text.add_text("Hello there !")
text.onclick = say_hello


my_layout = Layout([
    (100, [                         ]),
    ("?", ["80",    rectangle, "80" ]),
    (100, [                         ]),
    ("?", ["w/4",   text,   "w/4"   ]),
    (100, [                         ])
], area=stack.screen.area)


stack.add(my_layout)

stack.mainloop()