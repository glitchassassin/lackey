import inspect
import subprocess
import unittest
import time
import sys
import os
#sys.path.insert(0, os.path.abspath('..'))
import lackey
import numpy

from .appveyor_test_cases import *

# Python 3 compatibility
try:
    basestring
except NameError:
    basestring = str

@unittest.skipUnless(sys.platform.startswith("win"), "Platforms supported include: Windows")
class TestKeyboardMethods(unittest.TestCase):
    def setUp(self):
        self.kb = lackey.Keyboard()
        self.app = lackey.App("notepad.exe")
        self.app.open()
        time.sleep(1)

    def tearDown(self):
        self.app.close()

    def type_and_check_equals(self, typed, expected):
        self.kb.type(typed)
        time.sleep(0.2)
        lackey.type("a", lackey.Key.CTRL)
        lackey.type("c", lackey.Key.CTRL)

        self.assertEqual(lackey.getClipboard(), expected)

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

    def test_parsed_special_codes(self):
        OUTPUTS = {
            # Special codes should output the text below.
            # Multiple special codes should be parsed correctly.
            # False special codes should be typed out normally.
            "{SPACE}": " ",
            "{TAB}": "\t",
            "{SPACE}{SPACE}": "  ",
            "{TAB}{TAB}": "\t\t",
            "{ENTER}{ENTER}": "\r\n\r\n",
            "{TEST}": "{TEST}",
            "{TEST}{TEST}": "{TEST}{TEST}"
        }

        for code in OUTPUTS:
            self.type_and_check_equals(code, OUTPUTS[code])


class TestComplexFeatures(unittest.TestCase):
    def setUp(self):
        lackey.addImagePath(os.path.dirname(__file__))
        lackey.Screen(0).hover()
        lackey.Screen(0).click()

    def testTypeCopyPaste(self):
        """ Also tests the log file """
        lackey.Debug.setLogFile("logfile.txt")
        r = lackey.Screen(0)
        if sys.platform.startswith("win"):
            app = lackey.App("notepad.exe").open()
            time.sleep(1)
            r.type("This is a Test")
            r.type("a", lackey.Key.CTRL) # Select all
            r.type("c", lackey.Key.CTRL) # Copy
            self.assertEqual(r.getClipboard(), "This is a Test")
            r.type("{DELETE}") # Clear the selected text
            r.paste("This, on the other hand, is a {SHIFT}broken {SHIFT}record.") # Paste should ignore special characters and insert the string as is
            r.type("a", lackey.Key.CTRL) # Select all
            r.type("c", lackey.Key.CTRL) # Copy
            self.assertEqual(r.getClipboard(), "This, on the other hand, is a {SHIFT}broken {SHIFT}record.")
        elif sys.platform == "darwin":
            app = lackey.App("+open -e")
            lackey.sleep(2)
            #r.debugPreview()
            r.wait(lackey.Pattern("preview_open.png"), lackey.FOREVER)
            r.click(lackey.Pattern("preview_open.png"))
            lackey.type("n", lackey.KeyModifier.CMD)
            time.sleep(1)
            app = lackey.App("Untitled")
            r.type("This is a Test")
            r.type("a", lackey.KeyModifier.CMD) # Select all
            r.type("c", lackey.KeyModifier.CMD) # Copy
            self.assertEqual(r.getClipboard(), "This is a Test")
            r.type("{DELETE}") # Clear the selected text
            r.paste("This, on the other hand, is a {SHIFT}broken {SHIFT}record.") # Paste should ignore special characters and insert the string as is
            r.type("a", lackey.KeyModifier.CMD) # Select all
            r.type("c", lackey.KeyModifier.CMD) # Copy
            self.assertEqual(r.getClipboard(), "This, on the other hand, is a {SHIFT}broken {SHIFT}record.")
        else:
            raise NotImplementedError("Platforms supported include: Windows, OS X")

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
        if sys.platform.startswith("win"):
            r.doubleClick("notepad.png")
        elif sys.platform == "darwin":
            r.doubleClick("textedit.png")
            r.wait("preview_open.png")
            r.type("n", lackey.KeyModifier.CMD)
        time.sleep(2)
        r.type("This is a test")
        if sys.platform.startswith("win"):
            r.onAppear(lackey.Pattern("test_text.png").similar(0.6), test_observer)
        elif sys.platform == "darwin":
            r.onAppear(lackey.Pattern("mac_test_text.png").similar(0.6), test_observer)
        r.observe(30)
        self.assertTrue(r.TestFlag)
        self.assertGreater(r.getTime(), 0)
        if sys.platform.startswith("win"):
            r.rightClick(r.getLastMatch())
            r.click("select_all.png")
            r.type("c", lackey.Key.CTRL) # Copy
        elif sys.platform == "darwin":
            r.type("a", lackey.KeyModifier.CMD)
            r.type("c", lackey.KeyModifier.CMD)
        self.assertEqual(r.getClipboard(), "This is a test")
        r.type("{DELETE}")
        if sys.platform.startswith("win"):
            r.type("{F4}", lackey.Key.ALT)
        elif sys.platform == "darwin":
            r.type("w", lackey.KeyModifier.CMD)
            r.click(lackey.Pattern("textedit_save.png").targetOffset(-86, 41))
            lackey.sleep(0.5)
            r.type("q", lackey.KeyModifier.CMD)

    def testDragDrop(self):
        """ This relies on two specific icons on the desktop.

        This test will probably fail if you don't have the same setup I do.
        """
        r = lackey.Screen(0)
        if sys.platform.startswith("win"):
            r.dragDrop("test_file_txt.png", "notepad.png")
            self.assertTrue(r.exists("test_file_txt.png"))
            r.type("{F4}", lackey.Key.ALT)
        elif sys.platform == "darwin":
            r.dragDrop("test_file_rtf.png", "textedit.png")
            self.assertTrue(r.exists("test_file_rtf.png"))
            r.type("w", lackey.KeyModifier.CMD)
            r.type("q", lackey.KeyModifier.CMD)

    def testFindFailed(self):
        """ Sets up a region (which should not have the target icon) """

        r = lackey.Screen(0).get(lackey.Region.NORTH_EAST)
        with self.assertRaises(lackey.FindFailed) as context:
            r.find("notepad.png")
        r.setFindFailedResponse(r.SKIP)
        try:
            r.find("notepad.png")
        except lackey.FindFailed:
            self.fail("Incorrectly threw FindFailed exception; should have skipped")

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
