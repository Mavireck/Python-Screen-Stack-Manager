from PIL import Image
from .element import Element


class Static(Element):
    """
    A very simple element which only displays an image

    Arguments:
        image str or PIL Image: Path to image or PIL image
        centered bool: Center the image ?
        resize bool: Make it fit the area ? (proportions are respected)
        rotation int: an integer rotation angle
        background_color : an RGBA background color
    """
    def __init__(self, image, centered=False, resize=True, 
                 rotation=0, background_color=(0, 0, 0, 0), **kwargs):
        super().__init__(**kwargs)
        self.image_input = image
        self.resize = resize
        self.centered = centered
        self.rotation = rotation
        self.background_color = background_color
    
    def generator_img(self, area=None):
        if area:
            self.area = area
        (x, y), (w, h) = self.area
        if isinstance(self.image_input, str):
            pil_img = Image.open(self.image_input)
        else:
            pil_img = self.image_input
        # Rotate if required
        if self.rotation != 0:
            pil_img = pil_img.rotate(self.rotation,
                                         fillcolor=self.background_color)
        # Resize if required
        if self.resize:
            r = min(w/pil_img.width, h/pil_img.height)
            size = (int(pil_img.width*r), int(pil_img.height*r))
            pil_img = pil_img.resize(size)
        # Center if required
        if self.centered:
            img = Image.new("RGBA", (w, h), color=self.background_color)
            x = int(0.5*w-0.5*pil_img.width)
            y = int(0.5*h-0.5*pil_img.height)
            img.paste(pil_img, (x, y))
            pil_img = img
        # Then return
        self.image = pil_img.crop((0, 0, w, h))
        return pil_img
        