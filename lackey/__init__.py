import platform

## Lackey sub-files

from PlatformManagerWindows import PlatformManagerWindows
from KeyCodes import Button, Key, KeyModifier
from RegionMatching import Pattern, Region, Match, Screen, Location, Mouse, Keyboard, Window, App
from Exceptions import FindFailed

if platform.system() == "Windows":
	PlatformManager = PlatformManagerWindows() # No other input managers built yet
else:
	raise NotImplementedError("Pykuli v0.01 is currently only compatible with Windows.")