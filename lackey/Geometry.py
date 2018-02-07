import time

class Location(object):
    """ Basic 2D point object """
    def __init__(self, x, y):
        self.setLocation(x, y)

    def getX(self):
        """ Returns the X-component of the location """
        return self.x
    def getY(self):
        """ Returns the Y-component of the location """
        return self.y

    def setLocation(self, x, y):
        """Set the location of this object to the specified coordinates."""
        self.x = int(x)
        self.y = int(y)
        return self
    moveTo = setLocation
    move = setLocation
    def offset(self, dx, dy):
        """Get a new location which is dx and dy pixels away horizontally and vertically
        from the current location.
        """
        return Location(self.x+dx, self.y+dy)

    def above(self, dy):
        """Get a new location dy pixels vertically above the current location."""
        return Location(self.x, self.y-dy)
    def below(self, dy):
        """Get a new location dy pixels vertically below the current location."""
        return Location(self.x, self.y+dy)
    def left(self, dx):
        """Get a new location dx pixels horizontally to the left of the current location."""
        return Location(self.x-dx, self.y)
    def right(self, dx):
        """Get a new location dx pixels horizontally to the right of the current location."""
        return Location(self.x+dx, self.y)

    def getTuple(self):
        """ Returns coordinates as a tuple (for some PlatformManager methods) """
        return (self.x, self.y)
    def getScreen(self):
        """ Returns an instance of the ``Screen`` object this Location is inside.

        Returns None if the Location isn't positioned in any screen.
        """
        from .RegionMatching import PlatformManager, Screen
        screens = PlatformManager.getScreenDetails()
        for screen in screens:
            s_x, s_y, s_w, s_h = screen["rect"]
            if (self.x >= s_x) and (self.x < s_x + s_w) and (self.y >= s_y) and (self.y < s_y + s_h):
                # Top left corner is inside screen region
                return Screen(screens.index(screen))
        return None # Could not find matching screen
    def getMonitor(self):
        """ Returns an instance of the ``Screen`` object this Location is inside.

        Returns the primary screen if the Location isn't positioned in any screen.
        """
        from .RegionMatching import Screen
        scr = self.getScreen()
        return scr if scr is not None else Screen(0)
    def getColor(self):
        scr = self.getScreen()
        if scr is None:
            return None
        offset = scr.getTopLeft().getOffset(self)
        return self.getScreen().getBitmap()[offset.y, offset.x]
    def getOffset(self, loc):
        """ Returns the offset between the given point and this point """
        return Location(loc.x - self.x, loc.y - self.y)
    def grow(self, *args):
        """ Creates a region around the given point Valid arguments:

        * ``grow(wh)`` - Creates a region centered on this point with a width and height of ``wh``.
        * ``grow(w, h)`` - Creates a region centered on this point with a width of ``w`` and height
          of ``h``.
        * ``grow(Region.CREATE_X_DIRECTION, Region.CREATE_Y_DIRECTION, w, h)`` - Creates a region
          with this point as one corner, expanding in the specified direction
        
        """
        if len(args) == 1:
            return Region.grow(self.x, self.y, args[0], args[0])
        elif len(args) == 2:
            return Region(self.x, self.y, args[0], args[1])
        elif len(args) == 4:
            return Region.create(self, *args)
        else:
            raise ValueError("Unrecognized arguments for grow")
    def translate(self, dx, dy):
        self.x += dx
        self.y += dy
        return this
    def copyTo(self, screen):
        """ Creates a new point with the same offset on the target screen as this point has on the
        current screen """
        from .RegionMatching import Screen
        if not isinstance(screen, Screen):
            screen = RegionMatching.Screen(screen)
        return screen.getTopLeft().offset(self.getScreen().getTopLeft().getOffset(self))
    def hover(self):
        from .RegionMatching import Mouse
        RegionMatching.Mouse.moveSpeed(self)
        return self
    def click(self):
        from .RegionMatching import Mouse
        RegionMatching.Mouse.moveSpeed(self)
        RegionMatching.Mouse.click()
        return self
    def doubleClick(self):
        from .RegionMatching import Mouse
        RegionMatching.Mouse.moveSpeed(self)
        RegionMatching.Mouse.click()
        time.sleep(0.1)
        RegionMatching.Mouse.click()
        return self
    def click(self):
        from .RegionMatching import Mouse
        RegionMatching.Mouse.moveSpeed(self)
        RegionMatching.Mouse.click(button=RegionMatching.Mouse.RIGHT)
        return self
    def __repr__(self):
        return "(Location object at ({},{}))".format(self.x, self.y)
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.x == other.x and self.y == other.y
        return False
    def __ne__(self, other):
        return not self.__eq__(other)