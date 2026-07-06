#!/usr/bin/env python3
"""
野菜スライサー用 抑えふた (Vegetable Slicer Holder Lid)
Bambu Lab A1 mini 向け STL生成スクリプト

設計仕様:
  - 本体: 80x80mm 角形プレート (厚さ 5mm)
  - 取っ手: 中央上部に 30x20mm の握りやすいグリップ
  - スパイク: 4x4 = 16本の尖ったピン (下面) で野菜をしっかり固定
  - サポート不要, PLA推奨
"""

import math
import os

# ---------------------------------------------------------------------------
# STL ユーティリティ
# ---------------------------------------------------------------------------

def cross(a, b):
    return (
        a[1]*b[2] - a[2]*b[1],
        a[2]*b[0] - a[0]*b[2],
        a[0]*b[1] - a[1]*b[0],
    )

def normalize(v):
    l = math.sqrt(sum(x*x for x in v))
    if l == 0:
        return (0.0, 0.0, 1.0)
    return tuple(x/l for x in v)

def facet_normal(v1, v2, v3):
    u = (v2[0]-v1[0], v2[1]-v1[1], v2[2]-v1[2])
    v = (v3[0]-v1[0], v3[1]-v1[1], v3[2]-v1[2])
    return normalize(cross(u, v))

def write_stl(triangles, filepath, name="veggie_slicer_lid"):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        f.write(f"solid {name}\n")
        for v1, v2, v3 in triangles:
            n = facet_normal(v1, v2, v3)
            f.write(f"  facet normal {n[0]:.6f} {n[1]:.6f} {n[2]:.6f}\n")
            f.write("    outer loop\n")
            for v in (v1, v2, v3):
                f.write(f"      vertex {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
            f.write("    endloop\n")
            f.write("  endfacet\n")
        f.write(f"endsolid {name}\n")
    print(f"  -> {filepath} ({len(triangles)} triangles)")

# ---------------------------------------------------------------------------
# プリミティブ生成ヘルパー
# ---------------------------------------------------------------------------

def quad(v1, v2, v3, v4):
    """四角形を2つの三角形に分割"""
    return [(v1, v2, v3), (v1, v3, v4)]

def box_triangles(x0, y0, z0, x1, y1, z1):
    """軸平行直方体の全面三角形リストを返す"""
    tris = []
    # 底面 (z=z0, 法線下向き)
    tris += quad((x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0))[::-1]
    # 上面 (z=z1, 法線上向き)
    tris += quad((x0,y0,z1),(x0,y1,z1),(x1,y1,z1),(x1,y0,z1))
    # 前面 (y=y0)
    tris += quad((x0,y0,z0),(x0,y0,z1),(x1,y0,z1),(x1,y0,z0))
    # 後面 (y=y1)
    tris += quad((x1,y1,z0),(x1,y1,z1),(x0,y1,z1),(x0,y1,z0))
    # 左面 (x=x0)
    tris += quad((x0,y1,z0),(x0,y1,z1),(x0,y0,z1),(x0,y0,z0))
    # 右面 (x=x1)
    tris += quad((x1,y0,z0),(x1,y0,z1),(x1,y1,z1),(x1,y1,z0))
    return tris

def cylinder_triangles(cx, cy, z0, z1, r, segs=32):
    """円柱の全面三角形リストを返す"""
    tris = []
    angles = [2*math.pi*i/segs for i in range(segs)]
    pts_bot = [(cx + r*math.cos(a), cy + r*math.sin(a), z0) for a in angles]
    pts_top = [(cx + r*math.cos(a), cy + r*math.sin(a), z1) for a in angles]
    center_bot = (cx, cy, z0)
    center_top = (cx, cy, z1)
    for i in range(segs):
        j = (i+1) % segs
        # 底面
        tris.append((center_bot, pts_bot[j], pts_bot[i]))
        # 上面
        tris.append((center_top, pts_top[i], pts_top[j]))
        # 側面
        tris.append((pts_bot[i], pts_bot[j], pts_top[j]))
        tris.append((pts_bot[i], pts_top[j], pts_top[i]))
    return tris

def cone_triangles(cx, cy, z_base, z_tip, r_base, segs=16):
    """円錐の全面三角形リストを返す (スパイク用)"""
    tris = []
    angles = [2*math.pi*i/segs for i in range(segs)]
    pts = [(cx + r_base*math.cos(a), cy + r_base*math.sin(a), z_base) for a in angles]
    tip = (cx, cy, z_tip)
    center_bot = (cx, cy, z_base)
    for i in range(segs):
        j = (i+1) % segs
        # 底面
        tris.append((center_bot, pts[j], pts[i]))
        # 側面
        tris.append((pts[i], pts[j], tip))
    return tris

def rounded_box_triangles(x0, y0, z0, x1, y1, z1, r, segs=8):
    """四隅がR付きの直方体 (上面のみ角丸, 側面はストレート)"""
    tris = []
    # 角丸上面は4隅のコーナーアーク + 中央矩形 + 4辺矩形で近似
    # シンプル化のため: 上面を扇形 + 矩形ポリゴンで分割
    cx = [x0+r, x1-r, x1-r, x0+r]
    cy = [y0+r, y0+r, y1-r, y1-r]
    corner_angles = [math.pi, 3*math.pi/2, 0, math.pi/2]  # 各コーナー開始角

    # 上面頂点を全て収集してファンポリゴン化
    top_pts = []
    for k in range(4):
        a_start = corner_angles[k]
        for s in range(segs+1):
            a = a_start + (math.pi/2) * s / segs
            top_pts.append((cx[k] + r*math.cos(a), cy[k] + r*math.sin(a), z1))

    center_top = ((x0+x1)/2, (y0+y1)/2, z1)
    for i in range(len(top_pts)):
        j = (i+1) % len(top_pts)
        tris.append((center_top, top_pts[i], top_pts[j]))

    # 底面 (フラット)
    bot_pts = [(p[0], p[1], z0) for p in top_pts]
    center_bot = ((x0+x1)/2, (y0+y1)/2, z0)
    for i in range(len(bot_pts)):
        j = (i+1) % len(bot_pts)
        tris.append((center_bot, bot_pts[j], bot_pts[i]))

    # 側面
    n = len(top_pts)
    for i in range(n):
        j = (i+1) % n
        tris.append((bot_pts[i], bot_pts[j], top_pts[j]))
        tris.append((bot_pts[i], top_pts[j], top_pts[i]))

    return tris

# ---------------------------------------------------------------------------
# メイン形状生成
# ---------------------------------------------------------------------------

def generate(
    plate_w=80.0,    # プレート幅 (mm)
    plate_d=80.0,    # プレート奥行き (mm)
    plate_h=5.0,     # プレート厚さ (mm)
    grip_w=32.0,     # 取っ手幅
    grip_d=22.0,     # 取っ手奥行き
    grip_h=28.0,     # 取っ手高さ
    grip_r=5.0,      # 取っ手コーナーR
    spike_rows=4,    # スパイク行数
    spike_cols=4,    # スパイク列数
    spike_h=7.0,     # スパイク高さ (下方向)
    spike_r=1.8,     # スパイク根元半径
    spike_margin=10.0, # プレート端からのマージン
):
    tris = []
    # Z オフセット: スパイク先端を Z=0 に揃えてプリントベッドに置けるようにする
    oz = spike_h

    # --- プレート (角丸) ---
    r_plate = 4.0
    tris += rounded_box_triangles(
        0, 0, oz,
        plate_w, plate_d, oz + plate_h,
        r_plate, segs=6
    )

    # --- グリップ (取っ手) : プレート中央上部 ---
    gx0 = (plate_w - grip_w) / 2
    gy0 = (plate_d - grip_d) / 2
    gx1 = gx0 + grip_w
    gy1 = gy0 + grip_d
    tris += rounded_box_triangles(
        gx0, gy0, oz + plate_h,
        gx1, gy1, oz + plate_h + grip_h,
        grip_r, segs=8
    )

    # --- スパイク (下面, 円錐形) ---
    usable_w = plate_w - 2 * spike_margin
    usable_d = plate_d - 2 * spike_margin
    for row in range(spike_rows):
        for col in range(spike_cols):
            sx = spike_margin + col * usable_w / (spike_cols - 1)
            sy = spike_margin + row * usable_d / (spike_rows - 1)
            # 根元はプレート底面 (z=oz), 先端はベッド面 (z=0)
            tris += cone_triangles(sx, sy, oz, 0.0, spike_r, segs=12)

    return tris


# ---------------------------------------------------------------------------
# エントリポイント
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(__file__), "..", "models")
    out_path = os.path.join(out_dir, "veggie_slicer_lid.stl")

    print("野菜スライサー用 抑えふた を生成中...")
    tris = generate()
    write_stl(tris, out_path, name="veggie_slicer_lid")

    print("\n=== 印刷設定 (推奨) ===")
    print("  フィラメント : PLA または PETG")
    print("  レイヤー高さ : 0.20mm (Standard)")
    print("  インフィル   : 30% (スパイク強度のため)")
    print("  サポート     : なし")
    print("  印刷向き     : スパイクを上向きにして印刷 → 完成後に上下反転")
    print("  プレートサイズ: 80x80mm (A1 mini 180x180mm 内に収まります)")
    print("\n完了!")
