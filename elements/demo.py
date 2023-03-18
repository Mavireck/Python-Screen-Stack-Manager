from PIL import Image
from .element import Element


class Demo(Element):
    def __init__(self):
        super().__init__()
        self.area = [(0,0), (100, 200)]
    
    def generator_img(self):
        color = (255, 120, 0, 255)
        img = Image.new('RGBA', self.area[1], color=color)
        self.image = img