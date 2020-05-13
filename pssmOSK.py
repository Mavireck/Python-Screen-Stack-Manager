#!/usr/bin/env python
import os
import pssm
import json

path_to_pssmOSK = os.path.dirname(os.path.abspath(__file__))
default_keymap_path = os.path.join(path_to_pssmOSK,"config", "default-keymap-en_us.json")

# Constants:
KTstandardChar   = 0
KTcarriageReturn = 1
KTbackspace      = 2
KTdelete         = 3
KTcapsLock       = 4
KTcontrol        = 5
KTalt            = 6

class OSK(pssm.Layout):
	def __init__(self,keymapPath=default_keymap_path,onkeyPress = None, area=None,**kwargs):
		"""
		A PSSM Layout element which builds an on-screen keyboard
		: keymapPath (str) : a path to a PSSMOSK keymap (like the one included)
		: onkeyPress (fct) : A callback function. Will be given keyType and keyChar as argument
		"""
		self.keymapPath = keymapPath
		with open(self.keymapPath) as json_file:
			self.keymap = json.load(json_file)
        self.keymap   = keymap
        self.lang     = keymap["lang"]
        self.onkeyPress=onkeyPress
        self.build_layout()
        super().__init__(self.layout)
        self.area     = area
        for param in kwargs:
            setattr(self, param, kwargs[param])

    def build_layout(self):
        oskLayout = []
        spacing = self.keymap["spacing"]
        for row in self.keymap["rows"]:
            buttonRow = ["?",(None,spacing)]
            for key in row:
                label = self.getKeyLabel(key)
                background_color = pssm.light_gray if key["isPadding"] else pssm.white
                buttonElt = pssm.Button(text=label,background_color=background_color, onclickInside=self.handleKeyPress, user_data = key, invertOnClick=True)
                key_width = key["keyWidth"]
                buttonRow.append((buttonElt,key_width))
                buttonRow.append((None,spacing))
            oskLayout.append(buttonRow)
            oskLayout.append([spacing])
        self.layout = oskLayout
        return self.layout

    def handleKeyPress(self,elt,coords):
        keyType = elt.user_data["keyType"]
        keyChar = elt.user_data["char"]
        if self.onkeyPress:
            self.onkeyPress(keyType,keyChar)
        else:
            pass

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
