#!/usr/bin/env python3
"""Clamp-on speaker stand for a DENON USC-M5 (v2): base+jaw, clamp screw, pad, pillar, top.

The stand sits on the desk top and is clamped to the desk's front edge (25 mm
top) by a C-jaw on the base with a printed trapezoidal-thread clamp screw. The
speaker (135 W x 252 D x 241 H mm, 2.8 kg) sits on a top plate 150 mm above the
desk, fully over the desk (its front face ends at the desk edge).

Axes: X along the desk edge, Y toward the user (the desk front edge is Y = 0,
the desk extends toward -Y), Z up; the desk top surface is Z = 0.
Built with build123d (exact B-rep); writes STL + STEP per part.
"""

from __future__ import annotations

from pathlib import Path

from bd_warehouse.thread import MetricTrapezoidalThread
from build123d import (
    Align, Box, Cylinder, Pos, Rot, export_step, export_stl, fillet, scale, Axis,
)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "models"

DESK_T = 25.0  # measured
GAP = 26.0  # jaw opening (desk thickness + 1 mm play)
LIFT = 150.0  # speaker height above the desk top (requested ~15 cm)
SPEAKER = (135.0, 252.0, 241.0)  # W x D x H, measured; 2.8 kg

BASE_W, BASE_D, BASE_T = 170.0, 160.0, 10.0  # sits on the desk top
WALL_T = 10.0  # front wall / lower jaw thickness
JAW_D = 80.0  # lower jaw reach under the desk
FILLET = 3.0
BOSS_R = 20.0
THREAD = "20x4"  # printed trapezoidal clamp screw
THREAD_LEN = 42.0
THREAD_CLEAR = 1.1  # radial scale of the nut thread (printing clearance)
SCREW_Y = -45.0  # clamp screw axis (distance behind the desk edge)

PILLAR = (90.0, 40.0)  # section X x Y
PILLAR_Y = -124.0  # speaker front face lands on the desk edge
TENON = (60.0, 20.0, 10.0)  # X x Y x height, with 0.3 mm play in the socket
TOP_W, TOP_D, TOP_T = 160.0, 175.0, 8.0
RIM_H, RIM_W = 0.0, 4.0  # no rim: the user wants no anti-slip features

PAD_R = 17.0
PAD_POCKET = 6.0
JAW_TOP = -GAP  # top face of the lower jaw
JAW_BOT = JAW_TOP - WALL_T


def clamp_base():
    """Base on the desk top + front wall + lower jaw (a C frame) + threaded boss."""
    base = Pos(0, -BASE_D / 2, BASE_T / 2) * Box(BASE_W, BASE_D, BASE_T)
    wall_h = BASE_T + GAP + WALL_T
    wall = Pos(0, WALL_T / 2, BASE_T - wall_h / 2) * Box(BASE_W, WALL_T, wall_h)
    jaw = Pos(0, -JAW_D / 2 + WALL_T, JAW_BOT + WALL_T / 2) * Box(
        BASE_W, JAW_D + WALL_T, WALL_T
    )
    frame = base + wall + jaw
    boss = Pos(0, SCREW_Y, JAW_BOT + WALL_T / 2 - 6) * Cylinder(BOSS_R, WALL_T + 12)
    frame = frame + boss
    # threaded hole: cut the thread root, add the (radially enlarged) internal thread
    th = MetricTrapezoidalThread(THREAD, length=WALL_T + 12, external=False,
                                 end_finishes=("fade", "fade"))
    root = th.root_radius * THREAD_CLEAR
    th = scale(th, by=(THREAD_CLEAR, THREAD_CLEAR, 1.0))
    z0 = JAW_BOT + WALL_T / 2 - 6 - (WALL_T + 12) / 2
    hole = Pos(0, SCREW_Y, z0) * Cylinder(
        root, WALL_T + 14, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    frame = frame - Pos(0, 0, -1) * hole
    frame = frame + Pos(0, SCREW_Y, z0) * th
    # pillar socket on the base top
    sock = Pos(0, PILLAR_Y, BASE_T - TENON[2] / 2 + 0.01) * Box(
        TENON[0] + 0.6, TENON[1] + 0.6, TENON[2] + 0.02
    )
    # pocket in the jaw top so the pad can retract below the desk gap
    pocket = Pos(0, SCREW_Y, JAW_TOP - PAD_POCKET / 2 + 0.01) * Cylinder(PAD_R + 1.0, PAD_POCKET + 0.02)
    return frame - sock - pocket


def clamp_screw():
    """Printed trapezoidal screw with a knob; the tip is a pin for the pad."""
    ext = MetricTrapezoidalThread(THREAD, length=THREAD_LEN, external=True,
                                  end_finishes=("fade", "chamfer"))
    core = Cylinder(ext.root_radius, THREAD_LEN, align=(Align.CENTER, Align.CENTER, Align.MIN))
    shaft = core + ext
    knob = Pos(0, 0, -10) * Cylinder(24, 10, align=(Align.CENTER, Align.CENTER, Align.MIN))
    pin = Pos(0, 0, THREAD_LEN) * Cylinder(4, 4, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return knob + shaft + pin


def pad():
    """Pad for the desk underside (print in TPU or add a rubber disc)."""
    disc = Cylinder(PAD_R, 5, align=(Align.CENTER, Align.CENTER, Align.MIN))
    # blind socket open at the bottom (the screw pin enters from below)
    return disc - Pos(0, 0, -1) * Cylinder(4.2, 5, align=(Align.CENTER, Align.CENTER, Align.MIN))


def pillar():
    h = LIFT - BASE_T - TOP_T
    post = Pos(0, PILLAR_Y, BASE_T + h / 2 + TENON[2] - TENON[2]) * Box(PILLAR[0], PILLAR[1], h)
    ten_b = Pos(0, PILLAR_Y, BASE_T - TENON[2] / 2) * Box(TENON[0], TENON[1], TENON[2])
    ten_t = Pos(0, PILLAR_Y, BASE_T + h + TENON[2] / 2) * Box(TENON[0], TENON[1], TENON[2])
    return post + ten_b + ten_t


def top_plate():
    z = LIFT - TOP_T
    plate = Pos(0, PILLAR_Y, z + TOP_T / 2) * Box(TOP_W, TOP_D, TOP_T)
    # optional front/back rims (disabled)
    if RIM_H > 0:
        for sgn in (-1, 1):
            rim = Pos(0, PILLAR_Y + sgn * (TOP_D / 2 - RIM_W / 2), LIFT + RIM_H / 2) * Box(TOP_W, RIM_W, RIM_H)
            plate = plate + rim
    sock = Pos(0, PILLAR_Y, z + TENON[2] / 2 - 0.01) * Box(
        TENON[0] + 0.6, TENON[1] + 0.6, TENON[2] + 0.02
    )
    return plate - sock


def thread_test(clear):
    """12 mm nut block with the internal thread at a given radial clearance scale."""
    th = MetricTrapezoidalThread(THREAD, length=12, external=False, end_finishes=("fade", "fade"))
    root = th.root_radius * clear
    th = scale(th, by=(clear, clear, 1.0))
    blk = Cylinder(17, 12, align=(Align.CENTER, Align.CENTER, Align.MIN))
    blk = blk - Pos(0, 0, -1) * Cylinder(root, 14, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return blk + th


def thread_test_screw():
    ext = MetricTrapezoidalThread(THREAD, length=24, external=True, end_finishes=("fade", "chamfer"))
    core = Cylinder(ext.root_radius, 24, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return Pos(0, 0, -8) * Cylinder(14, 8, align=(Align.CENTER, Align.CENTER, Align.MIN)) + core + ext


PARTS = {
    "speaker_stand_base": clamp_base,
    "speaker_stand_screw": clamp_screw,
    "speaker_stand_pad": pad,
    "speaker_stand_pillar": pillar,
    "speaker_stand_top": top_plate,
    "speaker_stand_thread_test_screw": thread_test_screw,
    "speaker_stand_thread_test_nut_1p05": lambda: thread_test(1.05),
    "speaker_stand_thread_test_nut_1p10": lambda: thread_test(1.10),
    "speaker_stand_thread_test_nut_1p15": lambda: thread_test(1.15),
}


def main():
    for name, fn in PARTS.items():
        part = fn()
        export_stl(part, str(OUT / f"{name}.stl"), tolerance=0.02, angular_tolerance=0.2)
        export_step(part, str(OUT / f"{name}.step"))
        bb = part.bounding_box()
        print(f"{name}: valid={part.is_valid} size={bb.size.X:.0f}x{bb.size.Y:.0f}x{bb.size.Z:.0f}"
              f" vol={part.volume/1000:.1f} cm3")


if __name__ == "__main__":
    main()
