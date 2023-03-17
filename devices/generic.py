# ####
# Defines the core device class
#
# ####


class Screen:
    def __init__(self, width, height, **args):
        self.width = width
        self.height = height
        self.area = [(0, 0), (width, height)]
        self.image = None   
        self.isInverted = False
    
    def print(self, img, x, y):
        """
        Takes a PIL image and displays it

        Parameters:
            img : a PIL image
            x int: the x position
            y int: the y position
        """
        return NotImplementedError
    
    def clear(self):
        """
        Clears the screen
        """
        return NotImplementedError
    
    def refresh(self):
        """
        Refreshes the screen (useful for ereader)
        """
        return NotImplementedError
    
    def invert(self):
        """
        Inverts the whole screen. 
        Then all the images will have to be displayed inverted
        """
        return NotImplementedError
    
    def capture(self, full=False):
        """
        Takes a screenshot and returns the corresponding image
        Args:
            full bool: whether to recalculate the image completely, 
                or simply send back self.image
        """


class Hardware:
    def __init__(self, **args):
        self.has_frontlight = False
        self.has_wifi = False
    
    def wifi_up(self):
        return NotImplementedError
    
    def wifi_down(self):
        return NotImplementedError
    
    def get_ip(self):
        return NotImplementedError
    
    def get_battery(self):
        """
        Returns a (status, percentage) tuple
        """
        return NotImplementedError
    
    def wait(self):
        return NotImplementedError