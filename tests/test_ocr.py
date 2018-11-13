import lackey
r = lackey.Screen(1)
r.highlight()
print(r.text())
r.findText("IBUPROFEN SUSPENSION").highlight()
print(r.existsText("CHEESE"))
var = [print(m) for m in r.findAllText("IBUPROFEN")]