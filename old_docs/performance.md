### Some notes on performance:
(All ran on the demo5() of the simple_demo.py file, on the emulator)

**printStack_NEW OR printStack_OLD :**  
Time per button:  
~ 0.0142s  (Checking the intersection everytime, and crop)  
~ 0.020s   (Checking the intersection everytime, and no crop)  
~ 0.0157s  (current version)  
... That was unexpected

**_clickHandler**  
~ 0.037s  
Can be improved by using a proper dichotomy search.  

**handleKeyPress** - OSK  
(Tested using examples/osk.py)  
~ 0.029s  (including the printing of the text)


**Input.pssmOnClickInside**    
~ 0.383s (yeah... I disabled it by default, since it is also very buggy)  


**THE SUDOKU**  
Call cell.update() independently: ~ 0.50s  
Call each cell update between startBatchWriting() and stopBatchWriting(): ~ 0.55s   
Therefore, changing the indicator position is faster when simply batch updating
the screen. (That was not expected).  
Call simplePrintElt() after an update(skipGen=True) : ~ 0.04s !!!   


**BATCH PRINTING vs STANDARD PRINTING**  
Running demo5(n=50).   
Total time on H2O:  
~ 0.535s (batch)  
~ 0.575s (non batch)  
~ 1.0s  (when using FBInk's no_refresh to write in batch every single item)
Total time on the emulator:  
~ 0.104s (batch)   
~ 0.564s (non batch)  
