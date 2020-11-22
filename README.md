# Python-Screen-Stack-Manager
PSSM - A handy tool to create an image-based user interface with easier layer control.
It makes an extensive use of PIL (Pillow) to handle images.
If you need to run it on a Kobo/Kindle, you require FBInk and pyFBink.
If you need to test it on a computer, you need OpenCV.

**Warning** - I am no python expert, I had to work around quite a few simple issues. Do not expect the code to be work perfectly out of the box, nor to be written elegantly.

### Why have I made this ??
This tool was made to be used on Kobo e-readers.  
They are handheld devices running Linux, so people were able to run Python on it.   
However, no standard or up-to-date librairy will handle printing things on a their EInk framebuffer. Luckily NiLuJe provided a tool to print images on the screen and python (and Go and Lua) bindings to use it : [FBInk](https://github.com/NiLuJe/FBInk).  
So I made this tool to handle the creation of a user interface. Because being able to print things is nice, but when it comes to building a full menu, it can be very long and annoying, as you have to code every single line on the screen with a few lines of code.  
PSSM handles that for you. I drew inspiration from PySimpleGUI, because I really liked how simple it was to build a basic layout with it. I did however add a few features which allow to place elements exactly where you want on the screen, in order to match my needs.  




# WARNING  V3 IS COMING!!
**PSSM is currently being rewritten entirely. The last documented version can be found in the 'v2' branch of this repo.**