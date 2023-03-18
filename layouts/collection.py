from PIL import Image
from PSSM.elements import Element, Margin
from PSSM.utils import coords_in_area

class Collection(Element):
    """
    A collection is basically a list of Elements.
    It can be either a row (axis="x", default option) or a column (axis="y")
    """
    def __init__(self, coll=[], area=None, axis="x", **kwargs):
        super().__init__()
        self.background_color = None
        for param in kwargs:
            setattr(self, param, kwargs[param])
        self.coll = coll
        self.list_img = []
        self.list_area = []
        self.axis = axis
        self.area = area
        self.onclick = self._dispatch_click
        if self.axis not in ('x', 'y'):
            raise ValueError("Incompatible axis type : {}".format(axis))

    def generator_img(self, layout_only=False):
        """
        Builds one img out of all the Elements it is being given
        """
        self._convert_coll()
        self._make_list_area()
        self._make_list_img()
        [(x, y), (w, h)] = self.area
        self.image = Image.new("RGBA", (w, h), color=self.background_color)
        for i in range(len(self.list_area)):
            elt_x, elt_y = self.list_area[i][0]
            relative_x = elt_x - x
            relative_y = elt_y - y
            elt_img = self.list_img[i]
            if elt_img is not None:
                self.image.paste(self.list_img[i], (relative_x, relative_y))
        return self.image

    def _convert_coll(self):
        """
        Converts any str or int shorthands to proper elements.
        """
        if len(self.coll) == 0:
            # Empty row, let's create a Margin elt
            self.coll = ["?"]
        # Then we can go
        for i in range(len(self.coll)):
            elt = self.coll[i]
            if isinstance(elt, str) or isinstance(elt, int):
                # This is an empty element, which serves as margin.
                param = "width" if self.axis == "x" else "height"
                value = elt
                element = Margin()
                setattr(element, param, value)
                self.coll[i] = element
            # Let's add parse a few elt-variables
            self.coll[i].parent_layouts += self.parent_layouts
            self.coll[i].parent_layouts += [self]
            self.coll[i].parent_stack = self.parent_stack
            self.coll[i]._parse_styles()

    def _make_list_img(self, layout_only=False):
        if not self.list_area:
            message = "[PSSM Layout] Error, list_area has to be defined first"
            raise NameError(message)
        for i in range(len(self.coll)):
            elt = self.coll[i]
            elt_area = self.list_area[i]
            if not elt.is_layout and layout_only:
                elt_img = elt.image
            else:
                elt_img = elt.generator(area=elt_area, skip_styles=True)
            self.list_img.append(elt_img)
        return self.list_img

    def _make_list_area(self):
        """
        Builds the list of areas.
        """
        # STATUS:  TODO
        [(x, y), (w,h)] = self.area
        x0, y0 = x, y
        total_dim, total_qm = self._get_remaining_dim()
        if self.axis ==  "x":
            remaining_dim = w - total_dim
            for elt in self.coll:
                # TODO: handle when the users wants an element to be less high than the row's
                # for now it has the row's height
                elt_height = h
                # Retrieve the width
                elt_width = self._get_elt_dim(elt.width, remaining_dim, total_qm) 
                elt.area = [(x0, y0), (elt_width-1, elt_height-1)]
                x0 += elt_width
                self.list_area.append(elt.area)
        else:
            remaining_dim = h - total_dim
            for elt in self.coll:
                # TODO: handle when the users wants an element to be less wide than the row's
                # for now it has the row's width
                elt_width = w
                # Retrieve the height
                elt_height = self._get_elt_dim(elt.height, remaining_dim, total_qm)
                elt.area = [(x0, y0), (elt_width-1, elt_height-1)]
                y0 += elt_height
                self.list_area.append(elt.area)
    
    def _get_elt_dim(self, elt_width, remaining_dim, total_qm):
        converted_width = self._convert_dimension(elt_width)
        if isinstance(converted_width, int):
            # we can go
            return converted_width
        else:
            # There is still a question mark to parse
            dim = converted_width.replace("?", str(remaining_dim))
            dim += "/{}".format(total_qm)
            try:
                true_elt_width = int(eval(dim))
            except ValueError:
                raise ValueError("An invalid dimension was given \
                as element width : {}".format(converted_width))
            return true_elt_width

    def _get_remaining_dim(self):
        """
        Returns the total width + the total weight of "?" based dimensions
        """
        total_dim = 0
        total_qm = 0
        for elt in self.coll:
            dim = elt.width if self.axis == "x" else elt.height
            converted_dim = elt._convert_dimension(dim)
            if isinstance(converted_dim, int):
                total_dim += converted_dim
            elif isinstance(converted_dim, str) and "?" in converted_dim:
                dim = converted_dim.replace("?", "1")
                qm_weight = int(eval(dim))
                total_qm += qm_weight
        return (total_dim, total_qm)

    def _dispatch_click(self, click_x, click_y):
        """
        Dispatches the click.
        Linear search through the elements
        """
        ## TODO : implement dichotomy search
        for elt in self.coll:
            if coords_in_area(elt.area, click_x, click_y):
                self.parent_stack._click_handler_to_elt(elt, click_x, click_y)
                return True
        return False
