from PIL import Image, ImageDraw
from PSSM.element import Element


LOAD_STYLE = "Load style from stack"

class Rectangle(Element):
    """
    A rectangle
    Args:
        sides str: the sides to draw : "tlr" for Top, Left, Right for instance (and "b" for bottom)
        background_color: The background color
        sides_color tuple or dict: The border color. If dict, then it should look like {'t':(255,255,255,250)}
        sides_width int or dict: border width in pixels. If dict, then it looks like : {'t':1, 'l':2}
    """
    def __init__(self, sides=LOAD_STYLE, background_color=LOAD_STYLE, 
                 sides_color=LOAD_STYLE, sides_width=LOAD_STYLE, **kwargs):
        super().__init__(**kwargs)
        self.sides = sides
        self.background_color = background_color
        self.sides_color = sides_color
        self.sides_width = sides_width
    
    def generator_img(self):
        w, h = self.area[1]
        img = Image.new("RGBA", (w, h), color=self.background_color)
        draw = ImageDraw.Draw(img, "RGBA")
        # Get the colors of the sides
        if isinstance(self.sides_color, dict):
            default = (255,255,255,255)
            c_t = self.sides_color['t'] if 't' in self.sides_color else default
            c_l = self.sides_color['l'] if 'l' in self.sides_color else default
            c_r = self.sides_color['r'] if 'r' in self.sides_color else default
            c_b = self.sides_color['b'] if 'b' in self.sides_color else default
        else:
            c_t = c_l = c_r = c_b = self.sides_color
        # Get the width of the sides
        if isinstance(self.sides_width, int):
            off = self.sides_width // 2 - 1       
            off_t = off_l = off_r = off_b = off         # Offset
            w_t = w_l = w_r = w_b = self.sides_width    # Width
        else:
            w_t = self.sides_width['t'] if 't' in self.sides_width else 1
            w_l = self.sides_width['l'] if 'l' in self.sides_width else 1
            w_r = self.sides_width['r'] if 'r' in self.sides_width else 1
            w_b = self.sides_width['b'] if 'b' in self.sides_width else 1
            off_t = max(w_t // 2 - 1, 0)
            off_l = max(w_l // 2 - 1, 0)
            off_r = max(w_r // 2 - 1, 0)
            off_b = max(w_b // 2 - 1, 0)
        if "t" in self.sides:
            side = [(0, off_t+1), (w, off_t+1)]
            draw.line(side, fill=c_t, width=w_t)
        if "l" in self.sides:
            side = [(off_l+1, 0), (off_l+1, h)]
            draw.line(side, fill=c_l, width=w_l)
        if "r" in self.sides:
            side = [(w-off_r-2, 0), (w-off_r-2, h)]
            draw.line(side, fill=c_r, width=w_r)
        if "b" in self.sides:
            side = [(0, h-off_b-2), (w, h-off_b-2)]
            draw.line(side, fill=c_b, width=w_b)
        self.image = img
        return self.image