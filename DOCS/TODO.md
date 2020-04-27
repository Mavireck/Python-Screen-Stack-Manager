# TODO
(This is my own TODO list for the future)

**Emulator**
- [S] Make the emulator better
- [L] If the emulator is a success, then allow to use the computer's built-in keyboard.
- [S] Make sure it can handle RGB images ! (Perhaps use a boolean, like screen.is_rgb, in order not to deal with full RGB images on ereaders which will have limited resources)
- [M] Avoid looping continously to read click events on the emulator

**What to clean**
- [XS] Remove depecrecated nested structure (+ cleanup code)
- [S] Remove unnecessary deepcopies, and test mutability issues

**What to port**
- [L] Adapt Kobo-Input-Python to other kobo devices (it was only tested on H2O v1 so far)
- [L] Import Kobo-Python-OSKandUtils for use within PSSM
- [M] Publish my *Game of life* port as a demo, and to test performance
- [XXL] (Port my dashboard to PSSM and split it into multiple files)

**What else to do**
- [M +++++] Make a POL object with the "quit" icon -> use it in all my personal projects which require a Quit button
- [M +++++] More generally, make a POL function which makes a button out of a png icon
- [M ++] Add objects to pssmObjectsLibrairy
- [M] More documentation (including on pssmObjectsLibrairy)
