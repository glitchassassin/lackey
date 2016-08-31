PlatformManager API
===================

Introduction
------------

OS-specific functionality is abstracted into a PlatformManager object for ease of porting Lackey to other desktop platforms. Any object which obeys the interface definition provided herein can be used as a PlatformManager. New PlatformManagers should be added to the conditional statements in RegionMatching.py.

Properties
----------

PlatformManager has no public properties. Accessing private properties of a specific PlatformManager from outside the module is bad practice and is strongly discouraged.

Methods
-------

- **Mouse Functions**
    - **clickMouse** (button=0):
        - Clicks the specified mouse button (0=LEFT, 1=MIDDLE, 2=RIGHT)
    - **mouseButtonDown** (button=0):
        - Sets the specified mouse button to "down" (0=LEFT, 1=MIDDLE, 2=RIGHT)
    - **mouseButtonUp** (button=0):
        - Sets the specified mouse button to "up" (0=LEFT, 1=MIDDLE, 2=RIGHT)
    - **mouseWheel** (direction, steps):
        - Spins the mouse wheel ``steps`` ticks in ``direction`` (0=DOWN, 1=UP)
    - **setMousePos** (location):
        - Accepts a tuple ``(x,y)`` and sets the mouse position accordingly
    - **getMousePos** ():
        - Returns a tuple ``(x,y)`` of the current mouse position
- **Keyboard Functions**
    - **pressKey** (text):
        - Accepts a string of one or more keys in typeKeys() format (see below). Sets all of them to "down."
    - **releaseKey** (text):
        - Accepts a string of one or more keys in typeKeys() format (see below). Sets all of them to "up."
    - **typeKeys** ():
        - Accepts a string of one or more keys and translates them into a series of keypresses. Keys may be "special keys" noted by brackets (e.g., ``"Put in a new line{ENTER}"``). 
        - Uses shift key to enter uppercase letters/symbols.
            - ``"Hello!"`` translates to ``SHIFT,h,unshift,e,l,l,o,SHIFT,1,unshift``
        - Also supports SendKeys-style modifiers (e.g., ``"^v"`` to type CTRL+V). 
            - To enter a modifier as a key, put it in brackets: ``"{+}"``. 
            - To modify a group of characters, use parentheses: ``"+(bacon)"``
- **Clipboard Functions**
    - **osCopy** ():
        - Triggers the OS "copy" keyboard shortcut (usually CTRL+C or CMD+C)
    - **osPaste** ():
        - Triggers the OS "paste" keyboard shortcut (usually CTRL+V or CMD+V)
    - **setClipboard** (text):
        - Sets the system clipboard to ``text``
    - **getClipboard** ():
        - Returns any text in the clipboard
- **Window Functions**
    - **getWindowByTitle** (wildcard, windowNum=0):
        - Returns the native window handle (as a Python object) for a window that matches the specified regex. If multiple windows with the regex exist, return the ``windowNum`` -th of them (starting from 0).
    - **getWindowByPID** (pid, windowNum=0):
        - Returns the native window handle (as a Python object) for a window that is owned by the specified process. If multiple windows exist for the specified process, return the ``windowNum`` -th of them (starting from 0).
    - **getForegroundWindow** ():
        - Returns the native window handle (as a Python object) for the window currently in the foreground.
    - **getWindowPID** (handle):
        - Return the PID that owns the given native window handle (provided by a function like ``getWindowByTitle()``). Returns -1 if the process no longer exists.
    - **getWindowRect** (handle):
        - Return a rect ``(x1,y1,x2,y2)`` for the area of the window with the given native handle.
    - **getWindowTitle** (handle):
        - Return the title of the window with the given native handle.
    - **focusWindow** (handle):
        - Bring the specified window to the front and give it focus.
- **Screen Functions**
    - **getBitmapFromRect** (x, y, w, h):
        - Returns a numpy array of the specified area of the screen. If the area goes outside the virtual screen rect, truncate the area at the edge. If part of the area is outside of a visible screen (but inside the virtual screen rect), set it to black.
    - **getScreenBounds** (screen):
        - Returns the screen size of the specified monitor (0 being the primary monitor, 1+ being additional monitors; -1 to get the bounds of the virtual screen)
    - **getScreenDetails** ():
        - Returns a list of the screens attached to the system. Each screen object has one property, "rect", which is a tuple containing the rect ``(x,y,w,h)`` of the screen's area relative to the main monitor.
    - **isPointVisible** (x, y):
        - Checks if a point is visible (on any monitor).
- **Process Functions**
    - **isPIDValid** (pid):
        - Returns ``True`` if there is a running process associated with the PID, ``False`` otherwise
    - **killProcess** (pid):
        - Tries to terminate the process associated with the specified PID.
    - **getProcessName** (pid):
        - Returns the module path (executable name) for the process associated with the specified PID.


### Supported Key Codes ###

- **Modifiers**
    - ``+``: SHIFT
    - ``^``: CTRL
    - ``%``: ALT
    - ``@``: META/WIN/CMD
- **Special Keys**
    - ``{BACKSPACE}``
    - ``{TAB}``
    - ``{CLEAR}``
    - ``{ENTER}``
    - ``{SHIFT}``
    - ``{CTRL}``
    - ``{ALT}``
    - ``{PAUSE}``
    - ``{CAPS_LOCK}``
    - ``{ESCAPE}``
    - ``{SPACE}``
    - ``{PAGE_UP}``
    - ``{PAGE_DOWN}``
    - ``{END}``
    - ``{HOME}``
    - ``{LEFT}``
    - ``{UP}``
    - ``{RIGHT}``
    - ``{DOWN}``
    - ``{SELECT}``
    - ``{PRINT}``
    - ``{PRINT_SCREEN}``
    - ``{INSERT}``
    - ``{DELETE}``
    - ``{WIN}``
    - ``{NUM_0}``
    - ``{NUM_1}``
    - ``{NUM_2}``
    - ``{NUM_3}``
    - ``{NUM_4}``
    - ``{NUM_5}``
    - ``{NUM_6}``
    - ``{NUM_7}``
    - ``{NUM_8}``
    - ``{NUM_9}``
    - ``{F1}``
    - ``{F2}``
    - ``{F3}``
    - ``{F4}``
    - ``{F5}``
    - ``{F6}``
    - ``{F7}``
    - ``{F8}``
    - ``{F9}``
    - ``{F10}``
    - ``{F11}``
    - ``{F12}``
    - ``{F13}``
    - ``{F14}``
    - ``{F15}``
    - ``{F16}``
    - ``{NUM_LOCK}``
    - ``{SCROLL_LOCK}``
    - ``{[}``
    - ``{]}``
    - ``{+}``
    - ``{@}``
    - ``{^}``
    - ``{%}``
    - ``{~}``
    - ``{(}``
    - ``{)}``
    - ``{{}``
    - ``{}}``