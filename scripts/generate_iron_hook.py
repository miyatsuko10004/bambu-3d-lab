#!/usr/bin/env python3
"""
ヘアアイロン用 棚掛けフック (Iron Hanger Hook)
Bambu Lab A1 mini 向け STL生成スクリプト

構成:
  - 上部フック: 棚/カゴのへりに上から引っ掛ける (J字, 薄いふちに対応)
  - 下部フック: ヘアアイロンの根本 (リング状の持ち手) を掛ける (J字)
  - 側面フック: コードをまとめて掛ける小フック

印刷向き: 平らな側面 (プロファイル面) をベッドに寝かせて印刷 → サポート不要
"""

import math
import os

# ---------------------------------------------------------------------------
# STL ユーティリティ
# ---------------------------------------------------------------------------

def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])

def normalize(v):
    l = math.sqrt(sum(x*x for x in v))
    return (0.0, 0.0, 1.0) if l == 0 else tuple(x/l for x in v)

def facet_normal(v1, v2, v3):
    u = tuple(v2[i]-v1[i] for i in range(3))
    v = tuple(v3[i]-v1[i] for i in range(3))
    return normalize(cross(u, v))

def write_stl(triangles, filepath, name="model"):
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    with open(filepath, 'w') as f:
        f.write(f"solid {name}\n")
        for v1, v2, v3 in triangles:
            n = facet_normal(v1, v2, v3)
            f.write(f"  facet normal {n[0]:.6f} {n[1]:.6f} {n[2]:.6f}\n")
            f.write("    outer loop\n")
            for v in (v1, v2, v3):
                f.write(f"      vertex {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
            f.write("    endloop\n  endfacet\n")
        f.write(f"endsolid {name}\n")
    print(f"  -> {filepath} ({len(triangles)} triangles)")

# ---------------------------------------------------------------------------
# 帯状スイープ (centerline + 一定厚みの断面を Z 方向に押し出す)
# ---------------------------------------------------------------------------

def oriented_segment_tris(p0, p1, thickness, z0, z1):
    """
    2D centerline 上のセグメント p0->p1 を、垂直方向に thickness 幅を持つ
    矩形として Z 方向 (z0..z1) に押し出した六面体を返す。
    """
    dx, dy = p1[0]-p0[0], p1[1]-p0[1]
    l = math.hypot(dx, dy)
    if l == 0:
        return []
    nx, ny = -dy/l * thickness/2, dx/l * thickness/2
    c1 = (p0[0]+nx, p0[1]+ny)
    c2 = (p0[0]-nx, p0[1]-ny)
    c3 = (p1[0]+nx, p1[1]+ny)
    c4 = (p1[0]-nx, p1[1]-ny)

    def v(pt, z):
        return (pt[0], pt[1], z)

    tris = []
    def quad(a, b, c, d):
        tris.append((a, b, c))
        tris.append((a, c, d))

    # 上面 (z1)
    quad(v(c1,z1), v(c3,z1), v(c4,z1), v(c2,z1))
    # 底面 (z0)
    quad(v(c2,z0), v(c4,z0), v(c3,z0), v(c1,z0))
    # 側面1 (c1-c3)
    quad(v(c1,z0), v(c1,z1), v(c3,z1), v(c3,z0))
    # 側面2 (c3-c4)
    quad(v(c3,z0), v(c3,z1), v(c4,z1), v(c4,z0))
    # 側面3 (c4-c2)
    quad(v(c4,z0), v(c4,z1), v(c2,z1), v(c2,z0))
    # 側面4 (c2-c1)
    quad(v(c2,z0), v(c2,z1), v(c1,z1), v(c1,z0))
    return tris

def sweep_path(points, thickness, z0, z1):
    """centerline 点列を繋げて帯状のソリッドを生成 (各セグメントは独立した六面体)"""
    tris = []
    for i in range(len(points)-1):
        tris += oriented_segment_tris(points[i], points[i+1], thickness, z0, z1)
    return tris

def arc_points(cx, cy, r, deg_start, deg_end, segs=16):
    pts = []
    for i in range(segs+1):
        t = deg_start + (deg_end-deg_start) * i/segs
        a = math.radians(t)
        pts.append((cx + r*math.cos(a), cy + r*math.sin(a)))
    return pts

# ---------------------------------------------------------------------------
# メイン形状生成
# ---------------------------------------------------------------------------

def generate(
    width=22.0,        # 押し出し幅 (印刷時の高さになる)
    thickness=6.0,      # フック本体の帯の太さ
    shelf_thickness=6.0,   # 想定する棚/カゴのへりの厚さ
    clearance=3.0,      # 差し込みクリアランス
    top_arm_len=26.0,   # 上部フックの棚上に乗る長さ
    spine_len=75.0,     # 上部フックの下から下部フック開始点までの垂直長さ
    bottom_r=16.0,      # 下部フック (アイロン根本用) の曲げ半径
    cord_hook_r=8.0,    # 側面コードフックの曲げ半径
    cord_hook_height=35.0,  # 側面コードフックを取り付ける高さ (下部フック起点からの高さ)
):
    tris = []
    shelf_gap = shelf_thickness + clearance  # 上部フックの開口高さ

    # 基準: y=0 を「下部フックの根本(スパイン最下点)」に置き、後で全体を Z 方向に平行移動して
    # プリント時の設置面(実際の座標系では Z=0..width)を確定する。
    y_bottom = 0.0
    y_spine_top = y_bottom + spine_len              # 上部フック開口の下端
    y_top = y_spine_top + shelf_gap                  # 棚の上面 = 上部フック上端

    # --- 上部フック + スパイン (棚掛け部分 〜 垂直本体) ---
    path_top = [
        (top_arm_len, y_top),   # 腕の先端 (棚の奥側)
        (0.0, y_top),           # 前面上端 (エルボー)
        (0.0, y_spine_top),     # 開口下端
        (0.0, y_bottom),        # スパイン最下点 (下部フックの起点)
    ]
    tris += sweep_path(path_top, thickness, 0.0, width)

    # --- 下部フック (アイロンの根本を掛ける J字カーブ) ---
    # 中心を (bottom_r, y_bottom) に置き、180°(スパイン最下点)から
    # 420°(=60°, 前方やや上)まで掃引 → 下に膨らんでから前上方へ跳ね上がる形
    arc_bottom = arc_points(bottom_r, y_bottom, bottom_r, 180, 420, segs=20)
    tris += sweep_path(arc_bottom, thickness, 0.0, width)

    # --- 側面フック (コード掛け用の小さいJ字) ---
    # スパイン前面 (x=0) から手前 (-x方向) に張り出し、先端を上向きに曲げる。
    y_cord = y_bottom + cord_hook_height
    cord_out = cord_hook_r * 1.6
    path_cord_straight = [
        (0.0, y_cord),
        (-cord_out, y_cord),
    ]
    tris += sweep_path(path_cord_straight, thickness*0.8, 0.0, width)
    arc_cord = arc_points(-cord_out, y_cord + cord_hook_r, cord_hook_r, 270, 80, segs=14)
    tris += sweep_path(arc_cord, thickness*0.8, 0.0, width)

    return tris


if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "models")
    out_path = os.path.join(out_dir, "iron_hook.stl")

    print("ヘアアイロン用 棚掛けフック を生成中...")
    tris = generate()
    write_stl(tris, out_path, name="iron_hook")

    print("""
=== 印刷設定 (推奨) ===
  フィラメント : PETG (耐荷重・耐熱性のため) または PLA
  レイヤー高さ : 0.20mm
  インフィル   : 40%
  サポート     : なし (平らな面を下にして印刷)
  壁ループ数   : 4 (フック強度確保)
  印刷向き     : プロファイル面 (最も面積の大きい面) をベッドに接地させる
                 → Bambu Studio で自動的に平らな面を検出して配置されます

=== 使い方 ===
  上部フックを棚/カゴのへり (厚さ 6mm 目安, クリアランス込みで最大 9mm) に上から掛け、
  下部フックにヘアアイロンの根本(持ち手の輪)を、側面フックにまとめたコードを掛けます。
""")
