#!/usr/bin/env python
import os
import pssm
# Load Pillow
from PIL import Image, ImageDraw, ImageFont
from copy import deepcopy

path_to_pssm = os.path.dirname(os.path.abspath(__file__))
white = 255
light_gray = 230
gray = 128
black = 0

Merri_regular = os.path.join("fonts", "Merriweather-Regular.ttf")
Merri_bold = os.path.join("fonts", "Merriweather-Bold.ttf")
standard_font_size = 15

def returnFalse(*args):
	return False

def OLD_add_text(obj,text,font=Merri_regular,xPosition="left",yPosition="top",fill=0):
    """
    Adds text to an existing pillow object

    Valid inputs for xPosition and yPosition are :
    left,center,right or top,center,bottom or an absolute value in pixel
    """
    img = Image.frombytes('L',(obj.w,obj.h),obj.imgData)
    imgDraw = ImageDraw.Draw(img, 'L')
    text_w,text_h = imgDraw.textsize(text, font=font)
    x = tools_convertXArgsToPX(xPosition,obj.w,text_w)
    y = tools_convertYArgsToPX(yPosition,obj.h,text_h)
    imgDraw.text((x,y),text,font=font,fill=fill)
    return deepcopy(pssm.pillowImgToElement(img,obj.x,obj.y))

def OLD_add_centeredText(obj,text,font=Merri_regular,fill=0):
    """
    Shorthand to add_text([...] xPosition = Center, yPosition = Center)
    """
    return deepcopy(add_text(obj,text,font,xPosition="center",yPosition="center",fill=fill))

############################# - Layout Elements - ##############################
class Layout(pssm.Element):
    """
    A layout is a quite general kind of Element :
    If must be given the working area, and a layout, and will generate every element of the layout
    """
    def __init__(self,layout,area=None,onclickInside=returnFalse,isInverted=False,data=[],tags=set()):
        super().__init__(area=area,onclickInside=onclickInside,isInverted=isInverted,data=data,tags=tags)
        self.layout      = layout
        self.areaMatrix = None
        self.imgMatrix  = None
        self.borders    = None
        self.subclass = "Layout"

    def generator(self,min_height=-1,min_width=-1,max_height=-1,max_width=-1,area=None):
        """
        Builds one img out of all the Elements it is being given
        """
        if area != None:
            self.area = area
        self.createAreaMatrix(min_height=min_height,min_width=min_width,max_height=max_height,max_width=max_width)
        self.createImgMatrix()
        [(x,y),(w,h)] = self.area
        placeholder = Image.new('L', (w,h), color=255)
        for i in range(len(self.areaMatrix)):
            for j in range(len(self.areaMatrix[i])):
                [(elt_x,elt_y),(elt_w,elt_h)] = self.areaMatrix[i][j]
                relative_x = elt_x - x
                relative_y = elt_y - y
                elt_img = self.imgMatrix[i][j]
                if elt_img != None:
                    placeholder.paste(self.imgMatrix[i][j],(relative_x,relative_y))
        self.imgData = placeholder
        return self.imgData

    def createImgMatrix(self):
        matrix = []
        if not self.areaMatrix:
            print("Error, areaMatrix has to be defined first")
            return None
        for i in range(len(self.layout)):
            row = []
            for j in range(1,len(self.layout[i])):
                myElement,_   = self.layout[i][j]
                if myElement == None:
                    myElement_area  = self.areaMatrix[i][j-1]
                    myElement_img   = None
                else:
                    myElement_area  = self.areaMatrix[i][j-1]
                    myElement_img   = myElement.generator(area=myElement_area)
                row.append(myElement_img)
            matrix.append(row)
        self.imgMatrix = matrix

    def createAreaMatrix(self,min_height=-1,min_width=-1,max_height=-1,max_width=-1):
        # TODO : must honor question_mark dimensions
        matrix = []
        n_rows = len(self.layout)
        [(x,y),(w,h)] = self.area[:]
        x0,y0=x,y
        for i in range(len(self.layout)):     # Lets loop through the rows
            row = self.layout[i]
            row_cols = []           # All the columns of this particular row
            row_height = row[0]
            if row_height == "?":
                row_height = self.calculate_remainingHeight()
            n_cols = len(row)     # Do not forget that the first item of each row is an int indicating the row height
            for j in range(1,n_cols):
                (element,element_width) = row[j]
                if element_width == "?":
                    element_width = self.calculate_remainingWidth(i)
                    self.layout[i][j] = (self.layout[i][j][0], element_width)
                element_area = [(x0,y0),(element_width,row_height)]
                x0 += element_width +1
                row_cols.append(element_area)
            y0 += row_height +1
            x0 = x
            matrix.append(row_cols)
        self.areaMatrix = matrix

    def calculate_remainingHeight(self):
        rows = self.extract_rowsHeight()
        number_questionMarks = rows.count("?")
        total_height = 0
        for row in rows:
            if row != "?":
                total_height += row
        layout_height = self.area[1][1]
        return int((layout_height - total_height)/number_questionMarks)

    def calculate_remainingWidth(self,rowIndex):
        cols = self.extract_colsWidth(rowIndex)
        number_questionMarks = cols.count("?")
        total_width = 0
        for col in cols:
            if col != "?":
                total_width += col
        layout_width = self.area[1][0]
        return int((layout_width - total_width)/number_questionMarks)

    def extract_rowsHeight(self):
        rows = []
        for row in self.layout:
            rows.append(row[0])
        return rows

    def extract_colsWidth(self,rowIndex):
        cols = []
        for col in self.layout[rowIndex]:
            if isinstance(col,tuple):
                cols.append(col[1])
        return cols

    def dispatchClick(self,coords):
        # TODO : use dichotomy search instead of linear search with extract_rowsHeight and extract_colsWidth
        click_x,click_y = coords
        [(x,y),(w,h)] = self.area[:]
        is_found = False
        for i in range(len(self.areaMatrix)):
            for j in range(len(self.areaMatrix[i])):
                if pssm.coordsInArea(click_x,click_y,self.areaMatrix[i][j]):
                    row,col=i,j
                    is_found = True
                    break
            if is_found:
                break
        if is_found:
            element,element_width = self.layout[row][col+1]
            if element != None and element.onclickInside != None:
                if element.subclass == "Layout":
                    if element.onclickInside != None:
                        element.onclickInside(element,coords)
                    element.dispatchClick(coords)
                else:
                    element.onclickInside(element,coords)
            return True
        else:
            return False

class ButtonList(Layout):
    def __init__(self,buttons, margins=[0,0,0,0],spacing=0,**kwargs):
        """
        Generates a Layout with one item per row, all the same type (buttons) and same height and width
        :button : a [{"text":"my text","onclickInside":onclickInside},someOtherDict,someOtherDict] array
        :borders : a [top,bottom,left,right]
        """
        self.buttons = buttons
        self.margins = margins
        self.spacing = spacing
        layout = self.build_layoutFromButtons()
        super().__init__(layout)
        for param in kwargs:
            setattr(self, param, kwargs[param])

    def build_layoutFromButtons(self):
        #TODO : must honor min_width,max_width etc
        [top,bottom,left,right] = self.margins
        buttonLayout = [[top-self.spacing]]
        for button in self.buttons:
            buttonElt = Button(text=button['text'])
            for param in button:
                setattr(buttonElt, param, button[param])
            row_height = "?"
            buttonLayout.append([self.spacing])
            row = [row_height,(None,left),(buttonElt,"?"),(None,right)]
            buttonLayout.append(row)
        buttonLayout.append([bottom])
        return buttonLayout



############################# - Simple Elements - ##############################
class Rectangle(pssm.Element):
    def __init__(self,background_color=255,outline=50):
        super().__init__()
        self.background_color = background_color
        self.outline = outline

    def generator(self,area):
        [(x,y),(w,h)] = area
        self.area = area
        img = Image.new('L', (w+1,h+1), color=white)
        rect = ImageDraw.Draw(img, 'L')
        rect.rectangle([(0,0),(w,h)],fill=self.background_color,outline=self.outline)
        self.imgData = img
        return self.imgData

class RectangleRounded(pssm.Element):
    def __init__(self,radius=20,background_color=255,outline=0):
        super().__init__()
        self.radius = radius
        self.background_color = background_color
        self.outline = outline

    def generator(self,area):
        [(x,y),(w,h)] = area
        self.area = area
        rectangle = Image.new('L', (w,h), white)
        draw = ImageDraw.Draw(rectangle)
        draw.rectangle([(0,0),(w,h)],fill=self.background_color,outline=self.outline)
        draw.line([(self.radius,h-1),(w-self.radius,h-1)],fill=self.outline,width=1)
        draw.line([(w-1,self.radius),(w-1,h-self.radius)],fill=self.outline,width=1)
        corner = roundedCorner(self.radius, self.background_color,self.outline)
        rectangle.paste(corner, (0, 0))
        rectangle.paste(corner.rotate(90), (0, h - self.radius)) # Rotate the corner and paste it
        rectangle.paste(corner.rotate(180), (w - self.radius, h - self.radius))
        rectangle.paste(corner.rotate(270), (w - self.radius, 0))
        self.imgData = rectangle
        return self.imgData

class Button(pssm.Element):
    def __init__(
            self,
            text,
            font=Merri_regular,
            font_size=standard_font_size,
            background_color=255,
            outline=0,
            radius=0,
            text_color=0,
            **kwargs
        ):
        super().__init__()
        self.background_color   = background_color
        self.outline    = outline
        self.text       = text
        self.font       = font
        self.font_size  = font_size
        self.radius     = radius
        self.text_color = text_color
        for param in kwargs:
            setattr(self, param, kwargs[param])

    def generator(self,area=None):
        loaded_font = ImageFont.truetype(self.font, self.font_size)
        if area==None:
            area = self.area
        [(x,y),(w,h)] = area
        self.area = area
        if self.radius>0:
            rect = RectangleRounded(radius=self.radius,background_color=self.background_color,outline=self.outline)
        else:
            rect = Rectangle(background_color=self.background_color,outline=self.outline)
        rect_img = rect.generator(self.area)
        imgDraw = ImageDraw.Draw(rect_img, 'L')
        text_w,text_h = imgDraw.textsize(self.text, font=loaded_font)
        x = tools_convertXArgsToPX("center",w,text_w)
        y = tools_convertYArgsToPX("center",h,text_h)
        imgDraw.text((x,y),self.text,font=loaded_font,fill=self.text_color)
        self.imgData = rect_img
        return self.imgData

class Icon(pssm.Element):
    def __init__(self,file):
        super().__init__()
        self.file = file

    def generator(self,area):
        """
        Returns a  PIL image with the icon corresponding to the path you give as argument.
        If you pass "back", "delete" or another known image, it will fetch the integrated icons
        """
        path_to_file = tools_parseKnownImageFile(file)
        iconImg = Image.open(path_to_file).convert("L").resize((icon_size,icon_size))
        self.imgData = iconImg
        return iconImg


############################# - TOOLS - ########################################
def OLD_tools_createTable(area,rows,cols,borders=[(0,0),(0,0)],min_height=-1,min_width=-1,max_height=-1,max_width=-1):
    """
    Returns a list of coordinates in order to help create a rows*cols Table
    If any dimension is bigger than the corresponding max_size
    > area : a [(x,y),(w,h)] list
    > rows (int) : number of rows
    > cols (int) : number of columns
    > borders : [(border_left,border_top),(border_right,border_bottom)] - borders around each item
    """
    (x,y),(w,h) = area
    (b_left,b_top),(b_right,b_bottom) = borders
    if max_height<=0:
        max_height=h
    if max_width<=0:
        max_width=w
    calculated_height = int(h/rows - b_top  - b_bottom)
    calculated_width  = int(w/cols - b_left - b_right)
    item_height = min(max_height,max(min_height,calculated_height))
    item_width  = min(max_width, max(min_width, calculated_width ))
    total_item_width = b_left + item_width  + b_right
    total_item_height= b_top  + item_height + b_bottom
    table=[]
    x0=x
    for i in range(cols):
        col=[]
        y0=y
        for j in range(rows):
            item = [
                (x0 + b_left, y0 + b_top ),
                (item_width , item_height)
            ]
            y0 += total_item_height
            col.append(item)
        table.append(col)
        x0 += total_item_width
    return table

def roundedCorner(radius, fill=255,outline=50):
    """
    Draw a round corner
    """
    corner = Image.new('L', (radius, radius), white)
    draw = ImageDraw.Draw(corner)
    draw.pieslice((0, 0, radius * 2, radius * 2), 180, 270, fill=fill,outline=outline)
    return corner

def tools_convertXArgsToPX(xPosition,objw,textw):
    """
    Converts xPosition string arguments to numerical values
    """
    if xPosition == "left":
        x = 0
    elif xPosition == "center":
        x = int(0.5*objw-0.5*textw)
    elif xPosition == "right":
        x = int(objw-textw)
    else:
        try:
            x = int(xPosition)
        except:
            print("[PSSMOL] Invalid input for xPosition")
            return False
    return x

def tools_convertYArgsToPX(yPosition,objh,texth):
    """
    Converts yPosition string arguments to numerical values
    """
    if yPosition == "top":
        y = 0
    elif yPosition == "center":
        y = int(0.5*objh-0.5*texth)
    elif yPosition == "bottom":
        y = int(objh-texth)
    else:
        try:
            y = int(yPosition)
        except:
            print("[PSSMOL] Invalid input for yPosition")
            return False
    return y

def tools_parseKnownImageFile(file):
    if file=="back":
        return path_to_pssm + "/icons/back.png"
    elif file=="delete":
        return path_to_pssm + "/icons/delete.jpg"
    elif file=="frontlight-down":
        return path_to_pssm + "/icons/frontlight-down.jpg"
    elif file=="frontlight-up":
        return path_to_pssm + "/icons/frontlight-up.jpg"
    elif file=="invert":
        return path_to_pssm + "/icons/invert.jpg"
    elif file=="reboot":
        return path_to_pssm + "/icons/reboot.jpg"
    elif file=="save":
        return path_to_pssm + "/icons/save.png"
    elif file=="touch-off":
        return path_to_pssm + "/icons/touch-off.png"
    elif file=="touch-on":
        return path_to_pssm + "/icons/touch-on.png"
    elif file=="wifi-lock":
        return path_to_pssm + "/icons/wifi-lock.jpg"
    elif file=="wifi-on":
        return path_to_pssm + "/icons/wifi-on.jpg"
    elif file=="wifi-off":
        return path_to_pssm + "/icons/wifi-off.jpg"
    else:
        return file
