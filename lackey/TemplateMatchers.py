from PIL import Image
import itertools
import numpy
import cv2

from .SettingsDebug import Debug

class NaiveTemplateMatcher(object):
    """ Python wrapper for OpenCV's TemplateMatcher 

    Does not try to optimize speed
    """
    def __init__(self, haystack):
        self.haystack = haystack

    def findBestMatch(self, needle, similarity):
        """ Find the best match for ``needle`` that has a similarity better than or equal to ``similarity``.

        Returns a tuple of ``(position, confidence)`` if a match is found, or ``None`` otherwise.

        *Developer's Note - Despite the name, this method actually returns the **first** result
        with enough similarity, not the **best** result.*
        """
        method = cv2.TM_CCOEFF_NORMED
        position = None

        match = cv2.matchTemplate(self.haystack, needle, method)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(match)
        if method == cv2.TM_SQDIFF_NORMED or method == cv2.TM_SQDIFF:
            confidence = min_val
            if min_val <= 1-similarity:
                # Confidence checks out
                position = min_loc
        else:
            confidence = max_val
            if max_val >= similarity:
                # Confidence checks out
                position = max_loc

        if not position:
            return None

        return (position, confidence)

    def findAllMatches(self, needle, similarity):
        """ Find all matches for ``needle`` with confidence better than or equal to ``similarity``.

        Returns an array of tuples ``(position, confidence)`` if match(es) is/are found,
        or an empty array otherwise.
        """
        positions = []
        method = cv2.TM_CCOEFF_NORMED

        match = cv2.matchTemplate(self.haystack, self.needle, method)

        indices = (-match).argpartition(100, axis=None)[:100] # Review the 100 top matches
        unraveled_indices = numpy.array(numpy.unravel_index(indices, match.shape)).T
        for location in unraveled_indices:
            y, x = location
            confidence = match[y][x]
            if method == cv2.TM_SQDIFF_NORMED or method == cv2.TM_SQDIFF:
                if confidence <= 1-similarity:
                    positions.append(((x, y), confidence))
            else:
                if confidence >= similarity:
                    positions.append(((x, y), confidence))

        positions.sort(key=lambda x: (x[0][1], x[0][0]))
        return positions

class PyramidTemplateMatcher(object):
    """ Python wrapper for OpenCV's TemplateMatcher

    Uses a pyramid model to optimize matching speed
    """
    def __init__(self, haystack):
        self.haystack = cv2.cvtColor(haystack, cv2.COLOR_BGR2GRAY) # Convert to grayscale
        self._iterations = 3 # Number of times to downsample

    def findBestMatch(self, needle, similarity):
        """ Finds the best match using a search pyramid to improve efficiency

        Pyramid implementation unashamedly stolen from https://github.com/stb-tester/stb-tester

        *Developer's Note - Despite the name, this method actually returns the **first** result
        with enough similarity, not the **best** result.*
        """
        needle = cv2.cvtColor(needle, cv2.COLOR_BGR2GRAY) # Convert to grayscale
        haystack = self.haystack
        # Check if haystack or needle are a solid color - if so, switch to SQDIFF_NORMED

        if self._is_solid_color(needle):
            print("Solid color, using SQDIFF")
            method = cv2.TM_SQDIFF_NORMED
            if self._is_solid_black(needle):
                print("Inverting images")
                # Invert needle & haystack before matching
                needle = numpy.invert(needle)
                haystack = numpy.invert(haystack)
        else:
            #print("Not Solid color, using CCOEFF")
            method = cv2.TM_CCOEFF_NORMED

        levels = 3
        needle_pyramid = self._build_pyramid(needle, levels)
        # Needle will be smaller than haystack, so may not be able to create
        # ``levels`` smaller versions of itself. If not, create only as many
        # levels for ``haystack`` as we could for ``needle``.
        haystack_pyramid = self._build_pyramid(haystack, min(levels, len(needle_pyramid)))
        roi_mask = None

        # Run through each level in the pyramid, refining found ROIs
        for level in range(len(haystack_pyramid)):
            # Populate the heatmap with ones or zeroes depending on the appropriate method
            lvl_haystack = haystack_pyramid[level]
            lvl_needle = needle_pyramid[level]
            if (lvl_needle.shape[0] > lvl_haystack.shape[0]) or (lvl_needle.shape[1] > lvl_haystack.shape[1]):
                raise ValueError("Image to find is larger than search area")
            matches_heatmap = (
                (numpy.ones if method == cv2.TM_SQDIFF_NORMED else numpy.zeros)(
                    (lvl_haystack.shape[0] - lvl_needle.shape[0] + 1, lvl_haystack.shape[1] - lvl_needle.shape[1] + 1),
                    dtype=numpy.float32))

            # Scale up region of interest for the next level in the pyramid
            # (if it's been set and is a valid size)
            if roi_mask is not None:
                if any(x < 3 for x in roi_mask.shape):
                    roi_mask = None
                else:
                    roi_mask = cv2.pyrUp(roi_mask)

            # If roi_mask is set, only search the best candidates in haystack
            # for the needle:

            if roi_mask is None:
                # Initialize mask to the whole image
                rois = [(0, 0, matches_heatmap.shape[1], matches_heatmap.shape[0])]
            else:
                # Depending on version of OpenCV, findContours returns either a three-tuple
                # or a two-tuple. Unsure why the install is different (possibly linked to
                # OS version).
                try:
                    _, contours, _ = cv2.findContours(
                        roi_mask,
                        cv2.RETR_EXTERNAL,
                        cv2.CHAIN_APPROX_NONE)
                except ValueError:
                    contours, _ = cv2.findContours(
                        roi_mask,
                        cv2.RETR_EXTERNAL,
                        cv2.CHAIN_APPROX_NONE)
                # Expand contour rect by 1px on all sides with some tuple magic
                rois = [tuple(sum(y) for y in zip(cv2.boundingRect(x), (-1, -1, 2, 2))) for x in contours]


            for roi in rois:
                # Trim ROI bounds to zero (if negative)
                x, y, w, h = roi
                x = max(x, 0)
                y = max(y, 0)
                # Add needle dimensions to roi
                roi = (x, y, w+lvl_needle.shape[1]-1, h+lvl_needle.shape[0]-1)
                # numpy 2D slice
                roi_slice = (slice(roi[1], roi[1]+roi[3]), slice(roi[0], roi[0]+roi[2]))
                # numpy 2D slice
                r_slice = (slice(y, y+h), slice(x, x+w))

                # Search the region of interest for needle (and update heatmap)
                matches_heatmap[r_slice] = cv2.matchTemplate(
                    lvl_haystack[roi_slice],
                    lvl_needle,
                    method)

            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(matches_heatmap)
            # Reduce similarity to allow for scaling distortion
            # (unless we are on the original image)
            pyr_similarity = max(0, similarity - (0.2 if level < len(haystack_pyramid)-1 else 0))
            position = None
            confidence = None
            # Check for a match
            if method == cv2.TM_SQDIFF_NORMED:
                confidence = min_val
                if min_val <= 1-pyr_similarity:
                    # Confidence checks out
                    position = min_loc
            else:
                confidence = max_val
                if max_val >= pyr_similarity:
                    # Confidence checks out
                    position = max_loc

            if not position:
                break

            # Find the best regions of interest
            _, roi_mask = cv2.threshold(
                # Source image
                matches_heatmap,
                # Confidence threshold
                ((1-pyr_similarity) if method == cv2.TM_SQDIFF_NORMED else pyr_similarity),
                # Max value
                255,
                # Thresholding style
                (cv2.THRESH_BINARY_INV if method == cv2.TM_SQDIFF_NORMED else cv2.THRESH_BINARY))
            roi_mask = roi_mask.astype(numpy.uint8)

        # Whew! Let's see if there's a match after all that.

        if not position:
            Debug.log(3, "Best match: {} at {}".format(max_val, max_loc))
            return None

        # There was a match!
        if method == cv2.TM_SQDIFF_NORMED:
            confidence = 1 - confidence # Invert confidence if we used the SQDIFF method
        return (position, confidence)

    def findAllMatches(self, needle, similarity):
        """ Finds all matches above ``similarity`` using a search pyramid to improve efficiency

        Pyramid implementation unashamedly stolen from https://github.com/stb-tester/stb-tester
        """
        positions = []
        # Use findBestMatch to get the best match
        while True:
            best_match = self.findBestMatch(needle, similarity)
            if best_match is None: # No more matches
                break
            # Found a match. Add it to our list
            positions.append(best_match) # (position, confidence)

            # Erase the found match from the haystack.
            # Repeat this process until no other matches are found
            x, y = best_match[0]
            w = needle.shape[1]
            h = needle.shape[0]
            roi = (x, y, w, h)
            # numpy 2D slice
            roi_slice = (slice(roi[1], roi[1]+roi[3]), slice(roi[0], roi[0]+roi[2]))
            self.haystack[roi_slice] = 0

        # Whew! Let's see if there's a match after all that.
        positions.sort(key=lambda x: (x[0][1], x[0][0]))
        return positions

    def _build_pyramid(self, image, levels):
        """ Returns a list of reduced-size images, from smallest to original size """
        pyramid = [image]
        for l in range(levels-1):
            if any(x < 20 for x in pyramid[-1].shape[:2]):
                break
            pyramid.append(cv2.pyrDown(pyramid[-1]))
        return list(reversed(pyramid))
    def _is_solid_color(self, image):
        return image.ptp() == 0
    
    def _is_solid_black(self, image):
        return image.mean() == 0