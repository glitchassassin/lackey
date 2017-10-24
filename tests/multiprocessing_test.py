import lackey
import time
import os

def test_observer(appear_event):
    lackey.popup("Found it! Background job successful")
    region = appear_event.getRegion()
    print(region._observer)
    region.TestFlag = True
    assert appear_event.isAppear()
    img = appear_event.getImage()
    region.stopObserver()

def main(): 
    lackey.addImagePath(os.path.dirname(__file__))

    r = lackey.Screen(0)
    r.doubleClick("notepad.png")
    time.sleep(2)
    r.type("This is a test")
    r.onAppear(lackey.Pattern("test_text.png").similar(0.6), test_observer)
    r.observeInBackground(30)
    time.sleep(7)
    r.rightClick(lackey.Pattern("test_text.png").similar(0.6))
    r.click("select_all.png")
    r.type("c", lackey.Key.CTRL) # Copy
    assert r.getClipboard() == "This is a test"
    r.type("{DELETE}")
    r.type("{F4}", lackey.Key.ALT)

if __name__ == "__main__":
    main()