""" Sikuli script implementation for Python

See https://github.com/glitchassassin/lackey
"""

from zipfile import ZipFile
try:
    import Tkinter as tk
    import tkFileDialog
    import tkMessageBox
except ImportError:
    import tkinter as tk
    from tkinter import filedialog as tkFileDialog
    from tkinter import messagebox as tkMessageBox

import platform
import keyboard
try:
    import thread
except ImportError:
    import _thread as thread
import sys
import time
import os
import warnings
import requests

## Lackey sub-files

#from .PlatformManagerWindows import PlatformManagerWindows
from .KeyCodes import Button, Key, KeyModifier
from .RegionMatching import Pattern, Region, Match, Screen, ObserveEvent, PlatformManager, FOREVER
from .Geometry import Location
from .InputEmulation import Mouse, Keyboard
from .App import App
from .Exceptions import FindFailed, ImageMissing
from .SettingsDebug import Debug, Settings, DebugMaster, SettingsMaster
from .SikuliGui import PopupInput, PopupList, PopupTextarea
from ._version import __version__

from . import ImportHandler

VALID_PLATFORMS = ["Windows", "Darwin"]

## Define script abort hotkey (Alt+Shift+C)

def _abort_script():
    thread.interrupt_main()

keyboard.add_hotkey("alt+shift+c", _abort_script, suppress=True)

## Sikuli patching: Functions that map to the global Screen region
## Don't try this at home, kids!

# First, save the native functions by remapping them with a trailing underscore:

type_ = type
input_ = input
exit_ = sys.exit
#zip_ = zip


# Deprecated underscore functions

def _exit(code):
    warnings.warn("Please use exit_ instead.", DeprecationWarning)
    return exit_(code)

def _input(prompt):
    warnings.warn("Please use input_ instead.", DeprecationWarning)
    return input_(prompt)

def _type(obj):
    warnings.warn("Please use type_ instead.", DeprecationWarning)
    return type_(obj)


## Sikuli Convenience Functions

def sleep(seconds):
    """ Convenience function. Pauses script for `seconds`. """
    time.sleep(seconds)

def exit(value):
    """ Convenience function. Exits with code `value`. """
    sys.exit(value)

def setShowActions(value):
    """ Convenience function. Sets "show actions" setting (True or False) """
    Settings.ShowActions = bool(value)

def getBundlePath():
    """ Convenience function. Returns the path of the \\*.sikuli bundle. """
    return Settings.BundlePath
def getBundleFolder():
    """ Convenience function. Same as `getBundlePath()` plus the OS default path separator. """
    return getBundlePath() + os.path.sep
def setBundlePath(path):
    """ Convenience function. Changes the path of the \\*.sikuli bundle. """
    if os.path.exists(path):
        Settings.BundlePath = path
    else:
        raise OSError("File not found: " + path)
def getImagePath():
    """ Convenience function. Returns a list of paths to search for images. """
    return [getBundlePath()] + Settings.ImagePaths
def addImagePath(new_path):
    """ Convenience function. Adds a path to the list of paths to search for images.

    Can be a URL (but must be accessible). """
    if os.path.exists(new_path):
        Settings.ImagePaths.append(new_path)
    elif "http://" in new_path or "https://" in new_path:
        request = requests.get(new_path)
        if request.status_code < 400:
            # Path exists
            Settings.ImagePaths.append(new_path)
        else:
            raise OSError("Unable to connect to " + new_path)
    else:
        raise OSError("File not found: " + new_path)
def addHTTPImagePath(new_path):
    """ Convenience function. Same as `addImagePath()`. """
    addImagePath(new_path)

def getParentPath():
    """ Convenience function. Returns the parent folder of the \\*.sikuli bundle. """
    return os.path.dirname(Settings.BundlePath)
def getParentFolder():
    """ Convenience function. Same as `getParentPath()` plus the OS default path separator. """
    return getParentPath() + os.path.sep
def makePath(*args):
    """ Convenience function. Returns a path from a series of path components.

    Same as `os.path.join`. """
    return os.path.join(*args)
def makeFolder(*args):
    """ Convenience function. Same as `makePath()` plus the OS default path separator. """
    return makePath(*args) + os.path.sep

## Sikuli implements the unzip() file, below. Included here to avoid breaking old
## scripts. ``zipfile()`` is coded here, but not included in Sikuli, so I've
## commented it out for the time being. Note that ``zip`` is a reserved keyword
## in Python.

def unzip(from_file, to_folder):
    """ Convenience function.

    Extracts files from the zip file `fromFile` into the folder `toFolder`. """
    with ZipFile(os.path.abspath(from_file), 'r') as to_unzip:
        to_unzip.extractall(os.path.abspath(to_folder))
#def zipfile(fromFolder, toFile):
#	with ZipFile(toFile, 'w') as to_zip:
#		for root, dirs, files in os.walk(fromFolder):
#			for file in files:
#				to_zip.write(os.path.join(root, file))


## Popup/input dialogs

def popat(*args):
    """ Convenience function. Sets the popup location (currently not used). """
    if len(args) == 2 and isinstance(args[0], int) and isinstance(args[1], int):
        # popat(x,y)
        Settings.PopupLocation = Location(args[0], args[1])
    elif len(args) == 1 and isinstance(args[0], Location):
        # popat(location)
        Settings.PopupLocation = args[0]
    elif len(args) == 1 and isinstance(args[0], Region):
        Settings.PopupLocation = args[0].getCenter()
    elif len(args) == 0:
        Settings.PopupLocation = SCREEN.getCenter()
    else:
        raise TypeError("Unrecognized parameter(s) for popat")

def popup(text, title="Lackey Info"):
    """ Creates an info dialog with the specified text. """
    root = tk.Tk()
    root.withdraw()
    tkMessageBox.showinfo(title, text)
def popError(text, title="Lackey Error"):
    """ Creates an error dialog with the specified text. """
    root = tk.Tk()
    root.withdraw()
    tkMessageBox.showerror(title, text)
def popAsk(text, title="Lackey Decision"):
    """ Creates a yes-no dialog with the specified text. """
    root = tk.Tk()
    root.withdraw()
    return tkMessageBox.askyesno(title, text)

# Be aware this overwrites the Python input() command-line function.
def input(msg="", default="", title="Lackey Input", hidden=False):
    """ Creates an input dialog with the specified message and default text.

    If `hidden`, creates a password dialog instead. Returns the entered value. """
    root = tk.Tk()
    input_text = tk.StringVar()
    input_text.set(default)
    PopupInput(root, msg, title, hidden, input_text)
    root.focus_force()
    root.mainloop()
    return str(input_text.get())
def inputText(message="", title="Lackey Input", lines=9, width=20, text=""):
    """ Creates a textarea dialog with the specified message and default text.

    Returns the entered value. """
    root = tk.Tk()
    input_text = tk.StringVar()
    input_text.set(text)
    PopupTextarea(root, message, title, lines, width, input_text)
    root.focus_force()
    root.mainloop()
    return str(input_text.get())
def select(message="", title="Lackey Input", options=None, default=None):
    """ Creates a dropdown selection dialog with the specified message and options

     `default` must be one of the options.

     Returns the selected value. """
    if options is None or len(options) == 0:
        return ""
    if default is None:
        default = options[0]
    if default not in options:
        raise ValueError("<<default>> not in options[]")
    root = tk.Tk()
    input_text = tk.StringVar()
    input_text.set(message)
    PopupList(root, message, title, options, default, input_text)
    root.focus_force()
    root.mainloop()
    return str(input_text.get())
def popFile(title="Lackey Open File"):
    """ Creates a file selection dialog with the specified message and options.

    Returns the selected file. """
    root = tk.Tk()
    root.withdraw()
    return str(tkFileDialog.askopenfilename(title=title))

# If this is a valid platform, set up initial Screen object. Otherwise, might be ReadTheDocs
if platform.system() in VALID_PLATFORMS:
    SCREEN = Screen(0)
    for prop in dir(SCREEN):
        if callable(getattr(SCREEN, prop, None)) and prop[0] != "_":
            # Property is a method, and is not private. Dump it into the global namespace.
            globals()[prop] = getattr(SCREEN, prop, None)
            