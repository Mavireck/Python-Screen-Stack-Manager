# TODO
(This is my own TODO list for the future)


- [Element] Write a PopupText class to prompt text
- [Element] Write a PopupChoices class with a button for each choice (which works a bit like ButtonList)

- [Emulator] Rewrite it using a proper librairy and not openCV (will be more flexible to handle touch events and keypress)
- [Emulator] Handle partial screen inversion

- [Enhancement] Handle rotation, on initialization at least:  
                screen = pssm.PSSMScreen(device, 'Main', rotation=90)  
                screen.rotate(180)  
- [Enhancement] Handle swipes:  
                Element.onSwipe  (must accept : [(x1,y1),(x2,y2),(..,..),..,(xn,yn)] as argument)  
                # And add  a helper function pssm.getDirection(list_of_coords)
                # which returns the direction in ["left","right","up","down","diagonal1","diagonal2"]
                # (Probably based on the first and last coords, assuming the user does not draw circles)


- [Performance] Test the performance gain when drawing in batch (with FBInk's no_refresh) when printing a whole layout instead of doing the operation with pillow
- [Performance] Learn more about HW dithering modes and other EInk tweaks (especially to make partial inversion faster, it is soooo slow)

- [WIP] Rewrite my dashboard with PSSM
