import lackey
r = lackey.Region(10, 10, 100, 100)
assert r.x == 10
assert r.y == 10
assert r.getRow(1, 4).y > 10
assert r.getCol(1, 4).x > 10
