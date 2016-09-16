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
		self.pattern = lackey.Pattern("test_pattern.png")
	
	def test_defaults(self):
		self.assertEqual(self.pattern.similarity, 0.7)
		self.assertIsInstance(self.pattern.offset, lackey.Location)
		self.assertEqual(self.pattern.offset.getTuple(), (0,0))
		self.assertEqual(self.pattern.path, "test_pattern.png")

	def test_setters(self):
		test_pattern = self.pattern.similar(0.5)
		self.assertEqual(test_pattern.similarity, 0.5)
		self.assertEqual(test_pattern.path, "test_pattern.png")
		test_pattern = self.pattern.exact()
		self.assertEqual(test_pattern.similarity, 1.0)
		self.assertEqual(test_pattern.path, "test_pattern.png")
		test_pattern = self.pattern.targetOffset(3, 5)
		self.assertEqual(test_pattern.similarity, 0.7)
		self.assertEqual(test_pattern.path, "test_pattern.png")
		self.assertEqual(test_pattern.offset.getTuple(), (3,5))

	def test_getters(self):
		self.assertEqual(self.pattern.getFilename(), "test_pattern.png")
		self.assertEqual(self.pattern.getTargetOffset().getTuple(), (0,0))

#class TestMouseMethods(unittest.TestCase):
#	def setUp(self):
#		self.mouse = lackey.Mouse()
#
#	def test_movement(self):
#		self.mouse.move(lackey.Location(10,10))
#		self.assertEqual(self.mouse.getPos().getTuple(), (10,10))
#		self.mouse.moveSpeed(lackey.Location(100,200), 1)
#		self.assertEqual(self.mouse.getPos().getTuple(), (100,200))
#		
#	def test_clicks(self):
#		"""
#		Not sure how to build these tests yet
#		"""
#		pass

# class TestKeyboardMethods(unittest.TestCase):
# 	def setUp(self):
# 		self.kb = lackey.Keyboard()

# 	def test_keys(self):
# 		self.kb.keyDown("{SHIFT}")
# 		self.kb.keyUp("{CTRL}")
# 		self.kb.keyUp("{SHIFT}")
# 		self.kb.type("%{CTRL}")
# 		# Really this should check to make sure these keys have all been released, but 
# 		# I'm not sure how to make that work without continuously monitoring the keyboard
# 		# (which is the usual scenario). Ah well... if your computer is acting weird after
# 		# you run this test, the SHIFT, CTRL, or ALT keys might not have been released
# 		# properly.

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
		self.assertHasMethod(lackey.Region, "wheel", 4)
		self.assertHasMethod(lackey.Region, "keyDown", 2)
		self.assertHasMethod(lackey.Region, "keyUp", 2)

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

		## Keyboard input methods
		self.assertHasMethod(lackey.PlatformManagerWindows, "pressKey", 2)
		self.assertHasMethod(lackey.PlatformManagerWindows, "releaseKey", 2)
		self.assertHasMethod(lackey.PlatformManagerWindows, "typeKeys", 3)

		## Mouse input methods
		self.assertHasMethod(lackey.PlatformManagerWindows, "setMousePos", 2)
		self.assertHasMethod(lackey.PlatformManagerWindows, "getMousePos", 1)
		self.assertHasMethod(lackey.PlatformManagerWindows, "mouseButtonDown", 2)
		self.assertHasMethod(lackey.PlatformManagerWindows, "mouseButtonUp", 2)
		self.assertHasMethod(lackey.PlatformManagerWindows, "clickMouse", 2)
		self.assertHasMethod(lackey.PlatformManagerWindows, "mouseWheel", 3)

		## Screen methods
		self.assertHasMethod(lackey.PlatformManagerWindows, "getBitmapFromRect", 5)
		self.assertHasMethod(lackey.PlatformManagerWindows, "getScreenBounds", 2)
		self.assertHasMethod(lackey.PlatformManagerWindows, "getScreenDetails", 1)
		self.assertHasMethod(lackey.PlatformManagerWindows, "isPointVisible", 3)

		## Clipboard methods
		self.assertHasMethod(lackey.PlatformManagerWindows, "getClipboard", 1)
		self.assertHasMethod(lackey.PlatformManagerWindows, "setClipboard", 2)
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

# class TestAppMethods(unittest.TestCase):
# 	def setUp(self):
# 		if sys.platform.startswith("win"):
# 			self.app = lackey.App("notepad.exe")
# 			self.app.setUsing("test_cases.py")
# 			self.app.open()
# 			time.sleep(1)
# 		else:
# 			raise NotImplementedError("Platforms supported include: Windows")
# 		self.app.focus()
# 	def tearDown(self):
# 		if sys.platform.startswith("win"):
# 			self.app.close()
# 		time.sleep(1)		

# 	def test_getters(self):
# 		self.assertEqual(self.app.getName(), "notepad.exe")
# 		self.assertTrue(self.app.isRunning())
# 		self.assertEqual(self.app.getWindow(), "test_cases.py - Notepad")
# 		self.assertNotEqual(self.app.getPID(), -1)
# 		region = self.app.window()
# 		self.assertIsInstance(region, lackey.Region)
# 		self.assertGreater(region.getW(), 0)
# 		self.assertGreater(region.getH(), 0)

# class TestScreenMethods(unittest.TestCase):
# 	def setUp(self):
# 		self.primaryScreen = lackey.Screen(0)

# 	def testScreenInfo(self):
# 		self.assertGreater(self.primaryScreen.getNumberScreens(), 0)
# 		x,y,w,h = self.primaryScreen.getBounds()
# 		self.assertEqual(x, 0) # Top left corner of primary screen should be 0,0
# 		self.assertEqual(y, 0) # Top left corner of primary screen should be 0,0
# 		self.assertGreater(w, 0) # Primary screen should be wider than 0
# 		self.assertGreater(h, 0) # Primary screen should be taller than 0

# 	def testCapture(self):
# 		tpath = self.primaryScreen.capture()
# 		self.assertIsInstance(tpath, basestring)
# 		self.assertNotEqual(tpath, "")

# class TestComplexFeatures(unittest.TestCase):
# 	def testTypeCopyPaste(self):
# 		if sys.platform.startswith("win"):
# 			app = lackey.App("notepad.exe").open()
# 			time.sleep(1)
# 		else:
# 			raise NotImplementedError("Platforms supported include: Windows")
# 		r = app.window()

# 		r.type("This is a +test") # Type should translate "+" into shift modifier for capital first letters
# 		r.type("^a") # Select all
# 		r.type("^c") # Copy
# 		self.assertEqual(r.getClipboard(), "This is a Test")
# 		r.type("{DELETE}") # Clear the selected text
# 		r.paste("This, on the other hand, is a +broken +record.") # Paste should ignore special characters and insert the string as is
# 		r.type("^a") # Select all
# 		r.type("^c") # Copy
# 		self.assertEqual(r.getClipboard(), "This, on the other hand, is a +broken +record.")

# 		if sys.platform.startswith("win"):
# 			app.close()

# 	def testOpenApp(self):
# 		""" This looks for the specified Notepad icon on the desktop.

# 		This test will probably fail if you don't have the same setup I do. 
# 		"""
# 		r = lackey.Screen(0)
# 		r.doubleClick("notepad.png")
# 		time.sleep(2)
# 		r.type("This is a test")
# 		r.rightClick(lackey.Pattern("test_text.png").similar(0.6))
# 		r.click("select_all.png")
# 		r.type("^c") # Copy
# 		self.assertEqual(r.getClipboard(), "This is a test")
# 		r.type("{DELETE}")
# 		r.type("%{F4}")

# class TestRegionFeatures(unittest.TestCase):
# 	def setUp(self):
# 		self.r = lackey.Screen(0)

# 	def testValidityMethods(self):
# 		self.assertTrue(self.r.isRegionValid())
# 		clipped = self.r.clipRegionToScreen()
# 		self.assertIsNotNone(clipped)
# 		self.assertEqual(clipped.getX(), self.r.getX())
# 		self.assertEqual(clipped.getY(), self.r.getY())
# 		self.assertEqual(clipped.getW(), self.r.getW())
# 		self.assertEqual(clipped.getH(), self.r.getH())

# 	def testAroundMethods(self):
# 		center_region = self.r.get(lackey.Region.MID_BIG)
# 		below_region = center_region.below()
# 		self.assertTrue(below_region.isRegionValid())
# 		above_region = center_region.above()
# 		self.assertTrue(center_region.isRegionValid())
# 		right_region = center_region.right()
# 		self.assertTrue(right_region.isRegionValid())
# 		left_region = center_region.left()
# 		self.assertTrue(left_region.isRegionValid())
# 		nearby_region = center_region.nearby(10)
# 		self.assertTrue(nearby_region.isRegionValid())
# 		grow_region = center_region.grow(10, 5)
# 		self.assertTrue(grow_region.isRegionValid())

# class TestRasterMethods(unittest.TestCase):
# 	def setUp(self):
# 		self.r = lackey.Screen(0)

# 	def testRaster(self):
# 		# This should preview the specified sections of the primary screen.
# 		self.r.debugPreview("Full screen")
# 		self.r.get(lackey.Region.NORTH).debugPreview("Top half")
# 		self.r.get(lackey.Region.SOUTH).debugPreview("Bottom half")
# 		self.r.get(lackey.Region.NORTH_WEST).debugPreview("Upper right corner")
# 		self.r.get(522).debugPreview("Center (small)")
# 		self.r.get(lackey.Region.MID_BIG).debugPreview("Center (half)")

if __name__ == '__main__':
	unittest.main()