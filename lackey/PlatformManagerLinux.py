""" Platform-specific code for Linux is encapsulated in this module. """

# Working notes:
#
# Cloned initial draft from PlatformManagerWindows.
#
# Pyglet does a lot of low-level X stuff here:
#   https://bitbucket.org/pyglet/pyglet/src/default/pyglet/libs/x11/

import os
import re
import time
import numpy
import Xlib
import Xlib.display
import Xlib.X
import threading
try:
    import Tkinter as tk
except ImportError:
    import tkinter as tk
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

class PlatformManagerLinux(object):
    """ Abstracts Linux-specific OS-level features """
    def __init__(self):
        pass

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
        monitors = []
        disp = Xlib.display.Display()
        if disp.xinerama_is_active() == 1:
            # Get multi-monitor layout from xinerama if available
            screens = disp.xinerama_query_screens().screens
            for screen in screens:
                monitors.append({
                    "rect": (
                        screen.x,
                        screen.y,
                        screen.width,
                        screen.height
                    )
                })
        else:
            # Xinerama is not available, fallback to single screen details from xlib
            screen = disp.screen()
            monitors.append({
                "rect": (
                    0,
                    0,
                    screen.width_in_pixels,
                    screen.height_in_pixels
                )
            })
        return monitors
    def isPointVisible(self, x, y):
        """ Checks if a point is visible on any monitor. """
        for monitor in self.getScreenDetails():
            if (monitor["rect"][0] <= x <= monitor["rect"][0] + monitor["rect"][3] and
                monitor["rect"][1] <= y <= monitor["rect"][1] + monitor["rect"][4]):
                return True
        return False
    def _getVirtualScreenRect(self):
        """ Returns the rect of all attached screens as (x, y, w, h) """
        monitors = self.getScreenDetails()
        x1 = min([s["rect"][0] for s in monitors])
        y1 = min([s["rect"][1] for s in monitors])
        x2 = max([s["rect"][0]+s["rect"][2] for s in monitors])
        y2 = max([s["rect"][1]+s["rect"][3] for s in monitors])
    def _getVirtualScreenBitmap(self):
        """ Returns a PIL bitmap (BGR channel order) of all monitors

        Arranged like the Virtual Screen
        """

        disp = Xlib.display.Display()
        screen = disp.screen()
        w = screen.width_in_pixels
        h = screen.height_in_pixels
        root = screen.root
        raw = root.get_image(0,0,w,h, Xlib.X.ZPixmap, 0xffffffff)
        image = Image.frombytes("RGB", (w, h), raw.data, "raw", "BGRX")
        return image


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
        EnumLinuxProc = ctypes.WINFUNCTYPE(
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
        ctypes.windll.user32.EnumLinux(EnumLinuxProc(callback), ctypes.py_object(data))
        return data["handle"]
    def getWindowByPID(self, pid, order=0):
        """ Returns a handle for the first window that matches the provided PID """
        if pid <= 0:
            return None
        EnumLinuxProc = ctypes.WINFUNCTYPE(
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
        ctypes.windll.user32.EnumLinux(EnumLinuxProc(callback), ctypes.py_object(data))
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
