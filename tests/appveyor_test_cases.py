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
        outside_loc = lackey.Location(-9000, -9000)
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

if __name__ == '__main__':
    unittest.main()