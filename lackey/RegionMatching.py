from PIL import Image, ImageTk
from numbers import Number
try:
    import Tkinter as tk
    import tkMessageBox as tkmb
except ImportError:
    import tkinter as tk
    import tkinter.messagebox as tkmb
import multiprocessing
import subprocess
import pyperclip
import tempfile
import platform
import numpy
import time
import uuid
import cv2
import sys
import os
import re

from .InputEmulation import Mouse as MouseClass, Keyboard
from .Exceptions import FindFailed, ImageMissing
from .SettingsDebug import Settings, Debug
from .TemplateMatchers import PyramidTemplateMatcher as TemplateMatcher
from .Geometry import Location

if platform.system() == "Windows" or os.environ.get('READTHEDOCS') == 'True':
    # Avoid throwing an error if it's just being imported for documentation purposes
    from .PlatformManagerWindows import PlatformManagerWindows
    PlatformManager = PlatformManagerWindows()
elif platform.system() == "Darwin":
    from .PlatformManagerDarwin import PlatformManagerDarwin
    PlatformManager = PlatformManagerDarwin()
else:
    raise NotImplementedError("Lackey is currently only compatible with Windows and OSX.")
    

# Python 3 compatibility
try:
    basestring
except NameError:
    basestring = str
try:
    FOREVER = float("inf")
except:
    import math
    FOREVER = math.inf

# Instantiate input emulation objects
Mouse = MouseClass()
keyboard = Keyboard()

class Pattern(object):
    """ Defines a pattern based on a bitmap, similarity, and target offset """
    def __init__(self, target=None):
        self.path = None
        self.similarity = Settings.MinSimilarity
        self.offset = Location(0, 0)
        self.imagePattern = False
        if isinstance(target, Pattern):
            self.image = target.getImage()
            self.similarity = target.similarity
            self.offset = target.offset.offset(0, 0) # Clone Location
            self.imagePattern = target.isImagePattern()
        elif isinstance(target, basestring):
            self.setFilename(target)
        elif isinstance(target, numpy.ndarray):
            self.setImage(target)
        elif target is not None:
            raise TypeError("Unrecognized argument for Pattern()")

    def similar(self, similarity):
        """ Returns a new Pattern with the specified similarity threshold """
        pattern = Pattern(self.path)
        pattern.similarity = similarity
        return pattern
    def getSimilar(self):
        """ Returns the current minimum similarity """
        return self.similarity
    def exact(self):
        """ Returns a new Pattern with a similarity threshold of 1.0 """
        pattern = Pattern(self.path)
        pattern.similarity = 1.0
        return pattern
    def isValid(self):
        return (self.image is not None)
    def targetOffset(self, dx, dy):
        """ Returns a new Pattern with the given target offset """
        pattern = Pattern(self.path)
        pattern.similarity = self.similarity
        pattern.offset = Location(dx, dy)
        return pattern

    def getFilename(self):
        """ Returns the path to this Pattern's bitmap """
        return self.path
    def setFilename(self, filename):
        """ Set the filename of the pattern's image (and load it) """
        ## Loop through image paths to find the image
        found = False
        for image_path in sys.path + [Settings.BundlePath, os.getcwd()] + Settings.ImagePaths:
            full_path = os.path.join(image_path, filename)
            if os.path.exists(full_path):
                # Image file not found
                found = True
                break
        ## Check if path is valid
        if not found:
            self.path = filename
            print(Settings.ImagePaths)
            raise ImageMissing(ImageMissingEvent(pattern=self, event_type="IMAGEMISSING"))
        self.path = full_path
        self.image = cv2.imread(self.path)
        return self
    def setImage(self, img):
        self.image = img
        self.imagePattern = True
        return self
    def getImage(self):
        return self.image
    def getTargetOffset(self):
        """ Returns the target offset as a Location(dx, dy) """
        return self.offset
    def isImagePattern(self):
        return self.imagePattern
    def debugPreview(self, title="Debug"):
        """ Loads and displays the image at ``Pattern.path`` """
        haystack = Image.open(self.path)
        haystack.show()

class Region(object):
    def __init__(self, *args):
        if len(args) == 4:
            x, y, w, h = args
        elif len(args) == 1:
            if isinstance(args[0], Region):
                x, y, w, h = args[0].getTuple()
            elif isinstance(args[0], tuple):
                x, y, w, h = args[0]
            else:
                raise TypeError("Unrecognized argument for Region()")
        elif len(args) == 5:
            # We can safely ignore Sikuli's screen argument, as that's
            # checked dynamically by the location of the region
            x, y, w, h, screen = args
        elif len(args) == 2:
            # Minimal point-like region
            x, y = args
            w = 1
            h = 1
        else:
            raise TypeError("Unrecognized argument(s) for Region()")
        self.FOREVER = None

        self.setROI(x, y, w, h)
        self._lastMatch = None
        self._lastMatches = []
        self._lastMatchTime = 0
        self.autoWaitTimeout = 3.0
        # Converts searches per second to actual second interval
        self._defaultScanRate = None
        self._defaultTypeSpeed = 0.05
        self._raster = (0, 0)
        self._observer = Observer(self)
        self._observeScanRate = None
        self._repeatWaitTime = 0.3
        self._throwException = True
        self._findFailedResponse = "ABORT"
        self._findFailedHandler = None
        self._highlighter = None
    
    CREATE_X_DIRECTION_LEFT = 0
    CREATE_X_DIRECTION_RIGHT = 1
    CREATE_Y_DIRECTION_TOP = 0
    CREATE_Y_DIRECTION_BOTTOM = 1
    @classmethod
    def create(cls, *args):
        if len(args) == 3 and isinstance(args[0], Location):
            return cls(args[0].x, args[0].y, args[1], args[2])
        elif len(args) == 5 and isinstance(args[0], Location):
            loc, create_x_direction, create_y_direction, w, h = args
            if create_x_direction == cls.CREATE_X_DIRECTION_LEFT:
                x = loc.x
            else:
                x = loc.x - w
            if create_y_direction == cls.CREATE_Y_DIRECTION_TOP:
                y = loc.y
            else:
                y = loc.y - h
            return cls(x, y, w, h)

    def setX(self, x):
        """ Set the x-coordinate of the upper left-hand corner """
        self.x = int(x)
    def setY(self, y):
        """ Set the y-coordinate of the upper left-hand corner """
        self.y = int(y)
    def setW(self, w):
        """ Set the width of the region """
        self.w = max(1, int(w))
    def setH(self, h):
        """ Set the height of the region """
        self.h = max(1, int(h))

    def getX(self):
        """ Get the x-coordinate of the upper left-hand corner """
        return self.x
    def getY(self):
        """ Get the y-coordinate of the upper left-hand corner """
        return self.y
    def getW(self):
        """ Get the width of the region """
        return self.w
    def getH(self):
        """ Get the height of the region """
        return self.h
    def getTuple(self):
        """ Returns the shape of the region as (x, y, w, h) """
        return (self.x, self.y, self.w, self.h)

    def setLocation(self, location):
        """ Change the upper left-hand corner to a new ``Location``

        Doesn't change width or height
        """
        if not location or not isinstance(location, Location):
            raise ValueError("setLocation expected a Location object")
        self.x = location.x
        self.y = location.y
        return self
    moveTo = setLocation
    def setROI(self, *args):
        """ Set Region of Interest (same as Region.setRect()) """
        if len(args) == 4:
            x, y, w, h = args
        elif len(args) == 1:
            if isinstance(args[0], Region):
                x, y, w, h = args[0].getTuple()
            elif isinstance(args[0], tuple):
                x, y, w, h = args[0]
            else:
                raise TypeError("Unrecognized argument for Region()")
        else:
            raise TypeError("Unrecognized argument(s) for Region()")
        self.setX(x)
        self.setY(y)
        self.setW(w)
        self.setH(h)
    setRect = setROI
    def contains(self, point_or_region):
        """ Checks if ``point_or_region`` is within this region """
        if isinstance(point_or_region, Location):
            return (self.x < point_or_region.x < self.x + self.w) and (self.y < point_or_region.y < self.y + self.h)
        elif isinstance(point_or_region, Region):
            return ((self.x < point_or_region.getX() < self.x + self.w) and
                    (self.y < point_or_region.getY() < self.y + self.h) and
                    (self.x < point_or_region.getX() + point_or_region.getW() < self.x + self.w) and
                    (self.y < point_or_region.getY() + point_or_region.getH() < self.y + self.h))
        else:
            raise TypeError("Unrecognized argument type for contains()")
    def containsMouse(self):
        return self.contains(Mouse.getPos())
    def morphTo(self, region):
        """ Change shape of this region to match the given ``Region`` object """
        if not region or not isinstance(region, Region):
            raise TypeError("morphTo expected a Region object")
        self.setROI(region)
        return self
    def copyTo(self, screen):
        if not isinstance(screen, Screen):
            # Parameter was screen ID instead of object
            screen = Screen(screen)
        zero_coord = Location(screen.getX(), screen.getY())
        this_screen = self.getScreen()
        offset = Location(this_screen.getX() - zero_coord.x, this_screen.getY() - zero_coord.y)
        target_coord = zero_coord.offset(offset.x, offset.y)
        return Region(self).setLocation(target_coord)

    def getCenter(self):
        """ Return the ``Location`` of the center of this region """
        return Location(self.x+(self.w/2), self.y+(self.h/2))
    def getTopLeft(self):
        """ Return the ``Location`` of the top left corner of this region """
        return Location(self.x, self.y)
    def getTopRight(self):
        """ Return the ``Location`` of the top right corner of this region """
        return Location(self.x+self.w, self.y)
    def getBottomLeft(self):
        """ Return the ``Location`` of the bottom left corner of this region """
        return Location(self.x, self.y+self.h)
    def getBottomRight(self):
        """ Return the ``Location`` of the bottom right corner of this region """
        return Location(self.x+self.w, self.y+self.h)

    def getScreen(self):
        """ Return an instance of the ``Screen`` object this region is inside.

        Checks the top left corner of this region (if it touches multiple screens) is inside.
        Returns None if the region isn't positioned in any screen.
        """
        return self.getTopLeft().getScreen()

    def getLastMatch(self):
        """ Returns the last successful ``Match`` returned by ``find()``, ``exists()``, etc. """
        return self._lastMatch
    def getLastMatches(self):
        """ Returns the last successful set of ``Match`` objects returned by ``findAll()`` """
        return self._lastMatches
    def getTime(self):
        """ Returns the elapsed time in milliseconds to find the last match """
        return self._lastMatchTime

    def setAutoWaitTimeout(self, seconds):
        """ Specify the time to wait for an image to appear on the screen """
        self.autoWaitTimeout = float(seconds)
    def getAutoWaitTimeout(self):
        """ Returns the time to wait for an image to appear on the screen """
        return self.autoWaitTimeout
    def setWaitScanRate(self, seconds=None):
        """Set this Region's scan rate

        A find op should repeat the search for the given Visual rate times per second until
        found or the maximum waiting time is reached.
        """
        self._defaultScanRate = float(seconds)
    def getWaitScanRate(self):
        """ Get the current scan rate """
        return self._defaultScanRate if not self._defaultScanRate is None else Settings.WaitScanRate

    def offset(self, location, dy=0):
        """ Returns a new ``Region`` offset from this one by ``location``

        Width and height remain the same
        """
        if not isinstance(location, Location):
            # Assume variables passed were dx,dy
            location = Location(location, dy)
        r = Region(self.x+location.x, self.y+location.y, self.w, self.h).clipRegionToScreen()
        if r is None:
            raise ValueError("Specified region is not visible on any screen")
            return None
        return r
    def grow(self, width, height=None):
        """ Expands the region by ``width`` on both sides and ``height`` on the top and bottom.

        If only one value is provided, expands the region by that amount on all sides.
        Equivalent to ``nearby()``.
        """
        if height is None:
            return self.nearby(width)
        else:
            return Region(
                self.x-width,
                self.y-height,
                self.w+(2*width),
                self.h+(2*height)).clipRegionToScreen()
    def inside(self):
        """ Returns the same object. Included for Sikuli compatibility. """
        return self
    def nearby(self, expand=50):
        """ Returns a new Region that includes the nearby neighbourhood of the the current region.

        The new region is defined by extending the current region's dimensions
        all directions by range number of pixels. The center of the new region remains the
        same.
        """
        return Region(
            self.x-expand,
            self.y-expand,
            self.w+(2*expand),
            self.h+(2*expand)).clipRegionToScreen()
    def above(self, expand=None):
        """ Returns a new Region above the current region with a height of ``expand`` pixels.

        Does not include the current region. If range is omitted, it reaches to the top of the
        screen. The new region has the same width and x-position as the current region.
        """
        if expand == None:
            x = self.x
            y = 0
            w = self.w
            h = self.y
        else:
            x = self.x
            y = self.y - expand
            w = self.w
            h = expand
        return Region(x, y, w, h).clipRegionToScreen()
    def below(self, expand=None):
        """ Returns a new Region below the current region with a height of ``expand`` pixels.

        Does not include the current region. If range is omitted, it reaches to the bottom
        of the screen. The new region has the same width and x-position as the current region.
        """
        if expand == None:
            x = self.x
            y = self.y+self.h
            w = self.w
            h = self.getScreen().getBounds()[3] - y # Screen height
        else:
            x = self.x
            y = self.y + self.h
            w = self.w
            h = expand
        return Region(x, y, w, h).clipRegionToScreen()
    def left(self, expand=None):
        """ Returns a new Region left of the current region with a width of ``expand`` pixels.

        Does not include the current region. If range is omitted, it reaches to the left border
        of the screen. The new region has the same height and y-position as the current region.
        """
        if expand == None:
            x = 0
            y = self.y
            w = self.x
            h = self.h
        else:
            x = self.x-expand
            y = self.y
            w = expand
            h = self.h
        return Region(x, y, w, h).clipRegionToScreen()
    def right(self, expand=None):
        """ Returns a new Region right of the current region with a width of ``expand`` pixels.

        Does not include the current region. If range is omitted, it reaches to the right border
        of the screen. The new region has the same height and y-position as the current region.
        """
        if expand == None:
            x = self.x+self.w
            y = self.y
            w = self.getScreen().getBounds()[2] - x
            h = self.h
        else:
            x = self.x+self.w
            y = self.y
            w = expand
            h = self.h
        return Region(x, y, w, h).clipRegionToScreen()
    def add(self, l, r, t, b):
        x = self.getX() - l
        y = self.getY() - t
        w = self.getW() + l + r
        h = self.getH() + t + b
        self.setRect(x, y, w, h)
        return self
    
    def getBitmap(self):
        """ Captures screen area of this region, at least the part that is on the screen

        Returns image as numpy array
        """
        return PlatformManager.getBitmapFromRect(self.x, self.y, self.w, self.h)
    def debugPreview(self, title="Debug"):
        """ Displays the region in a preview window.

        If the region is a Match, circles the target area. If the region is larger than half the
        primary screen in either dimension, scales it down to half size.
        """
        region = self
        haystack = self.getBitmap()
        if isinstance(region, Match):
            cv2.circle(
                haystack,
                (region.getTarget().x - self.x, region.getTarget().y - self.y),
                5,
                255)
        if haystack.shape[0] > (Screen(0).getBounds()[2]/2) or haystack.shape[1] > (Screen(0).getBounds()[3]/2):
            # Image is bigger than half the screen; scale it down
            haystack = cv2.resize(haystack, (0, 0), fx=0.5, fy=0.5)
        Image.fromarray(haystack).show()

    def highlight(self, *args):
        """ Highlights the region with a colored frame. Accepts the following parameters:

        highlight([toEnable], [seconds], [color])
        
        * toEnable (boolean): Enables or disables the overlay
        * seconds (number): Seconds to show overlay
        * color (string): Hex code ("#XXXXXX") or color name ("black")
        """
        toEnable = (self._highlighter is None)
        seconds = 3
        color = "red"
        if len(args) > 3:
            raise TypeError("Unrecognized argument(s) for highlight()")
        for arg in args:
            if type(arg) == bool:
                toEnable = arg
            elif isinstance(arg, Number):
                seconds = arg
            elif isinstance(arg, basestring):
                color = arg
        if self._highlighter is not None:
                self._highlighter.close()
        if toEnable:
            self._highlighter = PlatformManager.highlight((self.getX(), self.getY(), self.getW(), self.getH()), color, seconds)
            

    def find(self, pattern):
        """ Searches for an image pattern in the given region

        Throws ``FindFailed`` exception if the image could not be found.
        Sikuli supports OCR search with a text parameter. This does not (yet).
        """
        findFailedRetry = True
        while findFailedRetry:
            match = self.exists(pattern)
            if match is not None:
                break
            path = pattern.path if isinstance(pattern, Pattern) else pattern
            findFailedRetry = self._raiseFindFailed("Could not find pattern '{}'".format(path))
            if findFailedRetry:
                time.sleep(self._repeatWaitTime)
        return match
    def findAll(self, pattern):
        """ Searches for an image pattern in the given region

        Returns ``Match`` object if ``pattern`` exists, empty array otherwise (does not
        throw exception). Sikuli supports OCR search with a text parameter. This does not (yet).
        """
        find_time = time.time()
        r = self.clipRegionToScreen()
        if r is None:
            raise ValueError("Region outside all visible screens")
            return None
        seconds = self.autoWaitTimeout
        if not isinstance(pattern, Pattern):
            if not isinstance(pattern, basestring):
                raise TypeError("find expected a string [image path] or Pattern object")
            pattern = Pattern(pattern)
        needle = cv2.imread(pattern.path)
        if needle is None:
            raise ValueError("Unable to load image '{}'".format(pattern.path))
        needle_height, needle_width, needle_channels = needle.shape
        positions = []
        timeout = time.time() + seconds

        # Check TemplateMatcher for valid matches
        matches = []
        while time.time() < timeout and len(matches) == 0:
            matcher = TemplateMatcher(r.getBitmap())
            matches = matcher.findAllMatches(needle, pattern.similarity)
            time.sleep(1/self._defaultScanRate if self._defaultScanRate is not None else 1/Settings.WaitScanRate)

        if len(matches) == 0:
            Debug.info("Couldn't find '{}' with enough similarity.".format(pattern.path))
            return iter([])

        # Matches found! Turn them into Match objects
        lastMatches = []
        for match in matches:
            position, confidence = match
            x, y = position
            lastMatches.append(
                Match(
                    confidence,
                    pattern.offset,
                    ((x+self.x, y+self.y), (needle_width, needle_height))))
        self._lastMatches = iter(lastMatches)
        Debug.info("Found match(es) for pattern '{}' at similarity ({})".format(pattern.path, pattern.similarity))
        self._lastMatchTime = (time.time() - find_time) * 1000 # Capture find time in milliseconds
        return self._lastMatches

    def wait(self, pattern, seconds=None):
        """ Searches for an image pattern in the given region, given a specified timeout period

        Functionally identical to find(). If a number is passed instead of a pattern,
        just waits the specified number of seconds.
        Sikuli supports OCR search with a text parameter. This does not (yet).
        """
        if isinstance(pattern, (int, float)):
            if pattern == FOREVER:
                while True:
                    time.sleep(1) # Infinite loop
            time.sleep(pattern)
            return None

        if seconds is None:
            seconds = self.autoWaitTimeout
        
        findFailedRetry = True
        timeout = time.time() + seconds
        while findFailedRetry:
            while True:
                match = self.exists(pattern)
                if match:
                    return match
                if time.time() >= timeout:
                    break
            path = pattern.path if isinstance(pattern, Pattern) else pattern
            findFailedRetry = self._raiseFindFailed("Could not find pattern '{}'".format(path))
            if findFailedRetry:
                time.sleep(self._repeatWaitTime)
        return None
    def waitVanish(self, pattern, seconds=None):
        """ Waits until the specified pattern is not visible on screen.

        If ``seconds`` pass and the pattern is still visible, raises FindFailed exception.
        Sikuli supports OCR search with a text parameter. This does not (yet).
        """
        r = self.clipRegionToScreen()
        if r is None:
            raise ValueError("Region outside all visible screens")
            return None
        if seconds is None:
            seconds = self.autoWaitTimeout
        if not isinstance(pattern, Pattern):
            if not isinstance(pattern, basestring):
                raise TypeError("find expected a string [image path] or Pattern object")
            pattern = Pattern(pattern)

        needle = cv2.imread(pattern.path)
        match = True
        timeout = time.time() + seconds

        while match and time.time() < timeout:
            matcher = TemplateMatcher(r.getBitmap())
            # When needle disappears, matcher returns None
            match = matcher.findBestMatch(needle, pattern.similarity)
            time.sleep(1/self._defaultScanRate if self._defaultScanRate is not None else 1/Settings.WaitScanRate)
        if match:
            return False
            #self._findFailedHandler(FindFailed("Pattern '{}' did not vanish".format(pattern.path)))
    def exists(self, pattern, seconds=None):
        """ Searches for an image pattern in the given region

        Returns Match if pattern exists, None otherwise (does not throw exception)
        Sikuli supports OCR search with a text parameter. This does not (yet).
        """
        find_time = time.time()
        r = self.clipRegionToScreen()
        if r is None:
            raise ValueError("Region outside all visible screens")
            return None
        if seconds is None:
            seconds = self.autoWaitTimeout
        if isinstance(pattern, int):
            # Actually just a "wait" statement
            time.sleep(pattern)
            return
        if not pattern:
            time.sleep(seconds)
        if not isinstance(pattern, Pattern):
            if not isinstance(pattern, basestring):
                raise TypeError("find expected a string [image path] or Pattern object")
            pattern = Pattern(pattern)
        needle = cv2.imread(pattern.path)
        if needle is None:
            raise ValueError("Unable to load image '{}'".format(pattern.path))
        needle_height, needle_width, needle_channels = needle.shape
        match = None
        timeout = time.time() + seconds

        # Consult TemplateMatcher to find needle
        while not match:
            matcher = TemplateMatcher(r.getBitmap())
            match = matcher.findBestMatch(needle, pattern.similarity)
            time.sleep(1/self._defaultScanRate if self._defaultScanRate is not None else 1/Settings.WaitScanRate)
            if time.time() > timeout:
                break

        if match is None:
            Debug.info("Couldn't find '{}' with enough similarity.".format(pattern.path))
            return None

        # Translate local position into global screen position
        position, confidence = match
        position = (position[0] + self.x, position[1] + self.y)
        self._lastMatch = Match(
            confidence,
            pattern.offset,
            (position, (needle_width, needle_height)))
        #self._lastMatch.debug_preview()
        Debug.info("Found match for pattern '{}' at ({},{}) with confidence ({}). Target at ({},{})".format(
            pattern.path,
            self._lastMatch.getX(),
            self._lastMatch.getY(),
            self._lastMatch.getScore(),
            self._lastMatch.getTarget().x,
            self._lastMatch.getTarget().y))
        self._lastMatchTime = (time.time() - find_time) * 1000 # Capture find time in milliseconds
        return self._lastMatch

    def click(self, target=None, modifiers=""):
        """ Moves the cursor to the target location and clicks the default mouse button. """
        if target is None:
            target = self._lastMatch or self # Whichever one is not None

        target_location = None
        if isinstance(target, Pattern):
            target_location = self.find(target).getTarget()
        elif isinstance(target, basestring):
            target_location = self.find(target).getTarget()
        elif isinstance(target, Match):
            target_location = target.getTarget()
        elif isinstance(target, Region):
            target_location = target.getCenter()
        elif isinstance(target, Location):
            target_location = target
        else:
            raise TypeError("click expected Pattern, String, Match, Region, or Location object")
        if modifiers != "":
            keyboard.keyDown(modifiers)

        Mouse.moveSpeed(target_location, Settings.MoveMouseDelay)
        time.sleep(0.1) # For responsiveness
        if Settings.ClickDelay > 0:
            time.sleep(min(1.0, Settings.ClickDelay))
            Settings.ClickDelay = 0.0
        Mouse.click()
        time.sleep(0.1)

        if modifiers != 0:
            keyboard.keyUp(modifiers)
        Debug.history("Clicked at {}".format(target_location))
    def doubleClick(self, target=None, modifiers=""):
        """ Moves the cursor to the target location and double-clicks the default mouse button. """
        if target is None:
            target = self._lastMatch or self # Whichever one is not None
        target_location = None
        if isinstance(target, Pattern):
            target_location = self.find(target).getTarget()
        elif isinstance(target, basestring):
            target_location = self.find(target).getTarget()
        elif isinstance(target, Match):
            target_location = target.getTarget()
        elif isinstance(target, Region):
            target_location = target.getCenter()
        elif isinstance(target, Location):
            target_location = target
        else:
            raise TypeError("doubleClick expected Pattern, String, Match, Region, or Location object")
        if modifiers != "":
            keyboard.keyDown(modifiers)

        Mouse.moveSpeed(target_location, Settings.MoveMouseDelay)
        time.sleep(0.1)
        if Settings.ClickDelay > 0:
            time.sleep(min(1.0, Settings.ClickDelay))
            Settings.ClickDelay = 0.0
        Mouse.click()
        time.sleep(0.1)
        if Settings.ClickDelay > 0:
            time.sleep(min(1.0, Settings.ClickDelay))
            Settings.ClickDelay = 0.0
        Mouse.click()
        time.sleep(0.1)

        if modifiers != 0:
            keyboard.keyUp(modifiers)
    def rightClick(self, target=None, modifiers=""):
        """ Moves the cursor to the target location and clicks the right mouse button. """
        if target is None:
            target = self._lastMatch or self # Whichever one is not None
        target_location = None
        if isinstance(target, Pattern):
            target_location = self.find(target).getTarget()
        elif isinstance(target, basestring):
            target_location = self.find(target).getTarget()
        elif isinstance(target, Match):
            target_location = target.getTarget()
        elif isinstance(target, Region):
            target_location = target.getCenter()
        elif isinstance(target, Location):
            target_location = target
        else:
            raise TypeError("rightClick expected Pattern, String, Match, Region, or Location object")

        if modifiers != "":
            keyboard.keyDown(modifiers)

        Mouse.moveSpeed(target_location, Settings.MoveMouseDelay)
        time.sleep(0.1)
        if Settings.ClickDelay > 0:
            time.sleep(min(1.0, Settings.ClickDelay))
            Settings.ClickDelay = 0.0
        Mouse.click(button=Mouse.RIGHT)
        time.sleep(0.1)

        if modifiers != "":
            keyboard.keyUp(modifiers)

    def hover(self, target=None):
        """ Moves the cursor to the target location """
        if target is None:
            target = self._lastMatch or self # Whichever one is not None
        target_location = None
        if isinstance(target, Pattern):
            target_location = self.find(target).getTarget()
        elif isinstance(target, basestring):
            target_location = self.find(target).getTarget()
        elif isinstance(target, Match):
            target_location = target.getTarget()
        elif isinstance(target, Region):
            target_location = target.getCenter()
        elif isinstance(target, Location):
            target_location = target
        else:
            raise TypeError("hover expected Pattern, String, Match, Region, or Location object")

        Mouse.moveSpeed(target_location, Settings.MoveMouseDelay)
    def drag(self, dragFrom=None):
        """ Starts a dragDrop operation.

        Moves the cursor to the target location and clicks the mouse in preparation to drag
        a screen element """
        if dragFrom is None:
            dragFrom = self._lastMatch or self # Whichever one is not None
        dragFromLocation = None
        if isinstance(dragFrom, Pattern):
            dragFromLocation = self.find(dragFrom).getTarget()
        elif isinstance(dragFrom, basestring):
            dragFromLocation = self.find(dragFrom).getTarget()
        elif isinstance(dragFrom, Match):
            dragFromLocation = dragFrom.getTarget()
        elif isinstance(dragFrom, Region):
            dragFromLocation = dragFrom.getCenter()
        elif isinstance(dragFrom, Location):
            dragFromLocation = dragFrom
        else:
            raise TypeError("drag expected dragFrom to be Pattern, String, Match, Region, or Location object")
        Mouse.moveSpeed(dragFromLocation, Settings.MoveMouseDelay)
        time.sleep(Settings.DelayBeforeMouseDown)
        Mouse.buttonDown()
        Debug.history("Began drag at {}".format(dragFromLocation))
    def dropAt(self, dragTo=None, delay=None):
        """ Completes a dragDrop operation

        Moves the cursor to the target location, waits ``delay`` seconds, and releases the mouse
        button """
        if dragTo is None:
            dragTo = self._lastMatch or self # Whichever one is not None
        if isinstance(dragTo, Pattern):
            dragToLocation = self.find(dragTo).getTarget()
        elif isinstance(dragTo, basestring):
            dragToLocation = self.find(dragTo).getTarget()
        elif isinstance(dragTo, Match):
            dragToLocation = dragTo.getTarget()
        elif isinstance(dragTo, Region):
            dragToLocation = dragTo.getCenter()
        elif isinstance(dragTo, Location):
            dragToLocation = dragTo
        else:
            raise TypeError("dragDrop expected dragTo to be Pattern, String, Match, Region, or Location object")

        Mouse.moveSpeed(dragToLocation, Settings.MoveMouseDelay)
        time.sleep(delay if delay is not None else Settings.DelayBeforeDrop)
        Mouse.buttonUp()
        Debug.history("Ended drag at {}".format(dragToLocation))
    def dragDrop(self, target, target2=None, modifiers=""):
        """ Performs a dragDrop operation.

        Holds down the mouse button on ``dragFrom``, moves the mouse to ``dragTo``, and releases
        the mouse button.

        ``modifiers`` may be a typeKeys() compatible string. The specified keys will be held
        during the drag-drop operation.
        """
        if modifiers != "":
            keyboard.keyDown(modifiers)
        
        if target2 is None:
            dragFrom = self._lastMatch
            dragTo = target
        else:
            dragFrom = target
            dragTo = target2

        self.drag(dragFrom)
        time.sleep(Settings.DelayBeforeDrag)
        self.dropAt(dragTo)

        if modifiers != "":
            keyboard.keyUp(modifiers)

    def type(self, *args):
        """ Usage: type([PSMRL], text, [modifiers])

        If a pattern is specified, the pattern is clicked first. Doesn't support text paths.

        Special keys can be entered with the key name between brackets, as `"{SPACE}"`, or as
        `Key.SPACE`.
        """
        pattern = None
        text = None
        modifiers = None
        if len(args) == 1 and isinstance(args[0], basestring):
            # Is a string (or Key) to type
            text = args[0]
        elif len(args) == 2:
            if not isinstance(args[0], basestring) and isinstance(args[1], basestring):
                pattern = args[0]
                text = args[1]
            else:
                text = args[0]
                modifiers = args[1]
        elif len(args) == 3 and not isinstance(args[0], basestring):
            pattern = args[0]
            text = args[1]
            modifiers = args[2]
        else:
            raise TypeError("type method expected ([PSMRL], text, [modifiers])")

        if pattern:
            self.click(pattern)

        Debug.history("Typing '{}' with modifiers '{}'".format(text, modifiers))
        kb = keyboard
        if modifiers:
            kb.keyDown(modifiers)
        if Settings.TypeDelay > 0:
            typeSpeed = min(1.0, Settings.TypeDelay)
            Settings.TypeDelay = 0.0
        else:
            typeSpeed = self._defaultTypeSpeed
        kb.type(text, typeSpeed)
        if modifiers:
            kb.keyUp(modifiers)
        time.sleep(0.2)
    def paste(self, *args):
        """ Usage: paste([PSMRL], text)

        If a pattern is specified, the pattern is clicked first. Doesn't support text paths.
        ``text`` is pasted as is using the OS paste shortcut (Ctrl+V for Windows/Linux, Cmd+V
        for OS X). Note that `paste()` does NOT use special formatting like `type()`.
        """
        target = None
        text = ""
        if len(args) == 1 and isinstance(args[0], basestring):
            text = args[0]
        elif len(args) == 2 and isinstance(args[1], basestring):
            self.click(target)
            text = args[1]
        else:
            raise TypeError("paste method expected [PSMRL], text")

        pyperclip.copy(text)
        # Triggers OS paste for foreground window
        PlatformManager.osPaste()
        time.sleep(0.2)
    def getClipboard(self):
        """ Returns the contents of the clipboard

        Can be used to pull outside text into the application, if it is first
        copied with the OS keyboard shortcut (e.g., "Ctrl+C") """
        return pyperclip.paste()
    def text(self):
        """ OCR method. Todo. """
        raise NotImplementedError("OCR not yet supported")

    def mouseDown(self, button=Mouse.LEFT):
        """ Low-level mouse actions. """
        return Mouse.buttonDown(button)
    def mouseUp(self, button=Mouse.LEFT):
        """ Low-level mouse actions """
        return Mouse.buttonUp(button)
    def mouseMove(self, PSRML=None, dy=0):
        """ Low-level mouse actions """
        if PSRML is None:
            PSRML = self._lastMatch or self # Whichever one is not None
        if isinstance(PSRML, Pattern):
            move_location = self.find(PSRML).getTarget()
        elif isinstance(PSRML, basestring):
            move_location = self.find(PSRML).getTarget()
        elif isinstance(PSRML, Match):
            move_location = PSRML.getTarget()
        elif isinstance(PSRML, Region):
            move_location = PSRML.getCenter()
        elif isinstance(PSRML, Location):
            move_location = PSRML
        elif isinstance(PSRML, int):
            # Assume called as mouseMove(dx, dy)
            offset = Location(PSRML, dy)
            move_location = Mouse.getPos().offset(offset)
        else:
            raise TypeError("doubleClick expected Pattern, String, Match, Region, or Location object")
        Mouse.moveSpeed(move_location)
    def wheel(self, *args): # [PSRML], direction, steps
        """ Clicks the wheel the specified number of ticks. Use the following parameters:

        wheel([PSRML], direction, steps, [stepDelay])
        """
        if len(args) == 2:
            PSRML = None
            direction = int(args[0])
            steps = int(args[1])
            stepDelay = None
        elif len(args) == 3:
            PSRML = args[0]
            direction = int(args[1])
            steps = int(args[2])
            stepDelay = None
        elif len(args) == 4:
            PSRML = args[0]
            direction = int(args[1])
            steps = int(args[2])
            stepDelay = int(args[3])
        
        if PSRML is not None:
            self.mouseMove(PSRML)
        Mouse.wheel(direction, steps)
    def atMouse(self):
        return Mouse.at()
    def keyDown(self, keys):
        """ Concatenate multiple keys to press them all down. """
        return keyboard.keyDown(keys)
    def keyUp(self, keys):
        """ Concatenate multiple keys to up them all. """
        return keyboard.keyUp(keys)
    def write(self, text):
        """ Has fancy special options. Not implemented yet. """
        raise NotImplementedError()
    def delayType(millisecs):
        Settings.TypeDelay = millisecs
    def isRegionValid(self):
        """ Returns false if the whole region is not even partially inside any screen, otherwise true """
        screens = PlatformManager.getScreenDetails()
        for screen in screens:
            s_x, s_y, s_w, s_h = screen["rect"]
            if self.x+self.w >= s_x and s_x+s_w >= self.x and self.y+self.h >= s_y and s_y+s_h >= self.y:
                # Rects overlap
                return True
        return False

    def clipRegionToScreen(self):
        """ Returns the part of the region that is visible on a screen

        If the region equals to all visible screens, returns Screen(-1).
        If the region is visible on multiple screens, returns the screen with the smallest ID.
        Returns None if the region is outside the screen.
        """
        if not self.isRegionValid():
            return None
        screens = PlatformManager.getScreenDetails()
        total_x, total_y, total_w, total_h = Screen(-1).getBounds()
        containing_screen = None
        for screen in screens:
            s_x, s_y, s_w, s_h = screen["rect"]
            if self.x >= s_x and self.x+self.w <= s_x+s_w and self.y >= s_y and self.y+self.h <= s_y+s_h:
                # Region completely inside screen
                return self
            elif self.x+self.w <= s_x or s_x+s_w <= self.x or self.y+self.h <= s_y or s_y+s_h <= self.y:
                # Region completely outside screen
                continue
            elif self.x == total_x and self.y == total_y and self.w == total_w and self.h == total_h:
                # Region equals all screens, Screen(-1)
                return self
            else:
                # Region partially inside screen
                x = max(self.x, s_x)
                y = max(self.y, s_y)
                w = min(self.w, s_w)
                h = min(self.h, s_h)
                return Region(x, y, w, h)
        return None


    # Partitioning constants
    NORTH 			= 202 # Upper half
    NORTH_WEST 		= 300 # Left third in upper third
    NORTH_MID 		= 301 # Middle third in upper third
    NORTH_EAST 		= 302 # Right third in upper third
    SOUTH 			= 212 # Lower half
    SOUTH_WEST 		= 320 # Left third in lower third
    SOUTH_MID 		= 321 # Middle third in lower third
    SOUTH_EAST 		= 322 # Right third in lower third
    EAST 			= 220 # Right half
    EAST_MID 		= 310 # Middle third in right third
    WEST 			= 221 # Left half
    WEST_MID 		= 312 # Middle third in left third
    MID_THIRD 		= 311 # Middle third in middle third
    TT 				= 200 # Top left quarter
    RR 				= 201 # Top right quarter
    BB 				= 211 # Bottom right quarter
    LL 				= 210 # Bottom left quarter

    MID_VERTICAL 	= "MID_VERT" # Half of width vertically centered
    MID_HORIZONTAL	= "MID_HORZ" # Half of height horizontally centered
    MID_BIG			= "MID_HALF" # Half of width/half of height centered

    def setRaster(self, rows, columns):
        """ Sets the raster for the region, allowing sections to be indexed by row/column """
        rows = int(rows)
        columns = int(columns)
        if rows <= 0 or columns <= 0:
            return self
        self._raster = (rows, columns)
        return self.getCell(0, 0)
    def getRow(self, row, numberRows=None):
        """ Returns the specified row of the region (if the raster is set)

        If numberRows is provided, uses that instead of the raster
        """
        row = int(row)
        if self._raster[0] == 0 or self._raster[1] == 0:
            return self
        if numberRows is None or numberRows < 1 or numberRows > 9:
            numberRows = self._raster[0]
        rowHeight = self.h / numberRows
        if row < 0:
            # If row is negative, count backwards from the end
            row = numberRows - row
            if row < 0:
                # Bad row index, return last row
                return Region(self.x, self.y+self.h-rowHeight, self.w, rowHeight)
        elif row > numberRows:
            # Bad row index, return first row
            return Region(self.x, self.y, self.w, rowHeight)
        return Region(self.x, self.y + (row * rowHeight), self.w, rowHeight)
    def getCol(self, column, numberColumns=None):
        """ Returns the specified column of the region (if the raster is set)

        If numberColumns is provided, uses that instead of the raster
        """
        column = int(column)
        if self._raster[0] == 0 or self._raster[1] == 0:
            return self
        if numberColumns is None or numberColumns < 1 or numberColumns > 9:
            numberColumns = self._raster[1]
        columnWidth = self.w / numberColumns
        if column < 0:
            # If column is negative, count backwards from the end
            column = numberColumns - column
            if column < 0:
                # Bad column index, return last column
                return Region(self.x+self.w-columnWidth, self.y, columnWidth, self.h)
        elif column > numberColumns:
            # Bad column index, return first column
            return Region(self.x, self.y, columnWidth, self.h)
        return Region(self.x + (column * columnWidth), self.y, columnWidth, self.h)
    def getCell(self, row, column):
        """ Returns the specified cell (if a raster is set for the region) """
        row = int(row)
        column = int(column)
        if self._raster[0] == 0 or self._raster[1] == 0:
            return self
        rowHeight = self.h / self._raster[0]
        columnWidth = self.h / self._raster[1]
        if column < 0:
            # If column is negative, count backwards from the end
            column = self._raster[1] - column
            if column < 0:
                # Bad column index, return last column
                column = self._raster[1]
        elif column > self._raster[1]:
            # Bad column index, return first column
            column = 0
        if row < 0:
            # If row is negative, count backwards from the end
            row = self._raster[0] - row
            if row < 0:
                # Bad row index, return last row
                row = self._raster[0]
        elif row > self._raster[0]:
            # Bad row index, return first row
            row = 0
        return Region(self.x+(column*columnWidth), self.y+(row*rowHeight), columnWidth, rowHeight)
    def get(self, part):
        """ Returns a section of the region as a new region

        Accepts partitioning constants, e.g. Region.NORTH, Region.NORTH_WEST, etc.
        Also accepts an int 200-999:
        * First digit:  Raster (*n* rows by *n* columns)
        * Second digit: Row index (if equal to raster, gets the whole row)
        * Third digit:  Column index (if equal to raster, gets the whole column)

        Region.get(522) will use a raster of 5 rows and 5 columns and return
        the cell in the middle.

        Region.get(525) will use a raster of 5 rows and 5 columns and return the row in the middle.
        """
        if part == self.MID_VERTICAL:
            return Region(self.x+(self.w/4), y, self.w/2, self.h)
        elif part == self.MID_HORIZONTAL:
            return Region(self.x, self.y+(self.h/4), self.w, self.h/2)
        elif part == self.MID_BIG:
            return Region(self.x+(self.w/4), self.y+(self.h/4), self.w/2, self.h/2)
        elif isinstance(part, int) and part >= 200 and part <= 999:
            raster, row, column = str(part)
            self.setRaster(raster, raster)
            if row == raster and column == raster:
                return self
            elif row == raster:
                return self.getCol(column)
            elif column == raster:
                return self.getRow(row)
            else:
                return self.getCell(row,column)
        else:
            return self
    def setRows(self, rows):
        """ Sets the number of rows in the raster (if columns have not been initialized, set to 1 as well) """
        self._raster[0] = rows
        if self._raster[1] == 0:
            self._raster[1] = 1
    def setCols(self, columns):
        """ Sets the number of columns in the raster (if rows have not been initialized, set to 1 as well) """
        self._raster[1] = columns
        if self._raster[0] == 0:
            self._raster[0] = 1
    def isRasterValid(self):
        return self.getCols() > 0 and self.getRows() > 0
    def getRows(self):
        return self._raster[0]
    def getCols(self):
        return self._raster[1]
    def getRowH(self):
        if self._raster[0] == 0:
            return 0
        return self.h / self._raster[0]
    def getColW(self):
        if self._raster[1] == 0:
            return 0
        return self.w / self._raster[1]
    def showScreens(self):
        """ Synonym for showMonitors """
        Screen.showMonitors()
    def resetScreens(self):
        """ Synonym for resetMonitors """
        Screen.resetMonitors()
    def getTarget(self):
        """ By default, a region's target is its center """
        return self.getCenter()
    def setCenter(self, loc):
        """ Move this region so it is centered on ``loc`` """
        offset = self.getCenter().getOffset(loc) # Calculate offset from current center
        return self.setLocation(self.getTopLeft().offset(offset)) # Move top left corner by the same offset
    def setTopLeft(self, loc):
        """ Move this region so its top left corner is on ``loc`` """
        return self.setLocation(loc)
    def setTopRight(self, loc):
        """ Move this region so its top right corner is on ``loc`` """
        offset = self.getTopRight().getOffset(loc) # Calculate offset from current top right
        return self.setLocation(self.getTopLeft().offset(offset)) # Move top left corner by the same offset
    def setBottomLeft(self, loc):
        """ Move this region so its bottom left corner is on ``loc`` """
        offset = self.getBottomLeft().getOffset(loc) # Calculate offset from current bottom left
        return self.setLocation(self.getTopLeft().offset(offset)) # Move top left corner by the same offset
    def setBottomRight(self, loc):
        """ Move this region so its bottom right corner is on ``loc`` """
        offset = self.getBottomRight().getOffset(loc) # Calculate offset from current bottom right
        return self.setLocation(self.getTopLeft().offset(offset)) # Move top left corner by the same offset
    def setSize(self, w, h):
        """ Sets the new size of the region """
        self.setW(w)
        self.setH(h)
        return self
    def setRect(self, *args):
        """ Sets the rect of the region. Accepts the following arguments:

        setRect(rect_tuple)
        setRect(x, y, w, h)
        setRect(rect_region)
        """
        if len(args) == 1:
            if isinstance(args[0], tuple):
                x, y, w, h = args[0]
            elif isinstance(args[0], Region):
                x = Region.getX()
                y = Region.getY()
                w = Region.getW()
                h = Region.getH()
            else:
                raise TypeError("Unrecognized arguments for setRect")
        elif len(args) == 4:
            x, y, w, h = args
        else:
            raise TypeError("Unrecognized arguments for setRect")
        self.setX(x)
        self.setY(y)
        self.setW(w)
        self.setH(h)
        return self

    def saveScreenCapture(self, path=None, name=None):
        """ Saves the region's bitmap """
        bitmap = self.getBitmap()
        target_file = None
        if path is None and name is None:
            _, target_file = tempfile.mkstemp(".png")
        elif name is None:
            _, tpath = tempfile.mkstemp(".png")
            target_file = os.path.join(path, tfile)
        else:
            target_file = os.path.join(path, name+".png")
        cv2.imwrite(target_file, bitmap)
        return target_file
    def getLastScreenImage(self):
        """ Gets the last image taken on this region's screen """
        return self.getScreen().getLastScreenImageFromScreen()
    def saveLastScreenImage(self):
        """ Saves the last image taken on this region's screen to a temporary file """
        bitmap = self.getLastScreenImage()
        _, target_file = tempfile.mkstemp(".png")
        cv2.imwrite(target_file, bitmap)
    
    def asOffset(self):
        """ Returns bottom right corner as offset from top left corner """
        return Location(self.getW(), self.getH())

    def rightAt(self, offset=0):
        """ Returns point in the center of the region's right side (offset to the right
        by ``offset``) """
        return Location(self.getX() + self.getW() + offset, self.getY() + (self.getH() / 2))
    def leftAt(self, offset=0):
        """ Returns point in the center of the region's left side (offset to the left
        by negative ``offset``) """
        return Location(self.getX() + offset, self.getY() + (self.getH() / 2))
    def aboveAt(self, offset=0):
        """ Returns point in the center of the region's top side (offset to the top
        by negative ``offset``) """
        return Location(self.getX() + (self.getW() / 2), self.getY() + offset)
    def bottomAt(self, offset=0):
        """ Returns point in the center of the region's bottom side (offset to the bottom
        by ``offset``) """
        return Location(self.getX() + (self.getW() / 2), self.getY() + self.getH() + offset)

    def union(ur):
        """ Returns a new region that contains both this region and the specified region """
        x = min(self.getX(), ur.getX())
        y = min(self.getY(), ur.getY())
        w = max(self.getBottomRight().x, ur.getBottomRight().x) - x
        h = max(self.getBottomRight().y, ur.getBottomRight().y) - y
        return Region(x, y, w, h)
    def intersection(ir):
        """ Returns a new region that contains the overlapping portion of this region and the specified region (may be None) """
        x = max(self.getX(), ur.getX())
        y = max(self.getY(), ur.getY())
        w = min(self.getBottomRight().x, ur.getBottomRight().x) - x
        h = min(self.getBottomRight().y, ur.getBottomRight().y) - y
        if w > 0 and h > 0:
            return Region(x, y, w, h)
        return None
    def findAllByRow(self, target):
        """ Returns an array of rows in the region (defined by the raster), each
        row containing all matches in that row for the target pattern. """
        row_matches = []
        for row_index in range(self._raster[0]):
            row = self.getRow(row_index)
            row_matches[row_index] = row.findAll(target)
        return row_matches
    def findAllBycolumn(self, target):
        """ Returns an array of columns in the region (defined by the raster), each
        column containing all matches in that column for the target pattern. """
        column_matches = []
        for column_index in range(self._raster[1]):
            column = self.getRow(column_index)
            column_matches[column_index] = column.findAll(target)
        return column_matches
    def findBest(self, pattern):
        """ Returns the *best* match in the region (instead of the first match) """
        findFailedRetry = True
        while findFailedRetry:
            best_match = None
            all_matches = self.findAll(pattern)
            for match in all_matches:
                if best_match is None or best_match.getScore() < match.getScore():
                    best_match = match
            self._lastMatch = best_match
            if best_match is not None:
                break
            path = pattern.path if isinstance(pattern, Pattern) else pattern
            findFailedRetry = self._raiseFindFailed("Could not find pattern '{}'".format(path))
            if findFailedRetry:
                time.sleep(self._repeatWaitTime)
        return best_match
    def compare(self, image):
        """ Compares the region to the specified image """
        return exists(Pattern(image), 0)
    def findText(self, text, timeout=None):
        """ OCR function """
        raise NotImplementedError()
    def findAllText(self, text):
        """ OCR function """
        raise NotImplementedError()
    # Event Handlers

    def onAppear(self, pattern, handler=None):
        """ Registers an event to call ``handler`` when ``pattern`` appears in this region.

        The ``handler`` function should take one parameter, an ObserveEvent object
        (see below). This event is ignored in the future unless the handler calls
        the repeat() method on the provided ObserveEvent object.

        Returns the event's ID as a string.
        """
        return self._observer.register_event("APPEAR", pattern, handler)
    def onVanish(self, pattern, handler=None):
        """ Registers an event to call ``handler`` when ``pattern`` disappears from this region.

        The ``handler`` function should take one parameter, an ObserveEvent object
        (see below). This event is ignored in the future unless the handler calls
        the repeat() method on the provided ObserveEvent object.

        Returns the event's ID as a string.
        """
        return self._observer.register_event("VANISH", pattern, handler)
    def onChange(self, min_changed_pixels=None, handler=None):
        """ Registers an event to call ``handler`` when at least ``min_changed_pixels``
        change in this region.

        (Default for min_changed_pixels is set in Settings.ObserveMinChangedPixels)

        The ``handler`` function should take one parameter, an ObserveEvent object
        (see below). This event is ignored in the future unless the handler calls
        the repeat() method on the provided ObserveEvent object.

        Returns the event's ID as a string.
        """
        if isinstance(min_changed_pixels, int) and (callable(handler) or handler is None):
            return self._observer.register_event(
                "CHANGE",
                pattern=(min_changed_pixels, self.getBitmap()),
                handler=handler)
        elif (callable(min_changed_pixels) or min_changed_pixels is None) and (callable(handler) or handler is None):
            handler = min_changed_pixels or handler
            return self._observer.register_event(
                "CHANGE",
                pattern=(Settings.ObserveMinChangedPixels, self.getBitmap()),
                handler=handler)
        else:
            raise ValueError("Unsupported arguments for onChange method")
    def isChanged(self, min_changed_pixels, screen_state):
        """ Returns true if at least ``min_changed_pixels`` are different between
        ``screen_state`` and the current state.
        """
        r = self.clipRegionToScreen()
        current_state = r.getBitmap()
        diff = numpy.subtract(current_state, screen_state)
        return (numpy.count_nonzero(diff) >= min_changed_pixels)

    def observe(self, seconds=None):
        """ Begins the observer loop (synchronously).

        Loops for ``seconds`` or until this region's stopObserver() method is called.
        If ``seconds`` is None, the observer loop cycles until stopped. If this
        method is called while the observer loop is already running, it returns False.

        Returns True if the observer could be started, False otherwise.
        """
        # Check if observer is already running
        if self._observer.isRunning:
            return False # Could not start

        # Set timeout
        if seconds is not None:
            timeout = time.time() + seconds
        else:
            timeout = None

        # Start observe loop
        while (not self._observer.isStopped) and (seconds is None or time.time() < timeout):
            # Check registered events
            self._observer.check_events()
            # Sleep for scan rate
            time.sleep(1/self.getObserveScanRate())
        return True
    def getObserveScanRate(self):
        """ Gets the number of times per second the observe loop should run """
        return self._observeScanRate if self._observeScanRate is not None else Settings.ObserveScanRate
    def setObserveScanRate(self, scan_rate):
        """ Set the number of times per second the observe loop should run """
        self._observeScanRate = scan_rate
    def getRepeatWaitTime(self):
        """ Gets the wait time before repeating a search """
        return self._repeatWaitTime
    def setRepeatWaitTime(self, wait_time):
        """ Sets the wait time before repeating a search """
        self._repeatWaitTime = wait_time
    def observeInBackground(self, seconds=None):
        """ As Region.observe(), but runs in a background process, allowing the rest
        of your script to continue.

        Note that the subprocess operates on *copies* of the usual objects, not the original
        Region object itself for example. If your event handler needs to share data with your
        main process, check out the documentation for the ``multiprocessing`` module to set up
        shared memory.
        """
        if self._observer.isRunning:
            return False
        self._observer_process = multiprocessing.Process(target=self.observe, args=(seconds,))
        self._observer_process.start()
        return True
    def stopObserver(self):
        """ Stops this region's observer loop.

        If this is running in a subprocess, the subprocess will end automatically.
        """
        self._observer.isStopped = True
        self._observer.isRunning = False

    def hasObserver(self):
        """ Check whether at least one event is registered for this region.

        The observer may or may not be running.
        """
        return self._observer.has_events()
    def isObserving(self):
        """ Check whether an observer is running for this region """
        return self._observer.isRunning
    def hasEvents(self):
        """ Check whether any events have been caught for this region """
        return len(self._observer.caught_events) > 0
    def getEvents(self):
        """ Returns a list of all events that have occurred.

        Empties the internal queue.
        """
        caught_events = self._observer.caught_events
        self._observer.caught_events = []
        for event in caught_events:
            self._observer.activate_event(event["name"])
        return caught_events
    def getEvent(self, name):
        """ Returns the named event.

        Removes it from the internal queue.
        """
        to_return = None
        for event in self._observer.caught_events:
            if event["name"] == name:
                to_return = event
                break
        if to_return:
            self._observer.caught_events.remove(to_return)
            self._observer.activate_event(to_return["name"])
        return to_return
    def setInactive(self, name):
        """ The specified event is ignored until reactivated
        or until the observer restarts.
        """
        self._observer.inactivate_event(name)
    def setActive(self, name):
        """ Activates an inactive event type. """
        self._observer.activate_event(name)
    def _raiseImageMissing(self, pattern):
        """ Builds an ImageMissing event and triggers the default handler (or the custom handler,
        if one has been specified). Returns True if throwing method should retry, False if it
        should skip, and throws an exception if it should abort. """
        event = ImageMissingEvent(self, pattern=pattern, event_type="MISSING")

        if self._imageMissingHandler is not None:
            self._imageMissingHandler(event)
        response = (event._response or self._findFailedResponse)
        #if response == "PROMPT": # Prompt not valid for ImageMissing error
        #    response = _findFailedPrompt(pattern)
        if response == "ABORT":
            raise FindFailed(event)
        elif response == "SKIP":
            return False
        elif response == "RETRY":
            return True
    def setImageMissingHandler(self, handler):
        """ Set a handler to receive ImageMissing events (instead of triggering
        an exception). """
        if not callable(handler):
            raise ValueError("Expected ImageMissing handler to be a callable")
        self._imageMissingHandler = handler
    ## FindFailed event handling ##

    # Constants
    ABORT = "ABORT"
    SKIP = "SKIP"
    PROMPT = "PROMPT"
    RETRY = "RETRY"

    def setFindFailedResponse(self, response):
        """ Set the response to a FindFailed exception in this region.
        
        Can be ABORT, SKIP, PROMPT, or RETRY. """
        valid_responses = ("ABORT", "SKIP", "PROMPT", "RETRY")
        if response not in valid_responses:
            raise ValueError("Invalid response - expected one of ({})".format(", ".join(valid_responses)))
        self._findFailedResponse = response
    def setFindFailedHandler(self, handler):
        """ Set a handler to receive FindFailed events (instead of triggering
        an exception). """
        if not callable(handler):
            raise ValueError("Expected FindFailed handler to be a callable")
        self._findFailedHandler = handler
    def getFindFailedResponse(self):
        """ Returns the current default response to a FindFailed exception """
        return self._findFailedResponse
    def setThrowException(self, setting):
        """ Defines whether an exception should be thrown for FindFailed operations.

        ``setting`` should be True or False. """
        if setting:
            self._throwException = True
            self._findFailedResponse = "ABORT"
        else:
            self._throwException = False
            self._findFailedResponse = "SKIP"
    def getThrowException(self):
        """ Returns True if an exception will be thrown for FindFailed operations,
        False otherwise. """
        return self._throwException
    def _raiseFindFailed(self, pattern):
        """ Builds a FindFailed event and triggers the default handler (or the custom handler,
        if one has been specified). Returns True if throwing method should retry, False if it
        should skip, and throws an exception if it should abort. """
        event = FindFailedEvent(self, pattern=pattern, event_type="FINDFAILED")

        if self._findFailedHandler is not None:
            self._findFailedHandler(event)
        response = (event._response or self._findFailedResponse)
        if response == "PROMPT":
            response = _findFailedPrompt(pattern)

        if response == "ABORT":
            raise FindFailed(event)
        elif response == "SKIP":
            return False
        elif response == "RETRY":
            return True
    def _findFailedPrompt(self, pattern):
        ret_value = tkmb.showerror(
            title="Sikuli Prompt", 
            message="Could not find target '{}'. Abort, retry, or skip?".format(pattern), 
            type=tkmb.ABORTRETRYIGNORE)
        value_map = {
            "abort": "ABORT",
            "retry": "RETRY",
            "ignore": "SKIP"
        }
        return value_map[ret_value]

class Observer(object):
    def __init__(self, region):
        self._supported_events = ("APPEAR", "VANISH", "CHANGE")
        self._region = region
        self._events = {}
        self.isStopped = False
        self.isRunning = False
        self.caught_events = []

    def inactivate_event(self, name):
        if name in self._events:
            self._events[name].active = False

    def activate_event(self, name):
        if name in self._events:
            self._events[name].active = True

    def has_events(self):
        return len(self._events) > 0

    def register_event(self, event_type, pattern, handler):
        """ When ``event_type`` is observed for ``pattern``, triggers ``handler``.

        For "CHANGE" events, ``pattern`` should be a tuple of ``min_changed_pixels`` and
        the base screen state.
        """
        if event_type not in self._supported_events:
            raise ValueError("Unsupported event type {}".format(event_type))
        if event_type != "CHANGE" and not isinstance(pattern, Pattern) and not isinstance(pattern, basestring):
            raise ValueError("Expected pattern to be a Pattern or string")
        if event_type == "CHANGE" and not (len(pattern)==2 and isinstance(pattern[0], int) and isinstance(pattern[1], numpy.ndarray)):
            raise ValueError("For \"CHANGE\" events, ``pattern`` should be a tuple of ``min_changed_pixels`` and the base screen state.")

        # Create event object
        event = {
            "pattern": pattern,
            "event_type": event_type,
            "count": 0,
            "handler": handler,
            "name": uuid.uuid4(),
            "active": True
        }
        self._events[event["name"]] = event
        return event["name"]

    def check_events(self):
        for event_name in self._events.keys():
            event = self._events[event_name]
            if not event["active"]:
                continue
            event_type = event["event_type"]
            pattern = event["pattern"]
            handler = event["handler"]
            if event_type == "APPEAR" and self._region.exists(event["pattern"], 0):
                # Call the handler with a new ObserveEvent object
                appear_event = ObserveEvent(self._region,
                                            count=event["count"],
                                            pattern=event["pattern"],
                                            event_type=event["event_type"])
                if callable(handler):
                    handler(appear_event)
                self.caught_events.append(appear_event)
                event["count"] += 1
                # Event handlers are inactivated after being caught once
                event["active"] = False
            elif event_type == "VANISH" and not self._region.exists(event["pattern"], 0):
                # Call the handler with a new ObserveEvent object
                vanish_event = ObserveEvent(self._region,
                                            count=event["count"],
                                            pattern=event["pattern"],
                                            event_type=event["event_type"])
                if callable(handler):
                    handler(vanish_event)
                else:
                    self.caught_events.append(vanish_event)
                event["count"] += 1
                # Event handlers are inactivated after being caught once
                event["active"] = False
            # For a CHANGE event, ``pattern`` is a tuple of
            # (min_pixels_changed, original_region_state)
            elif event_type == "CHANGE" and self._region.isChanged(*event["pattern"]):
                # Call the handler with a new ObserveEvent object
                change_event = ObserveEvent(self._region,
                                            count=event["count"],
                                            pattern=event["pattern"],
                                            event_type=event["event_type"])
                if callable(handler):
                    handler(change_event)
                else:
                    self.caught_events.append(change_event)
                event["count"] += 1
                # Event handlers are inactivated after being caught once
                event["active"] = False


class ObserveEvent(object):
    def __init__(self, region=None, count=0, pattern=None, match=None, event_type="GENERIC"):
        self._valid_types = ["APPEAR", "VANISH", "CHANGE", "GENERIC", "FINDFAILED", "MISSING"]
        self._type = event_type
        self._region = region
        self._pattern = pattern
        self._match = match
        self._count = count
    def getType(self):
        return self._type
    def isAppear(self):
        return (self._type == "APPEAR")
    def isVanish(self):
        return (self._type == "VANISH")
    def isChange(self):
        return (self._type == "CHANGE")
    def isGeneric(self):
        return (self._type == "GENERIC")
    def isFindFailed(self):
        return (self._type == "FINDFAILED")
    def isMissing(self):
        return (self._type == "MISSING")
    def getRegion(self):
        return self._region
    def getPattern(self):
        return self._pattern
    def getImage(self):
        valid_types = ["APPEAR", "VANISH", "FINDFAILED", "MISSING"]
        if self._type not in valid_types:
            raise TypeError("This is a(n) {} event, but method getImage is only valid for the following event types: ({})".format(self._type, ", ".join(valid_types)))
        elif self._pattern is None:
            raise ValueError("This event's pattern was not set!")
        return cv2.imread(self._pattern.path)
    def getMatch(self):
        valid_types = ["APPEAR", "VANISH"]
        if self._type not in valid_types:
            raise TypeError("This is a(n) {} event, but method getMatch is only valid for the following event types: ({})".format(self._type, ", ".join(valid_types)))
        elif self._match is None:
            raise ValueError("This event's match was not set!")
        return self._match
    def getChanges(self):
        valid_types = ["CHANGE"]
        if self._type not in valid_types:
            raise TypeError("This is a(n) {} event, but method getChanges is only valid for the following event types: ({})".format(self._type, ", ".join(valid_types)))
        elif self._match is None:
            raise ValueError("This event's match was not set!")
        return self._match
    def getCount(self):
        return self._count
class FindFailedEvent(ObserveEvent):
    def __init__(self, *args, **kwargs):
        ObserveEvent.__init__(self, *args, **kwargs)
        self._response = None
    def setResponse(response):
        valid_responses = ("ABORT", "SKIP", "PROMPT", "RETRY")
        if response not in valid_responses:
            raise ValueError("Invalid response - expected one of ({})".format(", ".join(valid_responses)))
        else:
            self._response = response
    def __repr__(self):
        if hasattr(self._pattern, "path"):
            return self._pattern.path
        return self._pattern
class ImageMissingEvent(ObserveEvent):
    def __init__(self, *args, **kwargs):
        ObserveEvent.__init__(self, *args, **kwargs)
        self._response = None
    def setResponse(response):
        valid_responses = ("ABORT", "SKIP", "RETRY")
        if response not in valid_responses:
            raise ValueError("Invalid response - expected one of ({})".format(", ".join(valid_responses)))
        else:
            self._response = response
    def __repr__(self):
        if hasattr(self._pattern, "path"):
            return self._pattern.path
        return self._pattern
class Match(Region):
    """ Extended Region object with additional data on click target, match score """
    def __init__(self, score, target, rect):
        super(Match, self).__init__(rect[0][0], rect[0][1], rect[1][0], rect[1][1])
        self._score = float(score)
        if not target or not isinstance(target, Location):
            raise TypeError("Match expected target to be a Location object")
        self._target = target

    def getScore(self):
        """ Returns confidence score of the match """
        return self._score

    def getTarget(self):
        """ Returns the location of the match click target (center by default, but may be offset) """
        return self.getCenter().offset(self._target.x, self._target.y)

    def __repr__(self):
        return "Match[{},{} {}x{}] score={:2f}, target={}".format(self.x, self.y, self.w, self.h, self._score, self._target.getTuple())

class Screen(Region):
    """ Individual screen objects can be created for each monitor in a multi-monitor system.

    Screens are indexed according to the system order. 0 is the primary monitor (display 1),
    1 is the next monitor, etc.

    Lackey also makes it possible to search all screens as a single "virtual screen," arranged
    according to the system's settings. Screen(-1) returns this virtual screen. Note that the
    larger your search region is, the slower your search will be, so it's best practice to adjust
    your region to the particular area of the screen where you know your target will be.

    Note that Sikuli is inconsistent in identifying screens. In Windows, Sikuli identifies the
    first hardware monitor as Screen(0) rather than the actual primary monitor. However, on OS X
    it follows the latter convention. We've opted to make Screen(0) the actual primary monitor
    (wherever the Start Menu/System Menu Bar is) across the board.
    """
    primaryScreen = 0
    def __init__(self, screenId=None):
        """ Defaults to the main screen. """
        if not isinstance(screenId, int) or screenId < -1 or screenId >= len(PlatformManager.getScreenDetails()):
            screenId = Screen.getPrimaryID()
        self._screenId = screenId
        x, y, w, h = self.getBounds()
        self.lastScreenImage = None
        super(Screen, self).__init__(x, y, w, h)
    @classmethod
    def getNumberScreens(cls):
        """ Get the number of screens in a multi-monitor environment at the time the script is running """
        return len(PlatformManager.getScreenDetails())
    def getBounds(self):
        """ Returns bounds of screen as (x, y, w, h) """
        return PlatformManager.getScreenBounds(self._screenId)
    def capture(self, *args): #x=None, y=None, w=None, h=None):
        """ Captures the region as an image """
        if len(args) == 0:
            # Capture screen region
            region = self
        elif isinstance(args[0], Region):
            # Capture specified region
            region = args[0]
        elif isinstance(args[0], tuple):
            # Capture region defined by specified tuple
            region = Region(*args[0])
        elif isinstance(args[0], basestring):
            # Interactive mode
            raise NotImplementedError("Interactive capture mode not defined")
        elif isinstance(args[0], int):
            # Capture region defined by provided x,y,w,h
            region = Region(*args)
        self.lastScreenImage = region.getBitmap()
        return self.lastScreenImage
    captureForHighlight = capture
    def selectRegion(self, text=""):
        """ Not yet implemented """
        raise NotImplementedError()
    def doPrompt(self, message, obs):
        """ Not yet implemented """
        raise NotImplementedError()
    def closePrompt(self):
        """ Not yet implemented """
        raise NotImplementedError()
    def resetPrompt(self):
        """ Not yet implemented """
        raise NotImplementedError()
    def hasPrompt(self):
        """ Not yet implemented """
        raise NotImplementedError()
    def userCapture(self, message=""):
        """ Not yet implemented """
        raise NotImplementedError()
    def saveCapture(self, name, reg=None):
        """ Not yet implemented """
        raise NotImplementedError()
    def getCurrentID(self):
        """ Returns screen ID """
        return self._screenId
    getID = getCurrentID
    @classmethod
    def getPrimaryID(cls):
        """ Returns primary screen ID """
        return cls.primaryScreen
    @classmethod
    def getPrimaryScreen(cls):
        """ Returns the primary screen """
        return Screen(cls.primaryScreen)
    @classmethod
    def showMonitors(cls):
        """ Prints debug information about currently detected screens """
        Debug.info("*** monitor configuration [ {} Screen(s)] ***".format(cls.getNumberScreens()))
        Debug.info("*** Primary is Screen {}".format(cls.primaryScreen))
        for index, screen in enumerate(PlatformManager.getScreenDetails()):
            Debug.info("Screen {}: ({}, {}, {}, {})".format(index, *screen["rect"]))
        Debug.info("*** end monitor configuration ***")
    def resetMonitors(self):
        """ Recalculates screen based on changed monitor setup """
        Debug.error("*** BE AWARE: experimental - might not work ***")
        Debug.error("Re-evaluation of the monitor setup has been requested")
        Debug.error("... Current Region/Screen objects might not be valid any longer")
        Debug.error("... Use existing Region/Screen objects only if you know what you are doing!")
        self.__init__(self._screenId)
        self.showMonitors()
    def newRegion(self, loc, width, height):
        """ Creates a new region on the current screen at the specified offset with the specified
        width and height. """
        return Region.create(self.getTopLeft().offset(loc), width, height)
    def getLastScreenImageFromScreen(self):
        """ Returns the last captured image from this screen """
        return self.lastScreenImage
    def newLocation(self, loc):
        """ Creates a new location on this screen, with the same offset it would have had on the
        default screen """
        return Location(loc).copyTo(self)
    def showTarget(self):
        """ Not yet implemented """
        raise NotImplementedError()