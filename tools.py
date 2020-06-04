import os
from PIL import ImageOps
from copy import deepcopy
import functools
import time

PATH_TO_PSSM = os.path.dirname(os.path.abspath(__file__))

# ######################## - DECORATORS - ####################################
timer_recall = {}

def timer(func):
    global timer_recall
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        val =  func(*args, **kwargs)
        delay = time.time()-start
        fname = func.__name__
        if fname in timer_recall:
            timer_recall[fname].append(delay)
        else:
            timer_recall[fname] = [delay]
        avg = sum(timer_recall[fname])/len(timer_recall[fname])
        print(f"[DEBUG Timer] {fname} took {delay}s. Average {avg}s on {len(timer_recall[fname])} exec.")
        return val
    return wrapper


def debug(func):
    """Print the function signature and return value"""
    @functools.wraps(func)
    def wrapper_debug(*args, **kwargs):
        args_repr = [repr(a) for a in args]                      # 1
        kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]  # 2
        signature = ", ".join(args_repr + kwargs_repr)           # 3
        print(f"Calling {func.__name__}({signature})")
        value = func(*args, **kwargs)
        print(f"{func.__name__!r} returned {value!r}")           # 4
        return value
    return wrapper_debug


# ########################## - OTHERS - ######################################
def returnFalse(*args): return False


def coordsInArea(click_x, click_y, area):
    """
    Returns a boolean indicating if the click was in the given area
    Args:
        click_x (str): The x coordinate of the click
        click_y (str): The y coordinate of the click
        area (list): The area (of shape : [(x, y), (w, h)])
    """
    [(x, y), (w, h)] = area
    if click_x >= x and click_x < x+w and click_y >= y and click_y < y+h:
        return True
    else:
        return False


def insertStr(string, char, pos):
    """ Returns a string with the characther insterted at said position """
    return string[:pos] + char + string[pos:]


def getRectanglesIntersection(area1, area2):
    (x1, y1), (w1, h1) = area1
    (x2, y2), (w2, h2) = area2
    x0a = max(x1, x2)        # Top left
    x0b = min(x1+w1, x2+w2)  # Bottom right
    y0a = max(y1, y2)        # Top left
    y0b = min(y1+h1, y2+h2)  # Bottom right
    w0 = x0b-x0a
    h0 = y0b-y0a
    if w0 > 0 and h0 > 0:
        return [(x0a, y0a), (w0, h0)]
    else:
        return None


def getPartialEltImg(elt, rectIntersection):
    """
    Returns a PIL image of the the interesection of the Element image and
    the rectangle coordinated given as parameter.
    (Honors invertion)
    Args:
        elt (Element): a PSSM Element
        rectIntersection (list): a [(x, y), (w, h)] array
    """
    [(x, y), (w, h)] = elt.area
    [(x1, y1), (w1, h1)] = rectIntersection
    img = deepcopy(elt.imgData)
    # Then, lets crop it:
    left = + x1 - x
    upper = + y1 - y
    right = left + w1
    lower = upper + h1
    print(x,y,w,h)
    print(left,upper,right,lower)
    img_cropped = img.crop(box=(left, upper, right, lower))
    #img = img.crop((rectIntersection[0][0]-obj.x, rectIntersection[0][1]-obj.y, rectIntersection[1][0]-obj.x, rectIntersection[1][1]-obj.y))
    if elt.isInverted:
        return ImageOps.invert(img_cropped)
    else:
        return img_cropped


def tools_convertXArgsToPX(xPosition, objw, textw, myElt=None):
    """
    Converts xPosition string arguments to numerical values
    Accepted inputs: "left", "center", "right", an inteteger value, or "w/2"
    """
    xPosition = xPosition.lower()
    if xPosition == "left":
        x = 0
    elif xPosition == "center":
        x = int(0.5*objw-0.5*textw)
    elif xPosition == "right":
        x = int(objw-textw)
    else:
        converted = myElt.convertDimension(xPosition)
        x = int(converted)
    return x


def tools_convertYArgsToPX(yPosition, objh, texth, myElt=None):
    """
    Converts yPosition string arguments to numerical values
    """
    yPosition = yPosition.lower()
    if yPosition == "top":
        y = 0
    elif yPosition == "center":
        y = int(0.5*objh-0.5*texth)
    elif yPosition == "bottom":
        y = int(objh-texth)
    else:
        converted = myElt.convertDimension(yPosition)
        y = int(converted)
    return y


def tools_parseKnownImageFile(file):
    """
    Finds the path to a image file if its argument is one of pssm images.
    """
    files = {
        'back': PATH_TO_PSSM + "/icons/back.png",
        'delete': PATH_TO_PSSM + "/icons/delete.jpg",
        "frontlight-down": PATH_TO_PSSM + "/icons/frontlight-down.jpg",
        "frontlight-up": PATH_TO_PSSM + "/icons/frontlight-up.jpg",
        "invert": PATH_TO_PSSM + "/icons/invert.jpg",
        "reboot": PATH_TO_PSSM + "/icons/reboot.jpg",
        "save": PATH_TO_PSSM + "/icons/save.png",
        "touch-off": PATH_TO_PSSM + "/icons/touch-off.png",
        "touch-on": PATH_TO_PSSM + "/icons/touch-on.png",
        "wifi-lock": PATH_TO_PSSM + "/icons/wifi-lock.jpg",
        "wifi-on": PATH_TO_PSSM + "/icons/wifi-on.jpg",
        "wifi-off": PATH_TO_PSSM + "/icons/wifi-off.jpg"
    }
    if file in files:
        return files[file]
    else:
        return file


def tools_parseKnownFonts(font):
    """
    Finds the path to a image file if its argument is one of pssm images.
    """
    fonts = {
        'default': PATH_TO_PSSM + "/fonts/Merriweather-Regular.ttf",
        'default-Regular': PATH_TO_PSSM + "/fonts/Merriweather-Regular.ttf",
        'default-Bold': PATH_TO_PSSM + "/fonts/Merriweather-Bold.ttf",
        'Merriweather-Regular': PATH_TO_PSSM
                                + "/fonts/Merriweather-Regular.ttf",
        'Merriweather-Bold': PATH_TO_PSSM + "/fonts/Merriweather-Bold.ttf"
    }
    if font in fonts:
        return fonts[font]
    else:
        return font


colorsL = {'black': 0, 'white': 255}
colorsRGBA = {'black': (0, 0, 0, 0), 'white': (255, 255, 255, 1)}
for i in range(16):
    s = int(i*255/15)
    colorsL['gray' + str(i)] = s
    colorsRGBA['gray' + str(i)] = (s, s, s, 1)


def get_Color(color, deviceColorType):
    if isinstance(color, str):
        if deviceColorType == "L":
            if color in colorsL:
                return colorsL[color]
            else:
                print("Invalid color, ", color)
                return color
        elif deviceColorType == "RGBA":
            if color in colorsRGBA:
                return colorsRGBA[color]
            else:
                print("Invalid color, ", color)
                return color
    elif isinstance(color, list) or isinstance(color, tuple):
        if deviceColorType == "RGBA":
            if len(color) == 4:
                return color
            else:
                # That's probably RGB
                if isinstance(color, list):
                    return color + [1]
                else:
                    return color + (1)
        else:
            r, g, b = color[0], color[1], color[2]
            gray = 0.2989 * r + 0.5870 * g + 0.1140 * b
            return gray
