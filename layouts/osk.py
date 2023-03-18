import os
import json
from PSSM.layouts import Collection
from PSSM.elements import Element, Rectangle

########### Constants

PATH_TO_FILE = os.path.dirname(os.path.abspath(__file__))

DEFAULT_KEYMAP_PATH_STANDARD = os.path.join(PATH_TO_FILE,
                                            "config",
                                            "default-keymap-en_us.json")
DEFAULT_KEYMAP_PATH_CAPS = os.path.join(PATH_TO_FILE,
                                        "config",
                                        "default-keymap-en_us_CAPS.json")
DEFAULT_KEYMAP_PATH_ALT = os.path.join(PATH_TO_FILE,
                                       "config",
                                       "default-keymap-en_us_ALT.json")

DEFAULT_KEYMAP_PATH = {
    'standard': DEFAULT_KEYMAP_PATH_STANDARD,
    'caps': DEFAULT_KEYMAP_PATH_CAPS,
    'alt': DEFAULT_KEYMAP_PATH_ALT
}

KTstandardChar = 0
KTcarriageReturn = 1
KTbackspace = 2
KTdelete = 3
KTcapsLock = 4
KTcontrol = 5
KTalt = 6

################### CODE

## OSKButton class
class OSKButton(Rectangle):
    """
    A button for the OSK
    """
    def __init__(self, key_type, key_char="", key_is_padding=False, on_key_press=None, **kwargs):
        super().__init__()
        self.key_type = key_type
        self.key_is_padding= key_is_padding
        self.key_char = key_char
        self.on_key_press = on_key_press
        if self.on_key_press:
            self.onclick = lambda click_x, click_y : on_key_press(self.key_type, self.key_char)
        # Style
        is_standard_char = self.key_type == KTstandardChar
        self.background_color = (255,255,255,255) if is_standard_char else (220,220,220,255)
        self.sides_color = (255,255,255,255) if self.key_is_padding else (0,0,0,255)
        willChangeLayout = key_type in [KTcapsLock, KTalt, KTcarriageReturn]
        self.onclick_invert = False if willChangeLayout else True
        # Get label
        self.get_key_label()
        # Add text
        self.add_text(self.key_label, x="center", y="center")
        # Set param
        for param in kwargs:
            setattr(self, param, kwargs[param])

    def get_key_label(self):
        if self.key_type == KTstandardChar:
            self.key_label = self.key_char
        elif self.key_type == KTalt:
            self.key_label =  "ALT"
        elif self.key_type == KTbackspace:
            self.key_label =  "BACK"
        elif self.key_type == KTcapsLock:
            self.key_label =  "CAPS"
        elif self.key_type == KTcarriageReturn:
            self.key_label =  "RET"
        elif self.key_type == KTcontrol:
            self.key_label =  "CTRL"
        elif self.key_type == KTdelete:
            self.key_label =  "DEL"
        else:
            self.key_label = self.key_char

        

## OSK Class
class OSK(Element):
    """
    A PSSM Layout element which builds an on-screen keyboard
    Args:
        keymap_path (str): a path to a PSSMOSK keymap (like the one included)
        on_key_press (function): A callback function. Will be given keyType and
            keyChar as argument
    """
    def __init__(self, keymap_path=DEFAULT_KEYMAP_PATH, on_key_press=None,
                 area=None, **kwargs):
        super().__init__()
        if area is None:
            x = 0
            y = "H*2/3"
            w = "W"
            h = "H/3"
            self.area = [(x, y), (w, h)]
        self.keymap = {'standard': None, 'caps': None, 'alt': None}
        self.keymap_coll = {'standard': None, 'caps': None, 'alt': None}
        self.keymap_imgs = {'standard': None, 'caps': None, 'alt': None}
        self.keymap_paths = keymap_path if keymap_path else DEFAULT_KEYMAP_PATH
        # Load keymaps
        with open(self.keymap_paths['standard']) as json_file:
            self.keymap['standard'] = json.load(json_file)
        with open(self.keymap_paths['caps']) as json_file:
            self.keymap['caps'] = json.load(json_file)
        with open(self.keymap_paths['alt']) as json_file:
            self.keymap['alt'] = json.load(json_file)
        # Continue init
        self.lang = self.keymap['standard']["lang"]
        self.on_key_press = on_key_press
        # Default view
        self.view = 'standard'
        # Create the Collections
        self.keymap_coll['standard'] = self.build_layout(
                                               self.keymap['standard'])
        self.keymap_coll['caps'] = self.build_layout(self.keymap['caps'])
        self.keymap_coll['alt'] = self.build_layout(self.keymap['alt'])
        # the keyboard images are going to be created on generator_img call
        # Initialize layout with standard view
        self.coll = self.keymap_coll[self.view]
        self.onclick = self.coll.onclick
        for param in kwargs:
            setattr(self, param, kwargs[param])

    def generator_img(self, layout_only=False):
        """
        This generator is a bit special : we don't want it to regenerate
        everything everytime we change view. So we will generate all the views
        at once the first time. Then, unless asked to, we will only return the
        appropriate image.
        """
        if not self.keymap_imgs[self.view]: 
            self.keymap_coll[self.view].area = self.area
            self.keymap_coll[self.view].parent_stack = self.parent_stack
            self.keymap_imgs[self.view] = self.keymap_coll[self.view].generator_img()
        self.image = self.keymap_imgs[self.view]
        return  self.image

    def build_layout(self, keymap):
        # TODO : To be checked
        rows = []
        spacing = keymap["spacing"]
        for row in keymap["rows"]:
            cols = [spacing]
            for key in row:
                key_elt = OSKButton(
                    key_type        = key["keyType"],
                    key_char        = key["char"],
                    key_is_padding  = key["isPadding"],
                    width           = key["keyWidth"],
                    on_key_press    = self.on_key_press
                )
                cols.append(key_elt)
                cols.append(spacing)
            rows.append(Collection(coll=cols, axis="x", height="?"))
            rows.append(Collection(coll=[], height=spacing))
        return Collection(rows, axis="y")