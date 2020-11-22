import os

PATH_TO_PSSM = os.path.dirname(os.path.abspath(__file__))
PATH_TO_FONTS = os.path.join(PATH_TO_PSSM, "fonts")


DEFAULT = {
    'text':{
        'font' : os.path.join(PATH_TO_FONTS, "Merriweather-Regular.ttf"), 
        'color' : (0, 0, 0, 255),
        'size' : 18, 
        'x' : 'top', 
        'y' : 'left'
    },
    'Rectangle' : {
        'sides' : 'tblr',
        'background_color': (255,255,255,255),
        'sides_color' : (0,0,0,255),
        'sides_width' : 1
    },
    'Layout' : {
        'background_color': (255,255,255,255),
    }
}


DEMO = {
    'text':{
        'font' : os.path.join(PATH_TO_FONTS, "Merriweather-Regular.ttf"), 
        'color' : (0, 0, 0, 255),
        'size' : 16, 
        'x' : 'center', 
        'y' : 'center'
    },
    'Rectangle' : {
        'sides' : 'tb',
        'background_color': (120,120,120,255),
        'sides_color' : (0,0,0,255),
        'sides_width' : {'t':2, 'b':1}
    },
    'Layout' : {
        'background_color': (255,255,255,255),
    }
}