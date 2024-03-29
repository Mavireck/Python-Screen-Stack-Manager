from PIL import ImageDraw, ImageFont
from ..styles import DEFAULT as DEFAULT_STYLE

last_used_id = 0
LOAD_STYLE = "Load style from stack"

class Element():
    def __init__(self, **kwargs):
        global last_used_id
        self.id = last_used_id
        last_used_id += 1
        self.image = None
        self.area = [(None,None), ("?", "?")]        # Shape [(x, y), (w, h)]
        self.is_layout = False
        self.is_inverted = None
        self.is_generated = False
        self.width = None
        self.height = None
        self.style = {}
        # Events on click
        self.onclick = None
        self.onclick_invert = False
        self.onclick_invert_duration = 80   # Time in milliseconds
        # Useful stuff
        self.parent_layouts = []
        self.parent_stack = None
        # Text data
        self.add_text("")   # Initialize with default values
        # Anything else ?
        for param in kwargs:
            setattr(self, param, kwargs[param])

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.id == other.id

    def generator(self, area=None, skip_styles=False, layout_only=False):
        """
        The generator is the function which is called when the container layout
        wants to build an image.
        """
        if area:
            self.area = area
        self._convert_area()
        if not skip_styles:
            self._parse_styles()
        self.generator_img()
        if self.text:
            self.generator_text()
        self.is_generated = True
        return self.image
    
    def generator_img(self):
        """
        Creates the image. Each subclass will have to implement this function.
        """
        return NotImplemented
    
    def generator_text(self):
        """
        Add the text (if any) to the element.
        """
        x, y = self.text_x, self.text_y
        area_w, area_h = self.area[1]
        # Get font size
        size = self._convert_dimension(self.text_size)
        # Load image
        draw = ImageDraw.Draw(self.image)
        # Load font
        font = ImageFont.truetype(self.text_font, size)
        text_w, text_h = draw.textsize(self.text, font=font)
        # Find x position
        if isinstance(x, str):
            x.lower()
        if x in ["left", "l"]:
            x = 0
        elif x in ["center", "c", "centered"]:
            x = int(0.5*area_w - 0.5*text_w)
        elif x in ["right", "r"]:
            x = int(area_w - text_w)
        else:
            x = self._convert_dimension(x)
            if not isinstance(y, int):
                raise ValueError("Invalid text position : {}".format(self.text_x))
        # Find y position
        if isinstance(y, str):
            y.lower()
        if y in ["top", 't']:
            y = 0
        elif y in ["center", "c", "centered"]:
            y = int(0.5*area_h - 0.5*text_h)
        elif y in ["bottom", "b"]:
            y = int(area_h - text_h)
        else:
            y = self._convert_dimension(y)
            if not isinstance(y, int):
                raise ValueError("Invalid text position : {}".format(self.text_y))
        # Draw text
        draw.text((x, y), self.text, fill=self.text_color, font=font)
        return self.image

    def update(self, attr={}, skip_gen=False, skip_print=False, on_top=False):
        """
        Pass a dict as argument, and it will update the Element's attributes
        accordingly (both its attribute and then the screen).

        Arguments:
            attr dict: the dictionnary of attributes to set
            skip_gen bool: whether to skip the generation of this element
            skip_print bool: whether to skip printing
            on_top bool: whether to force print it on top of the stack, 
                whatever the actual stack position (can be much faster).
        """
        # First, we set the attributes
        for param in attr:
            setattr(self, param, attr[param])
        if not skip_gen:
            # we recreate the pillow image of this particular object
            self.generator()
        if (not skip_print) and (not skip_gen):  # No need to update if no regen
            if on_top:
                self.parent_stack._print_elt(self)
            else:
                hasParent = len(self.parent_layouts) > 0
                # We don't want unncesseray generation when printing batch
                if hasParent:
                    # We recreate the pillow image of the oldest parent
                    # And it is not needed to regenerate standard objects, since
                    oldest_parent = self.parent_layouts[0]
                    oldest_parent.generator(layout_only=True)
                # Then, let's reprint the stack
                self.parent_stack.print_stack(area=self.area)
        return True
    
    def _convert_area(self):
        [(x,y), (w,h)] = self.area
        x = self._convert_dimension(x)
        y = self._convert_dimension(y)
        w = self._convert_dimension(w)
        h = self._convert_dimension(h)
        self.area = [(x,y), (w,h)]
        return True

    def _convert_dimension(self, dimension):
        """
        Converts the user dimension input (like "h*0.1") to to proper integer
        amount of pixels.
        Basically, you give it a string. And it will change a few characters to
        their corresponding value, then return the evaluated string.

        Examples:
            I HIGHLY recommend doing only simple operation, like "H*0.1", or
            "W/10", always starting with the corresponding variable.
            But you can if you want do more complicated things:
            elt.convertDimension("H+W")
                    ->  screen_height + screen_width
            elt.convertDimension("p*300+max(w, h)")
                    -> 300 + max(element_width, screen_height)

        Note:
            When using question mark dimension (like "?*2"), the question mark
            MUST be at the beginning of the string
        """
        if isinstance(dimension, int):
            return dimension
        elif isinstance(dimension, str):
            # INIT
            W = self.parent_stack.screen.width
            H = self.parent_stack.screen.height
            if self.area:
                w, h = self.area[1]
            else:
                # area not defined. Instead of being stuck, let's assume the
                # screen height and width are a decent alternative
                w, h = W, H
            replace_dict = {
                'p' : '1',
                'P' : '1',
                'W' : str(W),
                'H' : str(H),
                'w' : str(w),
                'h' : str(h)
            }
            # We replace every 'w' or 'h' with their corresponding value
            for key in replace_dict.keys():
                dimension = dimension.replace(key, replace_dict[key])
            if "?" in dimension:
                return dimension
            else:
                return int((eval(dimension)))
        else:
            message = "[PSSM] Could not parse dimension : {}".format(dimension)
            raise TypeError(message)    

    def add_text(self, text, font=LOAD_STYLE, color=LOAD_STYLE,
                 size=LOAD_STYLE, x=LOAD_STYLE, y=LOAD_STYLE):
        """
        Adds text on the element. Note that the text is not actually printed on
        the image, but it will be when the generator is called.

        Valid inputs for x are ["left", "l", "center", "c", "centered", "right", "r"]
        Valid inputs for y are ["top", "t", "center", "c", "centered", "bottom", "b"]
        """
        self.text  = text
        self.text_font  = font
        self.text_color = color
        self.text_size  = size
        self.text_x     = x
        self.text_y     = y

    def _parse_styles(self, list_styles=[]):
        """
        Parse the all the "style" arguments

        Arguments:
            list_styles list: list of styles to parse (if empty, will 
                              parse them all)
        """

        def is_defined(arg):
            return arg is not None and arg != LOAD_STYLE
        
        parent_style = self.parent_stack.style

        # Avoid errors if i forgot to add the default style
        elt_type = self.__class__.__name__

        if not elt_type in DEFAULT_STYLE:
            mes = "[PSSM Internal eror] No default style defined\
                   for {}".format(elt_type)
            raise NameError(mes)

        if len(list_styles)>0:
            where_from = list_styles
        else:
            where_from = DEFAULT_STYLE[elt_type]
    
        # then loop through the possible styles and parse them
        for arg in where_from:
            set_style = getattr(self, arg)
            if not is_defined(set_style):
                if arg in self.style and is_defined(self.style[arg]):
                    # We set it using self.style if possible
                    setattr(self, arg, self.style[arg])
                elif elt_type in parent_style and arg in parent_style[elt_type]:
                    # else, we set it with the stack style
                    elementstyle = parent_style[elt_type]
                    setattr(self, arg, elementstyle[arg])
                else:
                    # else, we rollback to the default one from pssm
                    setattr(self, arg, DEFAULT_STYLE[elt_type][arg])
        