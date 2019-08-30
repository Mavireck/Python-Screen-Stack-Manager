#!/usr/bin/env python
import pssm
# Load Pillow
from PIL import Image, ImageDraw, ImageFont

white = 255
black = 0
gray = 128
light_gray = 230

def rectangle(x,y,w,h,fill=255,outline=50):
	img = Image.new('L', (w+1,h+1), color=white)
	rect = ImageDraw.Draw(img, 'L')
	rect.rectangle([(0,0),(w,h)],fill=fill,outline=outline)
	return pssm.pillowImgToScreenObject(img,x,y)

def add_centeredText(obj,text,font,fill=0):
	img = Image.frombytes('L',(obj.w,obj.h),obj.imgData)
	imgDraw = ImageDraw.Draw(img, 'L')
	text_w,text_h = imgDraw.textsize(text, font=font)
	imgDraw.text((int(0.5*obj.w-0.5*text_w),int(0.5*obj.h-0.5*text_h)),text,font=font,fill=fill)
	return pssm.pillowImgToScreenObject(img,obj.x,obj.y)


def roundedCorner(radius, fill=255,outline=50):
    """Draw a round corner"""
    corner = Image.new('L', (radius, radius), white)
    draw = ImageDraw.Draw(corner)
    draw.pieslice((0, 0, radius * 2, radius * 2), 180, 270, fill=fill,outline=outline)
    return corner
 
def roundedRectangle(x,y,w,h, radius=20, fill=255,outline=50):
    """Draw a rounded rectangle"""
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
    return pssm.pillowImgToScreenObject(rectangle,x,y)

