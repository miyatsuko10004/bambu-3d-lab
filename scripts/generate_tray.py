#!/usr/bin/env python3
"""Generate a compact desk tray with pockets and lean-back holders.

Fits the Bambu A1 mini bed (180 mm). Item sizes are the user's measured values
and already include clearance, so no extra clearance is added here.

Layout (X to the right, Y toward the back), 147 x 160 mm:
  left   : Beats Fit Pro case, ring case (finger scoop), steel band oval
  middle : one flat pocket for the two soft Ocean Band parts (stacked)
  right  : two identical lean-back (75 deg) slots along Y (wallet, iPhone)
  rear   : L-shaped small-items pocket in the spare area
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import trimesh
from shapely.affinity import scale, translate
from shapely.geometry import Point, box

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "models" / "tray.stl"

WIDTH = 147.0
DEPTH = 160.0
HEIGHT = 22.0
FLOOR = 4.0  # material under the deepest cut
LEAN_DEG = 15.0  # tilt from vertical (75 deg recline)


def extrude(poly, z0, z1):
    mesh = trimesh.creation.extrude_polygon(poly, z1 - z0)
    mesh.apply_translation([0, 0, z0])
    return mesh


def pocket(x0, y0, w, d, depth, radius=3.0):
    """Rounded rectangular pocket cut from the top, `depth` deep."""
    poly = box(x0, y0, x0 + w, y0 + d).buffer(-radius).buffer(radius, 24)
    return extrude(poly, HEIGHT - depth, HEIGHT + 1)


def scoop(x, y, radius, depth):
    return extrude(Point(x, y).buffer(radius, 32), HEIGHT - depth, HEIGHT + 1)


def lean_slot(x_bottom, y0, length, thickness, height=40.0):
    """Slot along Y (y0..y0+length) leaning toward +X.

    The slot bottom centre sits at x = x_bottom, z = FLOOR.
    """
    cutter = trimesh.creation.box(extents=[thickness, length, height])
    rot = trimesh.transformations.rotation_matrix(np.radians(LEAN_DEG), [0, 1, 0])
    cutter.apply_transform(rot)
    axis = rot[:3, :3] @ np.array([0, 0, height / 2])
    cutter.apply_translation(np.array([x_bottom, y0 + length / 2, FLOOR]) + axis)
    return cutter


def build():
    outline = box(0, 0, WIDTH, DEPTH).buffer(-4).buffer(4, 32)
    body = extrude(outline, 0, HEIGHT)
    cuts = []

    # Left column (x 3..68): Beats 65x65x30, ring 50x50x25, steel band 55x35 oval.
    cuts.append(pocket(3, 3, 65, 65, 16, radius=6))
    cuts.append(pocket(3, 70, 50, 50, 12))
    cuts.append(scoop(53, 85, 8, 12))
    oval = scale(Point(0, 0).buffer(1, 64), 27.5, 17.5)
    cuts.append(extrude(translate(oval, 3 + 27.5, 122 + 17.5), HEIGHT - 12, HEIGHT + 1))

    # Middle column (x 71..106): Ocean Band 35x125x7 + 35x85x10 stacked flat.
    cuts.append(pocket(71, 3, 35, 125, 17, radius=4))
    cuts.append(scoop(71, 105, 9, 12))

    # Right columns: two identical slots (134 long, 11 thick) for the wallet
    # (100x70x10) and iPhone 12 mini; footprints x 109..125 and x 128..144.
    cuts.append(lean_slot(114.7, 3, 134, 11))
    cuts.append(lean_slot(133.7, 3, 134, 11))

    # Spare area behind the slots/band pocket: L-shaped tray for small items.
    spare = box(71, 131, 106, 157).union(box(71, 140, 144, 157))
    spare = spare.buffer(-3).buffer(3, 24)
    cuts.append(extrude(spare, HEIGHT - 14, HEIGHT + 1))

    return body.difference(cuts, engine="manifold")


def main():
    mesh = build()
    mesh.export(OUTPUT)
    print(f"watertight={mesh.is_watertight} extents={mesh.extents.round(2)}")
    print(f"wrote {OUTPUT}")


if __name__ == "__main__":
    main()
