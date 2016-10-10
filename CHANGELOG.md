## Changelog ##

v0.4.0a1
* Merged Sikuli shim into Lackey main code

v0.3.1a1
* Implemented pyramid matcher to improve image search efficiency

v0.3.0a1
* Implemented the rest of the main Sikuli classes, including `App`, `Settings`, and `Debug`

v0.2.2a1
* Fixed #14 TypeError on doubleClick()

v0.2.1a1
* Fixed #5 bad region validation
* Fixed #7 findAll() listiterator error
* Fixed #9 _convert_sikuli_wildcards should be a class method
* Fixed #10 Region.below(), Region.right() getScreen error
* Fixed #11 clipRegionToScreen() errors
* Fixed #12 memory leak

v0.2.0a1
* Added multi-monitor support (Screen() class should be fully functional and Sikuli-compatible, except for interactive functions)
* Moved `capture()` method to `Screen` class instead of `Region` (where it had incorrectly been placed)
* Screen class now properly inherits Region
* Added lastMatch shortcut for click()
* Implemented raster functions for Region

v0.1.0a1
* Initial build with basic Sikuli support