# TODO
(This is my own TODO list for the future)

**Emulator**
- Make an emulator with OpenCV (by replacing pssm_kobo.py with pssm_opencv.py, passing as argument --emulator True) - With this, check that it can easily be adapted to other devices / systems (why not even make a web app, or an android app with it ;) - I will have a look at how to adapt it to handle some sort of animation)
- *If the emulator is a success, then allow to use the computer's built-in keyboard.*
- Make sure it can handle RGB images ! (Perhaps use a boolean, like screen.is_rgb, in order not to deal with full RGB images on ereaders which will have limited resources)

**What to clean**
- Remove depecrecated nested structure (+ cleanup code)
- Remove unnecessary deepcopies, and test mutability issues

**What to port**
- Adapt Kobo-Input-Python to other kobo devices (it was only tested on H2O v1 so far)
- Import Kobo-Python-OSKandUtils for use within PSSM
- Publish my *Game of life* port as a demo, and to test performance
- (Port my dashboard to PSSM and split it into multiple files)

**What else to do**
- [+++++++] Make a POL object with the "quit" icon -> use it in all my personal projects which require a Quit button
- [+++++++] More generally, make a POL function which makes a button out of a png icon
- [++] Add objects to pssmObjectsLibrairy
- More documentation (including on pssmObjectsLibrairy)
