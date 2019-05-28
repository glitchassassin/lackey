import pytesseract
import csv
import re

from .SettingsDebug import Debug

class OCR():
    def start(self):
        """
        Returns the object itself (a hack for Sikuli compatibility)
        """
        return self # Dummy method for Sikuli compatibility
    def image_to_text(self, image):
        """
        Returns the text found in the given image.
        """
        return pytesseract.image_to_string(image)
    def find_word(self, image, text, confidence=0.6):
        """
        Finds the first word in `image` that matches `text`.
        Currently ignores confidence
        """
        data = pytesseract.image_to_data(image)
        reader = csv.DictReader(data.split("\n"), delimiter="\t", quoting=csv.QUOTE_NONE)
        for rect in reader:
            if re.search(text, rect["text"]):
                return (
                    (
                        rect["left"],
                        rect["top"],
                        rect["width"],
                        rect["height"]
                    ),
                    rect["conf"]
                )
        return None
    def find_line(self, image, text, confidence=0.6):
        """
        Finds all lines in `image` that match `text`.
        Currently ignores confidence
        """
        data = pytesseract.image_to_data(image)
        reader = csv.DictReader(data.split("\n"), delimiter="\t", quoting=csv.QUOTE_NONE)
        lines = {}
        for rect in reader:
            key = (int(rect["page_num"]), int(rect["block_num"]), int(rect["par_num"]), int(rect["line_num"]))
            if key not in lines:
                lines[key] = ""
            lines[key] += " " + rect["text"]
        for line in lines:
            if re.search(text, line):
                return (
                    (
                        rect["left"],
                        rect["top"],
                        rect["width"],
                        rect["height"]
                    ),
                    rect["conf"]
                )
        return None
    def find_all_in_image(self, image, text, confidence=0.6):
        """
        Finds all blocks of text in `image` that match `text`.
        Currently ignores confidence
        """
        confidence = confidence*100 # Scaling for pytesseract
        data = pytesseract.image_to_data(image)
        print(data)
        reader = csv.DictReader(data.split("\n"), delimiter="\t", quoting=csv.QUOTE_NONE)
        rects = [r for r in reader]
        # Debug.info("Rects: " + repr(rects))
        line = []
        matches = []
        for rect in rects:
            if len(line) and (line[0]["page_num"], line[0]["block_num"], line[0]["par_num"], line[0]["line_num"]) == (rect["page_num"], rect["block_num"], rect["par_num"], rect["line_num"]):
                # This rect is on the same line
                line.append(rect)
            else:
                # Debug.info("Line: " + " ".join(e["text"] for e in line if e["text"] is not None)) # int(e["conf"]) > confidence and 
                line = [rect]
            
            if self._check_if_line_matches(line, text, confidence):
                matches.append(self._reduce_line_matches(line, text, confidence))
                line = []
            # Start with first element in line
            # Check if it matches
            # If so, and there are multiple elements, try removing the first one and see if it still matches.
            # If not, add next element, and check if it matches
        return matches
    def find_in_image(self, image, text, confidence=0.6):
        """
        Finds first match of `text` in `image` (may be a regex).
        Currently ignores confidence
        """
        matches = self.find_all_in_image(image, text, confidence)
        # Debug.info("Matches: " + repr(matches))
        if matches:
            return matches[0]
        return None
    def _check_if_line_matches(self, line, text, confidence):
        # Join the `text` property from each element in `line` and compare it with the `text` regex
        return re.search(text, " ".join(e["text"] for e in line if e["text"] is not None)) is not None # int(e["conf"]) > confidence and
    def _reduce_line_matches(self, line, text, confidence):
        # Remove the first element from line and see if it still matches
        while self._check_if_line_matches(line, text, confidence):
            # If so, continue
            last_element = line.pop(0)
        # If not, replace the element, and calculate the bounding box of the remaining elements
        line = [last_element] + line
        #print("Matched line: " + repr(line)) # DEBUG
        corners = []
        for e in line:
            corners.append((int(e["left"]), int(e["top"])))
            corners.append((int(e["left"])+int(e["width"]), int(e["top"])+int(e["height"])))
        bbox = (
            min(corner[0] for corner in corners), # X
            min(corner[1] for corner in corners), # Y
            max(corner[0] for corner in corners) - min(corner[0] for corner in corners), # W
            max(corner[1] for corner in corners) - min(corner[1] for corner in corners), # H
        )
        return (bbox, confidence)

TextOCR = OCR()