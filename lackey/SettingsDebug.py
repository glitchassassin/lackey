""" Defines Settings and Debug objects """
import datetime
import os
import __main__

from io import open # For Python 2 native line endings compatibility

from ._version import __version__, __sikuli_version__

class DebugMaster(object):
    """ Used to create the global Debug object """
    _log_file = None
    _debug_level = 0
    _logger = None
    _logger_no_prefix = False
    _logger_methods = {
        "user": None,
        "info": None,
        "action": None,
        "error": None,
        "debug": None
    }
    def user(self, message):
        """ Creates a user log (if user logging is turned on)

        Uses the log path defined by ``Debug.setUserLogFile()``. If no log file is
        defined, sends to STDOUT

        Note: Does *not* use Java string formatting like Sikuli.
        Format your message with Python ``basestring.format()`` instead.
        """
        if Settings.UserLogs:
            self._write_log(Settings.UserLogPrefix, Settings.UserLogTime, message)
    def history(self, message):
        """ Records an Action-level log message

        Uses the log path defined by ``Debug.setUserLogFile()``. If no log file is
        defined, sends to STDOUT
        """
        if Settings.ActionLogs:
            self._write_log("action", Settings.LogTime, message)
    def error(self, message):
        """ Records an Error-level log message

        Uses the log path defined by ``Debug.setUserLogFile()``. If no log file is
        defined, sends to STDOUT
        """
        if Settings.ErrorLogs:
            self._write_log("error", Settings.LogTime, message)
    def info(self, message):
        """ Records an Info-level log message

        Uses the log path defined by ``Debug.setUserLogFile()``. If no log file is
        defined, sends to STDOUT
        """
        if Settings.InfoLogs:
            self._write_log("info", Settings.LogTime, message)
    def on(self, level):
        """ Turns on all debugging messages up to the specified level

        0 = None; 1 = User;
        """
        if isinstance(level, int) and level >= 0 and level <= 3:
            self._debug_level = level
    def off(self):
        """ Turns off all debugging messages """
        self._debug_level = 0
    def log(self, level, message):
        """ Records a Debug-level log message
        Uses the log path defined by ``Debug.setUserLogFile()``. If no log file is
        defined, sends to STDOUT
        """
        if level <= self._debug_level:
            self._write_log("debug", Settings.LogTime, message)

    def setLogger(self, logger_obj):
        """ Sets log handler to ``logger_obj`` """
        self._logger = logger_obj
    def setLoggerNoPrefix(self, logger_obj):
        """ Sets log handler to ``logger_obj`` """
        self._logger = logger_obj
        self._logger_no_prefix = True
    def setLoggerAll(self, mthd):
        """ Sends all messages to ``logger.[mthd]()`` for handling """
        for key in self._logger_methods:
            self._logger_methods[key] = mthd
    def setLoggerUser(self, mthd):
        """ Sends user messages to ``logger.[mthd]()`` for handling """
        self._logger_methods["user"] = mthd
    def setLoggerInfo(self, mthd):
        """ Sends info messages to ``logger.[mthd]()`` for handling """
        self._logger_methods["info"] = mthd
    def setLoggerAction(self, mthd):
        """ Sends action messages to ``logger.[mthd]()`` for handling """
        self._logger_methods["action"] = mthd
    def setLoggerError(self, mthd):
        """ Sends error messages to ``logger.[mthd]()`` for handling """
        self._logger_methods["error"] = mthd
    def setLoggerDebug(self, mthd):
        """ Sends debug messages to ``logger.[mthd]()`` for handling """
        self._logger_methods["debug"] = mthd
    def setLogFile(self, filepath):
        """ Defines the file to which output log messages should be sent.

        Set to `None` to print to STDOUT instead.
        """
        if filepath is None:
            self._log_file = None
            return
        parsed_path = os.path.abspath(filepath)
        # Checks if the provided log filename is in a real directory, and that
        # the filename itself is not a directory.
        if os.path.isdir(os.path.dirname(parsed_path)) and not os.path.isdir(parsed_path):
            self._log_file = parsed_path
        else:
            raise IOError("File not found: " + filepath)
    def _write_log(self, log_type, log_time, message):
        """ Private method to abstract log writing for different types of logs """
        timestamp = datetime.datetime.now().strftime(" %Y-%m-%d %H:%M:%S")
        log_entry = "[{}{}] {}".format(log_type, timestamp if log_time else "", message)
        if self._logger and callable(getattr(self._logger, self._logger_methods[log_type], None)):
            # Check for log handler (sends message only if _logger_no_prefix is True)
            getattr(
                self._logger,
                self._logger_methods[log_type],
                None
                )(message if self._logger_no_prefix else log_entry)
        elif self._log_file:
            # Otherwise write to file, if a file has been specified
            with open(self._log_file, 'a') as logfile:
                try:
                    logfile.write(unicode(log_entry + "\n"))
                except NameError: # `unicode` only works in Python 2
                    logfile.write(log_entry + "\n")
        else:
            # Otherwise, print to STDOUT
            print(log_entry)

class SettingsMaster(object):
    """ Global settings that Lackey refers to by default """
    ## Logging Settings
    ActionLogs = True # Message prefix: [log]
    InfoLogs = True # Message prefix: [info]
    DebugLogs = False # Message prefix: [debug]
    ErrorLogs = False # Message prefix: [error]
    LogTime = False
    ### User Logging
    UserLogs = True
    UserLogPrefix = "user"
    UserLogTime = True

    ## Region Settings
    MinSimilarity = 0.7
    SlowMotionDelay = 3 # Extra duration of slowed-down visual effects
    WaitScanRate = 3	# Searches per second
    ObserveScanRate = 3 # Searches per second (observers)
    OberveMinChangedPixels = 50 # Threshold to trigger onChange() (not implemented yet)

    ## Keyboard/Mouse Settings
    MoveMouseDelay = 0.3 # Time to take moving mouse to target location
    DelayBeforeMouseDown = 0.3
    DelayBeforeDrag = 0.3
    DelayBeforeDrop = 0.3
    ClickDelay = 0.0 # Resets to 0 after next click
    TypeDelay = 0.0 # Resets to 0 after next keypress

    ## Action Settings
    ShowActions = False

    ## File Settings
    # Path to Sikuli project - might not be current directory
    try:
        BundlePath = os.path.dirname(os.path.abspath(os.path.join(os.getcwd(), __main__.__file__)))
    except AttributeError:
        BundlePath = os.path.dirname(os.path.abspath(os.getcwd()))
    ImagePaths = []
    OcrDataPath = None

    ## Popup settings
    PopupLocation = None

    # Environment methods

    def getSikuliVersion(self):
        return "Lackey {} (compatible with SikuliX {})".format(__version__, __sikuli_version__)


Debug = DebugMaster()
Settings = SettingsMaster()
