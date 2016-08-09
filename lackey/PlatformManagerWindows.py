import ctypes

class PlatformManagerWindows(object):
	""" Abstracts Windows-specific OS-level features like mouse/keyboard control """
	def __init__(self):
		user32 = ctypes.WinDLL('user32', use_last_error=True)
		self._user32 = user32
		self._INPUT_MOUSE    = 0
		self._INPUT_KEYBOARD = 1
		self._INPUT_HARDWARE = 2
		self._KEYEVENTF_EXTENDEDKEY = 0x0001
		self._KEYEVENTF_KEYUP       = 0x0002
		self._KEYEVENTF_UNICODE     = 0x0004
		self._KEYEVENTF_SCANCODE    = 0x0008
		KEYEVENTF_EXTENDEDKEY = 0x0001
		KEYEVENTF_KEYUP       = 0x0002
		KEYEVENTF_UNICODE     = 0x0004
		KEYEVENTF_SCANCODE    = 0x0008
		MAPVK_VK_TO_VSC = 0
		# C struct definitions
		
		class MOUSEINPUT(ctypes.Structure):
			_fields_ = (("dx",          ctypes.wintypes.LONG),
						("dy",          ctypes.wintypes.LONG),
						("mouseData",   ctypes.wintypes.DWORD),
						("dwFlags",     ctypes.wintypes.DWORD),
						("time",        ctypes.wintypes.DWORD),
						("dwExtraInfo", ctypes.wintypes.WPARAM))
		self._MOUSEINPUT = MOUSEINPUT

		class KEYBDINPUT(ctypes.Structure):
			_fields_ = (("wVk",         ctypes.wintypes.WORD),
						("wScan",       ctypes.wintypes.WORD),
						("dwFlags",     ctypes.wintypes.DWORD),
						("time",        ctypes.wintypes.DWORD),
						("dwExtraInfo", ctypes.wintypes.WPARAM))
			def __init__(self, *args, **kwds):
				super(KEYBDINPUT, self).__init__(*args, **kwds)
				# some programs use the scan code even if KEYEVENTF_SCANCODE
				# isn't set in dwFflags, so attempt to map the correct code.
				if not self.dwFlags & KEYEVENTF_UNICODE:
					self.wScan = user32.MapVirtualKeyExW(self.wVk, MAPVK_VK_TO_VSC, 0)
		self._KEYBDINPUT = KEYBDINPUT

		class HARDWAREINPUT(ctypes.Structure):
			_fields_ = (("uMsg",    ctypes.wintypes.DWORD),
						("wParamL", ctypes.wintypes.WORD),
						("wParamH", ctypes.wintypes.WORD))
		self._HARDWAREINPUT = HARDWAREINPUT

		class INPUT(ctypes.Structure):
			class _INPUT(ctypes.Union):
				_fields_ = (("ki", KEYBDINPUT),
							("mi", MOUSEINPUT),
							("hi", HARDWAREINPUT))
			_anonymous_ = ("_input",)
			_fields_ = (("type",   ctypes.wintypes.DWORD),
						("_input", _INPUT))
		self._INPUT = INPUT

		LPINPUT = ctypes.POINTER(INPUT)
		user32.SendInput.errcheck = self._check_count
		user32.SendInput.argtypes = (ctypes.wintypes.UINT, # nInputs
										  LPINPUT,       # pInputs
										  ctypes.c_int)  # cbSize

	def _check_count(self, result, func, args):
		if result == 0:
			raise ctypes.WinError(ctypes.get_last_error())
		return args

	## Keyboard input methods ##

	def PressKey(self, hexKeyCode):
		""" Set key state to down """
		x = self._INPUT(type=self._INPUT_KEYBOARD, ki=self._KEYBDINPUT(wVk=hexKeyCode))
		self._user32.SendInput(1, ctypes.byref(x), ctypes.sizeof(x))
	def ReleaseKey(self, hexKeyCode):
		""" Set key state to up """
		x = self._INPUT(type=self._INPUT_KEYBOARD, ki=self._KEYBDINPUT(wVk=hexKeyCode, dwFlags=self._KEYEVENTF_KEYUP))
		self._user32.SendInput(1, ctypes.byref(x), ctypes.sizeof(x))
	def TypeKeys(self, text):
		""" Translates a string (with modifiers) into a series of keystrokes.

		Equivalent to Microsoft's SendKeys, with the addition of "@" as a Win-key modifier.
		Avoids some issues SendKeys had with applications like Citrix.
		"""
		special_keycodes = {
			"BACKSPACE": 	0x08,
			"TAB": 			0x09,
			"CLEAR": 		0x0c,
			"ENTER": 		0x0d,
			"SHIFT": 		0x10,
			"CTRL": 		0x11,
			"ALT": 			0x12,
			"PAUSE": 		0x13,
			"CAPS_LOCK": 	0x14,
			"ESCAPE": 		0x1b,
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
		uppercase_special_keycodes = {
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
		modifier_keycodes = {
			"+":			0x10,
			"^":			0x11,
			"%":			0x12,
			"~":			0x0d,
			"@":			0x5b
		}
		regular_keycodes = {
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
		uppercase_keycodes = {
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
				if special_code in special_keycodes.keys():
					self.PressKey(special_keycodes[special_code])
					self.ReleaseKey(special_keycodes[special_code])
				elif special_code in uppercase_special_keycodes.keys():
					self.PressKey(special_keycodes["SHIFT"])
					self.PressKey(special_keycodes[special_code])
					self.ReleaseKey(special_keycodes[special_code])
					self.ReleaseKey(special_keycodes["SHIFT"])
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
					self.ReleaseKey(x)
				modifier_codes = []
				continue
			elif text[i] in modifier_keycodes.keys():
				modifier_codes.append(modifier_keycodes[text[i]])
				self.PressKey(modifier_keycodes[text[i]])
				modifier_held = True
			elif text[i] in regular_keycodes.keys():
				self.PressKey(regular_keycodes[text[i]])
				self.ReleaseKey(regular_keycodes[text[i]])
				if modifier_held:
					for x in modifier_codes:
						self.ReleaseKey(x)
			elif text[i] in uppercase_keycodes.keys():
				self.PressKey(special_keycodes["SHIFT"])
				self.PressKey(uppercase_keycodes[text[i]])
				self.ReleaseKey(uppercase_keycodes[text[i]])
				self.ReleaseKey(special_keycodes["SHIFT"])
				if modifier_held:
					for x in modifier_codes:
						self.ReleaseKey(x)
		pass

	## Mouse input methods

	def SetMousePos(self, location):
		""" Accepts a tuple (x,y) and sets the mouse position accordingly """
		x, y = location
		self._user32.SetCursorPos(x, y)
	def GetMousePos(self):
		""" Returns the current mouse position as a tuple (x,y) """
		class POINT(ctypes.Structure):
			_fields_ = [("x", ctypes.c_ulong), ("y", ctypes.c_ulong)]
		pt = POINT()
		self._user32.GetCursorPos(ctypes.byref(pt))
		return (pt.x, pt.y)
	def MouseButtonDown(self, button=0):
		""" Translates the button (0=LEFT, 1=MIDDLE, 2=RIGHT) and sends a mousedown to the OS """
		click_down_code = [0x0002, 0x0020, 0x0008][button]
		x = self._INPUT(type=self._INPUT_MOUSE, mi=self._MOUSEINPUT(dwFlags=click_down_code))
		self._user32.SendInput(1, ctypes.byref(x), ctypes.sizeof(x))
	def MouseButtonUp(self, button=0):
		""" Translates the button (0=LEFT, 1=MIDDLE, 2=RIGHT) and sends a mouseup to the OS """
		click_up_code = [0x0004, 0x0040, 0x0010][button]
		x = self._INPUT(type=self._INPUT_MOUSE, mi=self._MOUSEINPUT(dwFlags=click_up_code))
		self._user32.SendInput(1, ctypes.byref(x), ctypes.sizeof(x))
	def ClickMouse(self, button=0):
		""" Abstracts the clicking function """
		# LEFT = 0
		# MIDDLE = 1
		# RIGHT = 2
		self.MouseButtonDown(button)
		self.MouseButtonUp(button)

	## Screen functions

	def GetScreenSize(self):
		""" Returns the screen size of the main monitor. To be updated for multiple monitors. """
		return (self._user32.GetSystemMetrics(0), self._user32.GetSystemMetrics(1))


	## Clipboard functions

	def GetClipboard(self):
		""" Fetches any text on the clipboard. """
		to_return = ""
		CF_TEXT = 1
		self._user32.OpenClipboard(0)
		if self._user32.IsClipboardFormatAvailable(CF_TEXT):
			clipboard = self._user32.GetClipboardData(CF_TEXT)
			data_locked = ctypes.windll.kernel32.GlobalLock(clipboard)
			text = ctypes.c_char_p(data_locked)
			to_return = text.value
			ctypes.windll.kernel32.GlobalUnlock(data_locked)
		self._user32.CloseClipboard()
		return to_return

	def SetClipboard(self, text):
		""" Sets the clipboard to the contents of "text" """
		if not isinstance(text, basestring):
			raise TypeError("SetClipboard expected text to be a string")
		GMEM_DDESHARE = 0x2000
		CF_TEXT = 1
		self._user32.OpenClipboard(0)
		self._user32.EmptyClipboard()
		# Set up a memory space for the copied data
		clipdata_handle = ctypes.windll.kernel32.GlobalAlloc(GMEM_DDESHARE, len(bytes(text, "ascii"))+1)
		clipdata_data = ctypes.windll.kernel32.GlobalLock(clipdata_handle)
		ctypes.cdll.msvcrt.wcscpy(ctypes.c_wchar_p(clipdata_data), text)
		ctypes.windll.kernel32.GlobalUnlock(clipdata_handle)
		# Assign the pointer to the clipboard
		self._user32.SetClipboardData(CF_TEXT, clipdata_handle)
		self._user32.CloseClipboard()

	## Window functions

	def GetWindowByTitle(self, wildcard):
		""" Returns a platform-specific handle for the first window that matches the provided "wildcard" regex """
		data = {
			"handle": None,
			"wildcard": wildcard
		}
		self._user32.EnumWindows(self._window_enum_wildcard_callback, data)
		return data["handle"]

	def _window_enum_wildcard_callback(self, hwnd, wildcard):
		if re.match(data["wildcard"], str(self._user32.GetWindowText(hwnd))) != None:
			data["handle"] = hwnd

	def GetWindowRect(self, hwnd):
		""" Returns a rect (x1,y1,x2,y2) for the specified window's area """
		return self._user32.GetWindowRect(hwnd)

	def FocusWindow(self, hwnd):
		""" Brings specified window to the front """
		self._user32.SetForegroundWindow(hwnd)

	def GetWindowTitle(self, hwnd):
		""" Self explanatory """
		return self._user32.GetWindowText(hwnd)

	def GetWindowPID(self, hwnd):
		""" Gets the process ID that the specified window belongs to """
		return self._user32.GetWindowThreadProcessId(hwnd)