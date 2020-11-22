from PIL import Image, ImageDraw
from PSSM.element import Element



class Margin(Element):
    """
    A margin (transparent)
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.type = "Margin"
    
    def generator_img(self):
        return None