#!/usr/bin/env python
import os
import pssm
import json

path_to_pssmOSK = os.path.dirname(os.path.abspath(__file__))
default_keymap_path_STANDARD = os.path.join(path_to_pssmOSK,"config", "default-keymap-en_us.json")
default_keymap_path_CAPS 	 = os.path.join(path_to_pssmOSK,"config", "default-keymap-en_us_CAPS.json")
default_keymap_path_ALT      = os.path.join(path_to_pssmOSK,"config", "default-keymap-en_us_ALT.json")
default_keymap_path = {
	'standard' : default_keymap_path_STANDARD,
	'caps' : default_keymap_path_CAPS,
	'alt' : default_keymap_path_ALT
}

# Constants:
KTstandardChar   = 0
KTcarriageReturn = 1
KTbackspace      = 2
KTdelete         = 3
KTcapsLock       = 4
KTcontrol        = 5
KTalt            = 6

class OSK(pssm.Layout):
	"""
	A PSSM Layout element which builds an on-screen keyboard
	: keymapPath (str) : a path to a PSSMOSK keymap (like the one included)
	: onkeyPress (fct) : A callback function. Will be given keyType and keyChar as argument
	"""
	def __init__(self,keymapPath=default_keymap_path,onkeyPress = None, area=None,**kwargs):
		self.keymapPaths = keymapPath
		self.keymap = {'standard':None,'caps':None,'alt':None}
		self.keymap_layouts = {'standard':None,'caps':None,'alt':None}
		self.keymap_imgs = {'standard':None,'caps':None,'alt':None}
		with open(self.keymapPaths['standard']) as json_file:
			self.keymap['standard'] = json.load(json_file)
		with open(self.keymapPaths['caps']) as json_file:
			self.keymap['caps'] = json.load(json_file)
		with open(self.keymapPaths['alt']) as json_file:
			self.keymap['alt'] = json.load(json_file)
		self.lang     	= self.keymap['standard']["lang"]
		self.onkeyPress	= onkeyPress
		for param in kwargs:
			setattr(self, param, kwargs[param])
		self.view = 'standard'
		self.keymap_layouts['standard'] = self.build_layout(self.keymap['standard'])
		self.keymap_layouts['caps'] = self.build_layout(self.keymap['caps'])
		self.keymap_layouts['alt'] = self.build_layout(self.keymap['alt'])
		# Initialize layout with standard view
		self.layout = self.keymap_layouts['standard']
		super().__init__(self.layout)
		self.area     	= area

	def generator(self, area=None, forceRegenerate = False):
		"""
		This generator is a bit special : we don't want it to regenerate everything
		everytime we change view. So we will generate all the views at once the first time.
		Then, unless asked to, we will only return the appropriate image
		"""
		if forceRegenerate or (not self.keymap_imgs['standard']) or (not self.keymap_imgs['caps']) or (not self.keymap_imgs['alt']):
			print("[PSSM OSK] Regenration started")
			# Let's create all the Images
			# Standard view is created last, because it is the one which is to be displayed
			self.layout = self.keymap_layouts['caps']
			self.keymap_imgs['caps'] = super(OSK, self).generator(area=area)
			self.layout = self.keymap_layouts['alt']
			self.keymap_imgs['alt'] = super(OSK, self).generator(area=area)
			self.layout = self.keymap_layouts['standard']
			self.keymap_imgs['standard'] = super(OSK, self).generator(area=area)
		self.imgData = self.keymap_imgs[self.view]
		return self.keymap_imgs[self.view]

	def build_layout(self,keymap):
		oskLayout = []
		spacing = keymap["spacing"]
		for row in keymap["rows"]:
			buttonRow = ["?",(None,spacing)]
			for key in row:
				label = self.getKeyLabel(key)
				color_condition = key["isPadding"] or (key["keyType"] != KTstandardChar)
				background_color = "gray14" if color_condition else "white"
				buttonElt = pssm.Button(
					text				= label,
					background_color	= background_color,
					onclickInside		= self.handleKeyPress,
					user_data 			= key,
					wrap_textOverflow 	= False,
					invertOnClick		= True
				)
				key_width = key["keyWidth"]
				buttonRow.append((buttonElt,key_width))
				buttonRow.append((None,spacing))
			oskLayout.append(buttonRow)
			oskLayout.append([spacing])
		return oskLayout

	def handleKeyPress(self,elt,coords):
		keyType = elt.user_data["keyType"]
		keyChar = elt.user_data["char"]
		if keyType == KTcapsLock:
			## In this particular case, we can assume the keyboard will always be on top
			## Therefore, no need to print everything, let's just print the keyboard
			self.view = 'caps' if self.view != 'caps' else 'standard'
			self.layout = self.keymap_layouts[self.view]
			self.createAreaMatrix()
			self.update(
			    newAttributes={},
			    skipGeneration = True
			)
			self.parentStackManager.simplePrintElt(self)
		elif keyType == KTalt:
			## In this particular case, we can assume the keyboard will always be on top
			## Therefore, no need to print everything, let's just print the keyboard
			self.view = 'alt' if self.view != 'alt' else 'standard'
			self.layout = self.keymap_layouts[self.view]
			self.createAreaMatrix()
			self.update(
			    newAttributes={},
			    skipGeneration = True
			)
			self.parentStackManager.simplePrintElt(self)
		if self.onkeyPress:
			self.onkeyPress(keyType,keyChar)


	def getKeyLabel(self,key):
		kt = key["keyType"]
		if kt == KTstandardChar:
			return key["char"]
		elif kt == KTalt:
			return "ALT"
		elif kt == KTbackspace:
			return "BACK"
		elif kt == KTcapsLock:
			return "CAPS"
		elif kt == KTcarriageReturn:
			return "RET"
		elif kt == KTcontrol:
			return "CTRL"
		elif kt == KTdelete:
			return "DEL"
		return ""
