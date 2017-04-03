import inspect
import subprocess
import unittest
import time
import sys
import os
import lackey

class TestLocationMethods(unittest.TestCase):
    def setUp(self):
        self.test_loc = lackey.Location(10, 11)

    def test_getters(self):
        self.assertEqual(self.test_loc.getX(), 10)
        self.assertEqual(self.test_loc.getY(), 11)
        self.assertEqual(self.test_loc.getTuple(), (10,11))
        self.assertEqual(str(self.test_loc), "(Location object at (10,11))")

    def test_set_location(self):
        self.test_loc.setLocation(3, 5)
        self.assertEqual(self.test_loc.getX(), 3)
        self.assertEqual(self.test_loc.getY(), 5)
        self.test_loc.setLocation(-3, 1009)
        self.assertEqual(self.test_loc.getX(), -3)
        self.assertEqual(self.test_loc.getY(), 1009)

    def test_offsets(self):
        offset = self.test_loc.offset(3, -5)
        self.assertEqual(offset.getTuple(), (13,6))
        offset = self.test_loc.above(10)
        self.assertEqual(offset.getTuple(), (10,1))
        offset = self.test_loc.below(16)
        self.assertEqual(offset.getTuple(), (10,27))
        offset = self.test_loc.right(5)
        self.assertEqual(offset.getTuple(), (15,11))
        offset = self.test_loc.left(7)
        self.assertEqual(offset.getTuple(), (3,11))

class TestPatternMethods(unittest.TestCase):
    def setUp(self):
        self.pattern = lackey.Pattern("tests\\test_pattern.png")
    
    def test_defaults(self):
        self.assertEqual(self.pattern.similarity, 0.7)
        self.assertIsInstance(self.pattern.offset, lackey.Location)
        self.assertEqual(self.pattern.offset.getTuple(), (0,0))
        self.assertEqual(self.pattern.path[-len("tests\\test_pattern.png"):], "tests\\test_pattern.png")

    def test_setters(self):
        test_pattern = self.pattern.similar(0.5)
        self.assertEqual(test_pattern.similarity, 0.5)
        self.assertEqual(test_pattern.path[-len("tests\\test_pattern.png"):], "tests\\test_pattern.png")
        test_pattern = self.pattern.exact()
        self.assertEqual(test_pattern.similarity, 1.0)
        self.assertEqual(test_pattern.path[-len("tests\\test_pattern.png"):], "tests\\test_pattern.png")
        test_pattern = self.pattern.targetOffset(3, 5)
        self.assertEqual(test_pattern.similarity, 0.7)
        self.assertEqual(test_pattern.path[-len("tests\\test_pattern.png"):], "tests\\test_pattern.png")
        self.assertEqual(test_pattern.offset.getTuple(), (3,5))

    def test_getters(self):
        self.assertEqual(self.pattern.getFilename()[-len("tests\\test_pattern.png"):], "tests\\test_pattern.png")
        self.assertEqual(self.pattern.getTargetOffset().getTuple(), (0,0))
class TestObserverEventMethods(unittest.TestCase):
    def setUp(self):
        self.r = lackey.Region()
        self.generic_event = lackey.ObserveEvent(self.r, event_type="GENERIC")
        self.appear_event = lackey.ObserveEvent(self.r, event_type="APPEAR")
        self.vanish_event = lackey.ObserveEvent(self.r, event_type="VANISH")
        self.change_event = lackey.ObserveEvent(self.r, event_type="CHANGE")
    
    def test_validators(self):
        self.assertTrue(self.generic_event.isGeneric())
        self.assertFalse(self.generic_event.isAppear())
        self.assertTrue(self.appear_event.isAppear())
        self.assertFalse(self.appear_event.isVanish())
        self.assertTrue(self.vanish_event.isVanish())
        self.assertFalse(self.vanish_event.isChange())
        self.assertTrue(self.change_event.isChange())
        self.assertFalse(self.change_event.isGeneric())

    def test_getters(self):
        self.assertEqual(self.generic_event.getRegion(), self.r)
        self.assertRaises(self.generic_event.getImage())
        self.assertRaises(self.generic_event.getMatch())
        self.assertRaises(self.generic_event.getChanges())

class TestInterfaces(unittest.TestCase):
    """ This class tests Sikuli interface compatibility on a surface level.
    Makes sure the class has the correct methods, and that the methods have the
    expected number of arguments.
    """
    def test_app_interface(self):
        """ Checking App class interface methods """
        ## Class methods
        self.assertHasMethod(lackey.App, "pause", 2)
        self.assertHasMethod(lackey.App, "open", 2)
        self.assertHasMethod(lackey.App, "focus", 2)
        self.assertHasMethod(lackey.App, "close", 2)
        self.assertHasMethod(lackey.App, "focusedWindow", 1)

        ## Instance methods
        app = lackey.App()
        self.assertHasMethod(app, "__init__", 2)
        self.assertHasMethod(app, "isRunning", 2)
        self.assertHasMethod(app, "hasWindow", 1)
        self.assertHasMethod(app, "getWindow", 1)
        self.assertHasMethod(app, "getPID", 1)
        self.assertHasMethod(app, "getName", 1)
        self.assertHasMethod(app, "setUsing", 2)
        self.assertHasMethod(app, "open", 2)
        self.assertHasMethod(app, "focus", 1)
        self.assertHasMethod(app, "close", 1)
        self.assertHasMethod(app, "window", 2)

    def test_region_interface(self):
        """ Checking Region class interface methods """
        self.assertHasMethod(lackey.Region, "__init__", 1) # uses *args
        self.assertHasMethod(lackey.Region, "setX", 2)
        self.assertHasMethod(lackey.Region, "setY", 2)
        self.assertHasMethod(lackey.Region, "setW", 2)
        self.assertHasMethod(lackey.Region, "setH", 2)
        self.assertHasMethod(lackey.Region, "moveTo", 2)
        self.assertHasMethod(lackey.Region, "setROI", 1)   # uses *args
        self.assertHasMethod(lackey.Region, "setRect", 1)  # uses *args
        self.assertHasMethod(lackey.Region, "morphTo", 2)
        self.assertHasMethod(lackey.Region, "getX", 1)
        self.assertHasMethod(lackey.Region, "getY", 1)
        self.assertHasMethod(lackey.Region, "getW", 1)
        self.assertHasMethod(lackey.Region, "getH", 1)
        self.assertHasMethod(lackey.Region, "getTopLeft", 1)
        self.assertHasMethod(lackey.Region, "getTopRight", 1)
        self.assertHasMethod(lackey.Region, "getBottomLeft", 1)
        self.assertHasMethod(lackey.Region, "getBottomRight", 1)
        self.assertHasMethod(lackey.Region, "getScreen", 1)
        self.assertHasMethod(lackey.Region, "getLastMatch", 1)
        self.assertHasMethod(lackey.Region, "getLastMatches", 1)
        self.assertHasMethod(lackey.Region, "getTime", 1)
        self.assertHasMethod(lackey.Region, "isRegionValid", 1)
        self.assertHasMethod(lackey.Region, "setAutoWaitTimeout", 2)
        self.assertHasMethod(lackey.Region, "getAutoWaitTimeout", 1)
        self.assertHasMethod(lackey.Region, "setWaitScanRate", 2)
        self.assertHasMethod(lackey.Region, "getWaitScanRate", 1)
        self.assertHasMethod(lackey.Region, "get", 2)
        self.assertHasMethod(lackey.Region, "getRow", 3)
        self.assertHasMethod(lackey.Region, "getCol", 3)
        self.assertHasMethod(lackey.Region, "setRows", 2)
        self.assertHasMethod(lackey.Region, "setCols", 2)
        self.assertHasMethod(lackey.Region, "setRaster", 3)
        self.assertHasMethod(lackey.Region, "getCell", 3)
        self.assertHasMethod(lackey.Region, "isRasterValid", 1)
        self.assertHasMethod(lackey.Region, "getRows", 1)
        self.assertHasMethod(lackey.Region, "getCols", 1)
        self.assertHasMethod(lackey.Region, "getRowH", 1)
        self.assertHasMethod(lackey.Region, "getColW", 1)
        self.assertHasMethod(lackey.Region, "offset", 3)
        self.assertHasMethod(lackey.Region, "inside", 1)
        self.assertHasMethod(lackey.Region, "grow", 3)
        self.assertHasMethod(lackey.Region, "nearby", 2)
        self.assertHasMethod(lackey.Region, "above", 2)
        self.assertHasMethod(lackey.Region, "below", 2)
        self.assertHasMethod(lackey.Region, "left", 2)
        self.assertHasMethod(lackey.Region, "right", 2)
        self.assertHasMethod(lackey.Region, "find", 2)
        self.assertHasMethod(lackey.Region, "findAll", 2)
        self.assertHasMethod(lackey.Region, "wait", 3)
        self.assertHasMethod(lackey.Region, "waitVanish", 3)
        self.assertHasMethod(lackey.Region, "exists", 3)
        self.assertHasMethod(lackey.Region, "click", 3)
        self.assertHasMethod(lackey.Region, "doubleClick", 3)
        self.assertHasMethod(lackey.Region, "rightClick", 3)
        self.assertHasMethod(lackey.Region, "highlight", 2)
        self.assertHasMethod(lackey.Region, "hover", 2)
        self.assertHasMethod(lackey.Region, "dragDrop", 4)
        self.assertHasMethod(lackey.Region, "drag", 2)
        self.assertHasMethod(lackey.Region, "dropAt", 3)
        self.assertHasMethod(lackey.Region, "type", 1) 		# Uses *args
        self.assertHasMethod(lackey.Region, "paste", 1)		# Uses *args
        self.assertHasMethod(lackey.Region, "text", 1)
        self.assertHasMethod(lackey.Region, "mouseDown", 2)
        self.assertHasMethod(lackey.Region, "mouseUp", 2)
        self.assertHasMethod(lackey.Region, "mouseMove", 3)
        self.assertHasMethod(lackey.Region, "wheel", 1)     # Uses *args
        self.assertHasMethod(lackey.Region, "keyDown", 2)
        self.assertHasMethod(lackey.Region, "keyUp", 2)
        # Event Handler Methods
        self.assertHasMethod(lackey.Region, "onAppear", 3)
        self.assertHasMethod(lackey.Region, "onVanish", 3)
        self.assertHasMethod(lackey.Region, "onChange", 3)
        self.assertHasMethod(lackey.Region, "isChanged", 3)
        self.assertHasMethod(lackey.Region, "observe", 2)
        self.assertHasMethod(lackey.Region, "observeInBackground", 2)
        self.assertHasMethod(lackey.Region, "stopObserver", 1)
        self.assertHasMethod(lackey.Region, "hasObserver", 1)
        self.assertHasMethod(lackey.Region, "isObserving", 1)
        self.assertHasMethod(lackey.Region, "hasEvents", 1)
        self.assertHasMethod(lackey.Region, "getEvents", 1)
        self.assertHasMethod(lackey.Region, "getEvent", 2)
        self.assertHasMethod(lackey.Region, "setInactive", 2)
        self.assertHasMethod(lackey.Region, "setActive", 2)
        # FindFailed event methods
        self.assertHasMethod(lackey.Region, "setFindFailedResponse", 2)
        self.assertHasMethod(lackey.Region, "setFindFailedHandler", 2)
        self.assertHasMethod(lackey.Region, "getFindFailedResponse", 1)
        self.assertHasMethod(lackey.Region, "setThrowException", 2)
        self.assertHasMethod(lackey.Region, "getThrowException", 1)
        self.assertHasMethod(lackey.Region, "_raiseFindFailed", 2)
        self.assertHasMethod(lackey.Region, "_findFailedPrompt", 2)

    def test_pattern_interface(self):
        """ Checking App class interface methods """
        self.assertHasMethod(lackey.Pattern, "__init__", 2)
        self.assertHasMethod(lackey.Pattern, "similar", 2)
        self.assertHasMethod(lackey.Pattern, "exact", 1)
        self.assertHasMethod(lackey.Pattern, "targetOffset", 3)
        self.assertHasMethod(lackey.Pattern, "getFilename", 1)
        self.assertHasMethod(lackey.Pattern, "getTargetOffset", 1)

    def test_match_interface(self):
        """ Checking Match class interface methods """
        self.assertHasMethod(lackey.Match, "getScore", 1)
        self.assertHasMethod(lackey.Match, "getTarget", 1)

    def test_location_interface(self):
        """ Checking Match class interface methods """
        self.assertHasMethod(lackey.Location, "__init__", 3)
        self.assertHasMethod(lackey.Location, "getX", 1)
        self.assertHasMethod(lackey.Location, "getY", 1)
        self.assertHasMethod(lackey.Location, "setLocation", 3)
        self.assertHasMethod(lackey.Location, "offset", 3)
        self.assertHasMethod(lackey.Location, "above", 2)
        self.assertHasMethod(lackey.Location, "below", 2)
        self.assertHasMethod(lackey.Location, "left", 2)
        self.assertHasMethod(lackey.Location, "right", 2)

    def test_screen_interface(self):
        """ Checking Match class interface methods """
        self.assertHasMethod(lackey.Screen, "__init__", 2)
        self.assertHasMethod(lackey.Screen, "getNumberScreens", 1)
        self.assertHasMethod(lackey.Screen, "getBounds", 1)
        self.assertHasMethod(lackey.Screen, "capture", 1) 			# Uses *args
        self.assertHasMethod(lackey.Screen, "selectRegion", 2)

    def test_platform_manager_interface(self):
        """ Checking Platform Manager interface methods """

        ## Screen methods
        self.assertHasMethod(lackey.PlatformManagerWindows, "getBitmapFromRect", 5)
        self.assertHasMethod(lackey.PlatformManagerWindows, "getScreenBounds", 2)
        self.assertHasMethod(lackey.PlatformManagerWindows, "getScreenDetails", 1)
        self.assertHasMethod(lackey.PlatformManagerWindows, "isPointVisible", 3)

        ## Clipboard methods
        self.assertHasMethod(lackey.PlatformManagerWindows, "osCopy", 1)
        self.assertHasMethod(lackey.PlatformManagerWindows, "osPaste", 1)

        ## Window methods
        self.assertHasMethod(lackey.PlatformManagerWindows, "getWindowByTitle", 3)
        self.assertHasMethod(lackey.PlatformManagerWindows, "getWindowByPID", 3)
        self.assertHasMethod(lackey.PlatformManagerWindows, "getWindowRect", 2)
        self.assertHasMethod(lackey.PlatformManagerWindows, "focusWindow", 2)
        self.assertHasMethod(lackey.PlatformManagerWindows, "getWindowTitle", 2)
        self.assertHasMethod(lackey.PlatformManagerWindows, "getWindowPID", 2)
        self.assertHasMethod(lackey.PlatformManagerWindows, "getForegroundWindow", 1)

        ## Process methods
        self.assertHasMethod(lackey.PlatformManagerWindows, "isPIDValid", 2)
        self.assertHasMethod(lackey.PlatformManagerWindows, "killProcess", 2)
        self.assertHasMethod(lackey.PlatformManagerWindows, "getProcessName", 2)


    def assertHasMethod(self, cls, mthd, args=0):
        """ Custom test to make sure a class has the specified method (and that it takes `args` parameters) """
        self.assertTrue(callable(getattr(cls, mthd, None)))
        if args > 0:
            self.assertEqual(len(inspect.getargspec(getattr(cls, mthd))[0]), args)

class TestConvenienceFunctions(unittest.TestCase):
    def test_function_defs(self):
        self.assertHasMethod(lackey, "sleep", 1)
        self.assertHasMethod(lackey, "exit", 1)
        self.assertHasMethod(lackey, "setShowActions", 1)
        self.assertHasMethod(lackey, "getBundlePath", 0)
        self.assertHasMethod(lackey, "getBundleFolder", 0)
        self.assertHasMethod(lackey, "setBundlePath", 1)
        self.assertHasMethod(lackey, "getImagePath", 0)
        self.assertHasMethod(lackey, "addImagePath", 1)
        self.assertHasMethod(lackey, "addHTTPImagePath", 1)
        self.assertHasMethod(lackey, "getParentPath", 0)
        self.assertHasMethod(lackey, "getParentFolder", 0)
        self.assertHasMethod(lackey, "makePath", 0) # Uses *args
        self.assertHasMethod(lackey, "makeFolder", 0) # Uses *args
        self.assertHasMethod(lackey, "unzip", 2)
        self.assertHasMethod(lackey, "popat", 0) # Uses *args
        self.assertHasMethod(lackey, "popup", 2)
        self.assertHasMethod(lackey, "popError", 2)
        self.assertHasMethod(lackey, "popAsk", 2)
        self.assertHasMethod(lackey, "input", 4)
        self.assertHasMethod(lackey, "inputText", 5)
        self.assertHasMethod(lackey, "select", 4)
        self.assertHasMethod(lackey, "popFile", 1)

    def assertHasMethod(self, cls, mthd, args=0):
        """ Custom test to make sure a class has the specified method (and that it takes `args` parameters) """
        self.assertTrue(callable(getattr(cls, mthd, None)))
        if args > 0:
            self.assertEqual(len(inspect.getargspec(getattr(cls, mthd))[0]), args)

if __name__ == '__main__':
    unittest.main()