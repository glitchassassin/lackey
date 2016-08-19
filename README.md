# Lackey v0.2.0a1 #
## A Graphical Python Automation Suite ##
[![Documentation Status](https://readthedocs.org/projects/lackey/badge/?version=latest)](http://lackey.readthedocs.io/en/latest/?badge=latest)

Developed by [Jon Winsley](https://github.com/glitchassassin)

## Third Party Library Requirements ##

* numpy
* pillow
* opencv (included)

## Introduction ##

Lackey is an automation library for Python, designed for ease of use and cross-compatibility with Sikuli automation scripts. It provides a simple but powerful API for finding images on screen and performing basic user input with the mouse & keyboard.

## Usage ##

### Installation ##

Installation is easy:

    pip install Lackey

To use the Sikuli shim, you'll want to download `sikuli.py` from this repo and place it in your Sikuli project directory. Then just add the following line to the top of your Sikuli script:

    from sikuli import *

That will interface any global Sikuli functionality (like `find()` or `click()`) to the appropriate method of the screen region. For more information, see the **Sikuli Patching** section below.

### General ###

The Lackey library is divided up into classes for finding and interacting with particular regions of the screen. Patterns are provided as bitmap files (supported formats include `.bmp`, `.pbm`, `.ras`, `.jpg`, `.tiff`, and `.png`). These patterns are compared to a Region of the screen, and, if they exist, can target a mouse move/click action.

If you've used Sikuli, you'll feel right at home. Comprehensive documentation is forthcoming in the not-too-distant future.

Sample code:

    import lackey

    r = Screen().to_region()
    r.click("Start_Button.png")
    r.wait("Control_Panel.png", 5) # Maybe the Start menu is slow
    r.click("Notepad.png")

## Documentation ##

Full API documentation can be found at [ReadTheDocs](http://lackey.readthedocs.io/en/latest/).

## Rationale ##

In my line of work, I have a lot of tasks walking through line-of-business applications to do boring things that any computer could do. Laziness being the mother of invention, I decided to script what I could. I found [SikuliX](http://sikulix.com/) to be a tremendously valuable tool for the job, but its Java dependencies and limited Python coupling posed problems in several cases. So, I decided to implement my own graphical automation library in pure Python.

There are some existing libraries for this purpose, like `pywinauto` and `autopy`, but they didn't work for me for one reason or another. I wasn't doing a lot of Windows GUI interaction with these particular applications, so `pywinauto`'s approach wouldn't help. I needed something that could search for and use images on screen. `autopy` was closer, but it had quite a few outstanding issues, hadn't been updated in a while, and didn't work nearly as well as SikuliX, which I was used to.

Most of my automation is in Windows, so I've begun this library with only Windows support. However, it's designed to eventually be extended with support for Mac OS X and Linux simply by implementing additional "PlatformManager" classes. I'll get around to these at some point, but if you'd like to contribute one sooner, please feel free!

### Sikuli Patching ###

Part of my goal with this project is to be able to easily reuse my existing library of Sikuli scripts. To that end, I've included a patch script, `sikuli.py`, to map certain functions of the screen region (`find()`, `click()`) to the global scope. This means you can use the Sikuli IDE for development, and run the final product with pure Python! Copy `sikuli.py` to your Sikuli project directory, add the following line to your Sikuli python script, and you should be able to run it in Python largely without issue:

    from sikuli import *

Note that I *have* had to adjust some of my image search similarity settings in a couple cases. Your mileage may vary. Please report any issues that you encounter and I'll try to get them patched.

## Structure ##

Each platform (Windows/OSX/Linux) needs its own PlatformManager (see documentation above) to abstract OS-level functionality, like simulating mouse clicks or key presses. Ideally, these should be implemented with as few 3rd-party library dependencies as possible. If you'd like to contribute a PlatformManager for your OS, feel free to submit a pull request! 

Don't forget to update the unit tests and verify that they still run.

## Fair Warning ##

This library is currently under development, and is missing many features needed for full Sikuli compatibility (and plenty of bugs). Fork at your own risk!
