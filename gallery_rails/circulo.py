import cadquery as cq
dowels = cq.Workplane("front").circle(10).extrude(4)
show_object(dowels)