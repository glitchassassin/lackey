import inspect
import subprocess
import unittest
import numpy
import time
import sys
import os
import lackey

# Python 2/3 compatibility
try:
    unittest.TestCase.assertRegex
except AttributeError:
    unittest.TestCase.assertRegex =  unittest.TestCase.assertRegexpMatches

class TestMouseMethods(unittest.TestCase):
    def setUp(self):
        self.mouse = lackey.Mouse()

    def test_movement(self):
        self.mouse.move(lackey.Location(10, 10))
        lackey.sleep(0.01)
        self.assertEqual(self.mouse.getPos().getTuple(), (10, 10))
        self.mouse.moveSpeed(lackey.Location(100, 200), 0.5)
        self.assertEqual(self.mouse.getPos().getTuple(), (100, 200))
        lackey.wheel(self.mouse.getPos(), 0, 3) # Mostly just verifying it doesn't crash

class TestKeyboardMethods(unittest.TestCase):
    def setUp(self):
        self.kb = lackey.Keyboard()

    def test_keys(self):
        self.kb.keyDown("{SHIFT}")
        self.kb.keyUp("{CTRL}")
        self.kb.keyUp("{SHIFT}")
        self.kb.type("{CTRL}")
        # Really this should check to make sure these keys have all been released, but
        # I'm not sure how to make that work without continuously monitoring the keyboard
        # (which is the usual scenario). Ah well... if your computer is acting weird after
        # you run this test, the SHIFT, CTRL, or ALT keys might not have been released
        # properly.

class TestAppMethods(unittest.TestCase):
    def test_getters(self):
        if sys.platform.startswith("win"):
            app = lackey.App("notepad.exe tests\\test_cases.py")
            app2 = lackey.App("notepad.exe tests\\test_cases.py")
            #app.setUsing("test_cases.py")
            app.open()
            app2.open()
            lackey.sleep(1)
            app2.close()
            app.focus()
            self.assertEqual(app.getName(), "notepad.exe")
            self.assertTrue(app.isRunning())
            self.assertEqual(app.getWindow(), "test_cases(.py)? - Notepad")
            self.assertNotEqual(app.getPID(), -1)
            region = app.window()
            self.assertIsInstance(region, lackey.Region)
            self.assertGreater(region.getW(), 0)
            self.assertGreater(region.getH(), 0)
            app.close()
        elif sys.platform == "darwin":
            a = lackey.App("+open -a TextEdit tests/test_cases.py")
            a2 = lackey.App("open -a TextEdit tests/appveyor_test_cases.py")
            lackey.sleep(1)
            app = lackey.App("test_cases.py")
            app2 = lackey.App("appveyor_test_cases.py")
            #app.setUsing("test_cases.py")
            lackey.sleep(1)
            app2.close()
            app.focus()
            print(app.getPID())
            self.assertEqual(app.getName()[-len("TextEdit"):], "TextEdit")
            self.assertTrue(app.isRunning())
            #self.assertEqual(app.getWindow(), "test_cases.py") # Doesn't work on `open`-triggered apps
            self.assertNotEqual(app.getPID(), -1)
            region = app.window()
            self.assertIsInstance(region, lackey.Region)
            self.assertGreater(region.getW(), 0)
            self.assertGreater(region.getH(), 0)
            app.close()
        else:
            raise NotImplementedError("Platforms supported include: Windows, OS X")

    def test_launchers(self):
        if sys.platform.startswith("win"):
            app = lackey.App("notepad.exe")
            app.setUsing("tests\\test_cases.py")
            app.open()
            lackey.wait(1)
            self.assertEqual(app.getName(), "notepad.exe")
            self.assertTrue(app.isRunning())
            self.assertEqual(app.getWindow(), "test_cases(.py)? - Notepad")
            self.assertNotEqual(app.getPID(), -1)
            app.close()
            lackey.wait(0.9)
        elif sys.platform.startswith("darwin"):
            a = lackey.App("open")
            a.setUsing("-a TextEdit tests/test_cases.py")
            a.open()
            lackey.wait(1)
            app = lackey.App("test_cases.py")
            self.assertEqual(app.getName()[-len("TextEdit"):], "TextEdit")
            self.assertTrue(app.isRunning())
            #self.assertEqual(app.getWindow(), "test_cases.py")  # Doesn't work on `open`-triggered apps
            self.assertNotEqual(app.getPID(), -1)
            app.close()
            lackey.wait(0.9)
        else:
            raise NotImplementedError("Platforms supported include: Windows, OS X")

class TestScreenMethods(unittest.TestCase):
    def setUp(self):
        self.primaryScreen = lackey.Screen(0)

    def testScreenInfo(self):
        self.assertGreater(self.primaryScreen.getNumberScreens(), 0)
        x, y, w, h = self.primaryScreen.getBounds()
        self.assertEqual(x, 0) # Top left corner of primary screen should be 0,0
        self.assertEqual(y, 0) # Top left corner of primary screen should be 0,0
        self.assertGreater(w, 0) # Primary screen should be wider than 0
        self.assertGreater(h, 0) # Primary screen should be taller than 0

    def testCapture(self):
        tpath = self.primaryScreen.capture()
        self.assertIsInstance(tpath, numpy.ndarray)

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

    def test_screen_methods(self):
        outside_loc = lackey.Location(-10, -10)
        self.assertIsNone(outside_loc.getScreen()) # Should be outside all screens and return None
        self.assertEqual(self.test_loc.getScreen().getID(), 0) # Test location should be on screen 0
        self.assertEqual(outside_loc.getMonitor().getID(), 0) # Outside all screens, should return default monitor (0)
        self.assertEqual(self.test_loc.getMonitor().getID(), 0) # Outside all screens, should return default monitor (0)
        self.assertIsNone(outside_loc.getColor()) # No color outside all screens, should return None
        self.assertIsInstance(self.test_loc.getColor(), numpy.ndarray) # No color outside all screens, should return None



class TestPatternMethods(unittest.TestCase):
    def setUp(self):
        self.file_path = os.path.join("tests", "test_pattern.png")
        self.pattern = lackey.Pattern(self.file_path)
    
    def test_defaults(self):
        self.assertEqual(self.pattern.similarity, 0.7)
        self.assertIsInstance(self.pattern.offset, lackey.Location)
        self.assertEqual(self.pattern.offset.getTuple(), (0,0))
        self.assertEqual(self.pattern.path[-len(self.file_path):], self.file_path)

    def test_setters(self):
        test_pattern = self.pattern.similar(0.5)
        self.assertEqual(test_pattern.similarity, 0.5)
        self.assertEqual(test_pattern.path[-len(self.file_path):], self.file_path)
        test_pattern = self.pattern.exact()
        self.assertEqual(test_pattern.similarity, 1.0)
        self.assertEqual(test_pattern.path[-len(self.file_path):], self.file_path)
        test_pattern = self.pattern.targetOffset(3, 5)
        self.assertEqual(test_pattern.similarity, 0.7)
        self.assertEqual(test_pattern.path[-len(self.file_path):], self.file_path)
        self.assertEqual(test_pattern.offset.getTuple(), (3,5))

    def test_getters(self):
        self.assertEqual(self.pattern.getFilename()[-len(self.file_path):], self.file_path)
        self.assertEqual(self.pattern.getTargetOffset().getTuple(), (0,0))
        self.assertEqual(self.pattern.getSimilar(), 0.7)

    def test_constructor(self):
        cloned_pattern = lackey.Pattern(self.pattern)
        self.assertTrue(cloned_pattern.isValid())
        pattern_from_image = lackey.Pattern(self.pattern.getImage())
        self.assertTrue(pattern_from_image.isImagePattern())
        with self.assertRaises(TypeError):
            lackey.Pattern(True)
        with self.assertRaises(lackey.ImageMissing):
            lackey.Pattern("non_existent_file.png")

class TestRegionMethods(unittest.TestCase):
    def setUp(self):
        self.r = lackey.Screen(0)

    def test_constructor(self):
        self.assertIsInstance(lackey.Region(self.r), lackey.Region)
        self.assertIsInstance(lackey.Region((0, 0, 5, 5)), lackey.Region)
        self.assertIsInstance(lackey.Region(0, 0), lackey.Region)
        self.assertIsInstance(lackey.Region(0, 0, 10, 10, 3), lackey.Region)
        with self.assertRaises(TypeError):
            lackey.Region("foobar")
        with self.assertRaises(TypeError):
            lackey.Region()
        self.assertIsInstance(lackey.Region.create(lackey.Location(0,0), 5, 5), lackey.Region)
        self.assertIsInstance(lackey.Region.create(
            lackey.Location(0, 0), 
            lackey.Region.CREATE_X_DIRECTION_RIGHT,
            lackey.Region.CREATE_Y_DIRECTION_BOTTOM,
            10,
            10
        ), lackey.Region)
        self.assertIsInstance(lackey.Region.create(
            lackey.Location(10, 10),
            lackey.Region.CREATE_X_DIRECTION_LEFT,
            lackey.Region.CREATE_Y_DIRECTION_TOP,
            10,
            10
        ), lackey.Region)

    def test_changers(self):
        # setLocation
        self.assertEqual(self.r.getTopLeft(), lackey.Location(0, 0))
        self.assertEqual(self.r.setLocation(lackey.Location(10, 10)).getTopLeft(), lackey.Location(10, 10))
        with self.assertRaises(ValueError):
            self.r.setLocation(None)
        # setROI
        self.r.setROI((5, 5, 10, 10))
        new_region = lackey.Screen(0)
        new_region.morphTo(self.r)
        with self.assertRaises(TypeError):
            new_region.morphTo("werdz")
        self.assertEqual(self.r.getTopLeft(), new_region.getTopLeft())
        self.assertEqual(self.r.getTopRight(), new_region.getTopRight())
        self.assertEqual(self.r.getBottomLeft(), new_region.getBottomLeft())
        self.assertEqual(self.r.getBottomRight(), new_region.getBottomRight())
        with self.assertRaises(TypeError):
            new_region.setROI("hammersauce")
        with self.assertRaises(TypeError):
            new_region.setROI()
        new_region.add(5, 5, 5, 5)
        self.assertEqual(new_region.getTopLeft(), lackey.Location(0, 0))
        # copyTo - only guaranteed one screen, so just make sure it doesn't crash
        new_region.copyTo(0)
        new_region.copyTo(lackey.Screen(0))

    def test_info(self):
        self.assertFalse(self.r.contains(lackey.Location(-5, -5)))
        new_region = lackey.Region(-10, -10, 5, 5)
        self.assertFalse(self.r.contains(new_region))
        with self.assertRaises(TypeError):
            self.r.contains("werdz")
        self.r.hover()
        self.assertTrue(self.r.containsMouse())


    def test_validity_methods(self):
        self.assertTrue(self.r.isRegionValid())
        clipped = self.r.clipRegionToScreen()
        self.assertIsNotNone(clipped)
        self.assertEqual(clipped.getX(), self.r.getX())
        self.assertEqual(clipped.getY(), self.r.getY())
        self.assertEqual(clipped.getW(), self.r.getW())
        self.assertEqual(clipped.getH(), self.r.getH())

    def test_around_methods(self):
        center_region = self.r.get(lackey.Region.MID_BIG)
        below_region = center_region.below()
        self.assertTrue(below_region.isRegionValid())
        below_region = center_region.below(10)
        self.assertTrue(below_region.isRegionValid())
        above_region = center_region.above()
        self.assertTrue(above_region.isRegionValid())
        above_region = center_region.above(10)
        self.assertTrue(above_region.isRegionValid())
        right_region = center_region.right()
        self.assertTrue(right_region.isRegionValid())
        right_region = center_region.right(10)
        self.assertTrue(right_region.isRegionValid())
        left_region = center_region.left()
        self.assertTrue(left_region.isRegionValid())
        left_region = center_region.left(10)
        self.assertTrue(left_region.isRegionValid())
        nearby_region = center_region.nearby(10)
        self.assertTrue(nearby_region.isRegionValid())
        grow_region = center_region.grow(10, 5)
        self.assertTrue(grow_region.isRegionValid())
        grow_region = center_region.grow(10)
        self.assertTrue(grow_region.isRegionValid())
        inside_region = center_region.inside()
        self.assertTrue(inside_region.isRegionValid())
        offset_region = center_region.offset(lackey.Location(10, 10))
        self.assertTrue(offset_region.isRegionValid())
        with self.assertRaises(ValueError):
            offset_region = left_region.offset(-1000, -1000)

    def test_highlighter(self):
        center_region = self.r.get(lackey.Region.MID_BIG)
        center_region.highlight()
        center_region.highlight(2, "blue")
        center_region.highlight(True, 0)
        print("Doing stuff...")
        time.sleep(1)
        center_region.highlight(False)

    def test_settings(self):
        self.r.setAutoWaitTimeout(10)
        self.assertEqual(self.r.getAutoWaitTimeout(), 10.0)
        self.r.setWaitScanRate(2)
        self.assertEqual(self.r.getWaitScanRate(), 2.0)

class TestObserverEventMethods(unittest.TestCase):
    def setUp(self):
        self.r = lackey.Screen(0)
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
        with self.assertRaises(TypeError) as context:
            self.generic_event.getImage()
        with self.assertRaises(TypeError) as context:
            self.generic_event.getMatch()
        with self.assertRaises(TypeError) as context:
            self.generic_event.getChanges()

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
        self.assertHasMethod(lackey.Region, "highlight", 1) # Uses *args
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
        """ Checking Location class interface methods """
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
        """ Checking Screen class interface methods """
        self.assertHasMethod(lackey.Screen, "__init__", 2)
        self.assertHasMethod(lackey.Screen, "getNumberScreens", 1)
        self.assertHasMethod(lackey.Screen, "getBounds", 1)
        self.assertHasMethod(lackey.Screen, "capture", 1) 			# Uses *args
        self.assertHasMethod(lackey.Screen, "selectRegion", 2)

    def test_platform_manager_interface(self):
        """ Checking Platform Manager interface methods """

        ## Screen methods
        self.assertHasMethod(lackey.PlatformManager, "getBitmapFromRect", 5)
        self.assertHasMethod(lackey.PlatformManager, "getScreenBounds", 2)
        self.assertHasMethod(lackey.PlatformManager, "getScreenDetails", 1)
        self.assertHasMethod(lackey.PlatformManager, "isPointVisible", 3)

        ## Clipboard methods
        self.assertHasMethod(lackey.PlatformManager, "osCopy", 1)
        self.assertHasMethod(lackey.PlatformManager, "osPaste", 1)

        ## Window methods
        self.assertHasMethod(lackey.PlatformManager, "getWindowByTitle", 3)
        self.assertHasMethod(lackey.PlatformManager, "getWindowByPID", 3)
        self.assertHasMethod(lackey.PlatformManager, "getWindowRect", 2)
        self.assertHasMethod(lackey.PlatformManager, "focusWindow", 2)
        self.assertHasMethod(lackey.PlatformManager, "getWindowTitle", 2)
        self.assertHasMethod(lackey.PlatformManager, "getWindowPID", 2)
        self.assertHasMethod(lackey.PlatformManager, "getForegroundWindow", 1)

        ## Process methods
        self.assertHasMethod(lackey.PlatformManager, "isPIDValid", 2)
        self.assertHasMethod(lackey.PlatformManager, "killProcess", 2)
        self.assertHasMethod(lackey.PlatformManager, "getProcessName", 2)


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

    def test_renamed_builtin_functions(self):
        self.assertEqual(lackey.exit_, sys.exit)
        self.assertEqual(lackey.input_, input)
        self.assertEqual(lackey.type_, type)

    def assertHasMethod(self, cls, mthd, args=0):
        """ Custom test to make sure a class has the specified method (and that it takes `args` parameters) """
        self.assertTrue(callable(getattr(cls, mthd, None)))
        if args > 0:
            self.assertEqual(len(inspect.getargspec(getattr(cls, mthd))[0]), args)

if __name__ == '__main__':
    unittest.main()