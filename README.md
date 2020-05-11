# Python-Screen-Stack-Manager
PSSM - A handy tool to create an image-based user interface with easier layer control.
It makes an extensive use of PIL (Pillow) to handle images.
If you need to run it on a Kobo/Kindle, you require FBInk and pyFBink.
If you need to test it on a computer, you need OpenCV

**Warning** - I am no python expert, I had to work around quite a few simple issues. Do not expect the code to be work perfectly out of the bor, nor to be written elegantly.

### What it does
Look at the test file for an example.
When you create a user interface, you often find yourself to be needing an easy to print something on top of what was already there, then remove that thing.
My tool does exactly that.
First, you create a ScreenManagerObject.
Whenever you want to display something, you create a ScreenObject. Then you can add the ScreenObject to the ScreenManagerStack.
What this does, is that it displays the ScreenObject on top of what was previously here.
And what is great, is that you can remove what is under ScreenObject, without removing ScreenObject. You can also update things hidden behind ScreenObject etc...


And the ScreenManager can also handle touch inputs, it serves as a touch driver function. (And the touch driver function can be started as a separate thread if you want to do multiple things at once).
What it does in this case, is that it loops through the stack, the object on the top being the first looked, and it looks if a touch click was made in its area. If so, then it calls the function associated with the ScreenObject.

### Documentation
Have a look here :
[Documentation](DOCS/HELP.md)

### Images are worth thousands words
First, create a stackManager object:
`screen = ScreenStackManager(name='Main manager')`

Then, create your screen object: (I am using pillow here).
(See the docs for help).
PSSM now allows to create interfaces in a very visual way : what you see on the code... is what you get!

Then, you can display these objects (and a white canvas for instance)
```python
screen.clear()  # Not necessary
screen.refresh()
screen.createCanvas()
screen.addElt(obj1)
screen.addElt(obj2)
```
The output will look like that :
![PSSM1](DOCS/PSSM1.png)
Then, the magic comes in.
You can for instance remove the first object, although is has been printed UNDER obj2!
If you do this:
`screen.removeObj(obj1)`
You get this:
![PSSM2](DOCS/PSSM2.png)


There are a lot more features(like handling the screen inversion and partial inversion, attaching touch events etc...), I will let you dive into the source code for more information.
