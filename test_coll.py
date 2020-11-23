import sys
sys.path.append("../")
from PSSM import Stack
from PSSM.elements import Demo, Static, Rectangle, Margin
from time import sleep
from PSSM.styles import DEMO as DEMO_STYLE
from PSSM.styles import DEFAULT as DEFAULT_STYLE
from PSSM.layouts import Collection


def say_hello(*args):
    print("HELLO ", args)


stack = Stack(style=DEFAULT_STYLE)

# Rectangle
rectangle = Rectangle(width="?")

# Green rectangle with text
text = Rectangle(background_color=(0,255,0,255), height="?")
text.add_text("Hello there !")
text.onclick = say_hello

## Example of a row
# demo = Collection([ "10", rectangle, "20",text, "30"], area=stack.screen.area, axis="x")

## Example of a col
# demo = Collection([ "?", rectangle, "?*2", text, "?"], area=stack.screen.area, axis="y")

## Example of a Layout  (axis="x" being the default axis, no need to tell it)
demo = Collection(axis="y", area=stack.screen.area, coll=[
    Collection(["?", rectangle, "?*2", rectangle, "?"]),
    Collection([], height=100),
    Collection(["?",    text,   "?*2",    text,   "?"])
])

stack.add(demo)


# Start
stack.mainloop()