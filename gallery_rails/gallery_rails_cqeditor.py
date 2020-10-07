#!/usr/bin/env python
"""
Gallery Rails

- Author: @westurner
"""
import math
from fractions import Fraction

import cadquery as cq

if "log" not in globals():
    import logging

    LOG = logging.getLogger()
    LOG.setLevel(logging.DEBUG)

    def log(*args):
        """log the arguments"""
        LOG.debug(*args)


if "show_object" not in globals():
    if "display" in globals():
        from IPython.display import display

        def show_object(*args, **kwargs):
            """show the object with IPython"""
            display(*args, kwargs)

    else:

        def show_object(*args, **kwargs):
            """log the object"""
            log(("show_object", args, kwargs))


objects = {}


def get_parameters():
    data = {}
    room = data["room"] = {}
    wall = room["wall"] = {}

    wall["height"] = 96
    wall["width"] = (17 * 12) + 1.5
    wall["angle_height_off_floor"] = 53
    wall["angle_height"] = wall["height"] - wall["angle_height_off_floor"]
    wall["angle_width"] = 54
    wall["angle_angle"] = math.atan(
        Fraction(wall["angle_height"], wall["angle_width"])
    )  # tangent = opposite/adjacent
    wall["angle_angle_degrees"] = math.degrees(wall["angle_angle"])
    wall["studs"] = [21, 30, 54, 70, 86, 95, 101, 113, 132, 145, 165, 180, 186]
    wall["baseboard_height"] = 3 + Fraction(3, 8)
    wall["baseboard_depth"] = Fraction(1, 4)  # TODO
    wall["vent_height"] = 20
    wall["vent_from_left_wall"] = 39
    wall["vent_from_left_wall_to_outside_edge"] = 55
    wall["vent_width"] = (
        wall["vent_from_left_wall_to_outside_edge"]
        - wall["vent_from_left_wall"]
    )
    wall["vent_depth"] = Fraction(1, 4)  # TODO
    # TOOD: electrical_output
    wall["depth"] = 1
    wall["color"] = (174, 163, 147)
    wall["stud_depth"] = 3.5
    wall["stud_width"] = 1.5
    wall["stud_color"] = wall["color"]
    # wall['stud_color'] = (80, 80, 80)
    wall["vent_color"] = (234, 234, 234)
    wall["baseboard_color"] = (234, 234, 234)

    rail_params = data["rail_params"] = {}
    rail_params["rail_lengths"] = [
        # Fraction(163), 136 + Fraction("1/4"), 117 + Fraction(5 / 8) # Current
        Fraction(163),
        Fraction(117, 1),
        Fraction(80, 1),  # Eyeballed
        # Fraction(163), Fraction(98,1), Fraction(36,1) # ~38deg==ceiling angle
    ]
    rail_params["depth"] = 2  # TODO
    rail_params["tie_offset"] = 4
    rail_params["tie_spacing"] = 8
    rail_params["tie_hole_diameter"] = Fraction(1, 8)  # TODO
    rail_params["tie_hole_cskDiameter"] = 2 * rail_params["tie_hole_diameter"]
    rail_params["tie_hole_cskAngle"] = 82
    rail_params.setdefault(0, {})["stud_numbers"] = [1, 6, 10]
    rail_params.setdefault(1, {})["stud_numbers"] = [2, 6, 9]
    rail_params.setdefault(2, {})["stud_numbers"] = [3, 6, 8]
    rail_params["color"] = (234, 234, 234)

    dowels = data["dowels"] = {}
    dowels["diameter"] = 1 + Fraction(5, 8)  # TODO
    dowels["length_per_rod"] = 48  # TODO
    dowels["cut_length"] = 3.5  # TODO
    dowels["color"] = (255, 227, 155)

    return data


data = get_parameters()


# Draw the wall, studs, vent, and baseboard


def draw_wall(wall):

    # generate the points of the ceiling [tri]angles
    pts_zx = [
        ((wall["angle_height_off_floor"]), 0, (wall["depth"] / 2)),
        (
            (wall["angle_height_off_floor"]),
            -1 * wall["angle_width"],
            (wall["depth"] / 2),
        ),
        (0, (-1 * wall["angle_width"]), (wall["depth"] / 2)),
        ((wall["angle_height_off_floor"]), 0, (wall["depth"] / 2)),
    ]

    pts_zx_transformed = [
        (a, b + (-1 * wall["width"] / 2) + wall["angle_width"], c)
        for (a, b, c) in pts_zx
    ]

    pts_zx_transformed_otherside = [
        (a, -1 * (b + (-1 * wall["width"] / 2) + wall["angle_width"]), c)
        for (a, b, c) in pts_zx
    ]

    wall_object = (
        cq.Workplane("ZX")
        .box(wall["height"], wall["width"], wall["depth"])
        .polyline(pts_zx_transformed)
        .close()
        .cutThruAll()
        .polyline(pts_zx_transformed_otherside)
        .close()
        .cutThruAll()
        .translate(
            (
                -1 * wall["width"] / 2,
                -1 * wall["depth"] / 2,
                wall["height"] / 2,
            )
        )
    )
    show_object(wall_object, options=dict(color=wall["color"]))
    return wall_object


objects["wall"] = draw_wall(data["room"]["wall"])


def draw_vent(wall):
    vent = (
        cq.Workplane("ZX")
        .box(wall["vent_height"], wall["vent_width"], wall["vent_depth"])
        .translate(
            (
                -1 * (wall["vent_width"] / 2 + wall["vent_from_left_wall"]),
                wall["vent_depth"],
                wall["vent_height"] / 2 + wall["baseboard_height"],  # TODO
            )
        )
    )
    show_object(vent, options=dict(color=wall["vent_color"]))
    return vent


objects["vent"] = draw_vent(data["room"]["wall"])


def draw_baseboard(wall):
    baseboard = (
        cq.Workplane("ZX")
        .box(wall["baseboard_height"], wall["width"], wall["baseboard_depth"])
        .translate(
            (
                -1 * wall["width"] / 2,
                wall["baseboard_depth"],
                wall["baseboard_height"] / 2,
            )
        )
    )
    show_object(baseboard, options=dict(color=wall["baseboard_color"]))
    return baseboard


objects["baseboard"] = draw_baseboard(data["room"]["wall"])


def draw_studs(wall):
    workplane = cq.Workplane("ZX")

    studs = []
    for stud_n, stud_offset_from_wall in enumerate(wall["studs"]):
        # log(stud_offset_from_wall)
        stud_height = (
            wall["height"]
            if stud_n not in {0, 1, 10, 11, 12}
            else wall["height"] / 1.6
        )
        stud = (
            workplane.box(stud_height, wall["stud_width"], wall["stud_depth"])
            # TODO: .cutThruAll like wall .cutThruAll
            .translate(
                (
                    (-1 * wall["stud_width"] / 2)
                    + (-1 * stud_offset_from_wall)
                    + 0,
                    -1 * wall["stud_depth"] / 2,
                    stud_height / 2,
                )
            )
        )
        studs.append(stud)
        show_object(
            stud,
            options=dict(color=wall["stud_color"])
            # options={'color': (100+10*stud_n, 0, 0)})
        )
    return studs


objects["studs"] = draw_studs(data["room"]["wall"])


# Draw the dowels and rails


def calculate_rails_parameters(wall, rail_params):
    rails = {}
    starting_height = wall["vent_height"] + 8
    for i, length in enumerate(rail_params["rail_lengths"]):
        rail = {}
        rail["length"] = length
        rail["height"] = Fraction(1, 4)  # TODO
        rail["depth"] = rail_params["depth"]  # TODO
        rail["tie_offset"] = rail_params["tie_offset"]
        rail["tie_spacing"] = rail_params["tie_spacing"]
        rail["tie_count"], rail["tie_remainder"] = divmod(
            rail["length"] - (2 * rail["tie_offset"]), rail["tie_spacing"]
        )
        rail["color"] = rail_params["color"]
        initial_offset = rail["tie_offset"] - (
            rail_params["tie_hole_cskDiameter"] / 2
        )
        if initial_offset < 0:
            raise ValueError(f"initial_offset is < 0: {initial_offset}")
        rail["tie_initial_offset"] = initial_offset  # TODO: better name
        rail["tie_holes"] = [
            (initial_offset + (rail["tie_spacing"] * n))
            for n in range(rail["tie_count"] + 1)
        ]

        rail["height_off_floor"] = starting_height + (26 * i)
        rail["stud_numbers"] = rail_params[i]["stud_numbers"]
        rails[i] = rail
    return rails


data["rails"] = calculate_rails_parameters(
    data["room"]["wall"], data["rail_params"]
)


def draw_dowels(rails, dowels, studs):
    dowel_objects = []
    do = cq.Workplane("ZX")
    for railname, rail in rails.items():
        rail["_dowel_centers"] = []
        for stud_n in rail["stud_numbers"]:
            stud = studs[stud_n]
            studcenter = stud.val().Center().x
            rail["_dowel_centers"].append(studcenter)
            _dowel = (
                do.circle(dowels["diameter"] / 2)
                .extrude(dowels["cut_length"])
                .translate(
                    (
                        studcenter,
                        0,  # dowels['cut_length'],
                        rail["height_off_floor"] - dowels["diameter"] / 2,
                    )
                )
                # .faces('>Z').fillet(0.25)  # TODO: uncomment
            )
            dowel_objects.append(_dowel)
            show_object(_dowel, options=dict(color=dowels["color"]))
    return dowel_objects


objects["dowels"] = draw_dowels(
    data["rails"], data["dowels"], objects["studs"]
)


def calculate_dowel_distances(studs, stud_numbers=[1, 2, 3]):
    xvals = []
    for i, n in enumerate(stud_numbers):
        xvals.append(studs[n].val().Center().x)
        log((f"dowel{n}.x", xvals[i]))
    log(("dowel_distances", (xvals[1] - xvals[0], xvals[2] - xvals[1])))


def log_dowel_distances(rails, studs):
    for n, rail in rails.items():
        log((f"rail{n}"))
        calculate_dowel_distances(studs, rail["stud_numbers"])


log_dowel_distances(data["rails"], objects["studs"])

# Draw the rails


def draw_rails_hidden(wall, rails, rail_params):
    rails_plane = cq.Workplane("ZX")
    rails_objects = []
    for railname, rail in rails.items():
        holes = [
            (
                -1
                * (
                    y
                    - rail["length"] / 2
                    + rail_params["tie_hole_cskDiameter"]
                ),
                0,
            )
            for y in rail["tie_holes"]
        ]
        log(("holes", railname, holes))
        log(("rail", rail))
        _rail = (
            rails_plane.box(rail["height"], rail["length"], rail["depth"])
            # .faces("+Z").edges().fillet(0.125)  # TODO: uncomment
            .faces(">Z")
            .workplane()
            .pushPoints(holes)
            .cskHole(
                rail_params["tie_hole_diameter"],
                rail_params["tie_hole_cskDiameter"],
                rail_params["tie_hole_cskAngle"],
            )
            .translate(
                (
                    (
                        (-1 * rail["length"] / 2)
                        + (-1 * ((wall["width"] - rail["length"]) / 2))
                    ),
                    -1 * (wall["depth"] + wall["stud_depth"]),
                    rail["height_off_floor"] + rail["height"] / 2,
                )
            )
        )
        show_object(_rail, options=dict(color=rail["color"]))
        rails_objects.append(_rail)
    return rails_objects


objects["rails_hidden"] = draw_rails_hidden(
    data["room"]["wall"], data["rails"], data["rail_params"]
)


def recalculate_rail_tie_holes(rails, rail_params, rail_objects):
    for (railname, rail), railobj in zip(rails.items(), rail_objects):
        rail["_dowel_centers"]
        rail["length"]
        bb = railobj.val().BoundingBox()
        rail["_xmin"] = bb.xmin
        rail["_xmax"] = bb.xmax
        # TODO: note: these are reversed
        segment_points = [rail["_xmax"]]
        segment_points.extend(rail["_dowel_centers"])
        segment_points.append(rail["_xmin"])
        segments = [
            (x, y) for (x, y) in zip(segment_points, segment_points[1:])
        ]
        log((f"segments: {railname}", segments))
        holes = []
        n_segments = len(segments)
        tie_spacing = rail_params["tie_spacing"]
        hole_radius = rail_params["tie_hole_cskDiameter"] / 2
        for i, (start, end) in enumerate(segments):
            log((("i, start, end", (i, start, end))))
            length = end - start
            if i in {0, n_segments - 1}:
                n_holes, remainder = divmod(length, tie_spacing)
                log(("nholes, remainder", n_holes, remainder))
                tie_spacing = 4   # TODO: read from params
                offset = 1  # TODO: read from params
                points = [
                    start
                    + (remainder / 2)
                    + offset
                    + (tie_spacing * n)
                    + hole_radius
                    - rail["_xmax"]
                    for n in range(0, abs(int(n_holes)) + 1)
                ]
            else:
                n_holes, remainder = divmod(length, tie_spacing)
                log(("nholes, remainder", n_holes, remainder))
                points = [
                    start
                    + (remainder / 2)
                    + (tie_spacing * n)
                    + hole_radius
                    - rail["_xmax"]
                    for n in range(0, abs(int(n_holes)) + 1)
                ]
            holes.extend(points)
        rail["_tie_holes"] = holes


recalculate_rail_tie_holes(
    data["rails"], data["rail_params"], objects["rails_hidden"]
)


def draw_rails(wall, rails, rail_params, objects):
    rails_plane = cq.Workplane("ZX")
    rails_objects = []
    recalculate_rail_tie_holes(rails, rail_params, objects["rails_hidden"])

    for railname, rail in rails.items():
        log(("holes", railname, rail["_tie_holes"]))
        log(("rail", rail))
        _rail = (
            rails_plane.box(rail["height"], rail["length"], rail["depth"])
            # .faces("+Z").edges().fillet(0.125)  # TODO: uncomment
            .faces(">Z")
            .workplane()
            .pushPoints((-1 * x, 0) for x in rail["_tie_holes"])
            .cskHole(
                rail_params["tie_hole_diameter"],
                rail_params["tie_hole_cskDiameter"],
                rail_params["tie_hole_cskAngle"],
            )
            .translate(
                (
                    (
                        (-1 * rail["length"] / 2)
                        + (-1 * ((wall["width"] - rail["length"]) / 2))
                    ),
                    rail["depth"] + 0.5,
                    rail["height_off_floor"] + rail["height"] / 2,
                )
            )
        )
        show_object(_rail, options=dict(color=rail["color"]))
        rails_objects.append(_rail)
    return rails_objects


objects["rails"] = draw_rails(
    data["room"]["wall"], data["rails"], data["rail_params"], objects
)


# Calculate angles


def calculate_angles(wall, rails):
    log(("wall_angle", wall["angle_angle"], wall["angle_angle_degrees"]))

    rail_angles = dict()
    rails_to_calculate_angles_of = zip(
        list(rails.keys()), list(rails.keys())[1:]
    )
    rails_to_calculate_angles_of = list(rails_to_calculate_angles_of) + [
        (0, 2)
    ]
    for n1, n2 in rails_to_calculate_angles_of:
        length_difference = (rails[n1]["length"] - rails[n2]["length"]) / 2
        height_difference = (
            rails[n2]["height_off_floor"] - rails[n1]["height_off_floor"]
        )
        opposite = height_difference
        adjacent = length_difference
        # tangent = opposite / adjacent  # (sOH, cAH, tOA)
        tangent = math.atan(Fraction(opposite, adjacent))  # (sOH, cAH, tOA)
        angle = math.degrees(tangent)
        log(("angle", (n1, n2), tangent, angle))
        rail_angles[(n1, n2)] = (tangent, angle)
    # log(("average", ((rail_angles[(0, 1)][1] + rail_angles[(1, 2)][1]) / 2)))
    return rail_angles


data["rail_angles"] = calculate_angles(data["room"]["wall"], data["rails"])


# how long should rails 1 and 2 be in order to
# most closely match the roof angle, given the fixed length of rail 0?

# This is not correct (I should've just used a CAS like SymPy)
# height = rails[1]['height_off_floor']-rails[0]['height_off_floor']
# math.atan(height / (rails[0]['length']-x / 2)) = wall['angle_angle']
# math.atan(height / (lengthdiff / 2)) = wall['angle_angle]
# height / (lengthdiff / 2) = tan(wall['angle_angle'])
# height = tan(wall['angle_angle']) * (lengthdiff / 2)
# height / tan(tall['angle_angle']) = lengthdiff / 2
# 2*(height / tan(wall['angle_angle'])) = lengthdiff
# 2*(height / tan(wall['angle_angle'])) = x - rails[0]['length']
# 2*(height / tan(wall['angle_angle'])) + rails[0]['length'] = x
# 2*(height / math.tan(wall['angle_angle'])) + rails[0]['length'] = x
