import subprocess
import unittest
import time
import sys
import os
sys.path.insert(0, os.path.abspath('..'))
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
		self.pattern = lackey.Pattern("test_file.png")
	
	def test_defaults(self):
		self.assertEqual(self.pattern.similarity, 0.7)
		self.assertIsInstance(self.pattern.offset, lackey.Location)
		self.assertEqual(self.pattern.offset.getTuple(), (0,0))
		self.assertEqual(self.pattern.path, "test_file.png")

	def test_setters(self):
		test_pattern = self.pattern.similar(0.5)
		self.assertEqual(test_pattern.similarity, 0.5)
		self.assertEqual(test_pattern.path, "test_file.png")
		test_pattern = self.pattern.exact()
		self.assertEqual(test_pattern.similarity, 1.0)
		self.assertEqual(test_pattern.path, "test_file.png")
		test_pattern = self.pattern.targetOffset(3, 5)
		self.assertEqual(test_pattern.similarity, 0.7)
		self.assertEqual(test_pattern.path, "test_file.png")
		self.assertEqual(test_pattern.offset.getTuple(), (3,5))

	def test_getters(self):
		self.assertEqual(self.pattern.getFilename(), "test_file.png")
		self.assertEqual(self.pattern.getTargetOffset().getTuple(), (0,0))

class TestMouseMethods(unittest.TestCase):
	def setUp(self):
		self.mouse = lackey.Mouse()

	def test_movement(self):
		self.mouse.move(lackey.Location(10,10))
		self.assertEqual(self.mouse.getPos().getTuple(), (10,10))
		self.mouse.moveSpeed(lackey.Location(100,200), 1)
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
		self.kb.type("%{CTRL}")
		# Really this should check to make sure these keys have all been released, but 
		# I'm not sure how to make that work without continuously monitoring the keyboard
		# (which is the usual scenario). Ah well... if your computer is acting weird after
		# you run this test, the SHIFT, CTRL, or ALT keys might not have been released
		# properly.

class TestWindowMethods(unittest.TestCase):
	def setUp(self):
		if sys.platform.startswith("win"):
			self.app = subprocess.Popen(["notepad.exe"])
			time.sleep(1)
		else:
			raise NotImplementedError("Platforms supported include: Windows")
		self.window = lackey.Window("Untitled - Notepad")
	def tearDown(self):
		if sys.platform.startswith("win"):
			self.app.terminate()
		time.sleep(1)

	def test_getters(self):
		self.assertEqual(self.window.getTitle(), "Untitled - Notepad")
		self.assertNotEqual(self.window.getPID(), -1)
		region = self.window.getRegion()
		self.assertIsInstance(region, lackey.Region)
		self.assertGreater(region.getW(), 0)
		self.assertGreater(region.getH(), 0)

class TestAppMethods(unittest.TestCase):
	def setUp(self):
		if sys.platform.startswith("win"):
			self.subp = subprocess.Popen(["notepad.exe"])
			time.sleep(1)
		else:
			raise NotImplementedError("Platforms supported include: Windows")
		self.app = lackey.App("Untitled - Notepad")
		self.app.focus()
	def tearDown(self):
		if sys.platform.startswith("win"):
			self.app.close()
		time.sleep(1)

	def test_getters(self):
		print self.app.getTitle()
		self.assertEqual(self.app.getTitle(), "Untitled - Notepad")
		self.assertNotEqual(self.app.getPID(), -1)
		region = self.app.getRegion()
		self.assertIsInstance(region, lackey.Region)
		self.assertGreater(region.getW(), 0)
		self.assertGreater(region.getH(), 0)

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
		if sys.platform.startswith("win"):
			self.app = subprocess.Popen(["notepad.exe"])
			time.sleep(1)
		else:
			raise NotImplementedError("Platforms supported include: Windows")
		self.window = lackey.Window("Untitled - Notepad")
		self.r = self.window.getRegion()
	def tearDown(self):
		if sys.platform.startswith("win"):
			self.app.terminate()

	def testTypeCopyPaste(self):
		self.r.type("This is a +test") # Type should translate "+" into shift modifier for capital first letters
		self.r.type("^a") # Select all
		self.r.type("^c") # Copy
		self.assertEqual(self.r.getClipboard(), "This is a Test")
		self.r.type("{DELETE}") # Clear the selected text
		self.r.paste("This, on the other hand, is a +broken +record.") # Paste should ignore special characters and insert the string as is
		self.r.type("^a") # Select all
		self.r.type("^c") # Copy
		self.assertEqual(self.r.getClipboard(), "This, on the other hand, is a +broken +record.")

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