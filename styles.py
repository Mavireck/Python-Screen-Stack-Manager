import os

PATH_TO_PSSM = os.path.dirname(os.path.abspath(__file__))
PATH_TO_FONTS = os.path.join(PATH_TO_PSSM, "fonts")


# This is for what is common between all the elements: 
common = {
    'text_font' : os.path.join(PATH_TO_FONTS, "Merriweather-Regular.ttf"), 
    'text_color' : (0, 0, 0, 255),
    'text_size' : 18, 
    'text_x' : 'left', 
    'text_y' : 'top',
    'width' : '?',
    'height' : '?'
}


DEFAULT = {
    'Collection' : {
        'background_color': (255,255,255,255),
        **common
    },
    'Rectangle' : {
        'sides' : 'tblr',
        'background_color': (255,255,255,255),
        'sides_color' : (0,0,0,255),
        'sides_width' : 1,
        **common
    },
    'Row' : {
        'background_color': (255,255,255,255),
        **common
    },
    'Margin' : {**common},
    'Demo'   : {**common},
    'Static' : {**common},
    'OSKButton':{
        'sides' : 'tblr',
        'background_color': (255,255,255,255),
        'sides_color' : (0,0,0,255),
        'sides_width' : 1,
        'text_size':"H*0.02",
        **common
    },
    'OSK':{
        **common
    }
}


DEMO = {
    'Rectangle' : {
        'sides' : 'tb',
        'background_color': (120,120,120,255),
        'sides_color' : (0,0,0,255),
        'sides_width' : {'t':3, 'b':1},
        'text_x' : 'centered',
        'text_y' : 'centered'
    }
}