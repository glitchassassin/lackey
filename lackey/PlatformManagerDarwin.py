""" Platform-specific code for Darwin is encapsulated in this module. """

import os
import re
import tempfile
import threading
import subprocess
try:
    import Tkinter as tk
    import Queue as queue
except ImportError:
    import tkinter as tk
    import queue

import numpy
import AppKit
import Quartz
from PIL import Image, ImageTk

from .SettingsDebug import Debug
from .InputEmulation import Keyboard

# Python 3 compatibility
try:
    basestring
except NameError:
    basestring = str

class PlatformManagerDarwin(object):
    """ Abstracts Darwin-specific OS-level features """
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

    ## Screen functions

    def getBitmapFromRect(self, x, y, w, h):
        """ Capture the specified area of the (virtual) screen. """
        min_x, min_y, screen_width, screen_height = self._getVirtualScreenRect()
        img = self._getVirtualScreenBitmap() # TODO
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
    def _getVirtualScreenRect(self):
        """ Returns the rect of all attached screens as (x, y, w, h) """
        monitors = self.getScreenDetails()
        x1 = min([s["rect"][0] for s in monitors])
        y1 = min([s["rect"][1] for s in monitors])
        x2 = max([s["rect"][0]+s["rect"][2] for s in monitors])
        y2 = max([s["rect"][1]+s["rect"][3] for s in monitors])
        return (x1, y1, x2-x1, y2-y1)
    def _getVirtualScreenBitmap(self):
        """ Returns a bitmap of all attached screens """
        filenames = []
        screen_details = self.getScreenDetails()
        for screen in screen_details:
            fh, filepath = tempfile.mkstemp('.png')
            filenames.append(filepath)
            os.close(fh)
        subprocess.call(['screencapture', '-x'] + filenames)

        min_x, min_y, screen_w, screen_h = self._getVirtualScreenRect()
        virtual_screen = Image.new("RGB", (screen_w, screen_h))
        for filename, screen in zip(filenames, screen_details):
            # Capture virtscreen coordinates of monitor
            x, y, w, h = screen["rect"]
            # Convert image size if needed
            im = Image.open(filename)
            im.load()
            if im.size[0] != w or im.size[1] != h:
                im = im.resize((int(w), int(h)), Image.ANTIALIAS)
            # Convert to image-local coordinates
            x = x - min_x
            y = y - min_y
            # Paste on the virtual screen
            virtual_screen.paste(im, (x, y))
            os.unlink(filename)
        return virtual_screen

    def getScreenDetails(self):
        """ Return list of attached monitors

        For each monitor (as dict), ``monitor["rect"]`` represents the screen as positioned
        in virtual screen. List is returned in device order, with the first element (0)
        representing the primary monitor.
        """
        primary_screen = None
        screens = []
        for monitor in AppKit.NSScreen.screens():
            # Convert screen rect to Lackey-style rect (x,y,w,h) as position in virtual screen
            screen = {
                "rect": (
                    int(monitor.frame().origin.x),
                    int(monitor.frame().origin.y),
                    int(monitor.frame().size.width),
                    int(monitor.frame().size.height)
                )
            }
            screens.append(screen)
        return screens
    def isPointVisible(self, x, y):
        """ Checks if a point is visible on any monitor. """
        for screen in self.getScreenDetails():
            s_x, s_y, s_w, s_h = screen["rect"]
            if (s_x <= x < (s_x + s_w)) and (s_y <= y < (s_y + s_h)):
                return True
        return False

    ## Clipboard functions

    def osCopy(self):
        """ Triggers the OS "copy" keyboard shortcut """
        k = Keyboard()
        k.keyDown("{CTRL}")
        k.type("c")
        k.keyUp("{CTRL}")
    def osPaste(self):
        """ Triggers the OS "paste" keyboard shortcut """
        k = Keyboard()
        k.keyDown("{CTRL}")
        k.type("v")
        k.keyUp("{CTRL}")

    ## Window functions

    def getWindowByTitle(self, wildcard, order=0):
        """ Returns a handle for the first window that matches the provided "wildcard" regex """
        for w in self._get_window_list():
            if "kCGWindowName" in w and re.search(wildcard, w["kCGWindowName"], flags=re.I):
                # Matches - make sure we get it in the correct order
                if order == 0:
                    return w["kCGWindowNumber"]
                else:
                    order -= 1
        
    def getWindowByPID(self, pid, order=0):
        """ Returns a handle for the first window that matches the provided PID """
        for w in self._get_window_list():
            if "kCGWindowOwnerPID" in w and w["kCGWindowOwnerPID"] == pid:
                # Matches - make sure we get it in the correct order
                if order == 0:
                    return w["kCGWindowNumber"]
                else:
                    order -= 1
        raise OSError("Could not find window for PID {} at index {}".format(pid, order))
    def getWindowRect(self, hwnd):
        """ Returns a rect (x,y,w,h) for the specified window's area """
        for w in self._get_window_list():
            if "kCGWindowNumber" in w and w["kCGWindowNumber"] == hwnd:
                x = w["kCGWindowBounds"]["X"]
                y = w["kCGWindowBounds"]["Y"]
                width = w["kCGWindowBounds"]["Width"]
                height = w["kCGWindowBounds"]["Height"]
                return (x, y, width, height)
        raise OSError("Unrecognized window number {}".format(hwnd))
    def focusWindow(self, hwnd):
        """ Brings specified window to the front """
        Debug.log(3, "Focusing window: " + str(hwnd))
        # TODO
        pass
    def getWindowTitle(self, hwnd):
        """ Gets the title for the specified window """
        for w in self._get_window_list():
            if "kCGWindowNumber" in w and w["kCGWindowNumber"] == hwnd:
                return w["kCGWindowName"]
    def getWindowPID(self, hwnd):
        """ Gets the process ID that the specified window belongs to """
        for w in self._get_window_list():
            if "kCGWindowNumber" in w and w["kCGWindowNumber"] == hwnd:
                return w["kCGWindowOwnerPID"]
    def getForegroundWindow(self):
        """ Returns a handle to the window in the foreground """
        active_app = NSWorkspace.sharedWorkspace().frontmostApplication().localizedName()
        for w in self._get_window_list():
            if "kCGWindowOwnerName" in w and w["kCGWindowOwnerName"] == active_app:
                return w["kCGWindowNumber"]

    def _get_window_list(self):
        """ Returns a dictionary of details about open windows """
        window_list = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListExcludeDesktopElements, Quartz.kCGNullWindowID)
        return window_list

    ## Highlighting functions

    def highlight(self, rect, color="red", seconds=None):
        """ Simulates a transparent rectangle over the specified ``rect`` on the screen.

        Actually takes a screenshot of the region and displays with a
        rectangle border in a borderless window (due to Tkinter limitations)

        If a Tkinter root window has already been created somewhere else,
        uses that instead of creating a new one.
        """
        self.queue = queue.Queue()
        if seconds == 0:
            t = threading.Thread(target=self._do_until_timeout, args=(self.queue,(rect,color,seconds)))
            t.start()
            q = self.queue
            control_obj = lambda: None
            control_obj.close = lambda: q.put(True)
            return control_obj
        self._do_until_timeout(self.queue, (rect,color,seconds))
    
    def _do_until_timeout(self, queue, args):
        rect, color, seconds = args
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
        app = highlightWindow(root, rect, color, image_to_show, queue)
        app.do_until_timeout(seconds)

    ## Process functions
    def isPIDValid(self, pid):
        """ Checks if a PID is associated with a running process """
        try:
            os.kill(pid, 0) # Does nothing if valid, raises exception otherwise
        except OSError:
            return False
        else:
            return True
    def killProcess(self, pid):
        """ Kills the process with the specified PID (if possible) """
        os.kill(pid, 15)
    def getProcessName(self, pid):
        """ Searches all processes for the given PID, then returns the originating command """
        ps = subprocess.check_output(["ps", "aux"]).decode("ascii")
        processes = ps.split("\n")
        cols = len(processes[0].split()) - 1
        for row in processes[1:]:
            if row != "":
                proc = row.split(None, cols)
                if proc[1].strip() == str(pid):
                    return proc[-1]

## Helper class for highlighting

class highlightWindow(tk.Toplevel):
    def __init__(self, root, rect, frame_color, screen_cap, queue):
        """ Accepts rect as (x,y,w,h) """
        self.root = root
        self.root.tk.call('tk', 'scaling', 0.5)
        tk.Toplevel.__init__(self, self.root, bg="red", bd=0)

        self.queue = queue
        self.check_close_after = None

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
        self.tk_image = ImageTk.PhotoImage(Image.fromarray(screen_cap))
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
        self.check_close()
        if seconds is not None:
            self.root.after(seconds*1000, self.close)
        self.root.mainloop()

    def check_close(self):
        try:
            kill = self.queue.get_nowait()
            if kill == True:
                self.close()
                return
        except queue.Empty:
            pass

        self.check_close_after = self.root.after(500, self.check_close)
    def close(self):
        if self.check_close_after is not None:
            self.root.after_cancel(self.check_close_after)
        self.root.destroy()
