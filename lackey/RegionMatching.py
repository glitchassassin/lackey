import tempfile
import platform
import time
import os

import numpy
import cv2

from .PlatformManagerWindows import PlatformManagerWindows
from .Exceptions import FindFailed

if platform.system() == "Windows":
	PlatformManager = PlatformManagerWindows() # No other input managers built yet
else:
	if not (os.environ.get('READTHEDOCS') == 'True'): # Avoid throwing an error if it's just being imported for documentation purposes
		raise NotImplementedError("Lackey v0.1.0a is currently only compatible with Windows.")
	
class Pattern(object):
	""" Defines a pattern based on a bitmap, similarity, and target offset """
	def __init__(self, path, similarity=0.7, offset=None):
		self.path = path
		self.similarity = similarity
		self.offset = offset or Location(0,0)

	def similar(self, similarity):
		""" Returns a new Pattern with the specified similarity threshold """
		return Pattern(self.path, similarity)

	def exact(self):
		""" Returns a new Pattern with a similarity threshold of 1.0 """
		return Pattern(self.path, 1.0)

	def targetOffset(self, dx, dy):
		""" Returns a new Pattern with the given target offset """
		return Pattern(self.path, self.similarity, Location(dx, dy))

	def getFilename(self):
		""" Returns the path to this Pattern's bitmap """
		return self.path

	def getTargetOffset(self):
		""" Returns the target offset as a Location(dx, dy) """
		return self.offset

class Region(object):
	def __init__(self, x, y, w, h):
		self.setROI(x, y, w, h)
		self._lastMatch = None
		self._lastMatches = []
		self._lastMatchTime = 0
		self.autoWaitTimeout = 3.0
		self._defaultScanRate = 0.33
		self._defaultMouseSpeed = 1
		self._defaultTypeSpeed = 0.05
		self._raster = (0,0)

	def setX(self, x):
		""" Set the x-coordinate of the upper left-hand corner """
		self.x = int(x)
	def setY(self, y):
		""" Set the y-coordinate of the upper left-hand corner """
		self.y = int(y)
	def setW(self, w):
		""" Set the width of the region """
		self.w = int(w)
	def setH(self, h):
		""" Set the height of the region """
		self.h = int(h)

	def getX(self):
		""" Get the x-coordinate of the upper left-hand corner """
		return self.x
	def getY(self):
		""" Get the y-coordinate of the upper left-hand corner """
		return self.y
	def getW(self):
		""" Get the width of the region """
		return self.w
	def getH(self):
		""" Get the height of the region """
		return self.h

	def moveTo(self, location):
		""" Change the upper left-hand corner to a new ``Location`` (without changing width or height) """
		if not location or not isinstance(location, Location):
			raise ValueError("moveTo expected a Location object")
		self.x = location.x
		self.y = location.y
		return self

	def setROI(self, x, y, w, h):
		""" Set Region of Interest (same as Region.setRect()) """
		self.setX(x)
		self.setY(y)
		self.setW(w)
		self.setH(h)
	setRect = setROI

	def morphTo(self, region):
		""" Change shape of this region to match the given ``Region`` object """
		if not region or not isinstance(region, Region):
			raise TypeError("morphTo expected a Region object")
		self.setROI(region.x, region.y, region.w, region.h)
		return self

	def getCenter(self):
		""" Return the ``Location`` of the center of this region """
		return Location(self.x+(self.w/2), self.y+(self.h/2))
	def getTopLeft(self):
		""" Return the ``Location`` of the top left corner of this region """
		return Location(self.x, self.y)
	def getTopRight(self):
		""" Return the ``Location`` of the top right corner of this region """
		return Location(self.x+self.w, self.y)
	def getBottomLeft(self):
		""" Return the ``Location`` of the bottom left corner of this region """
		return Location(self.x, self.y+self.h)
	def getBottomRight(self):
		""" Return the ``Location`` of the bottom right corner of this region """
		return Location(self.x+self.w, self.y+self.h)

	def getScreen(self):
		""" Return an instance of the ``Screen`` object representing the screen this region is inside.

		Checks the top left corner of this region (if it touches multiple screens) is inside. Returns None if the region isn't positioned in any screen. """
		screens = PlatformManager.getScreenDetails()
		for screen in screens:
			s_x, s_y, s_w, s_h = screen["rect"]
			if (self.x >= s_x) and (self.x < s_x + s_w) and (self.y >= s_y) and (self.y < s_y + s_h):
				# Top left corner is inside screen region
				return Screen(screens.index(screen))
		return None # Could not find matching screen

	def getLastMatch(self):
		""" Returns the last successful ``Match`` returned by ``find()``, ``exists()``, etc. """
		return self._lastMatch
	def getLastMatches(self):
		""" Returns the last successful set of ``Match`` objects returned by ``findAll()`` """
		return self._lastMatches
	def getTime(self):
		""" Returns the elapsed time in milliseconds to find the last match """
		return self._lastMatchTime

	def setAutoWaitTimeout(self, seconds):
		""" Specify the time to wait for an image to appear on the screen """
		self.autoWaitTimeout = float(seconds)
	def getAutoWaitTimeout(self):
		""" Returns the time to wait for an image to appear on the screen """
		return self.autoWaitTimeout
	def setWaitScanRate(self, seconds):
		"""Set this Region's scan rate: A find op should repeat the search for the given Visual rate times per second until found or the maximum waiting time is reached."""
		if seconds == 0:
			seconds = 3
		self._defaultScanRate = 1/seconds
	def getWaitScanRate(self):
		""" Get the current scan rate """
		return 1/self._defaultScanRate

	def offset(self, location):
		""" Returns a new ``Region`` of the same width and height, but offset from this one by ``location`` """
		r = Region(self.x+location.x, self.y+location.y, self.w, self.h).clipRegionToScreen()
		if r is None:
			raise FindFailed("Specified region is not visible on any screen")
			return None
		return r
	def grow(self, width, height=None):
		""" Expands the region by ``width`` on both sides and ``height`` on the top and bottom.

		If only one value is provided, expands the region by that amount on all sides (equivalent to ``nearby()``).
		"""
		if height is None:
			return self.nearby(width)
		else:
			return Region(self.x-width, self.y-height, self.w+(2*width), self.h+(2*height)).clipRegionToScreen()
	def inside(self):
		""" Returns the same object. Included for Sikuli compatibility. """
		return self
	def nearby(self, expand):
		""" Returns a new Region that includes the nearby neighbourhood of the the current region. 

		The new region is defined by extending the current region's dimensions in 
		all directions by range number of pixels. The center of the new region remains the 
		same. 
		"""
		return Region(self.x-expand, self.y-expand, self.w+(2*expand), self.h+(2*expand)).clipRegionToScreen()
	def above(self, expand):
		""" Returns a new Region that is defined above the current region's top border with a height of range number of pixels. 

		So it does not include the current region. If range is omitted, it reaches to the top of the screen. 
		The new region has the same width and x-position as the current region. 
		"""
		if expand == None:
			x = self.x
			y = 0
			w = self.w
			h = self.y
		else:
			x = self.x
			y = self.y - expand
			w = self.w
			h = expand
		return Region(x, y, w, h).clipRegionToScreen()
	def below(self, expand):
		""" Returns a new Region that is defined below the current region's bottom border with a height of range number of pixels. 

		So it does not include the current region. If range is omitted, it reaches to the bottom of the screen. 
		The new region has the same width and x-position as the current region. 
		"""
		if expand == None:
			x = self.x
			y = self.y+self.h
			w = self.w
			h = self.screen.getBounds()[1][1] - y # Screen height
		else:
			x = self.x
			y = self.y + self.h
			w = self.w
			h = expand
		return Region(x, y, w, h).clipRegionToScreen()
	def left(self, expand):
		""" Returns a new Region that is defined left of the current region's left border with a width of range number of pixels. 

		So it does not include the current region. If range is omitted, it reaches to the left border of the screen. 
		The new region has the same height and y-position as the current region. 
		"""
		if expand == None:
			x = 0
			y = self.y
			w = self.x
			h = self.h
		else:
			x = self.x-expand
			y = self.y
			w = expand
			h = self.h
		return Region(x, y, w, h).clipRegionToScreen()
	def right(self, expand):
		""" Returns a new Region that is defined right of the current region's right border with a width of range number of pixels. 

		So it does not include the current region. If range is omitted, it reaches to the right border of the screen. 
		The new region has the same height and y-position as the current region. 
		"""
		if expand == None:
			x = self.x+self.w
			y = self.y
			w = self.screen.getBounds()[1][0] - x
			h = self.h
		else:
			x = self.x+self.w
			y = self.y
			w = expand
			h = self.h
		return Region(x, y, w, h).clipRegionToScreen()

	def getBitmap(self):
		""" Captures screen area of this region, at least the part that is on the screen 
		
		Returns image as numpy array
		"""
		return PlatformManager.getBitmapFromRect(self.x, self.y, self.w, self.h)
	def debugPreview(self, title="Debug"):
		""" Displays the region in a preview window. 

		If the region is a Match, circles the target area. If the region is larger than half the 
		primary screen in either dimension, scales it down to half size.
		"""
		region = self
		haystack = self.getBitmap()
		if isinstance(region, Match):
			cv2.circle(haystack, (region.getTarget().x - self.x, region.getTarget().y - self.y), 5, 255)
		if haystack.shape[0] > (Screen(0).getBounds()[2]/2) or haystack.shape[1] > (Screen(0).getBounds()[3]/2):
			# Image is bigger than half the screen; scale it down
			haystack = cv2.resize(haystack, (0,0), fx=0.5, fy=0.5)
		cv2.imshow(title, haystack)
		cv2.waitKey(0)
		cv2.destroyAllWindows()
	def highlight(self):
		""" Temporarily using ``debugPreview()`` to show the region instead of highlighting it

		Probably requires transparent GUI creation/manipulation. TODO
		"""
		return self.debugPreview()
		#raise NotImplementedError("highlight not yet supported.")

	def find(self, pattern, seconds=None):
		""" Searches for an image pattern in the given region

		Throws ``FindFailed`` exception if the image could not be found.
		Sikuli supports OCR search with a text parameter. This does not (yet).
		"""
		match = self.exists(pattern, seconds)
		if match is None:
			path = pattern.path if isinstance(pattern, Pattern) else pattern
			raise FindFailed("Could not find pattern '{}'".format(path))
			return None
		return match
	def findAll(self, pattern, seconds=None):
		""" Searches for an image pattern in the given region
		
		Returns ``Match`` object if ``pattern`` exists, empty array otherwise (does not throw exception)
		Sikuli supports OCR search with a text parameter. This does not (yet).
		"""
		find_time = time.time()
		r = self.clipRegionToScreen()
		if r is None:
			raise FindFailed("Region outside all visible screens")
			return None
		if seconds is None:
			seconds = self.autoWaitTimeout
		if isinstance(pattern, int):
			time.sleep(pattern)
			return
		if not pattern:
			time.sleep(seconds)
		if not isinstance(pattern, Pattern):
			if not isinstance(pattern, basestring):
				raise TypeError("find expected a string [image path] or Pattern object")
			pattern = Pattern(pattern)
		needle = cv2.imread(pattern.path)
		if needle is None:
			raise ValueError("Unable to load image '{}'".format(pattern.path))
		needle_height, needle_width, needle_channels = needle.shape
		positions = []
		timeout = time.time() + seconds
		method = cv2.TM_CCOEFF_NORMED
		while time.time() < timeout:
			haystack = r.getBitmap()
			match = cv2.matchTemplate(haystack,needle,method)
			indices = (-match).argpartition(100, axis=None)[:100] # Review the 100 top matches
			unraveled_indices = numpy.array(numpy.unravel_index(indices, match.shape)).T
			for location in unraveled_indices:
				y, x = location
				confidence = match[y][x]
				if method == cv2.TM_SQDIFF_NORMED or method == cv2.TM_SQDIFF:
					if confidence <= 1-pattern.similarity:
						positions.append((x,y,confidence))
				else:
					if confidence >= pattern.similarity:
						positions.append((x,y,confidence))
			time.sleep(self._defaultScanRate)
			if len(positions) > 0:
				break
		lastMatches = []
		
		if len(positions) == 0:
			print("Couldn't find '{}' with enough similarity.".format(pattern.path))
			return None
		# Translate local position into global screen position
		positions.sort(key=lambda x: (x[1], -x[0]))
		for position in positions:
			x, y, confidence = position
			lastMatches.append(Match(confidence, pattern.offset, ((x+self.x, y+self.y), (needle_width, needle_height))))
		self._lastMatches = iter(lastMatches)
		print("Found {} match(es) for pattern '{}' at similarity ({})".format(len(self._lastMatches), pattern.path, pattern.similarity))
		self._lastMatchTime = (time.time() - find_time) * 1000 # Capture find time in milliseconds
		return self._lastMatches
	def wait(self, pattern, seconds=None):
		""" Searches for an image pattern in the given region, given a specified timeout period

		Functionally identical to find()
		Sikuli supports OCR search with a text parameter. This does not (yet).
		"""
		return self.find(pattern, seconds)
	def waitVanish(self, pattern, seconds=None):
		""" Waits until the specified pattern is not visible on screen. 

		If ``seconds`` pass and the pattern is still visible, raises FindFailed exception.
		Sikuli supports OCR search with a text parameter. This does not (yet).
		"""
		r = self.clipRegionToScreen()
		if r is None:
			raise FindFailed("Region outside all visible screens")
			return None
		if seconds is None:
			seconds = self.autoWaitTimeout
		if isinstance(pattern, int):
			time.sleep(pattern)
			return
		if not pattern:
			time.sleep(seconds)
		if not isinstance(pattern, Pattern):
			if not isinstance(pattern, basestring):
				raise TypeError("find expected a string [image path] or Pattern object")
			pattern = Pattern(pattern)

		tolerance = pattern.getTolerance()
		needle = cv2.imread(pattern.path)
		#needle = cv2.cvtColor(needle, cv2.COLOR_BGR2GRAY)
		position = True
		timeout = time.time() + seconds
		method = cv2.TM_CCOEFF_NORMED
		while not position and time.time() < timeout:
			haystack = r.getBitmap()
			match = cv2.matchTemplate(haystack,needle,method)
			min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(match)
			if method == cv2.TM_SQDIFF_NORMED or method == cv2.TM_SQDIFF:
				confidence = min_val
				best_loc = min_loc
				if min_val <= 1-pattern.similarity:
					# Confidence checks out
					position = min_loc
			else:
				confidence = max_val
				best_loc = max_loc
				if max_val >= pattern.similarity:
					# Confidence checks out
					position = max_loc
			time.sleep(self._defaultScanRate)
		if position:
			return False
			#self._findFailedHandler(FindFailed("Pattern '{}' did not vanish".format(pattern.path)))
	def exists(self, pattern, seconds=None):
		""" Searches for an image pattern in the given region
		
		Returns Match if pattern exists, None otherwise (does not throw exception)
		Sikuli supports OCR search with a text parameter. This does not (yet).
		"""
		find_time = time.time()
		r = self.clipRegionToScreen()
		if r is None:
			raise FindFailed("Region outside all visible screens")
			return None
		if seconds is None:
			seconds = self.autoWaitTimeout
		if isinstance(pattern, int):
			# Actually just a "wait" statement
			time.sleep(pattern)
			return
		if not pattern:
			time.sleep(seconds)
		if not isinstance(pattern, Pattern):
			if not isinstance(pattern, basestring):
				raise TypeError("find expected a string [image path] or Pattern object")
			pattern = Pattern(pattern)
		needle = cv2.imread(pattern.path)
		if needle is None:
			raise ValueError("Unable to load image '{}'".format(pattern.path))
		needle_height, needle_width, needle_channels = needle.shape
		position = None
		timeout = time.time() + seconds
		method = cv2.TM_CCOEFF_NORMED
		while not position and time.time() < timeout:
			haystack = r.getBitmap()
			match = cv2.matchTemplate(haystack,needle,method)
			min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(match)
			if method == cv2.TM_SQDIFF_NORMED or method == cv2.TM_SQDIFF:
				confidence = min_val
				best_loc = min_loc
				if min_val <= 1-pattern.similarity:
					# Confidence checks out
					position = min_loc
			else:
				confidence = max_val
				best_loc = max_loc
				if max_val >= pattern.similarity:
					# Confidence checks out
					position = max_loc
			time.sleep(self._defaultScanRate)
		if not position:
			print("Couldn't find '{}' with enough similarity. Best match {} at ({},{})".format(pattern.path, confidence, best_loc[0], best_loc[1]))
			return None
		# Translate local position into global screen position
		position = (position[0] + self.x, position[1] + self.y)
		self._lastMatch = Match(confidence, pattern.offset, (position, (needle_width, needle_height)))
		#self._lastMatch.debug_preview()
		print("Found match for pattern '{}' at ({},{}) with confidence ({}). Target at ({},{})".format(pattern.path, self._lastMatch.getX(), self._lastMatch.getY(), self._lastMatch.getScore(), self._lastMatch.getTarget().x, self._lastMatch.getTarget().y))
		self._lastMatchTime = (time.time() - find_time) * 1000 # Capture find time in milliseconds
		return self._lastMatch

	def click(self, target, modifiers=""):
		""" Moves the cursor to the target location and clicks the default mouse button. """
		target_location = None
		mouse = Mouse()
		if isinstance(target, Pattern):
			target_location = self.find(target).getTarget()
		elif isinstance(target, basestring):
			target_location = self.find(target).getTarget()
		elif isinstance(target, Match):
			target_location = target.getTarget()
		elif isinstance(target, Region):
			target_location = target.getCenter()
		elif isinstance(target, Location):
			target_location = target
		elif target is None and isinstance(self._lastMatch, Match):
			target_location = self._lastMatch.getTarget()
		else:
			raise TypeError("click expected Pattern, String, Match, Region, or Location object")
		if modifiers != "":
			PlatformManager.pressKey(modifiers)

		mouse.moveSpeed(target_location, self._defaultMouseSpeed)
		mouse.click()
		time.sleep(0.2)

		if modifiers != 0:
			PlatformManager.releaseKey(modifiers)
	def doubleClick(self, target, modifiers=0):
		""" Moves the cursor to the target location and double-clicks the default mouse button. """
		target_location = None
		mouse = Mouse()
		if isinstance(target, Pattern):
			target_location = self.find(target).getTarget()
		elif isinstance(target, basestring):
			target_location = self.find(target).getTarget()
		elif isinstance(target, Match):
			target_location = target.getTarget()
		elif isinstance(target, Region):
			target_location = target.getCenter()
		elif isinstance(target, Location):
			target_location = target
		else:
			raise TypeError("doubleClick expected Pattern, String, Match, Region, or Location object")
		if modifiers != "":
			PlatformManager.pressKey(modifiers)

		mouse.moveSpeed(target_location, self._defaultMouseSpeed)
		mouse.click()
		time.sleep(0.1)
		mouse.click()
		time.sleep(0.2)

		if modifiers != 0:
			key.toggle('', False, modifiers)
	def rightClick(self, target, modifiers=0):
		""" Moves the cursor to the target location and clicks the right mouse button. """
		target_location = None
		mouse = Mouse()
		if isinstance(target, Pattern):
			target_location = self.find(target).getTarget()
		elif isinstance(target, basestring):
			target_location = self.find(target).getTarget()
		elif isinstance(target, Match):
			target_location = target.getTarget()
		elif isinstance(target, Region):
			target_location = target.getCenter()
		elif isinstance(target, Location):
			target_location = target
		else:
			raise TypeError("rightClick expected Pattern, String, Match, Region, or Location object")

		if modifiers != "":
			PlatformManager.pressKey(modifiers)

		mouse.moveSpeed(target_location, self._defaultMouseSpeed)
		mouse.click(button=autopy.mouse.RIGHT_BUTTON)
		time.sleep(0.2)

		if modifiers != "":
			PlatformManager.releaseKey(modifiers)

	def hover(self, target):
		""" Moves the cursor to the target location """
		target_location = None
		mouse = Mouse()
		if isinstance(target, Pattern):
			target_location = self.find(target).getTarget()
		elif isinstance(target, basestring):
			target_location = self.find(target).getTarget()
		elif isinstance(target, Match):
			target_location = target.getTarget()
		elif isinstance(target, Region):
			target_location = target.getCenter()
		elif isinstance(target, Location):
			target_location = target
		else:
			raise TypeError("hover expected Pattern, String, Match, Region, or Location object")

		mouse.moveSpeed(target_location, self._defaultMouseSpeed)
	def drag(self, dragFrom):
		""" Moves the cursor to the target location and clicks the mouse in preparation to drag a screen element """
		dragFromLocation = None
		mouse = Mouse()
		if isinstance(dragFrom, Pattern):
			dragFromLocation = self.find(dragFrom).getTarget()
		elif isinstance(dragFrom, basestring):
			dragFromLocation = self.find(dragFrom).getTarget()
		elif isinstance(dragFrom, Match):
			dragFromLocation = dragFrom.getTarget()
		elif isinstance(dragFrom, Region):
			dragFromLocation = dragFrom.getCenter()
		elif isinstance(dragFrom, Location):
			dragFromLocation = dragFrom
		else:
			raise TypeError("drag expected dragFrom to be Pattern, String, Match, Region, or Location object")
		mouse.moveSpeed(dragFromLocation, self._defaultMouseSpeed)
		mouse.buttonDown()
		return 1
	def dropAt(self, dragTo, delay=0.2):
		""" Moves the cursor to the target location, waits ``delay`` seconds, and releases the mouse button """
		if isinstance(dragTo, Pattern):
			dragToLocation = self.find(dragTo).getTarget()
		elif isinstance(dragTo, basestring):
			dragToLocation = self.find(dragTo).getTarget()
		elif isinstance(dragTo, Match):
			dragToLocation = dragTo.getTarget()
		elif isinstance(dragTo, Region):
			dragToLocation = dragTo.getCenter()
		elif isinstance(dragTo, Location):
			dragToLocation = dragTo
		else:
			raise TypeError("dragDrop expected dragTo to be Pattern, String, Match, Region, or Location object")

		mouse.moveSpeed(dragToLocation, self._defaultMouseSpeed)
		time.sleep(delay)
		mouse.buttonUp()
		return 1
	def dragDrop(self, dragFrom, dragTo, modifiers=""):
		""" Holds down the mouse button on ``dragFrom``, moves the mouse to ``dragTo``, and releases the mouse button 
		
		``modifiers`` may be a typeKeys() compatible string. The specified keys will be held during the drag-drop operation.
		"""
		if modifiers != "":
			PlatformManager.pressKey(modifiers)
		
		drag(dragFrom)
		dropAt(dragTo, 0.1)
		
		if modifiers != "":
			PlatformManager.releaseKey(modifiers)

	def type(self, *args):
		""" Usage: type([PSMRL], text, [modifiers])
		
		If a pattern is specified, the pattern is clicked first. Doesn't support text paths.
		``modifiers`` may be a typeKeys() compatible string. The specified keys will be held during the drag-drop operation.
		"""
		pattern = None
		text = None
		modifiers = None
		if len(args) == 1 and isinstance(args[0], basestring):
			# Is a string (or Key) to type
			text = args[0]
		elif len(args) == 2:
			if not isinstance(args[0], basestring) and isinstance(args[1], basestring):
				pattern = args[0]
				text = args[1]
			else:
				text = args[0]
				modifiers = args[1]
		elif len(args) == 3 and not isinstance(args[0], basestring):
			pattern = args[0]
			text = args[1]
			modifiers = args[2]
		else:
			raise TypeError("type method expected ([PSMRL], text, [modifiers])")

		if pattern:
			self.click(pattern)

		# Patch some Sikuli special codes
		text = text.replace("{PGDN}", "{PAGE_DOWN}")
		text = text.replace("{PGUP}", "{PAGE_UP}")

		print("Typing '{}'".format(text))
		kb = Keyboard()
		if modifiers:
			kb.keyDown(modifiers)
		kb.type(text, self._defaultTypeSpeed)
		if modifiers:
			kb.keyUp(modifiers)
		time.sleep(0.2)
	def paste(self, *args):
		""" Usage: paste([PSMRL], text)
		
		If a pattern is specified, the pattern is clicked first. Doesn't support text paths.
		``text`` is pasted as is using the OS paste shortcut (Ctrl+V for Windows/Linux, Cmd+V for OS X). Note that `paste()` does NOT use special formatting like `type()`.
		"""
		target = None
		text = ""
		if len(args) == 1 and isinstance(args[0], basestring):
			text = args[0]
		elif len(args) == 2 and isinstance(args[1], basestring):
			self.click(target)
			text = args[1]
		else:
			raise TypeError("paste method expected [PSMRL], text")

		PlatformManager.setClipboard(text)
		# Triggers OS paste for foreground window
		PlatformManager.osPaste()
		time.sleep(0.2)
	def getClipboard(self):
		""" Returns the contents of the clipboard (can be used to pull outside text into the application) """
		return PlatformManager.getClipboard()
	def text(self):
		""" OCR method. Todo. """
		raise NotImplementedError("OCR not yet supported")

	def mouseDown(self, button):
		""" Low-level mouse actions. Todo """
		return PlatformManager.mouseButtonDown(button)
	def mouseUp(self, button):
		""" Low-level mouse actions """
		return PlatformManager.mouseButtonUp(button)
	def mouseMove(self, PSRML):
		""" Low-level mouse actions """
		Mouse().moveSpeed(PSRML)
	def wheel(self, PSRML, direction, steps):
		""" Clicks the wheel the specified number of ticks """
		self.mouseMove(PSRML)
		Mouse().wheel(direction, steps)
	def keyDown(self, keys):
		""" Concatenate multiple keys to press them all down. """
		return Keyboard().keyDown(keys)
	def keyUp(self, *keys):
		""" Concatenate multiple keys to up them all. """
		return Keyboard().keyUp(keys)

	def isRegionValid(self):
		""" Returns false if the whole region is outside any screen, otherwise true """
		screens = PlatformManager.getScreenDetails()
		for screen in screens:
			s_x, s_y, s_w, s_h = screen["rect"]
			if (self.x+self.w < s_x or s_x+s_w < self.x or self.y+self.h < s_y or s_y+s_h < self.y):
				# Rects overlap
				return True
		return False

	def clipRegionToScreen(self):
		""" Returns the part of the region that is visible on a screen (or the screen with the smallest ID, if the region is visible on multiple screens). 

		Returns None if the region is outside the screen. 
		"""
		if not self.isRegionValid():
			return None
		screens = PlatformManager.getScreenDetails()
		containing_screen = None
		for screen in screens:
			s_x, s_y, s_w, s_h = screen["rect"]
			if (self.x >= s_x and self.x+self.w <= s_x+s_w and self.y >= s_y and self.y+self.h <= s_y+s_h):
				# Region completely inside screen
				return self
			elif (self.x+self.w < s_x or s_x+s_w < self.x or self.y+self.h < s_y or s_y+s_h < self.y):
				containing_screen = screen
				break
		x = max(self.x, s_x)
		y = max(self.y, s_y)
		w = min(self.w, s_w)
		h = min(self.h, s_h)
		return Region(x,y,w,h)


	# Partitioning constants
	NORTH 			= 202 # Upper half
	NORTH_WEST 		= 300 # Left third in upper third
	NORTH_MID 		= 301 # Middle third in upper third
	NORTH_EAST 		= 302 # Right third in upper third
	SOUTH 			= 212 # Lower half
	SOUTH_WEST 		= 320 # Left third in lower third
	SOUTH_MID 		= 321 # Middle third in lower third
	SOUTH_EAST 		= 322 # Right third in lower third
	EAST 			= 220 # Right half
	EAST_MID 		= 310 # Middle third in right third
	WEST 			= 221 # Left half
	WEST_MID 		= 312 # Middle third in left third
	MID_THIRD 		= 311 # Middle third in middle third
	TT 				= 200 # Top left quarter
	RR 				= 201 # Top right quarter
	BB 				= 211 # Bottom right quarter
	LL 				= 210 # Bottom left quarter

	MID_VERTICAL 	= "MID_VERT" # Half of width vertically centered
	MID_HORIZONTAL	= "MID_HORZ" # Half of height horizontally centered
	MID_BIG			= "MID_HALF" # Half of width/half of height centered
	
	def setRaster(self, rows, columns):
		""" Sets the raster for the region, allowing sections to be indexed by row/column """
		rows = int(rows)
		columns = int(columns)
		if rows <= 0 or columns <= 0:
			return self
		self._raster = (rows,columns)
		return self.getCell(0,0)
	def getRow(self, row):
		""" Returns the specified row of the region (if the raster is set) """
		row = int(row)
		if self._raster[0] == 0 or self._raster[1] == 0:
			return self
		rowHeight = self.h / self._raster[0]
		if row < 0:
			# If row is negative, count backwards from the end
			row = self._raster[0] - row
			if row < 0:
				# Bad row index, return last row
				return Region(self.x, self.y+self.h-rowHeight, self.w, rowHeight)
		elif row > self._raster[0]:
			# Bad row index, return first row
			return Region(self.x, self.y, self.w, rowHeight)
		return Region(self.x, self.y + (row * rowHeight), self.w, rowHeight)
	def getCol(self, column):
		""" Returns the specified column of the region (if the raster is set) """
		column = int(column)
		if self._raster[0] == 0 or self._raster[1] == 0:
			return self
		columnWidth = self.w / self._raster[1]
		if column < 0:
			# If column is negative, count backwards from the end
			column = self._raster[1] - column
			if column < 0:
				# Bad column index, return last column
				return Region(self.x+self.w-columnWidth, self.y, columnWidth, self.h)
		elif column > self._raster[1]:
			# Bad column index, return first column
			return Region(self.x, self.y, columnWidth, self.h)
		return Region(self.x + (column * columnWidth), self.y, columnWidth, self.h)
	def getCell(self, row, column):
		""" Returns the specified cell (if a raster is set for the region) """
		row = int(row)
		column = int(column)
		if self._raster[0] == 0 or self._raster[1] == 0:
			return self
		rowHeight = self.h / self._raster[0]
		columnWidth = self.h / self._raster[1]
		if column < 0:
			# If column is negative, count backwards from the end
			column = self._raster[1] - column
			if column < 0:
				# Bad column index, return last column
				column = self._raster[1]
		elif column > self._raster[1]:
			# Bad column index, return first column
			column = 0
		if row < 0:
			# If row is negative, count backwards from the end
			row = self._raster[0] - row
			if row < 0:
				# Bad row index, return last row
				row = self._raster[0]
		elif row > self._raster[0]:
			# Bad row index, return first row
			row = 0
		return Region(self.x+(column*columnWidth), self.y+(row*rowHeight), columnWidth, rowHeight)
	def get(self, part):
		""" Returns a section of the region as a new region

		Accepts partitioning constants, e.g. Region.NORTH, Region.NORTH_WEST, etc.
		Also accepts an int 200-999:
		* First digit:  Raster (*n* rows by *n* columns)
		* Second digit: Row index (if equal to raster, gets the whole row)
		* Third digit:  Column index (if equal to raster, gets the whole column)

		Region.get(522) will use a raster of 5 rows and 5 columns and return 
		the cell in the middle.

		Region.get(525) will use a raster of 5 rows and 5 columns and return the row in the middle.
		"""
		if part == self.MID_VERTICAL:
			return Region(self.x+(self.w/4), y, self.w/2, self.h)
		elif part == self.MID_HORIZONTAL:
			return Region(self.x,self.y+(self.h/4), self.w, self.h/2)
		elif part == self.MID_BIG:
			return Region(self.x+(self.w/4),self.y+(self.h/4), self.w/2, self.h/2)
		elif isinstance(part, int) and part >= 200 and part <= 999:
			raster, row, column = str(part)
			self.setRaster(raster,raster)
			#print self._raster
			if row == raster and column == raster:
				return self
			elif row == raster:
				return self.getCol(column)
			elif column == raster:
				return self.getRow(row)
			else:
				return self.getCell(row,column)
		else:
			return self
	def setRows(self, rows):
		""" Sets the number of rows in the raster (if columns have not been initialized, set to 1 as well) """
		self._raster[0] = rows
		if self._raster[1] == 0:
			self._raster[1] = 1
	def setCols(self, columns):
		""" Sets the number of columns in the raster (if rows have not been initialized, set to 1 as well) """
		self._raster[1] = columns
		if self._raster[0] == 0:
			self._raster[0] = 1
	def isRasterValid(self):
		return self.getCols() > 0 and self.getRows() > 0
	def getRows():
		return self._raster[0]
	def getCols():
		return self._raster[1]
	def getRowH():
		if self._raster[0] == 0:
			return 0
		return self.h / self._raster[0]
	def getColW():
		if self._raster[1] == 0:
			return 0
		return self.w / self._raster[1]

class Match(Region):
	""" Extended Region object with additional data on click target, match score """
	def __init__(self, score, target, rect):
		super(Match, self).__init__(rect[0][0], rect[0][1], rect[1][0], rect[1][1])
		self._score = float(score)
		if not target or not isinstance(target, Location):
			raise TypeError("Match expected target to be a Location object")
		self._target = target

	def getScore(self):
		""" Returns confidence score of the match """
		return self._score

	def getTarget(self):
		""" Returns the location of the match click target (center by default, but may be offset) """
		return self.getCenter().offset(self._target.x, self._target.y)

	def __repr__(self):
		return "Match[{},{} {}x{}] score={.2f}, target={}".format(self.x, self.y, self.w, self.h, self._score, self.target.getTuple())

class Screen(Region):
	""" Individual screen objects can be created for each monitor in a multi-monitor system. 

	Screens are indexed according to the system order. 0 is the primary monitor (display 1), 1 is the next monitor, etc.

	Lackey also makes it possible to search all screens as a single "virtual screen," arranged
	according to the system's settings. Screen(-1) returns this virtual screen. Note that the
	larger your search region is, the slower your search will be, so it's best practice to adjust
	your region to the particular area of the screen where you know your target will be.

	Note that Sikuli is inconsistent in identifying screens. In Windows, Sikuli identifies the
	first hardware monitor as Screen(0) rather than the actual primary monitor. However, on OS X
	it follows the latter convention. We've opted to make Screen(0) the actual primary monitor
	(wherever the Start Menu/System Menu Bar is) across the board.
	"""
	def __init__(self, screenId=None):
		""" Defaults to the main screen. """
		if not isinstance(screenId, int) or screenId < -1 or screenId >= len(PlatformManager.getScreenDetails()):
			screenId = 0
		self._screenId = screenId
		x, y, w, h = self.getBounds()
		super(Screen, self).__init__(x, y, w, h)
	def getNumberScreens(self):
		""" Get the number of screens in a multi-monitor environment at the time the script is running """
		return len(PlatformManager.getScreenDetails())
	def getBounds(self):
		""" Returns bounds of screen as (x, y, w, h) """
		return PlatformManager.getScreenBounds(self._screenId)
	def capture(self, x=None, y=None, w=None, h=None):
		""" Captures the region as an image and saves to a temporary file (specified by TMPDIR, TEMP, or TMP environmental variable) """
		if x is None:
			region = self
		elif isinstance(x, Region):
			region = x
		elif isinstance(x, tuple):
			region = Region(*x)
		elif isinstance(x, basestring):
			# Interactive mode
			raise NotImplementedError("Interactive capture mode not defined")
		elif isinstance(x, int):
			region = Region(x, y, w, h)
		bitmap = region.getBitmap()
		tfile, tpath = tempfile.mkstemp(".png")
		cv2.imwrite(tpath, bitmap)
		return tpath
	def selectRegion(self, text=""):
		""" Not yet implemented """
		raise NotImplementedError()

class Location(object):
	""" Basic 2D point object """
	def __init__(self, x, y):
		self.setLocation(x, y)

	def getX(self):
		""" Returns the X-component of the location """
		return self.x
	def getY(self):
		""" Returns the Y-component of the location """
		return self.y

	def setLocation(self, x, y):
		"""Set the location of this object to the specified coordinates."""
		self.x = int(x)
		self.y = int(y)

	def offset(self, dx, dy):
		"""Get a new location which is dx and dy pixels away horizontally and vertically from the current location."""
		return Location(self.x+dx, self.y+dy)

	def above(self, dy):
		"""Get a new location which is dy pixels vertically above the current location."""
		return Location(self.x, self.y-dy)
	def below(self, dy):
		"""Get a new location which is dy pixels vertically below the current location."""
		return Location(self.x, self.y+dy)
	def left(self, dx):
		"""Get a new location which is dx pixels horizontally to the left of the current location."""
		return Location(self.x-dx, self.y)
	def right(self, dx):
		"""Get a new location which is dx pixels horizontally to the right of the current location."""
		return Location(self.x+dx, self.y)

	def getTuple(self):
		""" Returns coordinates as a tuple (for some PlatformManager methods) """
		return (self.x, self.y)

	def __repr__(self):
		return "(Location object at ({},{}))".format(self.x, self.y)

class Mouse(object):
	""" Mid-level mouse routines. Interfaces with ``PlatformManager`` """
	def __init__(self):
		self._defaultScanRate = 0.01
	
	# Class constants
	WHEEL_DOWN = 0
	WHEEL_UP = 1
	LEFT = 0
	MIDDLE = 1
	RIGHT = 2

	def move(self, location):
		""" Moves cursor to specified ``Location`` """

		# Check if move point is outside a monitor rectangle
		if not PlatformManager.isPointVisible(location.x, location.y):
			# move point is outside a monitor rectangle. Snap to closest edge of primary monitor.
			s_x, s_y, s_w, s_h = Screen(0).getBounds()
			location.x = min(max(location.x, s_x), s_x+s_w)
			location.y = min(max(location.y, s_y), s_y+s_h)

		PlatformManager.setMousePos(location.getTuple())

	def getPos(self):
		""" Gets ``Location`` of cursor """
		x, y = PlatformManager.getMousePos()
		return Location(x, y)

	def moveSpeed(self, location, seconds=1):
		""" Moves cursor to specified ``Location`` over ``seconds``. 

		If ``seconds`` is 0, moves the cursor immediately. Used for smooth
		somewhat-human-like motion.
		"""
		if seconds == 0:
			# If the mouse isn't on the main screen, snap to point automatically instead of trying to track a path back
			self.move(location)
			return

		# Check if move point is outside a monitor rectangle
		if not PlatformManager.isPointVisible(location.x, location.y):
			# move point is outside a monitor rectangle. Snap to closest edge of primary monitor.
			s_x, s_y, s_w, s_h = Screen(0).getBounds()
			location.x = min(max(location.x, s_x), s_x+s_w)
			location.y = min(max(location.y, s_y), s_y+s_h)

		frames = int(seconds*0.1 / self._defaultScanRate)
		while frames > 0:
			mouse_pos = self.getPos()
			deltax = int(round(float(location.x - mouse_pos.x) / frames))
			deltay = int(round(float(location.y - mouse_pos.y) / frames))
			self.move(Location(mouse_pos.x + deltax, mouse_pos.y + deltay))
			frames -= 1
			time.sleep(self._defaultScanRate)

	def click(self, button=0):
		""" Clicks the specified mouse button.

		Use Mouse.LEFT, Mouse.MIDDLE, Mouse.RIGHT
		"""
		PlatformManager.clickMouse(button)
	def buttonDown(self, button=0):
		""" Holds down the specified mouse button.

		Use Mouse.LEFT, Mouse.MIDDLE, Mouse.RIGHT
		"""
		PlatformManager.mouseButtonDown(button)
	def buttonUp(self, button=0):
		""" Releases the specified mouse button.

		Use Mouse.LEFT, Mouse.MIDDLE, Mouse.RIGHT
		"""
		PlatformManager.mouseButtonUp(button)
	def wheel(self, direction, steps):
		""" Clicks the wheel the specified number of steps in the given direction.

		Use Mouse.WHEEL_DOWN, Mouse.WHEEL_UP
		"""
		return PlatformManager.mouseWheel(direction, steps)

class Keyboard(object):
	""" Mid-level keyboard routines. Interfaces with ``PlatformManager`` """
	def __init__(self):
		pass

	def keyDown(self, keys):
		""" Holds down the specified keys """
		return PlatformManager.pressKey(keys)
	def keyUp(self, keys):
		""" Releases the specified keys """
		return PlatformManager.releaseKey(keys)
	def type(self, text, delay=0.1):
		""" Types ``text`` with ``delay`` seconds between keypresses """
		return PlatformManager.typeKeys(text, delay)

class Window(object):
	""" Object to select (and perform basic manipulations on) a window. Stores platform-specific window handler """
	def __init__(self, identifier=None):
		self._handle = None
		if identifier:
			self.initialize_wildcard(identifier)

	def initialize_wildcard(self, wildcard):
		""" Gets a window handle based on the wildcard. If there are multiple matches, it only returns one, in no particular order. """
		self._handle = PlatformManager.getWindowByTitle(wildcard)
		return self

	def getRegion(self):
		""" Returns a ``Region`` object corresponding to the window's shape and location. """
		if self._handle is None:
			return None
		x1, y1, x2, y2 = PlatformManager.getWindowRect(self._handle)
		return Region(x1, y1, x2-x1, y2-y1)

	def focus(self, wildcard=None):
		""" Brings the window to the foreground and gives it focus """
		if self._handle is None:
			return self
		PlatformManager.focusWindow(self._handle)
		return self

	def getTitle(self):
		""" Returns the window's title """
		return PlatformManager.getWindowTitle(self._handle)

	def getPID(self):
		""" Returns the PID of the window's parent process """
		if self._handle is None:
			return -1
		return PlatformManager.getWindowPID(self._handle)

class App(Window):
	""" Sikuli compatibility class

	Eventually will allow windows to be selected by title, PID, or by starting an
	application directly.
	"""
	def __init__(self, identifier=None):
		super(App, self).__init__(identifier)
		self.focus = self._focus_instance

	@classmethod
	def focus(cls, wildcard):
		""" Sikuli-compatible "bring window to front" function
		 
		Accessible as App.focus(). Also converts Sikuli wildcard search to Python regex.
		"""
		wildcard_regex = self._convert_sikuli_wildcards(wildcard)
		app = cls(wildcard_regex)
		return app.focus()

	def _focus_instance(self, wildcard=None):
		""" For instances of App, the ``focus()`` classmethod is replaced with this instance method. """
		if wildcard is not None:
			self.initialize_wildcard(wildcard)
		if self._handle is None:
			return self
		PlatformManager.focusWindow(self._handle)
		return self

	def _convert_sikuli_wildcards(self, wildcard):
		""" Converts Sikuli wildcards to Python-compatible regex.

		TODO: Clean up this conversion routine. 
		"""
		return wildcard.replace("\\", "\\\\").replace(".", "\.").replace("*", ".*")