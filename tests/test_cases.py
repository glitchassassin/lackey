import subprocess
import unittest
import time
import sys
import os
sys.path.insert(0, os.path.abspath('..'))
import lackey

class TestLocationMethods(unittest.TestCase):
	print "Setting up TestLocationMethods"
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
	print "Setting up TestPatternMethods"
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
	print "Setting up TestMouseMethods"
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
	print "Setting up TestKeyboardMethods"
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
		print "Setting up TestWindowMethods"
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

class TestComplexFeatures(unittest.TestCase):
	def setUp(self):
		print "Setting up TestComplexFeatures"
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
		lackey.PlatformManager.setClipboard("") # Clear the clipboard
		self.r.type("This is a +test") # Type should translate "+" into shift modifier for capital first letters
		self.r.type("^a") # Select all
		self.r.type("^c") # Copy
		self.assertEqual(self.r.getClipboard(), "This is a Test")
		self.r.type("{DELETE}") # Clear the selected text
		self.r.paste("This, on the other hand, is a +broken +record.") # Paste should ignore special characters and insert the string as is
		self.r.type("^a") # Select all
		self.r.type("^c") # Copy
		self.assertEqual(self.r.getClipboard(), "This, on the other hand, is a +broken +record.")


if __name__ == '__main__':
	unittest.main()