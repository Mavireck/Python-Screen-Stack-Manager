#!/usr/bin/env python
import kssm
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
	return kssm.pillowImgToScreenObject(img,x,y)

def add_centeredText(obj,text,font,fill=0):
	img = Image.frombytes('L',(obj.w,obj.h),obj.imgData)
	imgDraw = ImageDraw.Draw(img, 'L')
	text_w,text_h = imgDraw.textsize(text, font=font)
	imgDraw.text((int(0.5*obj.w-0.5*text_w),int(0.5*obj.h-0.5*text_h)),text,font=font,fill=fill)
	return kssm.pillowImgToScreenObject(img,obj.x,obj.y)

def roundedRectangle(x,y,w,h,radius=10,fill=255,outline=50):
	img = Image.new('L', (w+1,h+1), color=white)
	rect = ImageDraw.Draw(img, 'L')
	rect.rounded_rectangle([(0,0),(w,h)],radius,fill=fill,outline=outline)
	return kssm.pillowImgToScreenObject(img2,x,y)



def rounded_rectangle_pil_helper(self,xy, corner_radius=10, fill=None, outline=None):
	"""
	Stolen from Welchel @ https://stackoverflow.com/questions/7787375/python-imaging-library-pil-drawing-rounded-rectangle-with-gradient/7788322#7788322
	"""
	upper_left_point = xy[0]
	bottom_right_point = xy[1]
	self.rectangle(
		[
			(upper_left_point[0], upper_left_point[1] + corner_radius),
			(bottom_right_point[0], bottom_right_point[1] - corner_radius)
		],
		fill=fill,
		outline=outline
	)
	self.rectangle(
		[
			(upper_left_point[0] + corner_radius, upper_left_point[1]),
			(bottom_right_point[0] - corner_radius, bottom_right_point[1])
		],
		fill=fill,
		outline=outline
	)
	self.pieslice([upper_left_point, (upper_left_point[0] + corner_radius * 2, upper_left_point[1] + corner_radius * 2)],
		180,
		270,
		fill=fill,
		outline=outline
	)
	self.pieslice([(bottom_right_point[0] - corner_radius * 2, bottom_right_point[1] - corner_radius * 2), bottom_right_point],
		0,
		90,
		fill=fill,
		outline=outline
	)
	self.pieslice([(upper_left_point[0], bottom_right_point[1] - corner_radius * 2), (upper_left_point[0] + corner_radius * 2, bottom_right_point[1])],
		90,
		180,
		fill=fill,
		outline=outline
	)
	self.pieslice([(bottom_right_point[0] - corner_radius * 2, upper_left_point[1]), (bottom_right_point[0], upper_left_point[1] + corner_radius * 2)],
		270,
		360,
		fill=fill,
		outline=outline
	)
ImageDraw.rounded_rectangle = rounded_rectangle_pil_helper
