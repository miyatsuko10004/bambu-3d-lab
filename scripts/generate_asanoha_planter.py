#!/usr/bin/env python3
"""
麻の葉 (あさのは) 文様 植木鉢
Bambu Lab A1 mini 向け STL生成スクリプト (ドナーメッシュ変位マッピング版)

伝統文様シリーズ (柄名=商品名) の1つ。方針・手法は generate_ichimatsu_planter.py
と同じ (models/sample/Planter.3mfの実メッシュに柄を変位マッピングし、排水穴・
脚・リムなど実用ディテールはそのまま保持する)。詳細はそちらのdocstring参照。

柄そのもの(正六角形の辺+放射スポークへの距離場によるリッジ)は
scripts/_pot_common.py の asanoha_height() をそのまま流用する。
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _mesh_pattern_common import (
    load_donor_mesh,
    subdivide_uniform,
    build_wall_mask,
    displace_radial,
    flag_new_overhangs,
    export_binary_stl,
)
from _pot_common import make_hex_centers, SeedGrid, asanoha_height


DONOR_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "models", "sample", "Planter.3mf")


def generate(
    donor_path=DONOR_PATH,
    donor_geometry_key="1",
    subdivisions=2,
    hex_r=11.0,                   # 六角形の外接半径 (mm、対辺距離は hex_r*sqrt(3)≈19mm)
    tex_amp=0.4,                  # リッジの最大突出量 (mm)
    tex_line_half_width=1.0,      # リッジの片側半幅 (mm、全幅は概ねこの2倍)
):
    mesh = load_donor_mesh(donor_path, donor_geometry_key)
    mesh = subdivide_uniform(mesh, times=subdivisions)
    mask, h, theta, r_ref = build_wall_mask(mesh)

    circumference = 2 * math.pi * r_ref
    h_min, h_max = float(h.min()), float(h.max())
    seeds, seed_cols, _ = make_hex_centers(circumference, h_min, h_max, hex_r)
    seed_grid = SeedGrid(seeds, circumference, hex_r * 1.8, seed_cols)

    def pattern_func(s, z):
        return asanoha_height(s, z, seed_grid, circumference, hex_r, tex_amp, tex_line_half_width)

    new_mesh, disp = displace_radial(mesh, mask, h, theta, r_ref, pattern_func)
    return new_mesh, disp


if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "models")
    out_path = os.path.join(out_dir, "asanoha_planter.stl")

    print("麻の葉文様 植木鉢 (asanoha_planter, ドナーメッシュ変位版) を生成中...")
    mesh, disp = generate()
    print(f"  watertight={mesh.is_watertight}, winding_consistent={mesh.is_winding_consistent}")
    flag_new_overhangs(mesh, disp)
    export_binary_stl(mesh, out_path, name="asanoha_planter")

    print(
        """
=== 印刷設定 (推奨) ===
  フィラメント : PLA (マット系推奨。細線レリーフのため明色の方が陰影が見えやすい)
  レイヤー高さ : 0.16〜0.20mm (細線を綺麗に出すため0.16mm推奨)
  壁ループ数   : 3 (排水/耐荷重強度のため)
  インフィル   : 15%
  サポート     : なし (ドナーの排水穴・脚は印刷実績のある設計をそのまま使用)
  ビルドプレート: Textured PEI Plate

=== 設計メモ ===
  models/sample/Planter.3mf (CC0) の実メッシュに麻の葉模様を変位マッピング。
  シルエット・排水穴・脚・リムはドナーの形状をそのまま保持。
"""
    )
