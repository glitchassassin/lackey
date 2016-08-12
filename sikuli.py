import time
from lackey import *
## Sikuli patching: Functions that map to the global Screen region

global_screen = Screen().toRegion()
find = global_screen.find
findAll = global_screen.findAll
wait = global_screen.wait
waitVanish = global_screen.waitVanish
exists = global_screen.exists
click = global_screen.click
rightClick = global_screen.rightClick
doubleClick = global_screen.doubleClick
hover = global_screen.hover
drag = global_screen.drag
dropAt = global_screen.dropAt
dragDrop = global_screen.dragDrop
type = global_screen.type
paste = global_screen.paste
mouseDown = global_screen.mouseDown
mouseUp = global_screen.mouseUp
mouseMove = global_screen.mouseMove
wheel = global_screen.wheel
keyDown = global_screen.keyDown
keyUp = global_screen.keyUp
debugPreview = global_screen.debugPreview
sleep = time.sleep