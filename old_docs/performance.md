### Some notes on performance:
(All ran on the demo5() of the simple_demo.py file, on the emulator)

**printStack_NEW OR printStack_OLD :**  
~ 0.0142s  (New version, without crop)  
~ 0.020s   (New version, with crop)  
~ 0.0157s  (old version)  
*... That was unexpected*

**_clickHandler**  
~ 0.037s

**handleKeyPress** - OSK  
(Tested using examples/osk.py)  
~ 0.029s

**addElt**  
~ 0.016s  (on the emulator)  
*Most of the time is take by simplePrintElt*

**Input.pssmOnClickInside**  
~ 0.383s (yeah... I disabled it by default, since it is also very buggy)  
