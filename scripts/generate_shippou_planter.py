#!/usr/bin/env python3
"""
七宝 (しっぽう) 文様 植木鉢
Bambu Lab A1 mini 向け STL生成スクリプト (ドナーメッシュ変位マッピング版)

伝統文様シリーズ (柄名=商品名) の1つ。方針・手法は generate_ichimatsu_planter.py
と同じ (models/sample/Planter.3mfの実メッシュに柄を変位マッピングし、排水穴・
脚・リムなど実用ディテールはそのまま保持する)。詳細はそちらのdocstring参照。

柄そのもの(正方格子上の円への距離場)は scripts/_pot_common.py の
shippou_height() をそのまま流用する。
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
from _pot_common import shippou_height


DONOR_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "models", "sample", "Planter.3mf")


def generate(
    donor_path=DONOR_PATH,
    donor_geometry_key="1",
    subdivisions=2,
    grid_spacing=13.5,            # 円の格子間隔 (mm)
    circle_radius=10.5,           # 円の半径 (mm、格子間隔よりやや小さく重なりを作る)
    tex_amp=0.35,                 # リッジの最大突出量 (mm)
    tex_line_half_width=1.2,      # リッジの片側半幅 (mm、全幅は概ねこの2倍)
):
    mesh = load_donor_mesh(donor_path, donor_geometry_key)
    mesh = subdivide_uniform(mesh, times=subdivisions)
    mask, h, theta, r_ref = build_wall_mask(mesh)

    circumference = 2 * math.pi * r_ref

    def pattern_func(s, z):
        return shippou_height(s, z, circumference, grid_spacing, circle_radius, tex_amp, tex_line_half_width)

    new_mesh, disp = displace_radial(mesh, mask, h, theta, r_ref, pattern_func)
    return new_mesh, disp


if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "models")
    out_path = os.path.join(out_dir, "shippou_planter.stl")

    print("七宝文様 植木鉢 (shippou_planter, ドナーメッシュ変位版) を生成中...")
    mesh, disp = generate()
    print(f"  watertight={mesh.is_watertight}, winding_consistent={mesh.is_winding_consistent}")
    flag_new_overhangs(mesh, disp)
    export_binary_stl(mesh, out_path, name="shippou_planter")

    print(
        """
=== 印刷設定 (推奨) ===
  フィラメント : PLA (黒/ダークグレー系、白/テラコッタ系いずれも可、単色)
  レイヤー高さ : 0.16〜0.20mm
  壁ループ数   : 3 (排水/耐荷重強度のため)
  インフィル   : 15%
  サポート     : なし (ドナーの排水穴・脚は印刷実績のある設計をそのまま使用)
  ビルドプレート: Textured PEI Plate

=== 設計メモ ===
  models/sample/Planter.3mf (CC0) の実メッシュに七宝模様を変位マッピング。
  シルエット・排水穴・脚・リムはドナーの形状をそのまま保持。
"""
    )
