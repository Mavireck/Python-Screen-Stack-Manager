from platform import machine
from PIL import Image
from .utils import coords_in_area
from .styles import DEFAULT as DEFAULT_STYLE

class Stack():
    def __init__(self, style=DEFAULT_STYLE):
        if machine() in ["x86", "AMD64", "i686", "x86_64"]:
            import PSSM.devices.emulator as pssm_device
        else:
            import PSSM.devices.kobo as pssm_device
        self.screen = pssm_device.Screen(onclick_handler=self._click_handler)
        self.hardware = pssm_device.Hardware()
        self.style = style
        self.stack = []

    def mainloop(self):
        """
        Actually starts the program
        """
        self.screen._start()

    def print_stack(self, area=None):
        # TODO: optimize ?
        dim = (self.screen.width, self.screen.height)
        white = (255, 255, 255, 255)
        img = Image.new("RGBA", dim, color=white)
        for elt in self.stack:
            (x, y) = elt.area[0]
            if elt.is_layout:
                elt.generator(layout_only=True)
            elif not elt.is_generated:
                elt.generator()
            if elt.image is not None:
                img.paste(elt.image, (x, y))
        if area:
            [(x, y), (w, h)] = area
            box = (x, y, x+w, y+h)
            img = img.crop(box=box)
        else:
            (x, y) = self.screen.area[0]
        self.screen.print(img, x, y)
        
    def _print_elt(self, elt):
        """
        Actually prints the element. Does not call the generator
        """
        # Then, we print it
        x, y = elt.area[0]
        self.screen.print(elt.image, x, y)

    def add(self, elt):
        """
        Adds an element to the stack and prints it
        """
        elt.parent_stack = self
        self.stack.append(elt)
        elt.generator()
        self._print_elt(elt)
    
    def remove(self, elt, skip_print=False):
        """
        Removes an element from the stack
        """
        self.stack.remove(elt)
        if not skip_print:
            self.print_stack(area=elt.area)

    def _click_handler(self, click_x, click_y):
        """
        Handles the click events from the device
        """
        for elt in self.stack[::-1]:
            if elt.area and coords_in_area(elt.area, click_x, click_y):
                self._click_handler_to_elt(elt, click_x, click_y)
                break

    def _click_handler_to_elt(self, elt, click_x, click_y):
        """
        Actually takes care of dispatching the click to the element
        """
        def invert_back():
            # Let's avoid printing something which may have been removed
            # from the stack in the meantime
            if elt in self.stack:
                inv = elt.is_inverted
                self.screen.print(elt.image, x, y, inverted=inv)
        
        if elt.onclick_invert:
            x, y = elt.area[0] 
            inv = not elt.is_inverted
            self.screen.print(elt.image, x, y, inverted=inv)
            self.screen.after(elt.onclick_invert_duration, invert_back)
        if elt.onclick is not None:
            elt.onclick(click_x, click_y)