import time
from lackey import *
## Sikuli patching: Functions that map to the global Screen region

SCREEN = Screen(0)
find = SCREEN.find
findAll = SCREEN.findAll
wait = SCREEN.wait
waitVanish = SCREEN.waitVanish
exists = SCREEN.exists
click = SCREEN.click
rightClick = SCREEN.rightClick
doubleClick = SCREEN.doubleClick
hover = SCREEN.hover
drag = SCREEN.drag
dropAt = SCREEN.dropAt
dragDrop = SCREEN.dragDrop
type = SCREEN.type
paste = SCREEN.paste
mouseDown = SCREEN.mouseDown
mouseUp = SCREEN.mouseUp
mouseMove = SCREEN.mouseMove
wheel = SCREEN.wheel
keyDown = SCREEN.keyDown
keyUp = SCREEN.keyUp
debugPreview = SCREEN.debugPreview
sleep = time.sleep