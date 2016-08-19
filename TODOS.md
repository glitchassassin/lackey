# Todos #

## Cleanup ##

* *Standardize formatting*
	* [X] Refactor names as `UpperCamelCase` for class names, `CAPITALIZED_WITH_UNDERSCORES` for constants, `lowerCamelCase` for methods/properties, `lowercase_with_underscores` for internal variables (for consistency with Sikuli). 
	* [X] Designate "private" properties with underscore ("_").

## Document ##

* *Code*
	* [X] Add/clean up docstrings for all classes/functions

* *Reference*
	* [X] Define PlatformManager API interface

## Implement ##

* Overall
	* [ ] Verbosity levels for console logging
	* [ ] Event handling
* Region
	* [ ] highlight()
	* [ ] text() (OCR functionality)
	* [X] Low-level mouse/keyboard functions (should map to PlatformManager)
	* [X] Raster functions
	* [ ] selectRegion()
* Screen
	* [X] Implement multi-monitor support
* App
	* [ ] focus(): Cleanup translation of Sikuli wildcards into regex
