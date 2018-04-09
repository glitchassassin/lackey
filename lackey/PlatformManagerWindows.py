""" Platform-specific code for Windows is encapsulated in this module. """

import os
import re
import time
import numpy
import ctypes
import threading
try:
    import Tkinter as tk
except ImportError:
    import tkinter as tk
from ctypes import wintypes
from PIL import Image, ImageTk, ImageOps

from .SettingsDebug import Debug

# Python 3 compatibility
try:
    basestring
except NameError:
    basestring = str
try:
    unicode
except:
    unicode = str

class PlatformManagerWindows(object):
    """ Abstracts Windows-specific OS-level features """
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

        # Pay attention to different screen DPI settings
        self._user32.SetProcessDPIAware()

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

    def _check_count(self, result, func, args):
        #pylint: disable=unused-argument
        """ Private function to return ctypes errors cleanly """
        if result == 0:
            raise ctypes.WinError(ctypes.get_last_error())
        return args

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
            return self._getVirtualScreenRect()
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
        SRCCOPY =    0x00CC0020
        CAPTUREBLT = 0x40000000
        DIB_RGB_COLORS = 0

        ## Begin logic
        self._gdi32.CreateDCW.restype = ctypes.c_void_p
        hdc = self._gdi32.CreateDCW(ctypes.c_wchar_p(str(device_name)), 0, 0, 0) # Convert to bytestring for c_wchar_p type
        if hdc == 0:
            raise ValueError("Empty hdc provided")

        # Get monitor specs
        self._gdi32.GetDeviceCaps.argtypes = [ctypes.c_void_p, ctypes.c_int]
        screen_width = self._gdi32.GetDeviceCaps(hdc, HORZRES)
        screen_height = self._gdi32.GetDeviceCaps(hdc, VERTRES)

        # Create memory device context for monitor
        self._gdi32.CreateCompatibleDC.restype = ctypes.c_void_p
        self._gdi32.CreateCompatibleDC.argtypes = [ctypes.c_void_p]
        hCaptureDC = self._gdi32.CreateCompatibleDC(hdc)
        if hCaptureDC == 0:
            raise WindowsError("gdi:CreateCompatibleDC failed")

        # Create bitmap compatible with monitor
        self._gdi32.CreateCompatibleBitmap.restype = ctypes.c_void_p
        self._gdi32.CreateCompatibleBitmap.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
        hCaptureBmp = self._gdi32.CreateCompatibleBitmap(hdc, screen_width, screen_height)
        if hCaptureBmp == 0:
            raise WindowsError("gdi:CreateCompatibleBitmap failed")

        # Select hCaptureBmp into hCaptureDC device context
        self._gdi32.SelectObject.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        self._gdi32.SelectObject(hCaptureDC, hCaptureBmp)

        # Perform bit-block transfer from screen to device context (and thereby hCaptureBmp)
        self._gdi32.BitBlt.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_ulong
        ]
        self._gdi32.BitBlt(hCaptureDC, 0, 0, screen_width, screen_height, hdc, 0, 0, SRCCOPY | CAPTUREBLT)

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

        self._gdi32.GetDIBits.restype = ctypes.c_int
        self._gdi32.GetDIBits.argtypes = [
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_uint,
            ctypes.c_uint,
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_uint
        ]
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
        self._gdi32.DeleteObject.argtypes = [ctypes.c_void_p]
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
        SM_CYVIRTUALSCREEN = 79 # Height of virtual screen

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
    def osCopy(self):
        """ Triggers the OS "copy" keyboard shortcut """
        from .InputEmulation import Keyboard
        k = Keyboard()
        k.keyDown("{CTRL}")
        k.type("c")
        k.keyUp("{CTRL}")
    def osPaste(self):
        """ Triggers the OS "paste" keyboard shortcut """
        from .InputEmulation import Keyboard
        k = Keyboard()
        k.keyDown("{CTRL}")
        k.type("v")
        k.keyUp("{CTRL}")

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
                if re.search(context["wildcard"], buff.value, flags=re.I) != None and not context["handle"]:
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
                pid = ctypes.c_ulong()
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
        pid = ctypes.c_ulong()
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        return int(pid.value)
    def getForegroundWindow(self):
        """ Returns a handle to the window in the foreground """
        return self._user32.GetForegroundWindow()

    ## Highlighting functions
    def highlight(self, rect, color="red", seconds=None):
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
        app = highlightWindow(root, rect, color, image_to_show)
        if seconds == 0:
            t = threading.Thread(target=app.do_until_timeout)
            t.start()
            return app
        app.do_until_timeout(seconds)
        

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
        SYNCHRONIZE = 0x00100000
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
        return os.path.basename(proc_name.value.decode("utf-8"))

## Helper class for highlighting

class highlightWindow(tk.Toplevel):
    def __init__(self, root, rect, frame_color, screen_cap):
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
            outline=frame_color,
            width=4)
        self.canvas.pack(fill=tk.BOTH, expand=tk.YES)

        ## Lift to front if necessary and refresh.
        self.lift()
        self.update()
    def do_until_timeout(self, seconds=None):
        if seconds is not None:
            self.root.after(seconds*1000, self.root.destroy)
        self.root.mainloop()

    def close(self):
        self.root.destroy()
