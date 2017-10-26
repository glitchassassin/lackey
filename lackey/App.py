""" Abstracts the capturing and interfacing of applications """
import os
import re
import time
import pyperclip
import platform
import subprocess

from .RegionMatching import Region
from .SettingsDebug import Debug

if platform.system() == "Windows":
    from .PlatformManagerWindows import PlatformManagerWindows
    PlatformManager = PlatformManagerWindows() # No other input managers built yet
elif platform.system() == "Darwin":
    from .PlatformManagerDarwin import PlatformManagerDarwin
    PlatformManager = PlatformManagerDarwin()
else:
    # Avoid throwing an error if it's just being imported for documentation purposes
    if not os.environ.get('READTHEDOCS') == 'True':
        raise NotImplementedError("Lackey is currently only compatible with Windows and OSX.")

# Python 3 compatibility
try:
    basestring
except NameError:
    basestring = str

class App(object):
    """ Allows apps to be selected by title, PID, or by starting an
    application directly. Can address individual windows tied to an
    app.

    For more information, see `Sikuli's App documentation <http://sikulix-2014.readthedocs.io/en/latest/appclass.html#App>`_.
    """
    def __init__(self, identifier=None):
        self._pid = None
        self._search = identifier
        self._title = ""
        self._exec = ""
        self._params = ""
        self._process = None
        self._devnull = None
        self._defaultScanRate = 0.1
        self.proc = None

        # Replace class methods with instance methods
        self.focus = self._focus_instance
        self.close = self._close_instance
        self.open = self._open_instance

        # Process `identifier`
        if isinstance(identifier, int):
            # `identifier` is a PID
            Debug.log(3, "Creating App by PID ({})".format(identifier))
            self._pid = identifier
        elif isinstance(identifier, basestring):
            # `identifier` is either part of a window title
            # or a command line to execute. If it starts with a "+",
            # launch it immediately. Otherwise, store it until open() is called.
            Debug.log(3, "Creating App by string ({})".format(identifier))
            launchNow = False
            if identifier.startswith("+"):
                # Should launch immediately - strip the `+` sign and continue
                launchNow = True
                identifier = identifier[1:]
            # Check if `identifier` is an executable commmand
            # Possible formats:
            # Case 1: notepad.exe C:\sample.txt
            # Case 2: "C:\Program Files\someprogram.exe" -flag

            # Extract hypothetical executable name
            if identifier.startswith('"'):
                executable = identifier[1:].split('"')[0]
                params = identifier[len(executable)+2:].split(" ") if len(identifier) > len(executable) + 2 else []
            else:
                executable = identifier.split(" ")[0]
                params = identifier[len(executable)+1:].split(" ") if len(identifier) > len(executable) + 1 else []

            # Check if hypothetical executable exists
            if self._which(executable) is not None:
                # Found the referenced executable
                self._exec = executable
                self._params = params
                # If the command was keyed to execute immediately, do so.
                if launchNow:
                    self.open()
            else:
                # No executable found - treat as a title instead. Try to capture window.
                self._title = identifier
                self.open()
        else:
            self._pid = -1 # Unrecognized identifier, setting to empty app

        self._pid = self.getPID() # Confirm PID is an active process (sets to -1 otherwise)

    def _which(self, program):
        """ Private method to check if an executable exists

        Shamelessly stolen from http://stackoverflow.com/questions/377017/test-if-executable-exists-in-python
        """
        def is_exe(fpath):
            return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

        fpath, fname = os.path.split(program)
        if fpath:
            if is_exe(program):
                return program
        else:
            for path in os.environ["PATH"].split(os.pathsep):
                path = path.strip('"')
                exe_file = os.path.join(path, program)
                if is_exe(exe_file):
                    return exe_file
        return None

    @classmethod
    def pause(cls, waitTime):
        time.sleep(waitTime)

    @classmethod
    def focus(cls, appName):
        """ Searches for exact text, case insensitive, anywhere in the window title. 

        Brings the matching window to the foreground.

        As a class method, accessible as `App.focus(appName)`. As an instance method,
        accessible as `App(appName).focus()`.
        """
        app = cls(appName)
        return app.focus()
    def _focus_instance(self):
        """ In instances, the ``focus()`` classmethod is replaced with this instance method. """
        if self._title:
            Debug.log(3, "Focusing app with title like ({})".format(self._title))
            PlatformManager.focusWindow(PlatformManager.getWindowByTitle(re.escape(self._title)))
            if self.getPID() == -1:
                self.open()
        elif self._pid and self._pid != -1:
            Debug.log(3, "Focusing app with pid ({})".format(self._pid))
            PlatformManager.focusWindow(PlatformManager.getWindowByPID(self._pid))
        return self

    @classmethod
    def close(cls, appName):
        """ Closes the process associated with the specified app.

        As a class method, accessible as `App.class(appName)`.
        As an instance method, accessible as `App(appName).close()`.
        """
        return cls(appName).close()
    def _close_instance(self):
        if self._process:
            self._process.terminate()
            self._devnull.close()
        elif self.getPID() != -1:
            PlatformManager.killProcess(self.getPID())

    @classmethod
    def open(self, executable):
        """ Runs the specified command and returns an App linked to the generated PID.

        As a class method, accessible as `App.open(executable_path)`.
        As an instance method, accessible as `App(executable_path).open()`.
        """
        return App(executable).open()
    def _open_instance(self, waitTime=0):
        if self._exec != "":
            # Open from an executable + parameters
            self._devnull = open(os.devnull, 'w')
            self._process = subprocess.Popen([self._exec] + self._params, shell=False, stderr=self._devnull, stdout=self._devnull)
            self._pid = self._process.pid
        elif self._title != "":
            # Capture an existing window that matches self._title
            self._pid = PlatformManager.getWindowPID(
                PlatformManager.getWindowByTitle(
                    re.escape(self._title)))
        time.sleep(waitTime)
        return self

    @classmethod
    def focusedWindow(cls):
        """ Returns a Region corresponding to whatever window is in the foreground """
        x, y, w, h = PlatformManager.getWindowRect(PlatformManager.getForegroundWindow())
        return Region(x, y, w, h)

    def getWindow(self):
        """ Returns the title of the main window of the currently open app.

        Returns an empty string if no match could be found.
        """
        if self.getPID() != -1:
            return PlatformManager.getWindowTitle(PlatformManager.getWindowByPID(self.getPID()))
        else:
            return ""
    def getName(self):
        """ Returns the short name of the app as shown in the process list """
        return PlatformManager.getProcessName(self.getPID())
    def getPID(self):
        """ Returns the PID for the associated app
        (or -1, if no app is associated or the app is not running)
        """
        if self._pid is not None:
            if not PlatformManager.isPIDValid(self._pid):
                self._pid = -1
            return self._pid
        return -1

    def hasWindow(self):
        """ Returns True if the process has a window associated, False otherwise """
        return PlatformManager.getWindowByPID(self.getPID()) is not None
    def waitForWindow(self, seconds=5):
        timeout = time.time() + seconds
        while True:
            window_region = self.window()
            if window_region is not None or time.time() < timeout:
                break
            time.sleep(0.5)
        return window_region
    def window(self, windowNum=0):
        """ Returns the region corresponding to the specified window of the app.

        Defaults to the first window found for the corresponding PID.
        """
        if self._pid == -1:
            return None
        x,y,w,h = PlatformManager.getWindowRect(PlatformManager.getWindowByPID(self._pid, windowNum))
        return Region(x,y,w,h).clipRegionToScreen()

    def setUsing(self, params):
        self._params = params.split(" ")

    def __repr__(self):
        """ Returns a string representation of the app """
        return "[{pid}:{executable} ({windowtitle})] {searchtext}".format(pid=self._pid, executable=self.getName(), windowtitle=self.getWindow(), searchtext=self._search)

    def isRunning(self, waitTime=0):
        """ If PID isn't set yet, checks if there is a window with the specified title. """
        waitUntil = time.time() + waitTime
        while True:
            if self.getPID() > 0:
                return True
            else:
                self._pid = PlatformManager.getWindowPID(PlatformManager.getWindowByTitle(re.escape(self._title)))

            # Check if we've waited long enough
            if time.time() > waitUntil:
                break
            else:
                time.sleep(self._defaultScanRate)
        return self.getPID() > 0
    def isValid(self):
        return (os.path.isfile(self._exec) or self.getPID() > 0)
    @classmethod
    def getClipboard(cls):
        """ Gets the contents of the clipboard (as classmethod) """
        return pyperclip.paste()
    @classmethod
    def setClipboard(cls, contents):
        """ Sets the contents of the clipboard (as classmethod) """
        return pyperclip.copy(contents)
