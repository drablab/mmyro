import time, os, sys
import globvars
try: 	 
     import PIL.Image as PyImage	     
except: 	 
     print >> sys.stderr, "WARNING: Image not found; do you need Python Imaging Library?" 	 

import array
import math
import exceptions

import myro.globvars
from copy import copy
from Queue import Queue
import thread
import atexit

class Picture(object):
    def __init__(self, original=None):
        if original is not None:
             self.width = original.width
             self.height = original.height
             self.image = original.image.copy()
             self.filename = original.filename
             self.mode = original.mode
             self.displayScale = original.displayScale
        else:
             self.width = 0
             self.height = 0
             self.image = None
             self.filename = None
             self.mode = None
             self.displayScale = 1
             

    def set(self, width, height, data=None, mode="color", value=255):
        self.width = width
        self.height = height
        self.mode = mode
        if mode.lower() == "color":
            if data == None:
                 if type(value) == int:
                      data = array.array('B', [value] * (height * width * 3))
                 elif len(value) == 3:
                      data = array.array('B', value * (height * width))
            self.image = PyImage.frombuffer("RGB", (self.width, self.height),
                                            data, "raw", "RGB", 0, 1)
        elif mode.lower() == "image": 	 
             self.image = data.copy()
        elif mode.lower() == "jpeg": 	 
             self.image = PyImage.open(data).resize((width,height),PyImage.BILINEAR)
             #self.image = PyImage.open(data)
        else: # "gray", "blob"
            self.image = PyImage.frombuffer("L", (self.width, self.height),
                                            data, 'raw', "L", 0, 1)
        if self.image.mode != "RGBA": # palette
             self.image = self.image.convert("RGBA")
        self.pixels = self.image.load()
        self.palette = self.image.getpalette()
        self.filename = 'Camera Image'
        if self.pixels == None:
            raise AttributeError, "Myro needs at least Python Imaging Library version 1.1.6"
        #self.image = ImageTk.PhotoImage(self.temp, master=_root)
        maxsize = max(self.width, self.height) 
        smallWindowThreshold = 250
        if maxsize < smallWindowThreshold:
             self.displayScale = smallWindowThreshold/maxsize

    def rotate(self, degreesCCwise):
         self.image = self.image.rotate(degreesCCwise)
         self.pixels = self.image.load()
         self.width = self.image.size[0]
         self.height = self.image.size[1]

    def resize(self, x, y):
         self.image = self.image.resize((int(x), int(y)))
         self.pixels = self.image.load()
         self.width = self.image.size[0]
         self.height = self.image.size[1]         

    def scale(self, xfactor=None, yfactor=None):
         if xfactor is None:
              xfactor = 1
         if yfactor is None:
              yfactor = xfactor
         newWidth = int(self.width * xfactor)
         newHeight = int(self.height * yfactor)
         self.resize(newWidth, newHeight)

    def load(self, filename):
        #self.image = tk.PhotoImage(file=filename, master=_root)
        self.image = PyImage.open(filename)
        if self.image.mode != "RGBA": # palette
             self.image = self.image.convert("RGBA")
        self.pixels = self.image.load()
        self.width = self.image.size[0]
        self.height = self.image.size[1]
        self.palette = self.image.getpalette()
        self.filename = filename
        if self.pixels == None:
            raise AttributeError, "Myro needs at least Python Imaging Library version 1.1.6"
    def __repr__(self):
        return "<Picture instance (%d x %d)>" % (self.width, self.height)
    def getPixels(self):
         return (Pixel(x, y, self) for x in range(self.width)
                 for y in range(self.height))
    def getPixel(self, x, y):
        return Pixel( x, y, self)
    def getColor(self, x, y):
        retval = self.pixels[x, y]
        return Color(retval)
    def setColor(self, x, y, newColor):
        self.pixels[x, y] = tuple(newColor.getRGBA())
    def setRGB(self, x, y, rgb):
        self.setColor(x, y, Color(*rgb))
    def getRGB(self, x, y):
        return self.pixels[x, y][:3]
    def getRGBA(self, x, y):
        return self.pixels[x, y]
    def getAlpha(self, x, y):
        return self.pixels[x, y][3]
    def getWidth(self):
         return self.width
    def getHeight(self):
         return self.height

class Pixel(object):
    def __init__(self, x, y, picture):
        self.x = x
        self.y = y
        self.picture = picture
        self.pixels = picture.pixels
        # we might need this, for gifs:
        self.palette = self.picture.image.getpalette()
    def __repr__(self):
        rgba = self.getRGBA()
        return ("<Pixel instance (r=%d, g=%d, b=%d, a=%d) at (%d, %d)>"  
                % (rgba[0],
                   rgba[1],
                   rgba[2],
                   rgba[3],
                   self.x, 
                   self.y))

    def getPixel(self, x, y):
        return Pixel( x, y, self.picture)
    def getColor(self):
        retval = self.pixels[self.x, self.y]
        return Color(retval)
    def setColor(self, newColor):
         self.pixels[self.x, self.y] = tuple(newColor.getRGBA())
    def setRGB(self, rgb):
         self.setColor(Color(*rgb))
    def getRGB(self):
        return self.pixels[self.x, self.y][:3]
    def getRGBA(self):
        return self.pixels[self.x, self.y]
    def getAlpha(self):
        return self.pixels[self.x, self.y][3]
    def setAlpha(self, alpha):
        rgba = self.pixels[self.x, self.y]
        self.pixels[self.x, self.y] = (rgba[0], rgba[1], rgba[2], alpha)
    def getX(self):
         return self.x
    def getY(self):
         return self.y

    def __eq__(self, other):
        o1 = self.getRGBA()
        o2 = other.getRGBA()
        return (o1[0] == o2[0] and 
                o1[1] == o2[1] and 
                o1[2] == o2[2] and
                o1[3] == o2[3])

    def __ne__(self,other):
        return not self.__eq__(other)

    def __sub__(self, other):
        o1 = self.getRGB()
        o2 = other.getRGB()
        return Color(o1[0] - o2[0], o1[1] - o2[1], o1[2] - o2[2])
    def __add__(self, other):
        o1 = self.getRGB()
        o2 = other.getRGB()
        return Color(o1[0] + o2[0], o1[1] + o2[1], o1[2] + o2[2])
    def makeLighter(self):
        r, g, b = self.getRGB()
        rgb = (int(max(min((255 - r) * .35 + r, 255), 0)),
               int(max(min((255 - g) * .35 + g, 255), 0)),
               int(max(min((255 - b) * .35 + b, 255), 0)))
        self.setColor(Color(rgb))
    def makeDarker(self):
        r, g, b = self.getRGB()
        rgb = (int(max(min(r * .65, 255), 0)),
               int(max(min(g * .65, 255), 0)),
               int(max(min(b * .65, 255), 0)))
        self.setColor(Color(rgb))

class Color(object):
    def __init__(self, *rgb):
        """
        Returns a Color object. Takes red, green, blue, and optionally
        a transparency (called alpha). All values are between 0 and 255).
        """
        self.alpha = 255
        if len(rgb) == 1:
	   #Accept a string in the hext fromat made by color_rgb func.
	    if isinstance(rgb[0],str):
               self.rgb = rgb_color(rgb[0])
	    else:
               self.rgb=rgb[0]
        elif len(rgb) == 3:
            self.rgb = rgb
        elif len(rgb) == 4:
            self.rgb = rgb[:-1]
            self.alpha = rgb[-1]
        else:
            raise AttributeError, "invalid arguments to Color(); needs at least 3 integers: red, green, blue (transparency optional)"
        self.rgb = map(lambda v: int(max(min(v,255),0)), self.rgb)
    def __repr__(self):
        return "<Color instance (r=%d, g=%d, b=%d, a=%d)>" % (self.rgb[0],
                                                               self.rgb[1],
                                                               self.rgb[2],
                                                               self.alpha)
    def getColor(self):
        return Color(self.rgb)
    def getAlpha(self):
         return self.alpha
    def setAlpha(self, value):
         self.alpha = value
    def setColor(self, color):
        self.rgb = color.getRGB()
    def setRGB(self, rgb):
        self.rgb = copy(rgb)
    def getRGB(self):
        return self.rgb
    def getRGBA(self):
        return (self.rgb[0], self.rgb[1], self.rgb[2], self.alpha)
    def __eq__(self, other):
        o1 = self.getRGBA()
        o2 = other.getRGBA()
        return (o1[0] == o2[0] and 
                o1[1] == o2[1] and 
                o1[2] == o2[2] and 
                o1[3] == o2[3])

    def __ne__(self, other):
        return not self.__eq__(other)

    def __sub__(self, other):
        o1 = self.getRGB()
        o2 = other.getRGB()
        return Color(o1[0] - o2[0], o1[1] - o2[1], o1[2] - o2[2])
    def __add__(self, other):
        o1 = self.getRGB()
        o2 = other.getRGB()
        return Color(o1[0] + o2[0], o1[1] + o2[1], o1[2] + o2[2])
    def makeLighter(self):
        r, g, b = self.rgb
        self.rgb = (int(max(min((255 - r) * .35 + r, 255), 0)),
                    int(max(min((255 - g) * .35 + g, 255), 0)),
                    int(max(min((255 - b) * .35 + b, 255), 0)))
    def makeDarker(self):
        r, g, b = self.rgb
        self.rgb = (int(max(min(r * .65, 255), 0)),
                    int(max(min(g * .65, 255), 0)),
                    int(max(min(b * .65, 255), 0)))

makeColor = Color
        
def color_rgb(r,g,b):
    """r,g,b are intensities of red, green, and blue in range(256)
    Returns color specifier string for the resulting color"""
    return "#%02x%02x%02x" % (r,g,b)

#Used by the Color object so that it can accept "colors" produced by
# the color_rgb() method <above> so that pixels and object graphics
# can use the same colors.
 
def rgb_color( color ):
   """ Returns (r,g,b), input '#rrggbb' or 'rrggbb' """
   color = color.strip()
   if color[0] == '#':
      color=color[1:]
   if len(color) != 6:
      raise ValueError, "#%s incorrect format use #rrggbb" % color
   r, g, b = color[:2], color[2:4], color[4:]
   r, g, b = [int(n, 16) for n in (r, g, b)]
   return (r, g, b)

black     = Color(  0,   0,   0)
white     = Color(255, 255, 255)
blue      = Color(  0,   0, 255)
red       = Color(255,   0,   0)
green     = Color(  0, 255,   0)
gray      = Color(128, 128, 128)
darkGray  = Color( 64,  64,  64)
lightGray = Color(192, 192, 192)
yellow    = Color(255, 255,   0)
pink      = Color(255, 175, 175)
magenta   = Color(255,   0, 255)
cyan      = Color(  0, 255, 255)


def rgb2hsv(red, green, blue):
     """Converts red, green, and blue to hue, saturation, and brightness """
     return colorsys.rgb_to_hsv(red, green, blue)

def hls2rgb(h, l, s):
     return colorsys.hls_to_rgb(h, l, s)

def hsv2rgb(h, s, v):
     return colorsys.hsv_to_rgb(h, s, v)

def rgb2hls(red, green, blue):
     return colorsys.rgb_to_hls(red, green, blue)

def rgb2yiq(red, green, blue):
     return colorsys.rgb_to_yiq(red, green, blue)

def yiq2rgb(y, i, q):
     return colorsys.yiq_to_rgb(y, i, q)

def yuv2rgb(Y, U, V):
    R = int(Y + (1.4075 * (V - 128)))
    G = int(Y - (0.3455 * (U - 128)) - (0.7169 * (V - 128)))
    B = int(Y + (1.7790 * (U - 128)))
    return [max(min(v,255),0) for v in (R, G, B)]

def rgb2yuv(R, G, B):
    Y = int(0.299 * R + 0.587 * G + 0.114 * B)
    U = int(-0.14713 * R - 0.28886 * G + 0.436 * B + 128)
    V = int( 0.615 * R - 0.51499* G - 0.10001 * B + 128)
    return [max(min(v,255),0) for v in (Y, U, V)]

_functions = ()

globvars.makeEnvironment(locals(), _functions)

_variables = (
     "black",
     "white",
     "blue",
     "red",
     "green",
     "gray",
     "dark Gray",
     "light Gray",
     "yellow",
     "pink",
     "magenta",
     "cyan",
     )

globvars.makeEnvironment(locals(), _variables, "variables")
