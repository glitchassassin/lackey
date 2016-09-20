from PIL import Image
import numpy
import cv2

#from .Settings import Debug

class NaiveTemplateMatcher(object):
	def __init__(self, haystack):
		self.haystack = haystack

	def updateHaystack(self, haystack):
		""" Update the ``haystack`` image """
		self.haystack = haystack

	def findBestMatch(self, needle, similarity):
		""" Find the best match for ``needle`` that has a similarity better than or equal to ``similarity``. 

		Returns a tuple of ``(position, confidence)`` if a match is found, or ``None`` otherwise.
		"""
		method = cv2.TM_CCOEFF_NORMED
		position = None

		match = cv2.matchTemplate(self.haystack,needle,method)
		min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(match)
		if method == cv2.TM_SQDIFF_NORMED or method == cv2.TM_SQDIFF:
			confidence = min_val
			best_loc = min_loc
			if min_val <= 1-similarity:
				# Confidence checks out
				position = min_loc
		else:
			confidence = max_val
			best_loc = max_loc
			if max_val >= similarity:
				# Confidence checks out
				position = max_loc

		if not position:
			return None

		return (position, confidence)

	def findAllMatches(self, needle, similarity):
		""" Find all matches for ``needle`` that has a similarity better than or equal to ``similarity``. 

		Returns an array of tuples ``(position, confidence)`` if match(es) is/are found, or an empty array otherwise.
		"""
		positions = []
		method = cv2.TM_CCOEFF_NORMED
		
		match = cv2.matchTemplate(self.haystack,self.needle,method)
		
		indices = (-match).argpartition(100, axis=None)[:100] # Review the 100 top matches
		unraveled_indices = numpy.array(numpy.unravel_index(indices, match.shape)).T
		for location in unraveled_indices:
			y, x = location
			confidence = match[y][x]
			if method == cv2.TM_SQDIFF_NORMED or method == cv2.TM_SQDIFF:
				if confidence <= 1-similarity:
					positions.append((x,y,confidence))
			else:
				if confidence >= similarity:
					positions.append((x,y,confidence))

		lastMatches = []
		
		if len(positions) == 0:
			return lastMatches
		positions.sort(key=lambda x: (x[1], -x[0]))
		for position in positions:
			x, y, confidence = position
			lastMatches.append(Match(confidence, pattern.offset, ((x+self.x, y+self.y), (needle_width, needle_height))))
		return lastMatches