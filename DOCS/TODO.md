# TODO
(This is my own TODO list for the future)

**PSSM**
- Do all the TODO in pssm.py
- [M] Make sure it can handle RGB images ! (Perhaps use a boolean, like screen.is_rgb, in order not to deal with full RGB images on ereaders which will have limited resources)
- [M] Allow rotations (on startup only - no way to rotate when it is already started)

**What to port**
- [L] Import Kobo-Python-OSKandUtils for use within PSSM
- [L] Adapt Kobo-Input-Python to other kobo devices (it was only tested on H2O v1 so far)
- [L] Merge frontlight, Wifi, Kobo-Input-Python into PSSM_kobo (and delete old repos)
- [XXL] (Port my dashboard to PSSM and split it into multiple files)

**What else to do**
- Make POL more coherent (pass area as argument instead of (x,y,w,h) - same in PSSM)
- POL : pass a font name + font size as argument, and open the font directly within POL
- [M] Add objects to pssmObjectsLibrairy
- [M] More documentation (including on pssmObjectsLibrairy)
