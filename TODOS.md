# Todos #

## Cleanup ##

*Standardize formatting*
[ ] Refactor names as `UpperCamelCase` for class names, `CAPITALIZED_WITH_UNDERSCORES` for constants, and `lowercase_separated_by_underscores` for other names. 
[ ] Designate "private" properties with underscore ("_").

## Document ##

*Code*
[ ] Add/clean up docstrings for all classes/functions

*Reference*
[ ] Define PlatformManager API interface

## Implement ##

* Region
	[ ] highlight()
	[ ] text() (OCR functionality)
	[ ] Low-level mouse/keyboard functions (should map to PlatformManager)
	[ ] selectRegion()
* Screen
	[ ] Implement multi-monitor support
* App
	[ ] focus(): Cleanup translation of Sikuli wildcards into regex