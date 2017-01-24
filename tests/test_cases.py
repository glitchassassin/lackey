import inspect
import subprocess
import unittest
import time
import sys
import os
#sys.path.insert(0, os.path.abspath('..'))
import lackey

from appveyor_test_cases import TestLocationMethods, TestPatternMethods, TestInterfaces, TestConvenienceFunctions

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
			#app.setUsing("test_cases.py")
			app.open()
			time.sleep(1)
		else:
			raise NotImplementedError("Platforms supported include: Windows")
		app.focus()

		self.assertEqual(app.getName(), "notepad.exe")
		self.assertTrue(app.isRunning())
		self.assertEqual(app.getWindow(), "test_cases.py - Notepad")
		self.assertNotEqual(app.getPID(), -1)
		region = app.window()
		self.assertIsInstance(region, lackey.Region)
		self.assertGreater(region.getW(), 0)
		self.assertGreater(region.getH(), 0)

		if sys.platform.startswith("win"):
			app.close()
		time.sleep(1)		

	def test_launchers(self):
		app = lackey.App("notepad.exe")
		app.setUsing("tests\\test_cases.py")
		app.open()
		time.sleep(1)
		self.assertEqual(app.getName(), "notepad.exe")
		self.assertTrue(app.isRunning())
		self.assertEqual(app.getWindow(), "test_cases.py - Notepad")
		self.assertNotEqual(app.getPID(), -1)
		app.close()
		time.sleep(1)

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
	def testTypeCopyPaste(self):
		if sys.platform.startswith("win"):
			app = lackey.App("notepad.exe").open()
			time.sleep(1)
		else:
			raise NotImplementedError("Platforms supported include: Windows")
		r = app.window()

		r.type("This is a Test") # Type should translate "+" into shift modifier for capital first letters
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

	def testOpenApp(self):
		""" This looks for the specified Notepad icon on the desktop.

		This test will probably fail if you don't have the same setup I do. 
		"""
		r = lackey.Screen(0)
		r.doubleClick("notepad.png")
		time.sleep(2)
		r.type("This is a test")
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