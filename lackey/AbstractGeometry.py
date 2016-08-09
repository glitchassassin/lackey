import platform
from .PlatformManagerWindows import PlatformManagerWindows
#from .RegionMatching import Region

if platform.system() == "Windows":
	PlatformManager = PlatformManagerWindows() # No other input managers built yet
else:
	raise NotImplementedError("Pykuli v0.01 is currently only compatible with Windows.")
