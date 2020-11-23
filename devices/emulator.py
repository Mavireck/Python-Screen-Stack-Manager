from time import sleep
from PIL import Image, ImageTk, ImageOps
import numpy as np
import tkinter as tk
from tkinter import ttk
from copy import copy
import socket
# Load generic device
import PSSM.devices.generic as generic

################### A FEW VARIABLES ###########################################
SCREEN_WIDTH=600
SCREEN_HEIGHT=800
WINDOW_NAME = "PSSM Emulator"
REFRESH_SIMULATION_TIME = 20

################### INIT FUNCTIONS   ##########################################
def make_blank(width, height, color=(255, 255, 255, 255)):
    """
    Returns a white (and transparent) image
    """
    img = Image.new('RGBA', (width, height), color=color)
    return img

def invert(image):
    if image.mode == 'RGBA':
        r, g, b, a = image.split()
        rgb_image = Image.merge('RGB', (r,g,b))
        inverted_image = ImageOps.invert(rgb_image)
        r2, g2, b2 = inverted_image.split()
        final_transparent_image = Image.merge('RGBA', (r2, g2, b2, a))
        return final_transparent_image
    else:
        inverted_image = ImageOps.invert(image)
        return inverted_image

################### The actual useful stuff ###################################
class Screen(generic.Screen):
    def __init__(self, onclick_handler):
        super().__init__(width=SCREEN_WIDTH,height=SCREEN_HEIGHT, grab_input=True)
        self.image = make_blank(self.width, self.height)
        self.onclick_handler = onclick_handler
        # Create window
        self._tkwindow = tk.Tk()
        # Create image
        image = ImageTk.PhotoImage(self.image)
        self._tklabel = ttk.Label(self._tkwindow, image=image)
        self._tklabel.image = image
        self._tklabel.pack()
        # Attach mouseclick event
        self._tklabel.bind("<Button 1>", self._onclick)

    def _start(self):
        tk.mainloop()
    
    def _stop(self):
        self._tkwindow.destroy()
    
    def _onclick(self, event):
        x = event.x
        y = event.y
        self.onclick_handler(x, y)
    
    def print(self, img, x=0, y=0, inverted=False, fast_invertion=False):
        """
        Takes a PIL image and pastes it on the screen at the correct coords

        Parameters:
            img : a PIL image
            x int: the x position
            y int: the y position
            inverted bool: whether to print the image inverted compared to the
                screen's inversion status
        """
        if inverted:
            img = invert(img)
        if self.isInverted:
            img = invert(img)
        self.image.paste(img, (x, y))
        self._update_image(self.image)
    
    def _update_image(self, img):
        """
        Takes care of updating the image
        """
        im = ImageTk.PhotoImage(img)
        self._tklabel.configure(image=im)
        self._tklabel.image = im

    def clear(self):
        """
        Clears the screen to a white image
        """
        blank = make_blank(self.width, self.height)
        self.print(blank, 0, 0)

    def refresh(self):
        """
        Refreshes the screen (useful for ereader)
        """
        # Let's do a simple animation
        image_before = self.capture()
        color = (0, 0, 0, 255)
        blank = make_blank(self.width, self.height, color)
        self._update_image(blank)
        self._tkwindow.after(
            REFRESH_SIMULATION_TIME, 
            lambda: self._update_image(image_before)
        )
    
    def invert(self):
        """
        Inverts the whole screen. 
        Then all the images will have to be displayed inverted
        """        
        self.isInverted = not self.isInverted
        self.image = invert(self.image)
        self._update_image(self.image)

    def set_waveform(self, mode):
        print("Waveform set : ", mode)
    
    def capture(self, full=False):
        """
        Takes a screenshot
        """
        # TODO: implement the "full" argument
        return copy(self.image)

    def after(self, milliseconds, callback, args=[]):
        """
        Execute the callback function with args after a few milliseconds
        """
        self._tkwindow.after(milliseconds, callback, *args)


class Hardware(generic.Hardware):
    def __init__(self):
        super().__init__()
        self.has_frontlight = False
        self.has_wifi = True
    
    def wifi_up(self):
        print("wifiUp - Not supported on the emulator")
        return True
    
    def wifi_down(self):
        print("wifiDown - Not supported on the emulator")
        return True
    
    def get_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except:
            print("Error gettin IP")
        finally:
            s.close()
        return IP
    
    def get_battery(self):
        """
        Returns a (status, percentage) tuple
        """
        print("get_battery - Not supported on the emulator, returning arbitrary values")
        return ("Discharging", 100)
    
    def set_frontlight(self, level):
        print("setFrontlightLevel -  Not supported on the emulator")
        return True


    