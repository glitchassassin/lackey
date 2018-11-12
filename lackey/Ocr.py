import pytesseract
from pprint import pprint
import csv
import re

#from .SettingsDebug import Debug

class TextOCR():
    def image_to_text(self, image):
        return pytesseract.image_to_string(image)
    
    def find_all_in_image(self, image, text, confidence=0.7):
        confidence = confidence*100 # Scaling for pytesseract
        data = pytesseract.image_to_data(image)
        reader = csv.DictReader(data.split("\n"), delimiter="\t")
        rects = [r for r in reader]
        line = []
        matches = []
        for rect in rects:
            if len(line) and (line[0]["page_num"], line[0]["block_num"], line[0]["par_num"], line[0]["line_num"]) == (rect["page_num"], rect["block_num"], rect["par_num"], rect["line_num"]):
                # This rect is on the same line
                line.append(rect)
            else:
                line = [rect]
            
            if self._check_if_line_matches(line, text, confidence):
                matches.append(self._reduce_line_matches(line, text, confidence))
                line = []
            # Start with first element in line
            # Check if it matches
            # If so, and there are multiple elements, try removing the first one and see if it still matches.
            # If not, add next element, and check if it matches
        return matches
    def find_in_image(self, image, text, confidence=0.7):
        matches = self.find_all_in_image(image, text, confidence)
        if matches:
            return matches[0]
        return None
    def _check_if_line_matches(self, line, text, confidence):
        # Join the `text` property from each element in `line` and compare it with the `text` regex
        return re.search(text, " ".join(e["text"] for e in line if int(e["conf"]) > confidence and e["text"] is not None)) is not None
    def _reduce_line_matches(self, line, text, confidence):
        # Remove the first element from line and see if it still matches
        while self._check_if_line_matches(line, text, confidence):
            # If so, continue
            last_element = line.pop(0)
        # If not, replace the element, and calculate the bounding box of the remaining elements
        line = [last_element] + line
        print("Matched line: " + repr(line)) # DEBUG
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
        return bbox

if __name__ == "__main__":
    ocr = TextOCR()
    pprint(ocr.find_all_in_image("/Users/jwinsley/Downloads/tesseract/homemeds.png", "Ibuprofen"))