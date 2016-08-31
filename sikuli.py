import os
import time
import requests
from zipfile import ZipFile
from lackey import *
## Sikuli patching: Functions that map to the global Screen region
## Don't try this at home, kids!

SCREEN = Screen(0)
for prop in dir(SCREEN):
	if callable(getattr(SCREEN, prop, None)) and prop[0] != "_":
		# Property is a method, and is not private. Dump it into the global namespace.
		globals()[prop] = getattr(SCREEN, prop, None)

## Sikuli Convenience Functions

def exit(value):
	sys.exit(value)

def setShowActions(value):
	Settings.ShowActions = bool(value)

def getBundlePath():
	return Settings.BundlePath
def getBundleFolder():
	return getBundlePath() + os.path.sep
def setBundlePath(path):
	if os.path.exists(path):
		Settings.BundlePath = path
	else:
		raise FileNotFoundError(path)
def getImagePath():
	return [getBundlePath()] + Settings.ImagePaths
def addImagePath(new_path):
	if os.path.exists(new_path):
		Settings.ImagePaths.append(new_path)
	elif "http://" in new_path or "https://" in new_path:
		request = requests.get(new_path)
		if request.status_code < 400:
			# Path exists
			Settings.ImagePaths.append(new_path)
		else:
			raise FileNotFoundError("Unable to connect to", new_path)
	else:
		raise FileNotFoundError(new_path)
def addHTTPImagePath(new_path):
	addImagePath(new_path)

def getParentPath():
	return os.path.dirname(Settings.BundlePath)
def getParentPath():
	return getParentPath() + os.path.sep
def makePath(*args):
	return os.path.join(*args)
def makeFolder(*args):
	return makePath(*args) + os.path.sep

## Sikuli implements the unzip() file, below. Included here to avoid breaking old
## scripts. ``zipfile()`` is coded, but not included in Sikuli, so I've
## commented it out for the time being. Note that ``zip`` is a reserved keyword
## in Python.

def unzip(fromFile, toFolder):
	with ZipFile(os.path.abspath(fromFile), 'r') as to_unzip:
		to_unzip.extractall(os.path.abspath(toFolder))
#def zipfile(fromFolder, toFile):
#	with ZipFile(toFile, 'w') as to_zip:
#		for root, dirs, files in os.walk(fromFolder):
#			for file in files:
#				to_zip.write(os.path.join(root, file))