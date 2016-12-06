""" Platform-specific code for Windows is encapsulated in this module. """

import os
import re
import time
import numpy
import ctypes
try:
    import Tkinter as tk
except ImportError:
    import tkinter as tk
from ctypes import wintypes
from PIL import Image, ImageTk, ImageOps
from .Settings import Debug

class PlatformManagerWindows(object):
    """ Abstracts Windows-specific OS-level features like mouse/keyboard control """
    def __init__(self):
        #self._root = tk.Tk()
        #self._root.overrideredirect(1)
        #self._root.withdraw()
        user32 = ctypes.WinDLL('user32', use_last_error=True)
        gdi32 = ctypes.WinDLL('gdi32', use_last_error=True)
        kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
        psapi = ctypes.WinDLL('psapi', use_last_error=True)
        self._user32 = user32
        self._gdi32 = gdi32
        self._kernel32 = kernel32
        self._psapi = psapi
        self._INPUT_MOUSE    = 0
        self._INPUT_KEYBOARD = 1
        self._INPUT_HARDWARE = 2
        self._KEYEVENTF_EXTENDEDKEY = 0x0001
        self._KEYEVENTF_KEYUP       = 0x0002
        self._KEYEVENTF_UNICODE     = 0x0004
        self._KEYEVENTF_SCANCODE    = 0x0008
        #KEYEVENTF_EXTENDEDKEY = 0x0001
        #KEYEVENTF_KEYUP       = 0x0002
        KEYEVENTF_UNICODE     = 0x0004
        #KEYEVENTF_SCANCODE    = 0x0008
        MAPVK_VK_TO_VSC = 0

        self._SPECIAL_KEYCODES = {
            "BACKSPACE": 	0x08,
            "TAB": 			0x09,
            "CLEAR": 		0x0c,
            "ENTER": 		0x0d,
            "SHIFT": 		0x10,
            "CTRL": 		0x11,
            "ALT": 			0x12,
            "PAUSE": 		0x13,
            "CAPS_LOCK": 	0x14,
            "ESC": 			0x1b,
            "SPACE":		0x20,
            "PAGE_UP":		0x21,
            "PAGE_DOWN":	0x22,
            "END":			0x23,
            "HOME":			0x24,
            "LEFT":			0x25,
            "UP":			0x26,
            "RIGHT":		0x27,
            "DOWN":			0x28,
            "SELECT":		0x29,
            "PRINT":		0x2a,
            "PRINT_SCREEN":	0x2c,
            "INSERT":		0x2d,
            "DELETE":		0x2e,
            "WIN":			0x5b,
            "NUM_0":		0x60,
            "NUM_1":		0x61,
            "NUM_2":		0x62,
            "NUM_3":		0x63,
            "NUM_4":		0x64,
            "NUM_5":		0x65,
            "NUM_6":		0x66,
            "NUM_7":		0x67,
            "NUM_8":		0x68,
            "NUM_9":		0x69,
            "F1":			0x70,
            "F2":			0x71,
            "F3":			0x72,
            "F4":			0x73,
            "F5":			0x74,
            "F6":			0x75,
            "F7":			0x76,
            "F8":			0x77,
            "F9":			0x78,
            "F10":			0x79,
            "F11":			0x7a,
            "F12":			0x7b,
            "F13":			0x7c,
            "F14":			0x7d,
            "F15":			0x7e,
            "F16":			0x7f,
            "NUM_LOCK":		0x90,
            "SCROLL_LOCK":	0x91,
            "[":			0xdb,
            "]":			0xdd
        }
        self._UPPERCASE_SPECIAL_KEYCODES = {
            "+":			0xbb,
            "@":			0x32,
            "^":			0x36,
            "%":			0x35,
            "~":			0xc0,
            "(":			0x39,
            ")":			0x30,
            "{":			0xdb,
            "}":			0xdd
        }
        self._MODIFIER_KEYCODES = {
            "+":			0x10,
            "^":			0x11,
            "%":			0x12,
            "~":			0x0d,
            "@":			0x5b
        }
        self._REGULAR_KEYCODES = {
            "0":			0x30,
            "1":			0x31,
            "2":			0x32,
            "3":			0x33,
            "4":			0x34,
            "5":			0x35,
            "6":			0x36,
            "7":			0x37,
            "8":			0x38,
            "9":			0x39,
            "a":			0x41,
            "b":			0x42,
            "c":			0x43,
            "d":			0x44,
            "e":			0x45,
            "f":			0x46,
            "g":			0x47,
            "h":			0x48,
            "i":			0x49,
            "j":			0x4a,
            "k":			0x4b,
            "l":			0x4c,
            "m":			0x4d,
            "n":			0x4e,
            "o":			0x4f,
            "p":			0x50,
            "q":			0x51,
            "r":			0x52,
            "s":			0x53,
            "t":			0x54,
            "u":			0x55,
            "v":			0x56,
            "w":			0x57,
            "x":			0x58,
            "y":			0x59,
            "z":			0x5A,
            ";":			0xba,
            "=":			0xbb,
            ",":			0xbc,
            "-":			0xbd,
            ".":			0xbe,
            "/":			0xbf,
            "`":			0xc0,
            "\\":			0xdc,
            "'":			0xde,
            " ":			0x20,
        }
        self._UPPERCASE_KEYCODES = {
            "!":			0x31,
            "#":			0x33,
            "$":			0x34,
            "&":			0x37,
            "*":			0x38,
            "A":			0x41,
            "B":			0x42,
            "C":			0x43,
            "D":			0x44,
            "E":			0x45,
            "F":			0x46,
            "G":			0x47,
            "H":			0x48,
            "I":			0x49,
            "J":			0x4a,
            "K":			0x4b,
            "L":			0x4c,
            "M":			0x4d,
            "N":			0x4e,
            "O":			0x4f,
            "P":			0x50,
            "Q":			0x51,
            "R":			0x52,
            "S":			0x53,
            "T":			0x54,
            "U":			0x55,
            "V":			0x56,
            "W":			0x57,
            "X":			0x58,
            "Y":			0x59,
            "Z":			0x5A,
            ":":			0xba,
            "<":			0xbc,
            "_":			0xbd,
            ">":			0xbe,
            "?":			0xbf,
            "|":			0xdc,
            "\"":			0xde,
        }

        # __init__ internal classes

        class MOUSEINPUT(ctypes.Structure):
            """ ctypes equivalent for Win32 MOUSEINPUT struct """
            _fields_ = (("dx",          wintypes.LONG),
                        ("dy",          wintypes.LONG),
                        ("mouseData",   wintypes.DWORD),
                        ("dwFlags",     wintypes.DWORD),
                        ("time",        wintypes.DWORD),
                        ("dwExtraInfo", wintypes.WPARAM))
        self._MOUSEINPUT = MOUSEINPUT

        class KEYBDINPUT(ctypes.Structure):
            """ ctypes equivalent for Win32 KEYBDINPUT struct """
            _fields_ = (("wVk",         wintypes.WORD),
                        ("wScan",       wintypes.WORD),
                        ("dwFlags",     wintypes.DWORD),
                        ("time",        wintypes.DWORD),
                        ("dwExtraInfo", wintypes.WPARAM))
            def __init__(self, *args, **kwds):
                super(KEYBDINPUT, self).__init__(*args, **kwds)
                # some programs use the scan code even if KEYEVENTF_SCANCODE
                # isn't set in dwFflags, so attempt to map the correct code.
                if not self.dwFlags & KEYEVENTF_UNICODE:
                    self.wScan = user32.MapVirtualKeyExW(self.wVk, MAPVK_VK_TO_VSC, 0)
        self._KEYBDINPUT = KEYBDINPUT

        class HARDWAREINPUT(ctypes.Structure):
            """ ctypes equivalent for Win32 HARDWAREINPUT struct """
            _fields_ = (("uMsg",    wintypes.DWORD),
                        ("wParamL", wintypes.WORD),
                        ("wParamH", wintypes.WORD))
        self._HARDWAREINPUT = HARDWAREINPUT

        class INPUT(ctypes.Structure):
            """ ctypes equivalent for Win32 INPUT struct """
            class _INPUT(ctypes.Union):
                _fields_ = (("ki", KEYBDINPUT),
                            ("mi", MOUSEINPUT),
                            ("hi", HARDWAREINPUT))
            _anonymous_ = ("_input",)
            _fields_ = (("type",   wintypes.DWORD),
                        ("_input", _INPUT))
        self._INPUT = INPUT

        LPINPUT = ctypes.POINTER(INPUT)
        user32.SendInput.errcheck = self._check_count
        user32.SendInput.argtypes = (wintypes.UINT, # nInputs
                                     LPINPUT,       # pInputs
                                     ctypes.c_int)  # cbSize

    def _check_count(self, result, func, args):
        #pylint: disable=unused-argument
        """ Private function to return ctypes errors cleanly """
        if result == 0:
            raise ctypes.WinError(ctypes.get_last_error())
        return args

    ## Keyboard input methods ##

    def _press_key_code(self, hex_key_code):
        """ Set key state to down for the specified hex key code """
        key_msg = self._INPUT(type=self._INPUT_KEYBOARD, ki=self._KEYBDINPUT(wVk=hex_key_code))
        self._user32.SendInput(1, ctypes.byref(key_msg), ctypes.sizeof(key_msg))
    def pressKey(self, text):
        """ Accepts a string of keys in typeKeys format (see below). Holds down all of them. """

        if not isinstance(text, basestring):
            raise TypeError("pressKey expected text to be a string")
        in_special_code = False
        special_code = ""
        for i in range(0, len(text)):
            if text[i] == "{":
                in_special_code = True
            elif text[i] == "}":
                in_special_code = False
                if special_code in self._SPECIAL_KEYCODES.keys():
                    self._press_key_code(self._SPECIAL_KEYCODES[special_code])
                else:
                    raise ValueError("Unsupported special code {{{}}}".format(special_code))
                continue
            elif in_special_code:
                special_code += text[i]
                continue
            elif text[i] in self._MODIFIER_KEYCODES.keys():
                self._press_key_code(self._MODIFIER_KEYCODES[text[i]])
            elif text[i] in self._REGULAR_KEYCODES.keys():
                self._press_key_code(self._REGULAR_KEYCODES[text[i]])
    def _release_key_code(self, hex_key_code):
        """ Set key state to up for the specified hex key code  """
        key_msg = self._INPUT(
            type=self._INPUT_KEYBOARD,
            ki=self._KEYBDINPUT(
                wVk=hex_key_code,
                dwFlags=self._KEYEVENTF_KEYUP))
        self._user32.SendInput(1, ctypes.byref(key_msg), ctypes.sizeof(key_msg))
    def releaseKey(self, text):
        """ Accepts a string of keys in typeKeys format (see below). Releases all of them. """

        in_special_code = False
        special_code = ""
        for i in range(0, len(text)):
            if text[i] == "{":
                in_special_code = True
            elif text[i] == "}":
                in_special_code = False
                if special_code in self._SPECIAL_KEYCODES.keys():
                    self._release_key_code(self._SPECIAL_KEYCODES[special_code])
                else:
                    raise ValueError("Unsupported special code {{{}}}".format(special_code))
                continue
            elif in_special_code:
                special_code += text[i]
                continue
            elif text[i] in self._MODIFIER_KEYCODES.keys():
                self._release_key_code(self._MODIFIER_KEYCODES[text[i]])
            elif text[i] in self._REGULAR_KEYCODES.keys():
                self._release_key_code(self._REGULAR_KEYCODES[text[i]])
    def typeKeys(self, text, delay=0.1):
        """ Translates a string (with modifiers) into a series of keystrokes.

        Equivalent to Microsoft's SendKeys, with the addition of "@" as a Win-key modifier.
        Avoids some issues SendKeys had with applications like Citrix.
        """
        in_special_code = False
        special_code = ""
        modifier_held = False
        modifier_stuck = False
        modifier_codes = []

        for i in range(0, len(text)):
            if text[i] == "{":
                in_special_code = True
            elif text[i] == "}":
                in_special_code = False
                if special_code in self._SPECIAL_KEYCODES.keys():
                    self._press_key_code(self._SPECIAL_KEYCODES[special_code])
                    self._release_key_code(self._SPECIAL_KEYCODES[special_code])
                elif special_code in self._UPPERCASE_SPECIAL_KEYCODES.keys():
                    self._press_key_code(self._SPECIAL_KEYCODES["SHIFT"])
                    self._press_key_code(self._UPPERCASE_SPECIAL_KEYCODES[special_code])
                    self._release_key_code(self._UPPERCASE_SPECIAL_KEYCODES[special_code])
                    self._release_key_code(self._SPECIAL_KEYCODES["SHIFT"])
                else:
                    raise ValueError("Unrecognized special code {{{}}}".format(special_code))
                continue
            elif in_special_code:
                special_code += text[i]
                continue
            elif text[i] == "(":
                modifier_stuck = True
                modifier_held = False
                continue
            elif text[i] == ")":
                modifier_stuck = False
                for x in modifier_codes:
                    self._release_key_code(x)
                modifier_codes = []
                continue
            elif text[i] in self._MODIFIER_KEYCODES.keys():
                modifier_codes.append(self._MODIFIER_KEYCODES[text[i]])
                self._press_key_code(self._MODIFIER_KEYCODES[text[i]])
                modifier_held = True
            elif text[i] in self._REGULAR_KEYCODES.keys():
                self._press_key_code(self._REGULAR_KEYCODES[text[i]])
                self._release_key_code(self._REGULAR_KEYCODES[text[i]])
                if modifier_held:
                    modifier_held = False
                    for x in modifier_codes:
                        self._release_key_code(x)
                    modifier_codes = []
            elif text[i] in self._UPPERCASE_KEYCODES.keys():
                self._press_key_code(self._SPECIAL_KEYCODES["SHIFT"])
                self._press_key_code(self._UPPERCASE_KEYCODES[text[i]])
                self._release_key_code(self._UPPERCASE_KEYCODES[text[i]])
                self._release_key_code(self._SPECIAL_KEYCODES["SHIFT"])
                if modifier_held:
                    modifier_held = False
                    for x in modifier_codes:
                        self._release_key_code(x)
                    modifier_codes = []
            if delay:
                time.sleep(delay)

        if modifier_stuck or modifier_held:
            for modifier in modifier_codes:
                self._release_key_code(modifier)

    ## Mouse input methods

    def setMousePos(self, location):
        """ Accepts a tuple (x,y) and sets the mouse position accordingly """
        x, y = location
        if self.isPointVisible(x, y):
            self._user32.SetCursorPos(x, y)
    def getMousePos(self):
        """ Returns the current mouse position as a tuple (x,y)

        Relative to origin of main screen top left (0,0). May be negative.
        """
        class POINT(ctypes.Structure):
            """ ctypes version of Win32 POINT struct """
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
        mouse_pos = POINT()
        self._user32.GetCursorPos(ctypes.byref(mouse_pos))
        return (mouse_pos.x, mouse_pos.y)
    def mouseButtonDown(self, button=0):
        """ Translates the button (0=LEFT, 1=MIDDLE, 2=RIGHT) and sends a mousedown to the OS """
        click_down_code = [0x0002, 0x0020, 0x0008][button]
        mouse_msg = self._INPUT(
            type=self._INPUT_MOUSE,
            mi=self._MOUSEINPUT(dwFlags=click_down_code))
        self._user32.SendInput(1, ctypes.byref(mouse_msg), ctypes.sizeof(mouse_msg))
    def mouseButtonUp(self, button=0):
        """ Translates the button (0=LEFT, 1=MIDDLE, 2=RIGHT) and sends a mouseup to the OS """
        click_up_code = [0x0004, 0x0040, 0x0010][button]
        mouse_msg = self._INPUT(type=self._INPUT_MOUSE, mi=self._MOUSEINPUT(dwFlags=click_up_code))
        self._user32.SendInput(1, ctypes.byref(mouse_msg), ctypes.sizeof(mouse_msg))
    def clickMouse(self, button=0):
        """ Abstracts the clicking function

        Button codes are (0=LEFT, 1=MIDDLE, 2=RIGHT) and should be provided as constants
        by the Mouse class
        """
        # LEFT = 0
        # MIDDLE = 1
        # RIGHT = 2
        self.mouseButtonDown(button)
        self.mouseButtonUp(button)
    def mouseWheel(self, direction, steps):
        """ Clicks the mouse wheel the specified number of steps in the given direction

        Valid directions are 0 (for down) and 1 (for up). These should be provided
        as constants by the Mouse class.
        """
        MOUSEEVENTF_WHEEL = 0x0800
        if direction == 1:
            wheel_moved = 120*steps
        elif direction == 0:
            wheel_moved = -120*steps
        else:
            raise ValueError("Expected direction to be 1 or 0")
        mouse_msg = self._INPUT(
            type=self._INPUT_MOUSE,
            mi=self._MOUSEINPUT(
                dwFlags=MOUSEEVENTF_WHEEL,
                mouseData=wheel_moved))
        self._user32.SendInput(1, ctypes.byref(mouse_msg), ctypes.sizeof(mouse_msg))

    ## Screen functions

    def getBitmapFromRect(self, x, y, w, h):
        """ Capture the specified area of the (virtual) screen. """
        min_x, min_y, screen_width, screen_height = self._getVirtualScreenRect()
        img = self._getVirtualScreenBitmap()
        # Limit the coordinates to the virtual screen
        # Then offset so 0,0 is the top left corner of the image
        # (Top left of virtual screen could be negative)
        x1 = min(max(min_x, x), min_x+screen_width) - min_x
        y1 = min(max(min_y, y), min_y+screen_height) - min_y
        x2 = min(max(min_x, x+w), min_x+screen_width) - min_x
        y2 = min(max(min_y, y+h), min_y+screen_height) - min_y
        return numpy.array(img.crop((x1, y1, x2, y2)))
    def getScreenBounds(self, screenId):
        """ Returns the screen size of the specified monitor (0 being the main monitor). """
        screen_details = self.getScreenDetails()
        if not isinstance(screenId, int) or screenId < -1 or screenId >= len(screen_details):
            raise ValueError("Invalid screen ID")
        if screenId == -1:
            # -1 represents the entire virtual screen
            x1, y1, x2, y2 = self._getVirtualScreenRect()
            return (x1, y1, x2-x1, y2-y1)
        return screen_details[screenId]["rect"]
    def getScreenDetails(self):
        """ Return list of attached monitors

        For each monitor (as dict), ``monitor["rect"]`` represents the screen as positioned
        in virtual screen. List is returned in device order, with the first element (0)
        representing the primary monitor.
        """
        monitors = self._getMonitorInfo()
        primary_screen = None
        screens = []
        for monitor in monitors:
            # Convert screen rect to Lackey-style rect (x,y,w,h) as position in virtual screen
            screen = {
                "rect": (
                    monitor["rect"][0],
                    monitor["rect"][1],
                    monitor["rect"][2] - monitor["rect"][0],
                    monitor["rect"][3] - monitor["rect"][1]
                )
            }
            screens.append(screen)
        return screens
    def isPointVisible(self, x, y):
        """ Checks if a point is visible on any monitor. """
        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
        pt = POINT()
        pt.x = x
        pt.y = y
        MONITOR_DEFAULTTONULL = 0
        hmon = self._user32.MonitorFromPoint(pt, MONITOR_DEFAULTTONULL)
        if hmon == 0:
            return False
        return True
    def _captureScreen(self, device_name):
        """ Captures a bitmap from the given monitor device name

        Returns as a PIL Image (BGR rather than RGB, for compatibility with OpenCV)
        """

        ## Define constants/structs
        class HBITMAP(ctypes.Structure):
            _fields_ = [("bmType", ctypes.c_long),
                        ("bmWidth", ctypes.c_long),
                        ("bmHeight", ctypes.c_long),
                        ("bmWidthBytes", ctypes.c_long),
                        ("bmPlanes", ctypes.wintypes.WORD),
                        ("bmBitsPixel", ctypes.wintypes.WORD),
                        ("bmBits", ctypes.wintypes.LPVOID)]
        class BITMAPINFOHEADER(ctypes.Structure):
            _fields_ = [("biSize", ctypes.wintypes.DWORD),
                        ("biWidth", ctypes.c_long),
                        ("biHeight", ctypes.c_long),
                        ("biPlanes", ctypes.wintypes.WORD),
                        ("biBitCount", ctypes.wintypes.WORD),
                        ("biCompression", ctypes.wintypes.DWORD),
                        ("biSizeImage", ctypes.wintypes.DWORD),
                        ("biXPelsPerMeter", ctypes.c_long),
                        ("biYPelsPerMeter", ctypes.c_long),
                        ("biClrUsed", ctypes.wintypes.DWORD),
                        ("biClrImportant", ctypes.wintypes.DWORD)]
        class BITMAPINFO(ctypes.Structure):
            _fields_ = [("bmiHeader", BITMAPINFOHEADER),
                        ("bmiColors", ctypes.wintypes.DWORD*3)]
        HORZRES = ctypes.c_int(8)
        VERTRES = ctypes.c_int(10)
        SRCCOPY = 0xCC0020
        DIB_RGB_COLORS = 0

        ## Begin logic
        hdc = self._gdi32.CreateDCA(ctypes.c_char_p(device_name), 0, 0, 0)
        if hdc == 0:
            raise ValueError("Empty hdc provided")

        # Get monitor specs
        screen_width = self._gdi32.GetDeviceCaps(hdc, HORZRES)
        screen_height = self._gdi32.GetDeviceCaps(hdc, VERTRES)

        # Create memory device context for monitor
        hCaptureDC = self._gdi32.CreateCompatibleDC(hdc)
        if hCaptureDC == 0:
            raise WindowsError("gdi:CreateCompatibleDC failed")

        # Create bitmap compatible with monitor
        hCaptureBmp = self._gdi32.CreateCompatibleBitmap(hdc, screen_width, screen_height)
        if hCaptureBmp == 0:
            raise WindowsError("gdi:CreateCompatibleBitmap failed")

        # Select hCaptureBmp into hCaptureDC device context
        self._gdi32.SelectObject(hCaptureDC, hCaptureBmp)

        # Perform bit-block transfer from screen to device context (and thereby hCaptureBmp)
        self._gdi32.BitBlt(hCaptureDC, 0, 0, screen_width, screen_height, hdc, 0, 0, SRCCOPY)

        # Capture image bits from bitmap
        img_info = BITMAPINFO()
        img_info.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        img_info.bmiHeader.biWidth = screen_width
        img_info.bmiHeader.biHeight = screen_height
        img_info.bmiHeader.biPlanes = 1
        img_info.bmiHeader.biBitCount = 32
        img_info.bmiHeader.biCompression = 0
        img_info.bmiHeader.biClrUsed = 0
        img_info.bmiHeader.biClrImportant = 0

        buffer_length = screen_width * 4 * screen_height
        image_data = ctypes.create_string_buffer(buffer_length)

        scanlines = self._gdi32.GetDIBits(
            hCaptureDC,
            hCaptureBmp,
            0,
            screen_height,
            ctypes.byref(image_data),
            ctypes.byref(img_info),
            DIB_RGB_COLORS)
        if scanlines != screen_height:
            raise WindowsError("gdi:GetDIBits failed")
        final_image = ImageOps.flip(
            Image.frombuffer(
                "RGBX",
                (screen_width, screen_height),
                image_data,
                "raw",
                "RGBX",
                0,
                1))
        # Destroy created device context & GDI bitmap
        self._gdi32.DeleteObject(hdc)
        self._gdi32.DeleteObject(hCaptureDC)
        self._gdi32.DeleteObject(hCaptureBmp)
        return final_image
    def _getMonitorInfo(self):
        """ Returns info about the attached monitors, in device order

        [0] is always the primary monitor
        """
        monitors = []
        CCHDEVICENAME = 32
        def _MonitorEnumProcCallback(hMonitor, hdcMonitor, lprcMonitor, dwData):
            class MONITORINFOEX(ctypes.Structure):
                _fields_ = [("cbSize", ctypes.wintypes.DWORD),
                            ("rcMonitor", ctypes.wintypes.RECT),
                            ("rcWork", ctypes.wintypes.RECT),
                            ("dwFlags", ctypes.wintypes.DWORD),
                            ("szDevice", ctypes.wintypes.WCHAR*CCHDEVICENAME)]
            lpmi = MONITORINFOEX()
            lpmi.cbSize = ctypes.sizeof(MONITORINFOEX)
            self._user32.GetMonitorInfoW(hMonitor, ctypes.byref(lpmi))
            #hdc = self._gdi32.CreateDCA(ctypes.c_char_p(lpmi.szDevice), 0, 0, 0)
            monitors.append({
                "hmon": hMonitor,
                #"hdc":  hdc,
                "rect": (lprcMonitor.contents.left,
                         lprcMonitor.contents.top,
                         lprcMonitor.contents.right,
                         lprcMonitor.contents.bottom),
                "name": lpmi.szDevice
                })
            return True
        MonitorEnumProc = ctypes.WINFUNCTYPE(
            ctypes.c_bool,
            ctypes.c_ulong,
            ctypes.c_ulong,
            ctypes.POINTER(ctypes.wintypes.RECT),
            ctypes.c_int)
        callback = MonitorEnumProc(_MonitorEnumProcCallback)
        if self._user32.EnumDisplayMonitors(0, 0, callback, 0) == 0:
            raise WindowsError("Unable to enumerate monitors")
        # Clever magic to make the screen with origin of (0,0) [the primary monitor]
        # the first in the list
        # Sort by device ID - 0 is primary, 1 is next, etc.
        monitors.sort(key=lambda x: (not (x["rect"][0] == 0 and x["rect"][1] == 0), x["name"]))

        return monitors
    def _getVirtualScreenRect(self):
        """ The virtual screen is the bounding box containing all monitors.

        Not all regions in the virtual screen are actually visible. The (0,0) coordinate
        is the top left corner of the primary screen rather than the whole bounding box, so
        some regions of the virtual screen may have negative coordinates if another screen
        is positioned in Windows as further to the left or above the primary screen.

        Returns the rect as (x, y, w, h)
        """
        SM_XVIRTUALSCREEN = 76  # Left of virtual screen
        SM_YVIRTUALSCREEN = 77  # Top of virtual screen
        SM_CXVIRTUALSCREEN = 78 # Width of virtual screen
        SM_CYVIRTUALSCREEN = 79 # Heigiht of virtual screen

        return (self._user32.GetSystemMetrics(SM_XVIRTUALSCREEN), \
                self._user32.GetSystemMetrics(SM_YVIRTUALSCREEN), \
                self._user32.GetSystemMetrics(SM_CXVIRTUALSCREEN), \
                self._user32.GetSystemMetrics(SM_CYVIRTUALSCREEN))
    def _getVirtualScreenBitmap(self):
        """ Returns a PIL bitmap (BGR channel order) of all monitors

        Arranged like the Virtual Screen
        """

        # Collect information about the virtual screen & monitors
        min_x, min_y, screen_width, screen_height = self._getVirtualScreenRect()
        monitors = self._getMonitorInfo()

        # Initialize new black image the size of the virtual screen
        virt_screen = Image.new("RGB", (screen_width, screen_height))

        # Capture images of each of the monitors and overlay on the virtual screen
        for monitor_id in range(0, len(monitors)):
            img = self._captureScreen(monitors[monitor_id]["name"])
            # Capture virtscreen coordinates of monitor
            x1, y1, x2, y2 = monitors[monitor_id]["rect"]
            # Convert to image-local coordinates
            x = x1 - min_x
            y = y1 - min_y
            # Paste on the virtual screen
            virt_screen.paste(img, (x, y))
        return virt_screen

    ## Clipboard functions

    def getClipboard(self):
        """ Uses Tkinter to fetch any text on the clipboard.

        If a Tkinter root window has already been created somewhere else,
        uses that instead of creating a new one.
        """
        if tk._default_root is None:
            temporary_root = True
            root = tk.Tk()
            root.withdraw()
        else:
            temporary_root = False
            root = tk._default_root
        root.update()
        to_return = str(root.clipboard_get())
        if temporary_root:
            root.destroy()
        return to_return
    def setClipboard(self, text):
        """ Uses Tkinter to set the system clipboard.

        If a Tkinter root window has already been created somewhere else,
        uses that instead of creating a new one.
        """
        if tk._default_root is None:
            temporary_root = True
            root = tk.Tk()
            root.withdraw()
        else:
            temporary_root = False
            root = tk._default_root
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()
        if temporary_root:
            root.destroy()
    def osCopy(self):
        """ Triggers the OS "copy" keyboard shortcut """
        self.typeKeys("^c")
    def osPaste(self):
        """ Triggers the OS "paste" keyboard shortcut """
        self.typeKeys("^v")

    ## Window functions

    def getWindowByTitle(self, wildcard, order=0):
        """ Returns a handle for the first window that matches the provided "wildcard" regex """
        EnumWindowsProc = ctypes.WINFUNCTYPE(
            ctypes.c_bool,
            ctypes.POINTER(ctypes.c_int),
            ctypes.py_object)
        def callback(hwnd, context):
            if ctypes.windll.user32.IsWindowVisible(hwnd):
                length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
                buff = ctypes.create_unicode_buffer(length + 1)
                ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
                if re.search(context["wildcard"], buff.value) != None and not context["handle"]:
                    if context["order"] > 0:
                        context["order"] -= 1
                    else:
                        context["handle"] = hwnd
            return True
        data = {"wildcard": wildcard, "handle": None, "order": order}
        ctypes.windll.user32.EnumWindows(EnumWindowsProc(callback), ctypes.py_object(data))
        return data["handle"]
    def getWindowByPID(self, pid, order=0):
        """ Returns a handle for the first window that matches the provided PID """
        if pid <= 0:
            return None
        EnumWindowsProc = ctypes.WINFUNCTYPE(
            ctypes.c_bool,
            ctypes.POINTER(ctypes.c_int),
            ctypes.py_object)
        def callback(hwnd, context):
            if ctypes.windll.user32.IsWindowVisible(hwnd):
                pid = ctypes.c_long()
                ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                if context["pid"] == int(pid.value) and not context["handle"]:
                    if context["order"] > 0:
                        context["order"] -= 1
                    else:
                        context["handle"] = hwnd
            return True
        data = {"pid": pid, "handle": None, "order": order}
        ctypes.windll.user32.EnumWindows(EnumWindowsProc(callback), ctypes.py_object(data))
        return data["handle"]
    def getWindowRect(self, hwnd):
        """ Returns a rect (x,y,w,h) for the specified window's area """
        rect = ctypes.wintypes.RECT()
        if ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            x1 = rect.left
            y1 = rect.top
            x2 = rect.right
            y2 = rect.bottom
            return (x1, y1, x2-x1, y2-y1)
        return None
    def focusWindow(self, hwnd):
        """ Brings specified window to the front """
        Debug.log(3, "Focusing window: " + str(hwnd))
        SW_RESTORE = 9
        if ctypes.windll.user32.IsIconic(hwnd):
            ctypes.windll.user32.ShowWindow(hwnd, SW_RESTORE)
        ctypes.windll.user32.SetForegroundWindow(hwnd)
    def getWindowTitle(self, hwnd):
        """ Gets the title for the specified window """
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buff = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
        return buff.value
    def getWindowPID(self, hwnd):
        """ Gets the process ID that the specified window belongs to """
        pid = ctypes.c_long()
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        return int(pid.value)
    def getForegroundWindow(self):
        """ Returns a handle to the window in the foreground """
        return self._user32.GetForegroundWindow()

    ## Highlighting functions

    def highlight(self, rect, seconds=1):
        """ Simulates a transparent rectangle over the specified ``rect`` on the screen.

        Actually takes a screenshot of the region and displays with a
        rectangle border in a borderless window (due to Tkinter limitations)

        If a Tkinter root window has already been created somewhere else,
        uses that instead of creating a new one.
        """
        if tk._default_root is None:
            Debug.log(3, "Creating new temporary Tkinter root")
            temporary_root = True
            root = tk.Tk()
            root.withdraw()
        else:
            Debug.log(3, "Borrowing existing Tkinter root")
            temporary_root = False
            root = tk._default_root
        image_to_show = self.getBitmapFromRect(*rect)
        app = highlightWindow(root, rect, image_to_show)
        timeout = time.time()+seconds
        while time.time() < timeout:
            app.update_idletasks()
            app.update()
        app.destroy()
        if temporary_root:
            root.destroy()

    ## Process functions
    def isPIDValid(self, pid):
        """ Checks if a PID is associated with a running process """
        ## Slightly copied wholesale from http://stackoverflow.com/questions/568271/how-to-check-if-there-exists-a-process-with-a-given-pid
        ## Thanks to http://stackoverflow.com/users/1777162/ntrrgc and http://stackoverflow.com/users/234270/speedplane
        class ExitCodeProcess(ctypes.Structure):
            _fields_ = [('hProcess', ctypes.c_void_p),
                        ('lpExitCode', ctypes.POINTER(ctypes.c_ulong))]
        SYNCHRONIZE = 0x100000
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        process = self._kernel32.OpenProcess(SYNCHRONIZE|PROCESS_QUERY_LIMITED_INFORMATION, 0, pid)
        if not process:
            return False
        ec = ExitCodeProcess()
        out = self._kernel32.GetExitCodeProcess(process, ctypes.byref(ec))
        if not out:
            err = self._kernel32.GetLastError()
            if self._kernel32.GetLastError() == 5:
                # Access is denied.
                logging.warning("Access is denied to get pid info.")
            self._kernel32.CloseHandle(process)
            return False
        elif bool(ec.lpExitCode):
            # There is an exit code, it quit
            self._kernel32.CloseHandle(process)
            return False
        # No exit code, it's running.
        self._kernel32.CloseHandle(process)
        return True
    def killProcess(self, pid):
        """ Kills the process with the specified PID (if possible) """
        SYNCHRONIZE = 0x00100000L
        PROCESS_TERMINATE = 0x0001
        hProcess = self._kernel32.OpenProcess(SYNCHRONIZE|PROCESS_TERMINATE, True, pid)
        result = self._kernel32.TerminateProcess(hProcess, 0)
        self._kernel32.CloseHandle(hProcess)
    def getProcessName(self, pid):
        if pid <= 0:
            return ""
        MAX_PATH_LEN = 2048
        proc_name = ctypes.create_string_buffer(MAX_PATH_LEN)
        PROCESS_VM_READ = 0x0010
        PROCESS_QUERY_INFORMATION = 0x0400
        hProcess = self._kernel32.OpenProcess(PROCESS_VM_READ|PROCESS_QUERY_INFORMATION, 0, pid)
        #self._psapi.GetProcessImageFileName.restype = ctypes.wintypes.DWORD
        self._psapi.GetModuleFileNameExA(hProcess, 0, ctypes.byref(proc_name), MAX_PATH_LEN)
        return os.path.basename(str(proc_name.value))

## Helper class for highlighting

class highlightWindow(tk.Toplevel):
    def __init__(self, root, rect, screen_cap):
        """ Accepts rect as (x,y,w,h) """
        self.root = root
        tk.Toplevel.__init__(self, self.root, bg="red", bd=0)

        ## Set toplevel geometry, remove borders, and push to the front
        self.geometry("{2}x{3}+{0}+{1}".format(*rect))
        self.overrideredirect(1)
        self.attributes("-topmost", True)

        ## Create canvas and fill it with the provided image. Then draw rectangle outline
        self.canvas = tk.Canvas(
            self,
            width=rect[2],
            height=rect[3],
            bd=0,
            bg="blue",
            highlightthickness=0)
        self.tk_image = ImageTk.PhotoImage(Image.fromarray(screen_cap[..., [2, 1, 0]]))
        self.canvas.create_image(0, 0, image=self.tk_image, anchor=tk.NW)
        self.canvas.create_rectangle(
            2,
            2,
            rect[2]-2,
            rect[3]-2,
            outline="red",
            width=4)
        self.canvas.pack(fill=tk.BOTH, expand=tk.YES)

        ## Lift to front if necessary and refresh.
        self.lift()
        self.update()
