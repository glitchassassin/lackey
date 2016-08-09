# Lackey v0.01 #
## A Graphical Python Automation Suite ##

Developed by [Jon Winsley](https://github.com/glitchassassin)

## Third Party Library Requirements ##

* numpy
* pillow
* opencv (included)

## Introduction ##

In my line of work, I have a lot of tasks walking through line-of-business applications to do boring things that any computer could do. Laziness being the mother of invention, I decided to script what I could. I found SikuliX to be a tremendously valuable tool for the job, but its Java dependencies and limited Python coupling posed problems in several cases. So, I decided to implement my own graphical automation library in pure Python.

There are some existing libraries for this purpose, like `pywinauto` and `autopy`, but they didn't work for me for one reason or another. I wasn't doing a lot of Windows GUI interaction with these particular applications, so `pywinauto`'s approach wouldn't help. I needed something that could search for and use images on screen. `autopy` was closer, but it had quite a few outstanding issues, hadn't been updated in a while, and didn't work nearly as well as SikuliX, which I was used to.

Most of my automation is in Windows, so I've begun this library with only Windows support. However, it's designed to eventually be extended with support for Mac OS X and Linux simply by implementing additional "PlatformManager" classes. I'll get around to these at some point, but if you'd like to contribute one sooner, please feel free!

## Usage ##

Part of my goal with this project is to be able to easily reuse my existing library of Sikuli scripts. To that end, I've included a patch script, `sikuli.py`, to map certain functions (`find(), click()`) to the global scope. This means you can use the Sikuli IDE for development, and run the final product with pure Python! Add the following line to your Sikuli python script and you should be able to run it largely without issue:

    from sikuli import *

Note that I *have* had to adjust some of my image search similarity settings in a couple cases. Your mileage may vary.

## Structure ##

Each platform (Windows/OSX/Linux) needs its own PlatformManager to abstract OS-level functionality, like simulating mouse clicks or key presses. Ideally, these should be implemented with as few 3rd-party library dependencies as possible. 