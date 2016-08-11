import platform
import time
import os

from PIL import ImageGrab
import numpy
import cv2

from .PlatformManagerWindows import PlatformManagerWindows
from .Exceptions import FindFailed

if platform.system() == "Windows":
	PlatformManager = PlatformManagerWindows() # No other input managers built yet
else:
	raise NotImplementedError("Pykuli v0.01 is currently only compatible with Windows.")
	
class Pattern(object):
	def __init__(self, path, similarity=0.7, offset=None):
		self.path = path
		self.similarity = similarity
		self.offset = offset or Location(0,0)

	def similar(self, similarity):
		return Pattern(self.path, similarity)

	def exact(self, ):
		return Pattern(self.path, 1.0)

	def targetOffset(self, dx, dy):
		return Pattern(self.path, self.similarity, Location(dx, dy))

	def getFilename(self):
		return self.path

	def getTargetOffset(self):
		return self.offset

	def getTolerance(self):
		# Convert Similarity to Tolerance for autopy
		return 1-self.similarity

class Region(object):
	def __init__(self, x, y, w, h):
		self.setROI(x, y, w, h)
		self.screen = Screen(0)
		self.lastMatch = None
		self.lastMatches = []
		self.autoWaitTimeout = 3.0
		self.defaultScanRate = 0.1
		self.defaultMouseSpeed = 1
		self.defaultTypeSpeed = 0.05

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		return

	def setX(self, x):
		self.x = int(x)
	def setY(self, y):
		self.y = int(y)
	def setW(self, w):
		self.w = int(w)
	def setH(self, h):
		self.h = int(h)

	def getX(self):
		return self.x
	def getY(self):
		return self.y
	def getW(self):
		return self.w
	def getH(self):
		return self.h

	def moveTo(self, location):
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
		if not region or not isinstance(region, Region):
			raise TypeError("morphTo expected a Region object")
		self.setROI(region.x, region.y, region.w, region.h)
		return self

	def getCenter(self):
		return Location(self.x+(self.w/2), self.y+(self.h/2))
	def getTopLeft(self):
		return Location(self.x, self.y)
	def getTopRight(self):
		return Location(self.x+self.w, self.y)
	def getBottomLeft(self):
		return Location(self.x, self.y+self.h)
	def getBottomRight(self):
		return Location(self.x+self.w, self.y+self.h)

	def getScreen(self):
		return self.screen

	def getLastMatch(self):
		return self.lastMatch
	def getLastMatches(self):
		return self.lastMatches

	def setAutoWaitTimeout(self, seconds):
		self.autoWaitTimeout = float(seconds)
	def getAutoWaitTimeout(self):
		return self.autoWaitTimeout

	def offset(self, location):
		return Region(self.x+location.x, self.y+location.y, self.w, self.h)
	def inside(self):
		return self
	def nearby(self, expand):
		return Region(self.x-expand, self.y-expand, self.w+(2*expand), self.h+(2*expand))
	def above(self, expand):
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
		return Region(x, y, w, h)
	def below(self, expand):
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
		return Region(x, y, w, h)
	def left(self, expand):
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
		return Region(x, y, w, h)
	def right(self, expand):
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
		return Region(x, y, w, h)

	def getBitmap(self):
		""" Captures screen area of this region, at least the part that is on the screen """
		max_x, max_y = self.screen.getBounds()[1]
		img = ImageGrab.grab(bbox=(max(0, self.x),max(0, self.y),min(max_x, self.w+self.x),min(max_y, self.y+self.h)))
		img_np = numpy.array(img)
		#img_np = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
		img_np = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
		return img_np

	def find(self, pattern, seconds=None):
		""" Searches for an image pattern in the given region

		Sikuli supports OCR search with a text parameter. This does not.
		"""
		match = self.exists(pattern, seconds)
		if match is None:
			path = pattern.path if isinstance(pattern, Pattern) else pattern
			raise FindFailed("Could not find pattern '{}'".format(path))
		return match
	def findAll(self, pattern, seconds=None):
		""" Searches for an image pattern in the given region
		
		Returns Match if pattern exists, None otherwise (does not throw exception)
		Sikuli supports OCR search with a text parameter. This does not.
		"""
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
			print os.getcwd()
			raise ValueError("Unable to load image '{}'".format(pattern.path))
		needle_height, needle_width, needle_channels = needle.shape
		positions = []
		timeout = time.time() + seconds
		method = cv2.TM_CCOEFF_NORMED
		while time.time() < timeout:
			haystack = self.getBitmap()
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
			time.sleep(self.defaultScanRate)
			if len(positions) > 0:
				break
		self.lastMatches = []
		
		if len(positions) == 0:
			print "Couldn't find '{}' with enough similarity.".format(pattern.path)
			return None
		# Translate local position into global screen position
		positions.sort(key=lambda x: (x[1], -x[0]))
		for position in positions:
			x, y, confidence = position
			self.lastMatches.append(Match(confidence, pattern.offset, ((x+self.x, y+self.y), (needle_width, needle_height))))
		print "Found {} match(es) for pattern '{}' at similarity ({})".format(len(self.lastMatches), pattern.path, pattern.similarity)
		return self.lastMatches

	def wait(self, pattern, seconds=None):
		""" Searches for an image pattern in the given region, given a specified timeout period

		Functionally identical to find()
		Sikuli supports OCR search with a text parameter. This does not.
		"""
		return self.find(pattern, seconds)

	def waitVanish(self, pattern, seconds=None):
		""" Searches for an image pattern in the given region, given a specified timeout period

		Functionally identical to find()
		Sikuli supports OCR search with a text parameter. This does not.
		"""

		""" Searches for an image pattern in the given region

		Sikuli supports OCR search with a text parameter. This does not.
		"""
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
			haystack = self.getBitmap()
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
			time.sleep(self.defaultScanRate)
		if position:
			raise FindFailed("Pattern '{}' did not vanish".format(pattern.path))

	def exists(self, pattern, seconds=None):
		""" Searches for an image pattern in the given region
		
		Returns Match if pattern exists, None otherwise (does not throw exception)
		Sikuli supports OCR search with a text parameter. This does not.
		"""
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
			print os.getcwd()
			raise ValueError("Unable to load image '{}'".format(pattern.path))
		#needle = cv2.cvtColor(needle, cv2.COLOR_BGR2GRAY)
		needle_height, needle_width, needle_channels = needle.shape
		position = None
		timeout = time.time() + seconds
		method = cv2.TM_CCOEFF_NORMED
		while not position and time.time() < timeout:
			haystack = self.getBitmap()
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
			time.sleep(self.defaultScanRate)
		if not position:
			# Debugging #
			print "Couldn't find '{}' with enough similarity. Best match {} at ({},{})".format(pattern.path, confidence, best_loc[0], best_loc[1])
			#cv2.rectangle(haystack, (best_loc[0], best_loc[1]), (best_loc[0] + needle_width, best_loc[1] + needle_height), 255, 2)
			#cv2.imshow("Debug", haystack)
			#cv2.waitKey(0)
			#cv2.destroyAllWindows()
			return None
		# Translate local position into global screen position
		position = (position[0] + self.x, position[1] + self.y)
		self.lastMatch = Match(confidence, pattern.offset, (position, (needle_width, needle_height)))
		#self.lastMatch.debug_preview()
		print "Found match for pattern '{}' at ({},{}) with confidence ({}). Target at ({},{})".format(pattern.path, self.lastMatch.getX(), self.lastMatch.getY(), self.lastMatch.getScore(), self.lastMatch.getTarget().x, self.lastMatch.getTarget().y)
		
		return self.lastMatch

	def debugPreview(self, region=None):
		if region is None:
			region = self
		haystack = self.getBitmap()
		cv2.rectangle(haystack, (region.x - self.x, region.y - self.y), (region.x - self.x + region.w, region.y - self.y + region.h), 255, 2)
		if isinstance(region, Match):
			cv2.circle(haystack, (region.getTarget().x - self.x, region.getTarget().y - self.y), 5, 255)
		cv2.imshow("Debug", haystack)
		cv2.waitKey(0)
		cv2.destroyAllWindows()

	def click(self, target, modifiers=0):
		target_location = None
		mouse = Mouse()
		if isinstance(target, Pattern):
			target_location = self.find(target).getTarget()
			#self.debug_preview(self.lastMatch)
		elif isinstance(target, basestring):
			target_location = self.find(target).getTarget()
			#self.debug_preview(self.lastMatch)
		elif isinstance(target, Match):
			target_location = target.getTarget()
			#self.debug_preview(target)
		elif isinstance(target, Region):
			target_location = target.getCenter()
			#self.debug_preview(target)
		elif isinstance(target, Location):
			target_location = target
		else:
			raise TypeError("click expected Pattern, String, Match, Region, or Location object")
		if modifiers != 0:
			key.toggle('', True, modifiers)

		mouse.moveSpeed(target_location, self.defaultMouseSpeed)
		mouse.click()
		time.sleep(0.2)

		if modifiers != 0:
			key.toggle('', False, modifiers)

	def doubleClick(self, target, modifiers=0):
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

		if modifiers != 0:
			key.toggle('', True, modifiers)

		mouse.moveSpeed(target_location, self.defaultMouseSpeed)
		mouse.click()
		time.sleep(0.1)
		mouse.click()

		if modifiers != 0:
			key.toggle('', False, modifiers)

	def rightClick(self, target, modifiers=0):
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

		if modifiers != 0:
			key.toggle('', True, modifiers)

		mouse.moveSpeed(target_location, self.defaultMouseSpeed)
		mouse.click(button=autopy.mouse.RIGHT_BUTTON)
		time.sleep(0.2)

		if modifiers != 0:
			key.toggle('', False, modifiers)

	def highlight(self):
		""" Not implemented yet

		Probably requires transparent GUI creation/manipulation. TODO
		"""
		raise NotImplementedError()

	def hover(self, target):
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

		mouse.moveSpeed(target_location, self.defaultMouseSpeed)

	def drag(self, dragFrom):
		dragFromLocation = None
		dragToLocation = None
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
		mouse.moveSpeed(dragFromLocation, self.defaultMouseSpeed)
		mouse.toggle(True)
		return 1
		

	def dropAt(self, dragTo, delay=0.2):
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

		mouse.moveSpeed(dragToLocation, self.defaultMouseSpeed)
		time.sleep(delay)
		mouse.toggle(False)
		return 1

	def dragDrop(self, dragFrom, dragTo, modifiers):
		if modifiers != 0:
			key.toggle('', True, modifiers)
		
		drag(dragFrom)
		dropAt(dragTo, 0.1)
		
		if modifiers != 0:
			key.toggle('', False, modifiers)

	def type(self, *args):
		text = None
		if len(args) == 1 and isinstance(args[0], basestring):
			# Is a string (or Key) to type
			text = args[0]
		elif len(args) == 2 and not isinstance(args[0], basestring):
			self.click(args[0])
			text = args[1]
		else:
			raise TypeError("type method expected [PSMRL], text")
		# Patch some Sikuli special codes
		text = text.replace("{PGDN}", "{PAGE_DOWN}")
		text = text.replace("{PGUP}", "{PAGE_UP}")

		print "Typing '{}'".format(text)
		PlatformManager.typeKeys(text, self.defaultTypeSpeed)

	def paste(self, *args):
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
		# Triggers OS paste
		self.type('^v')

	def text(self):
		""" OCR method. Todo. """
		raise NotImplementedError()

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
		""" Concatenate multiple keys to press them all down. Todo. """
		raise NotImplementedError()
			
	def keyUp(self, *keys):
		""" Concatenate multiple keys to up them all. Todo. """
		raise NotImplementedError()


class Match(Region):
	""" Extended Region object with additional data on click target, match score """
	def __init__(self, score, target, rect):
		super(Match, self).__init__(rect[0][0], rect[0][1], rect[1][0], rect[1][1])
		self.score = float(score)
		if not target or not isinstance(target, Location):
			raise TypeError("Match expected target to be a Location object")
		self.target = target

	def getScore(self):
		return self.score

	def getTarget(self):
		return self.getCenter().offset(self.target.x, self.target.y)

class Screen(object):
	""" Main screen only supported atm. Multi-monitor support is coming. """
	def __init__(self, id=0):
		""" Autopy doesn't support multiple screens at this time, so this will always default to the main screen """
		self.id = 0

	def getNumberScreens(self):
		""" Get the number of screens in a multi-monitor environment at the time the script is running

		Autopy doesn't support multiple screens at this time, so this will always default to one.
		"""
		return 1

	def getBounds(self):
		screen_size = PlatformManager.getScreenSize()
		return ((0, 0), screen_size)

	def pointVisible(self, location):
		# TODO: Implement multi-monitor support
		coords, screen_size = self.getBounds()
		screen_width, screen_height = screen_size
		return (location.x >= 0 and location.x < screen_width and location.y >= 0 and location.y < screen_height)

	def capture(self, *args):
		""" Captures the specified region and saves to a temporary file """
		if len(args) == 4:
			# List of coords
			x = int(args[0])
			y = int(args[1])
			w = int(args[2])
			h = int(args[3])
		elif len(args) == 1 and isinstance(args[0], Region):
			# Region object
			x = args[0].x
			y = args[0].y
			w = args[0].w
			h = args[0].h
		elif len(args) == 1 and len(args[0]) == 2:
			# Rectangle ((x, y), (w, h))
			rect = args[0]
			x = rect[0][0]
			y = rect[0][1]
			w = rect[1][0]-1
			h = rect[1][1]-1
		else:
			raise ValueError("capture didn't recognize coordinates")
		if not self.point_visible(Location(x+w, y+h)) or not self.point_visible(Location(x, y)):
			raise RuntimeError("capture coordinates outside of main screen resolution")
		bitmap = self.toRegion().getBitmap()
		tfile, tpath = tempfile.mkstemp(".png")
		cv2.imwrite(tpath, bitmap)

	def selectRegion(self, text=""):
		""" Included for completeness of API, but not supported """
		raise NotImplementedError()

	def toRegion(self):
		screen_size = self.getBounds()
		return Region(0, 0, *screen_size[1])

class Location(object):
	""" Basic 2D point object """
	def __init__(self, x, y):
		self.setLocation(x, y)

	def getX(self):
		return self.x
	def getY(self):
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
		return (self.x, self.y)

	def __repr__(self):
		return "(Location object at ({},{}))".format(self.x, self.y)

class Mouse(object):
	""" Mid-level mouse routines """
	def __init__(self):
		self.defaultScanRate = 0.01
		self.WHEEL_DOWN = 0
		self.WHEEL_UP = 1
		self.LEFT = 0
		self.MIDDLE = 1
		self.RIGHT = 2

	def move(self, location):
		PlatformManager.setMousePos(location.getTuple())

	def getPos(self):
		x, y = PlatformManager.getMousePos()
		return Location(x, y)

	def moveSpeed(self, location, seconds=1):
		if seconds == 0 or not Screen().pointVisible(self.get_pos()):
			# If the mouse isn't on the main screen, snap to point automatically instead of trying to track a path back
			self.move(location)
			return
		frames = int(seconds*0.1 / self.defaultScanRate)
		while frames > 0:
			mouse_pos = self.getPos()
			deltax = int(round(float(location.x - mouse_pos.x) / frames))
			deltay = int(round(float(location.y - mouse_pos.y) / frames))
			self.move(Location(mouse_pos.x + deltax, mouse_pos.y + deltay))
			frames -= 1
			time.sleep(self.defaultScanRate)

	def click(self, button=0):
		PlatformManager.clickMouse(button)
	def wheel(self, direction, steps):
		return PlatformManager.mouseWheel(direction, steps)

class Window(object):
	""" Object to select (and perform basic manipulations on) a window. Uses platform-specific handler """
	def __init__(self, identifier=None):
		self._handle = None
		if identifier:
			self.initialize_wildcard(identifier)

	def initialize_wildcard(self, wildcard):
		self._handle = PlatformManager.getWindowByTitle(wildcard)
		return self

	def getRegion(self):
		if self._handle is None:
			return None
		x1, y1, x2, y2 = PlatformManager.getWindowRect(self._handle)
		return Region(x1, y1, x2-x1, y2-y1)

	def focus(self, wildcard=None):
		if self._handle is None:
			return self
		PlatformManager.focusWindow(self._handle)
		return self

	def getTitle(self):
		return PlatformManager.getWindowTitle(self._handle)

	def getPID(self):
		if self._handle is None:
			return -1
		return PlatformManager.getWindowPID(self._handle)

class App(Window):
	def __init__(self, identifier=None):
		super(App, self).__init__(identifier)
		self.focus = self._focus_instance

	@classmethod
	def focus(cls, wildcard=None):
		# Modify wildcard from Sikuli format to regex
		# TODO - Clean up this cleanup
		wildcard_regex = wildcard.replace("\\", "\\\\").replace(".", "\.").replace("*", ".*")
		app = cls(wildcard_regex)
		return app.focus()

	def _focus_instance(self, wildcard=None):
		if wildcard is not None:
			self.initialize_wildcard(wildcard)
		if self._handle is None:
			return self
		PlatformManager.focusWindow(self._handle)
		return self