import cadquery as cq

length = 40
width = 3
holediam = 1
points = list(range(0, 2 * length, 8))
pts = [(0, x - length + holediam) for x in points]

x = (
    cq.Workplane("ZX")
    .box(2, width, length)
    .faces(">Z")
    .workplane()
    .pushPoints(pts)
    .cskHole(0.5, 1, 82, None)
)
