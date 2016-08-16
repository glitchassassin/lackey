sikuli shim
=============

The Sikuli shim makes it easy to port Sikuli Jython scripts to run in pure Python with Lackey. Just copy the `sikuli.py` shim to your Sikuli project folder and import the shim::

	from sikuli import * 

The shim will patch Sikuli's global screen functions (`find()`, `click()`, etc.) to the corresponding functions of the Lackey screen region.