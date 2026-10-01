#!/usr/bin/env python3
"""Generate a continuous blade-slit holder for Japanese (Type A) plugs, in two parts.

JIS C 8303 blades are ~6.8 x 1.2 mm at 12.7 mm pitch, ~12 mm long, so plugs
stand on their blades in two parallel long 2.2 mm slits (12.7 mm apart, one
per blade) and can be placed anywhere along them, whatever their body size. The base is 205 mm long (fits a 210 mm case) and
is split in the middle for the A1 mini bed; the parts are aligned by
pins/holes (glue them).
"""

from __future__ import annotations

from pathlib import Path

import trimesh
from shapely.geometry import box

ROOT = Path(__file__).resolve().parent.parent
OUT_A = ROOT / "models" / "plug_holder_a.stl"
OUT_B = ROOT / "models" / "plug_holder_b.stl"

LENGTH = 205.0
WIDTH = 45.0
HEIGHT = 22.0
SLOT_THICK = 2.2  # along Y: blade thickness 1.2 + play
SLOT_DEPTH = 14.0  # blade length ~12 mm
SLOT_END_WALL = 8.0
SLIT_PITCH = 12.7  # blade pitch (Y distance between the two slits)
SPLIT_X = LENGTH / 2
PIN_D = 4.5
PIN_LEN = 6.0
PIN_CLEARANCE = 0.2
PIN_Y = (WIDTH * 0.25, WIDTH * 0.75)
PIN_Z = 4.0


def extrude(poly, z0, z1):
    mesh = trimesh.creation.extrude_polygon(poly, z1 - z0)
    mesh.apply_translation([0, 0, z0])
    return mesh


def cube(x0, y0, z0, x1, y1, z1):
    m = trimesh.creation.box(extents=[x1 - x0, y1 - y0, z1 - z0])
    m.apply_translation([(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2])
    return m


def pin(y, length, diameter, x0):
    cyl = trimesh.creation.cylinder(radius=diameter / 2, height=length, sections=32)
    cyl.apply_transform(
        trimesh.transformations.rotation_matrix(3.141592653589793 / 2, [0, 1, 0])
    )
    cyl.apply_translation([x0 + length / 2, y, PIN_Z])
    return cyl


def build():
    outline = box(0, 0, LENGTH, WIDTH).buffer(-3).buffer(3, 24)
    body = extrude(outline, 0, HEIGHT)
    slits = []
    for dy in (-SLIT_PITCH / 2, SLIT_PITCH / 2):
        yc = WIDTH / 2 + dy
        slit = box(
            SLOT_END_WALL, yc - SLOT_THICK / 2,
            LENGTH - SLOT_END_WALL, yc + SLOT_THICK / 2,
        )
        slits.append(extrude(slit, HEIGHT - SLOT_DEPTH, HEIGHT + 1))
    body = body.difference(slits, engine="manifold")

    half_a = body.intersection(
        cube(-1, -1, -1, SPLIT_X, WIDTH + 1, HEIGHT + 1), engine="manifold"
    )
    half_b = body.intersection(
        cube(SPLIT_X, -1, -1, LENGTH + 1, WIDTH + 1, HEIGHT + 1), engine="manifold"
    )
    pins = [pin(y, PIN_LEN, PIN_D, SPLIT_X) for y in PIN_Y]
    holes = [
        pin(y, PIN_LEN + 0.4, PIN_D + 2 * PIN_CLEARANCE, SPLIT_X) for y in PIN_Y
    ]
    half_a = half_a.union(pins, engine="manifold")
    half_b = half_b.difference(holes, engine="manifold")
    return half_a, half_b


def main():
    for mesh, out in zip(build(), (OUT_A, OUT_B)):
        mesh.export(out)
        print(f"{out.name}: watertight={mesh.is_watertight} extents={mesh.extents.round(2)}")


if __name__ == "__main__":
    main()
