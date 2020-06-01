### Some notes on performance:
(All ran on the demo5() of the simple_demo.py file, on the emulator)

**printStack_NEW OR printStack_OLD :**  
Time per button:  
~ 0.0142s  (New version, without crop)  
~ 0.020s   (New version, with crop)  
~ 0.0157s  (old version)  
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
Updating one cell: ~ 0.50s  
Updating the whole screen: ~ 0.61s  
Therefore, changing the indicator position is faster when simply batch updating
the screen. (0.61s vs 2*0.50s).   
However, it is weird it takes twice as much time to update two cells, that is not the same behaviour as in demo5:   

**BATCH PRINTING vs STANDARD PRINTING**  
Running demo5(n=50).   
Total time on H2O:  
~ 0.535s (batch)  
~ 0.575s (non batch)  
Total time on the emulator:  
~ 0.104s (batch)   
~ 0.564s (non batch)  
