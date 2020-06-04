# TODO
(This is my own TODO list for the future)




- [Emulator] Rewrite it using a proper librairy and not openCV (will be more flexible to handle touch events and keypress)

- [Enhancement] Handle rotation, on initialization at least:  
                screen = pssm.PSSMScreen(device, 'Main', rotation=90)  
                screen.rotate(180)  
- [Enhancement] Handle swipes:  
                Element.onSwipe  (must accept : [(x1,y1),(x2,y2),(..,..),..,(xn,yn)] as argument)  
                # And add  a helper function pssm.getDirection(list_of_coords)
                # which returns the direction in ["left","right","up","down","diagonal1","diagonal2"]
                # (Probably based on the first and last coords, assuming the user does not draw circles)

- [WIP] Rewrite my dashboard with PSSM
