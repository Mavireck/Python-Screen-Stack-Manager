#!/usr/bin/env python
import os
import pssm
# Load Pillow
from PIL import Image, ImageDraw, ImageFont
from copy import deepcopy

path_to_pssm = os.path.dirname(os.path.abspath(__file__))
white = 255
black = 0
gray = 128
light_gray = 230

def rectangle(x,y,w,h,fill=255,outline=50):
    """
    Draw a simple rectange
    """
    img = Image.new('L', (w+1,h+1), color=white)
    rect = ImageDraw.Draw(img, 'L')
    rect.rectangle([(0,0),(w,h)],fill=fill,outline=outline)
    return deepcopy(pssm.pillowImgToScreenObject(img,x,y))

def roundedRectangle(x,y,w,h, radius=20, fill=255,outline=50):
    """
    Draw a rounded rectangle
    """
    rectangle = Image.new('L', (w,h), white)
    draw = ImageDraw.Draw(rectangle)
    draw.rectangle([(0,0),(w,h)],fill=fill,outline=outline)
    draw.line([(radius,h-1),(w-radius,h-1)],fill=outline,width=1)
    draw.line([(w-1,radius),(w-1,h-radius)],fill=outline,width=1)
    corner = roundedCorner(radius, fill,outline)
    rectangle.paste(corner, (0, 0))
    rectangle.paste(corner.rotate(90), (0, h - radius)) # Rotate the corner and paste it
    rectangle.paste(corner.rotate(180), (w - radius, h - radius))
    rectangle.paste(corner.rotate(270), (w - radius, 0))
    return deepcopy(pssm.pillowImgToScreenObject(rectangle,x,y))

def button(x,y,w,h,text,font,fill=255,outline=50,text_fill=0):
    """
    Draw a simple button with a text
    """
    #TODO : FIX IT
    img = Image.new('L', (w+1,h+1), color=white)
    rect = ImageDraw.Draw(img, 'L')
    rect.rectangle([(0,0),(w,h)],fill=fill,outline=outline)
    btn = add_text(img,text,font,xPosition="center",yPosition="center",fill=text_fill)
    return deepcopy(pssm.pillowImgToScreenObject(btn,x,y))

def icon(file,x,y,icon_size=50):
    """
    Returns a ScreenObject with the icon corresponding to the path you give as argument.
    If you pass "back", "delete" or another known image, it will fetch the integrated icons
    """
    path_to_file = tools_parseKnownImageFile(file)
    iconImg = Image.open(path_to_file).convert("L").resize((icon_size,icon_size))
    return deepcopy(pssm.pillowImgToScreenObject(iconImg,x,y))

def add_text(obj,text,font,xPosition="left",yPosition="top",fill=0):
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
    return deepcopy(pssm.pillowImgToScreenObject(img,obj.x,obj.y))

def add_centeredText(obj,text,font,fill=0):
    """
    Shorthand to add_text([...] xPosition = Center, yPosition = Center)
    """
    return deepcopy(add_text(obj,text,font,xPosition="center",yPosition="center",fill=fill))

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