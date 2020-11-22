from PIL import Image
from .element import Element
from .utils import coords_in_area
from PSSM.elements import Margin

class Layout(Element):
    """
    A layout is a quite general kind of Element :
    If must be given the working area, and a layout, and will generate every
    element of the layout

    Args:
        layout (list): The given layout (see example below). It is basically a
        list of rows. Each row is a list containing : the height of the row,
        then as many tuples as you want, each tuple being a
        (pssm.Element, width) instance
        background_color
        area
        ... all other arguments from the pssm.Element class

    Example of usage:
        See [examples](examples/index.html)
    """
    def __init__(self, layout, area=None, background_color=None, **kwargs):
        super().__init__(**kwargs)
        self.area = area
        self.layout = layout
        self.is_valid = self._test_layout()
        self.background_color = background_color
        self.matrix_area = None
        self.matrix_img = None
        self.is_layout = True
        self.type = "Layout"
        self.onclick = self._dispatch_click
        for param in kwargs:
            setattr(self, param, kwargs[param])

    def _test_layout(self):
        """
        Tests the structure of the Layout
        """
        assert type(self.layout) == list
        for row in self.layout:
            assert type(row) == tuple
            assert len(row) == 2
            assert type(row[0]) in (int, str)
            assert type(row[1]) == list
            for elt in row[1]:
                assert (isinstance(elt, int) or isinstance(elt, str) or isinstance(elt, Element))
        return True

    def generator_img(self, area=None, layout_only=False):
        """
        Builds one img out of all the Elements it is being given
        """
        if area is not None:
            self.area = area
        self._convert_layout()
        self.make_matrix_area()
        self.make_matrix_img(layout_only=layout_only)
        [(x, y), (w, h)] = self.area
        placeholder = Image.new("RGBA", (w, h), color=self.background_color)
        for i in range(len(self.matrix_area)):
            for j in range(len(self.matrix_area[i])):
                elt_x, elt_y = self.matrix_area[i][j][0]
                relative_x = elt_x - x
                relative_y = elt_y - y
                elt_img = self.matrix_img[i][j]
                if elt_img is not None:
                    pos = (relative_x, relative_y)
                    placeholder.paste(self.matrix_img[i][j], pos)
        self.image = placeholder
        return self.image

    def _convert_layout(self):
        """
        - Converts strings and integers element to proper margins
        - Tells each element what is its parent stack and layout
        - Parses the width of each individual element
        """
        for i in range(len(self.layout)):
            for j in range(len(self.layout[i][1])):
                elt = self.layout[i][1][j]
                # Test if a margin
                if isinstance(elt, int) or isinstance(elt, str):
                    # That's a margin, let's create a margin
                    self.layout[i][1][j] = Margin(width=elt)
                # Let's add parse a few elt-variables
                self.layout[i][1][j].parent_layouts += self.parent_layouts
                self.layout[i][1][j].parent_layouts += [self]
                self.layout[i][1][j].parent_stack = self.parent_stack
                # Then parse styles
                self.layout[i][1][j]._parse_styles(list_styles=['width'])
                    
    def make_matrix_img(self, layout_only=False):
        matrix = []
        if not self.matrix_area:
            message = "[PSSM Layout] Error, matrix_area has to be defined first"
            raise NameError(message)
        for i in range(len(self.layout)):
            row = []
            for j in range(len(self.layout[i][1])):
                elt = self.layout[i][1][j]
                elt_area = self.matrix_area[i][j]
                if not elt.is_layout and layout_only:
                    elt_img = elt.image
                else:
                    elt_img = elt.generator(area=elt_area)
                row.append(elt_img)
            matrix.append(row)
        self.matrix_img = matrix

    def make_matrix_area(self):
        matrix = []
        x, y = self.area[:][0]
        x0, y0 = x, y
        for i in range(len(self.layout)):
            row = self.layout[i]
            row_areas = []
            row_height = self._get_row_height(row[0])
            for j in range(len(row[1])):
                elt = self.layout[i][1][j]
                # Then retrieve the width
                elt_width = self._get_elt_width(elt.width, i)
                element_area = [(x0, y0), (elt_width, row_height)]
                self.layout[i][1][j].area = element_area
                x0 += elt_width
                row_areas.append(element_area)
            y0 += row_height
            x0 = x
            matrix.append(row_areas)
        self.matrix_area = matrix

    def _get_row_height(self, height):
        row_height = self._convert_dimension(height)
        if isinstance(row_height, int):
            true_row_height = row_height
        else:
            remaining_height = self._get_remaining_height()
            dim = row_height.replace("?", str(remaining_height))
            try:
                true_row_height = int(eval(dim))
            except ValueError:
                raise ValueError("An invalid dimension was given \
                    as row height : {}".format(row_height))
        return true_row_height
    
    def _get_elt_width(self, width, row_index):
        converted_width = self._convert_dimension(width)
        if isinstance(converted_width, int):
            true_elt_width = converted_width
        else:
            remaining_width = self._get_remaining_width(row_index)
            dim = converted_width.replace("?", str(remaining_width))
            try:
                true_elt_width = int(eval(dim))
            except ValueError:
                raise ValueError("An invalid dimension was given \
                as element width : {}".format(converted_width))
        return true_elt_width

    def _get_remaining_height(self):
        # First, get the list of the rows heights
        rows = []
        for row in self.layout:
            rows.append(row[0])
        total_qm_weight = 0     # total weight of Question Marks
        total_height = 0        
        for dimension in rows:
            converted_dimension = self._convert_dimension(dimension)
            if isinstance(converted_dimension, int):
                total_height += converted_dimension
            else:
                weight = converted_dimension.replace("?", "1")
                try:    
                    weight = eval(weight)
                except ValueError:
                    message = "Invalid dimension given : {}".format(dimension)
                    raise ValueError(message)
                total_qm_weight += weight
        layout_height = self.area[1][1]
        return int((layout_height - total_height)/total_qm_weight)

    def _get_remaining_width(self, row_index):
        # TODO : fix
        cols = []
        for elt in self.layout[row_index][1]:
            cols.append(elt.width)
        total_width = 0
        total_qm_weight = 0
        for dimension in cols:
            converted_dimension = self._convert_dimension(dimension)
            if isinstance(converted_dimension, int):
                total_width += converted_dimension
            else:
                weight = converted_dimension.replace("?", "1")
                try:
                    weight = eval(weight)
                except ValueError:
                    message = "Invalid dimension given : {}".format(dimension)
                    raise ValueError(message)
                total_qm_weight += weight
        layout_width = self.area[1][0]
        return int((layout_width - total_width)/total_qm_weight)

    def _dispatch_click(self, click_x, click_y):
        """
        Finds the element on which the user clicked
        Linear search throuh both the rows and the columns
        """
        # Linear search though the rows
        for i in range(len(self.matrix_area)):
            if len(self.matrix_area[i]) == 0:
                # That's a fake row (a margin row)
                continue
            first_row_elt = self.matrix_area[i][0]
            last_row_elt = self.matrix_area[i][-1]
            x = first_row_elt[0][0]
            y = first_row_elt[0][1]
            w = last_row_elt[0][0] + last_row_elt[1][0] - first_row_elt[0][0]
            h = last_row_elt[0][1] + last_row_elt[1][1] - first_row_elt[0][1]
            if coords_in_area([(x, y), (w, h)], click_x, click_y):
                # CLick was in that row
                for j in range(len(self.matrix_area[i])):
                    # Linear search through the columns
                    if coords_in_area(self.matrix_area[i][j], click_x, click_y):
                        # Click was on that element
                        elt = self.layout[i][1][j]
                        self.parent_stack._click_handler_to_elt(elt, click_x, click_y)
                        return True
        return False
