from PIL import Image, ImageDraw
from PSSM.element import Element


LOAD_STYLE = "Load style from stack"

class Margin(Element):
    """
    A margin (transparent)
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def generator_img(self):
        return None