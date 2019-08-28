# Kobo-Screen-Stack-Manager
KSSM - A handy tool to create an image-based user interface with easier layer control.


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