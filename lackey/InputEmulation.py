"""
Interfaces with ``keyboard`` to provide mid-level input emulation routines
"""
import time

import keyboard
from keyboard import mouse
from .Location import Location

# Python 3 compatibility
try:
    basestring
except NameError:
    basestring = str

class Mouse(object):
    """ Mid-level mouse routines. """
    def __init__(self):
        self._defaultScanRate = 0.01

    # Class constants
    WHEEL_DOWN = 0
    WHEEL_UP = 1
    LEFT = mouse.LEFT
    MIDDLE = mouse.MIDDLE
    RIGHT = mouse.RIGHT

    def move(self, location):
        """ Moves cursor to specified ``Location`` """
        mouse.move(location.x, location.y)

    def getPos(self):
        """ Gets ``Location`` of cursor """
        return Location(*mouse.get_position())

    @classmethod
    def at(cls):
        """ Gets ``Location`` of cursor (as class method) """
        return Location(*mouse.get_position())

    def moveSpeed(self, location, seconds=0.3):
        """ Moves cursor to specified ``Location`` over ``seconds``.

        If ``seconds`` is 0, moves the cursor immediately. Used for smooth
        somewhat-human-like motion.
        """
        original_location = mouse.get_position()
        mouse.move(location.x, location.y, duration=seconds)
        if mouse.get_position() == original_location and original_location != location.getTuple():
            raise IOError("""
                Unable to move mouse cursor. This may happen if you're trying to automate a 
                program running as Administrator with a script running as a non-elevated user.
            """)

    def click(self, button=mouse.LEFT):
        """ Clicks the specified mouse button.

        Use Mouse.LEFT, Mouse.MIDDLE, Mouse.RIGHT
        """
        mouse.click(button)
    def buttonDown(self, button=mouse.LEFT):
        """ Holds down the specified mouse button.

        Use Mouse.LEFT, Mouse.MIDDLE, Mouse.RIGHT
        """
        mouse.press(button)
    def buttonUp(self, button=mouse.LEFT):
        """ Releases the specified mouse button.

        Use Mouse.LEFT, Mouse.MIDDLE, Mouse.RIGHT
        """
        mouse.release(button)
    def wheel(self, direction, steps):
        """ Clicks the wheel the specified number of steps in the given direction.

        Use Mouse.WHEEL_DOWN, Mouse.WHEEL_UP
        """
        if direction == 1:
            wheel_moved = steps
        elif direction == 0:
            wheel_moved = -1*steps
        else:
            raise ValueError("Expected direction to be 1 or 0")
        return mouse.wheel(wheel_moved)

class Keyboard(object):
    """ Mid-level keyboard routines. Interfaces with ``PlatformManager`` """
    def __init__(self):
        # Mapping to `keyboard` names
        self._SPECIAL_KEYCODES = {
            "BACKSPACE": 	"backspace",
            "TAB": 			"tab",
            "CLEAR": 		"clear",
            "ENTER": 		"enter",
            "SHIFT": 		"shift",
            "CTRL": 		"ctrl",
            "ALT": 			"alt",
            "PAUSE": 		"pause",
            "CAPS_LOCK": 	"caps lock",
            "ESC": 			"esc",
            "SPACE":		"spacebar",
            "PAGE_UP":      "page up",
            "PAGE_DOWN":    "page down",
            "END":			"end",
            "HOME":			"home",
            "LEFT":			"left arrow",
            "UP":			"up arrow",
            "RIGHT":		"right arrow",
            "DOWN":			"down arrow",
            "SELECT":		"select",
            "PRINT":		"print",
            "PRINTSCREEN":	"print screen",
            "INSERT":		"ins",
            "DELETE":		"del",
            "WIN":			"win",
            "CMD":			"win",
            "META":			"win",
            "NUM0":		    "keypad 0",
            "NUM1":		    "keypad 1",
            "NUM2":		    "keypad 2",
            "NUM3":		    "keypad 3",
            "NUM4":		    "keypad 4",
            "NUM5":		    "keypad 5",
            "NUM6":		    "keypad 6",
            "NUM7":		    "keypad 7",
            "NUM8":		    "keypad 8",
            "NUM9":		    "keypad 9",
            "NUM9":		    "keypad 9",
            "SEPARATOR":    83,
            "ADD":	        78,
            "MINUS":        74,
            "MULTIPLY":     55,
            "DIVIDE":       53,
            "F1":			"f1",
            "F2":			"f2",
            "F3":			"f3",
            "F4":			"f4",
            "F5":			"f5",
            "F6":			"f6",
            "F7":			"f7",
            "F8":			"f8",
            "F9":			"f9",
            "F10":			"f10",
            "F11":			"f11",
            "F12":			"f12",
            "F13":			"f13",
            "F14":			"f14",
            "F15":			"f15",
            "F16":			"f16",
            "NUM_LOCK":		"num lock",
            "SCROLL_LOCK":	"scroll lock",
        }
        self._REGULAR_KEYCODES = {
            "0":			"0",
            "1":			"1",
            "2":			"2",
            "3":			"3",
            "4":			"4",
            "5":			"5",
            "6":			"6",
            "7":			"7",
            "8":			"8",
            "9":			"9",
            "a":			"a",
            "b":			"b",
            "c":			"c",
            "d":			"d",
            "e":			"e",
            "f":			"f",
            "g":			"g",
            "h":			"h",
            "i":			"i",
            "j":			"j",
            "k":			"k",
            "l":			"l",
            "m":			"m",
            "n":			"n",
            "o":			"o",
            "p":			"p",
            "q":			"q",
            "r":			"r",
            "s":			"s",
            "t":			"t",
            "u":			"u",
            "v":			"v",
            "w":			"w",
            "x":			"x",
            "y":			"y",
            "z":			"z",
            ";":			";",
            "=":			"=",
            ",":			",",
            "-":			"-",
            ".":			".",
            "/":			"/",
            "`":			"`",
            "[":			"[",
            "\\":			"\\",
            "]":			"]",
            "'":			"'",
            " ":			" ",
        }
        self._UPPERCASE_KEYCODES = {
            "~":			"`",
            "+":			"=",
            ")":			"0",
            "!":			"1",
            "@":			"2",
            "#":			"3",
            "$":			"4",
            "%":			"5",
            "^":			"6",
            "&":			"7",
            "*":			"8",
            "(":			"9",
            "A":			"a",
            "B":			"b",
            "C":			"c",
            "D":			"d",
            "E":			"e",
            "F":			"f",
            "G":			"g",
            "H":			"h",
            "I":			"i",
            "J":			"j",
            "K":			"k",
            "L":			"l",
            "M":			"m",
            "N":			"n",
            "O":			"o",
            "P":			"p",
            "Q":			"q",
            "R":			"r",
            "S":			"s",
            "T":			"t",
            "U":			"u",
            "V":			"v",
            "W":			"w",
            "X":			"x",
            "Y":			"y",
            "Z":			"z",
            ":":			";",
            "<":			",",
            "_":			"-",
            ">":			".",
            "?":			"/",
            "|":			"\\",
            "\"":			"'",
            "{":            "[",
            "}":            "]",
        }

    def keyDown(self, keys):
        """ Accepts a string of keys (including special keys wrapped in brackets or provided
        by the Key or KeyModifier classes). Holds down all of them. """
        if not isinstance(keys, basestring):
            raise TypeError("keyDown expected keys to be a string")
        in_special_code = False
        special_code = ""
        for i in range(0, len(keys)):
            if keys[i] == "{":
                in_special_code = True
            elif in_special_code and (keys[i] == "}" or keys[i] == " " or i == len(keys)-1):
                # End of special code (or it wasn't a special code after all)
                in_special_code = False
                if special_code in self._SPECIAL_KEYCODES.keys():
                    # Found a special code
                    keyboard.press(self._SPECIAL_KEYCODES[special_code])
                else:
                    # Wasn't a special code, just treat it as keystrokes
                    self.keyDown("{")
                    # Press the rest of the keys normally
                    self.keyDown(special_code)
                    self.keyDown(keys[i])
                special_code = ""
            elif in_special_code:
                special_code += keys[i]
            elif keys[i] in self._REGULAR_KEYCODES.keys():
                keyboard.press(keys[i])
            elif keys[i] in self._UPPERCASE_KEYCODES.keys():
                keyboard.press(self._SPECIAL_KEYCODES["SHIFT"])
                keyboard.press(self._UPPERCASE_KEYCODES[keys[i]])
    def keyUp(self, keys):
        """ Accepts a string of keys (including special keys wrapped in brackets or provided
        by the Key or KeyModifier classes). Releases any that are held down. """
        if not isinstance(keys, basestring):
            raise TypeError("keyUp expected keys to be a string")
        in_special_code = False
        special_code = ""
        for i in range(0, len(keys)):
            if keys[i] == "{":
                in_special_code = True
            elif in_special_code and (keys[i] == "}" or keys[i] == " " or i == len(keys)-1):
                # End of special code (or it wasn't a special code after all)
                in_special_code = False
                if special_code in self._SPECIAL_KEYCODES.keys():
                    # Found a special code
                    keyboard.release(self._SPECIAL_KEYCODES[special_code])
                else:
                    # Wasn't a special code, just treat it as keystrokes
                    self.keyUp("{")
                    # Release the rest of the keys normally
                    self.keyUp(special_code)
                    self.keyUp(keys[i])
                special_code = ""
            elif in_special_code:
                special_code += keys[i]
            elif keys[i] in self._REGULAR_KEYCODES.keys():
                keyboard.release(self._REGULAR_KEYCODES[keys[i]])
            elif keys[i] in self._UPPERCASE_KEYCODES.keys():
                keyboard.release(self._SPECIAL_KEYCODES["SHIFT"])
                keyboard.release(self._UPPERCASE_KEYCODES[keys[i]])
    def type(self, text, delay=0.1):
        """ Translates a string into a series of keystrokes.

        Respects Sikuli special codes, like "{ENTER}".
        """
        in_special_code = False
        special_code = ""
        modifier_held = False
        modifier_stuck = False
        modifier_codes = []

        for i in range(0, len(text)):
            if text[i] == "{":
                in_special_code = True
            elif in_special_code and (text[i] == "}" or text[i] == " " or i == len(text)-1):
                in_special_code = False
                if special_code in self._SPECIAL_KEYCODES.keys():
                    # Found a special code
                    keyboard.press_and_release(self._SPECIAL_KEYCODES[special_code])
                else:
                    # Wasn't a special code, just treat it as keystrokes
                    keyboard.press(self._SPECIAL_KEYCODES["SHIFT"])
                    keyboard.press_and_release(self._UPPERCASE_KEYCODES["{"])
                    keyboard.release(self._SPECIAL_KEYCODES["SHIFT"])
                    # Release the rest of the keys normally
                    self.type(special_code)
                    self.type(text[i])
            elif in_special_code:
                special_code += text[i]
            elif text[i] in self._REGULAR_KEYCODES.keys():
                keyboard.press(self._REGULAR_KEYCODES[text[i]])
                keyboard.release(self._REGULAR_KEYCODES[text[i]])
            elif text[i] in self._UPPERCASE_KEYCODES.keys():
                keyboard.press(self._SPECIAL_KEYCODES["SHIFT"])
                keyboard.press_and_release(self._UPPERCASE_KEYCODES[text[i]])
                keyboard.release(self._SPECIAL_KEYCODES["SHIFT"])
            if delay:
                time.sleep(delay)

