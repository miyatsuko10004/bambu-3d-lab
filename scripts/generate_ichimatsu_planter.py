#!/usr/bin/env python3
"""
市松 (いちまつ) 文様 植木鉢
Bambu Lab A1 mini 向け STL生成スクリプト (ドナーメッシュ変位マッピング版)

伝統文様シリーズ (柄名=商品名) の1つ。以前のバージョンは「シルエット/
プロポーションだけを参考にしてゼロから再生成」する方式だったが、それでは
参考モデル(models/sample/Planter.3mf)が持つ実績のある排水穴・脚の実用性が
再現できないというフィードバックを受け、方針を変更した:

  Planter.3mf (CC0, 模様なしの回転体主体+局所的な排水穴/脚/リム) の
  実メッシュをそのまま読み込み、「滑らかな回転体の外壁」と判定できる
  頂点だけに市松模様を法線(実際には半径)方向の変位として追加する。
  排水穴・脚・リムなど非回転体の実用ディテールは変位対象から除外し、
  ドナーの形状をそのまま(バイト単位で)保つ。

  models/sample/*.3mf のうち模様が焼き込まれていない Planter.3mf
  だからこそ成立する手法であり(Maceta_Triángulo/einstein-planterは
  柄/形状そのものが焼き込まれているため同じ手法は使えない)、CC0ライセンス
  でダウンロード時に商用利用可能と確認済み。

  trimesh/numpy/scipy 等に依存する (requirements.txt 参照)。
  実行前に: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt

壁面選定・変位・オーバーハング検証の実装は scripts/_mesh_pattern_common.py 参照。
柄そのもの(checkerboard_relief)は scripts/_pot_common.py のものを流用する
(ゼロから数式生成する版と同じテクスチャ関数、座標の与え方だけが違う)。
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
from _pot_common import checkerboard_relief


DONOR_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "models", "sample", "Planter.3mf")


def generate(
    donor_path=DONOR_PATH,
    donor_geometry_key="1",   # "1"=鉢本体, "3"=接着用リング(任意パーツ、今回は対象外)
    subdivisions=2,           # 一様分割回数 (細線パターンの解像度確保、watertightを壊さない)
    tex_cell_size=5.0,        # 市松セルの一辺 (mm)
    tex_amp=0.6,              # 市松レリーフの最大突出量 (mm、浅め=市松は陰影で読ませる)
    tex_edge_width=1.0,       # セル境界の遷移幅 (mm)
):
    mesh = load_donor_mesh(donor_path, donor_geometry_key)
    mesh = subdivide_uniform(mesh, times=subdivisions)
    mask, h, theta, r_ref = build_wall_mask(mesh)

    circumference = 2 * math.pi * r_ref
    n_theta = max(4, round(circumference / tex_cell_size))
    if n_theta % 2 != 0:
        n_theta += 1  # 市松の周方向セル数は偶数必須 (奇数だと継ぎ目でパリティが揃う)

    def pattern_func(s, z):
        col = (s / circumference) * n_theta
        row = z / tex_cell_size
        return checkerboard_relief(col, row, tex_cell_size, tex_amp, tex_edge_width)

    new_mesh, disp = displace_radial(mesh, mask, h, theta, r_ref, pattern_func)
    return new_mesh, disp


if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "models")
    out_path = os.path.join(out_dir, "ichimatsu_planter.stl")

    print("市松文様 植木鉢 (ichimatsu_planter, ドナーメッシュ変位版) を生成中...")
    mesh, disp = generate()
    print(f"  watertight={mesh.is_watertight}, winding_consistent={mesh.is_winding_consistent}")
    flag_new_overhangs(mesh, disp)
    export_binary_stl(mesh, out_path, name="ichimatsu_planter")

    print(
        """
=== 印刷設定 (推奨) ===
  フィラメント : PLA (黒/ダークグレー系、白/テラコッタ系いずれも可、単色)
  レイヤー高さ : 0.20mm (Standard)
  壁ループ数   : 3 (排水/耐荷重強度のため)
  インフィル   : 15%
  サポート     : なし (ドナーの排水穴・脚は印刷実績のある設計をそのまま使用)
  ビルドプレート: Textured PEI Plate

=== 設計メモ ===
  models/sample/Planter.3mf (CC0) の実メッシュに市松模様を変位マッピング。
  シルエット・排水穴・脚・リムはドナーの形状をそのまま保持し、
  「滑らかな回転体の外壁」と判定した頂点だけに柄を追加している。
  柄自体は他の伝統文様シリーズと同じ checkerboard_relief() を使用。
"""
    )
