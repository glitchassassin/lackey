import inspect
import subprocess
import unittest
import time
import sys
import os
#sys.path.insert(0, os.path.abspath('..'))
import lackey

from .appveyor_test_cases import TestLocationMethods, TestPatternMethods, TestInterfaces, TestConvenienceFunctions, TestObserverEventMethods

# Python 3 compatibility
try:
    basestring
except NameError:
    basestring = str

class TestMouseMethods(unittest.TestCase):
    def setUp(self):
        self.mouse = lackey.Mouse()

    def test_movement(self):
        self.mouse.move(lackey.Location(10,10))
        self.assertEqual(self.mouse.getPos().getTuple(), (10,10))
        self.mouse.moveSpeed(lackey.Location(100,200), 0.5)
        self.assertEqual(self.mouse.getPos().getTuple(), (100,200))
        lackey.wheel(self.mouse.getPos(), 0, 3) # Mostly just verifying it doesn't crash
        
    def test_clicks(self):
        """
        Not sure how to build these tests yet
        """
        pass

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
            self.assertEqual(app.getName(), "(open)")
            self.assertTrue(app.isRunning())
            self.assertEqual(app.getWindow(), "test_cases.py - Notepad")
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
            self.assertEqual(app.getName(), "(open)")
            self.assertTrue(app.isRunning())
            self.assertEqual(app.getWindow(), "test_cases.py")
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

    def test_app_title(self):
        """
        App selected by title should capture existing window if open,
        including case-insensitive matches.
        """
        if sys.platform.startswith("win"):
            app = lackey.App("notepad.exe")
            app.open()
            lackey.wait(1)
            app2 = lackey.App("Notepad")
            app3 = lackey.App("notepad")
            lackey.wait(1)

            self.assertTrue(app2.isRunning())
            self.assertTrue(app3.isRunning())
            self.assertEqual(app2.getName(), app.getName())
            self.assertEqual(app3.getName(), app.getName())
            app.close()
        elif sys.platform.startswith("darwin"):
            pass # Skip this test, due to issues with `open` not being the window owner on Mac
        else:
            raise NotImplementedError("Platforms supported include: Windows, OS X")


class TestScreenMethods(unittest.TestCase):
    def setUp(self):
        self.primaryScreen = lackey.Screen(0)

    def testScreenInfo(self):
        self.assertGreater(self.primaryScreen.getNumberScreens(), 0)
        x,y,w,h = self.primaryScreen.getBounds()
        self.assertEqual(x, 0) # Top left corner of primary screen should be 0,0
        self.assertEqual(y, 0) # Top left corner of primary screen should be 0,0
        self.assertGreater(w, 0) # Primary screen should be wider than 0
        self.assertGreater(h, 0) # Primary screen should be taller than 0

    def testCapture(self):
        tpath = self.primaryScreen.capture()
        self.assertIsInstance(tpath, basestring)
        self.assertNotEqual(tpath, "")

class TestComplexFeatures(unittest.TestCase):
    def setUp(self):
        lackey.addImagePath(os.path.dirname(__file__))

    def testTypeCopyPaste(self):
        """ Also tests the log file """
        lackey.Debug.setLogFile("logfile.txt")
        if sys.platform.startswith("win"):
            app = lackey.App("notepad.exe").open()
            time.sleep(1)
        else:
            raise NotImplementedError("Platforms supported include: Windows")
        r = app.window()

        r.type("This is a Test")
        r.type("a", lackey.Key.CONTROL) # Select all
        r.type("c", lackey.Key.CONTROL) # Copy
        self.assertEqual(r.getClipboard(), "This is a Test")
        r.type("{DELETE}") # Clear the selected text
        r.paste("This, on the other hand, is a {SHIFT}broken {SHIFT}record.") # Paste should ignore special characters and insert the string as is
        r.type("a", lackey.Key.CONTROL) # Select all
        r.type("c", lackey.Key.CONTROL) # Copy
        self.assertEqual(r.getClipboard(), "This, on the other hand, is a {SHIFT}broken {SHIFT}record.")

        if sys.platform.startswith("win"):
            app.close()

        lackey.Debug.setLogFile(None)

        self.assertTrue(os.path.exists("logfile.txt"))

    def testOpenApp(self):
        """ This looks for the specified Notepad icon on the desktop.

        This test will probably fail if you don't have the same setup I do.
        """
        def test_observer(appear_event):
            assert(appear_event.isAppear())
            img = appear_event.getImage()
            region = appear_event.getRegion()
            region.TestFlag = True
            region.stopObserver()
        r = lackey.Screen(0)
        r.doubleClick("notepad.png")
        time.sleep(2)
        r.type("This is a test")
        r.onAppear(lackey.Pattern("test_text.png").similar(0.6), test_observer)
        r.observe(30)
        self.assertTrue(r.TestFlag)
        r.rightClick(lackey.Pattern("test_text.png").similar(0.6))
        r.click("select_all.png")
        r.type("c", lackey.Key.CONTROL) # Copy
        self.assertEqual(r.getClipboard(), "This is a test")
        r.type("{DELETE}")
        r.type("{F4}", lackey.Key.ALT)

    def testDragDrop(self):
        """ This relies on two specific icons on the desktop.

        This test will probably fail if you don't have the same setup I do.
        """
        r = lackey.Screen(0)
        r.dragDrop("test_file_txt.png", "notepad.png")
        self.assertTrue(r.exists("test_file_text.png"))
        r.type("{F4}", lackey.Key.ALT)

    def testFindFailed(self):
        """ Sets up a region (which should not have the target icon) """

        r = lackey.Screen(0).get(lackey.Region.NORTH_EAST)
        with self.assertRaises(lackey.FindFailed) as context:
            r.find("notepad.png")
        r.setFindFailedResponse(r.SKIP)
        try:
            r.find("notepad.png")
        except FindFailed:
            self.fail("Incorrectly threw FindFailed exception; should have skipped")


class TestRegionFeatures(unittest.TestCase):
    def setUp(self):
        self.r = lackey.Screen(0)

    def testValidityMethods(self):
        self.assertTrue(self.r.isRegionValid())
        clipped = self.r.clipRegionToScreen()
        self.assertIsNotNone(clipped)
        self.assertEqual(clipped.getX(), self.r.getX())
        self.assertEqual(clipped.getY(), self.r.getY())
        self.assertEqual(clipped.getW(), self.r.getW())
        self.assertEqual(clipped.getH(), self.r.getH())

    def testAroundMethods(self):
        center_region = self.r.get(lackey.Region.MID_BIG)
        below_region = center_region.below()
        self.assertTrue(below_region.isRegionValid())
        above_region = center_region.above()
        self.assertTrue(center_region.isRegionValid())
        right_region = center_region.right()
        self.assertTrue(right_region.isRegionValid())
        left_region = center_region.left()
        self.assertTrue(left_region.isRegionValid())
        nearby_region = center_region.nearby(10)
        self.assertTrue(nearby_region.isRegionValid())
        grow_region = center_region.grow(10, 5)
        self.assertTrue(grow_region.isRegionValid())

class TestRasterMethods(unittest.TestCase):
    def setUp(self):
        self.r = lackey.Screen(0)

    def testRaster(self):
        # This should preview the specified sections of the primary screen.
        self.r.debugPreview("Full screen")
        self.r.get(lackey.Region.NORTH).debugPreview("Top half")
        self.r.get(lackey.Region.SOUTH).debugPreview("Bottom half")
        self.r.get(lackey.Region.NORTH_WEST).debugPreview("Upper right corner")
        self.r.get(522).debugPreview("Center (small)")
        self.r.get(lackey.Region.MID_BIG).debugPreview("Center (half)")

if __name__ == '__main__':
    unittest.main()
