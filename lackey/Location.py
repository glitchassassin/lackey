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

    def __repr__(self):
        return "(Location object at ({},{}))".format(self.x, self.y)

