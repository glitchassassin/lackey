import inspect
import subprocess
import unittest
import time
import sys
import os
#sys.path.insert(0, os.path.abspath('..'))
import lackey
import numpy

from .appveyor_test_cases import TestMouseMethods, TestLocationMethods, TestPatternMethods, TestInterfaces, TestConvenienceFunctions, TestObserverEventMethods, TestRegionMethods

# Python 3 compatibility
try:
    basestring
except NameError:
    basestring = str

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

class TestComplexFeatures(unittest.TestCase):
    def setUp(self):
        print(os.path.dirname(__file__))
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

@unittest.skip("Requires user intervention")
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
