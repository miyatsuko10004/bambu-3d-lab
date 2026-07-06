#!/usr/bin/env python3
"""
ヘアアイロン用 壁掛けホルダー (画像の白いパーツを参考にした形状)
Bambu Lab A1 mini 向け STL生成スクリプト

構成:
  - 本体プレート: 縦長のフラットな板
  - 前面フック: アイロンの持ち手の輪 (ピボット部のループ) を掛けるペグ
  - 右側バー : コードを巻きつける横棒
  - 背面スロット: 本体の裏に薄い板をすき間 (カード2枚分程度) をあけて取り付け、
                  棚/カゴなどの薄いへりを上から挟み込んで掛けられる構造

印刷向き: 本体プレートの背面 (スロット側) をベッドに接地 → サポート不要
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
# プリミティブ
# ---------------------------------------------------------------------------

def rounded_plate_tris(x0, y0, z0, x1, y1, z1, r, segs=8):
    """XY方向に角丸、Z方向にフラットな板"""
    tris = []
    cx = [x0+r, x1-r, x1-r, x0+r]
    cy = [y0+r, y0+r, y1-r, y1-r]
    starts = [math.pi, 3*math.pi/2, 0, math.pi/2]
    top_pts, bot_pts = [], []
    for k in range(4):
        for s in range(segs+1):
            a = starts[k] + (math.pi/2)*s/segs
            top_pts.append((cx[k]+r*math.cos(a), cy[k]+r*math.sin(a), z1))
            bot_pts.append((cx[k]+r*math.cos(a), cy[k]+r*math.sin(a), z0))
    n = len(top_pts)
    ct = ((x0+x1)/2, (y0+y1)/2, z1)
    cb = ((x0+x1)/2, (y0+y1)/2, z0)
    for i in range(n):
        j = (i+1) % n
        tris.append((ct, top_pts[i], top_pts[j]))
        tris.append((cb, bot_pts[j], bot_pts[i]))
        tris.append((bot_pts[i], bot_pts[j], top_pts[j]))
        tris.append((bot_pts[i], top_pts[j], top_pts[i]))
    return tris

def ring_pts(cx, cy, z, r, segs):
    a = [2*math.pi*i/segs for i in range(segs)]
    return [(cx+r*math.cos(t), cy+r*math.sin(t), z) for t in a]

def cylinder_tris(cx, cy, z0, z1, r, segs=24, cap_bot=True, cap_top=True):
    """Z軸方向に伸びる円柱"""
    tris = []
    pb = ring_pts(cx, cy, z0, r, segs)
    pt = ring_pts(cx, cy, z1, r, segs)
    cb, ct = (cx, cy, z0), (cx, cy, z1)
    for i in range(segs):
        j = (i+1) % segs
        if cap_bot:
            tris.append((cb, pb[j], pb[i]))
        if cap_top:
            tris.append((ct, pt[i], pt[j]))
        tris.append((pb[i], pb[j], pt[j]))
        tris.append((pb[i], pt[j], pt[i]))
    return tris

def horizontal_peg_tris(base, direction, length, r, tip_r_scale=1.6, segs=20):
    """
    X-Y平面上を水平に伸びるペグ (先端が太くなり抜け止めになる)
    base: (x,y,z) 根本中心, direction: (dx,dy) 正規化前でも可, z軸は固定 (垂直円柱の集合として近似)
    ここでは進行方向に沿って複数の円柱を繋げて丸ペグを表現する。
    """
    dx, dy = direction
    l = math.hypot(dx, dy)
    ux, uy = dx/l, dy/l
    bx, by, bz = base
    tris = []
    # 軸に沿った円柱本体を、進行方向を法線とする円の集合として近似するのは複雑なため、
    # ここでは単純に「立てた円柱を横に倒す」代わりに、進行方向にそって細かい球状ノードを
    # 連結する近似ではなく、水平円柱をそのまま解析的に生成する。
    n_seg = 12
    for i in range(n_seg):
        t0 = i / n_seg
        t1 = (i+1) / n_seg
        r0 = r * (1.0 if t0 < 0.85 else 1.0 + (tip_r_scale-1.0) * (t0-0.85)/0.15)
        r1 = r * (1.0 if t1 < 0.85 else 1.0 + (tip_r_scale-1.0) * (t1-0.85)/0.15)
        c0 = (bx + ux*length*t0, by + uy*length*t0, bz)
        c1 = (bx + ux*length*t1, by + uy*length*t1, bz)
        tris += cylinder_segment_along_axis(c0, c1, r0, r1, (ux, uy), segs)
    # 先端キャップ
    tip_center = (bx + ux*length, by + uy*length, bz)
    tris += disc_cap(tip_center, (ux, uy), r * tip_r_scale, segs, outward=True)
    return tris

def forward_peg_tris(base, length, r, tip_r_scale=1.6, segs=24, n_seg=12):
    """
    プレート面から手前 (+Z方向) にまっすぐ伸びるペグ。
    先端 (Z方向奥側 = 手前側) に向かうほど太くなり、抜け止めの太い部分が手前に来る。
    """
    bx, by, bz = base
    tris = []

    def ring_at(cz, rad):
        return [(bx + rad*math.cos(2*math.pi*i/segs), by + rad*math.sin(2*math.pi*i/segs), cz)
                for i in range(segs)]

    pts_prev = None
    for i in range(n_seg+1):
        t = i / n_seg
        rad = r * (1.0 + (tip_r_scale-1.0) * t)  # 根本 -> 先端にかけて太くなる
        ring = ring_at(bz + length*t, rad)
        if pts_prev is not None:
            for k in range(segs):
                kk = (k+1) % segs
                tris.append((pts_prev[k], pts_prev[kk], ring[kk]))
                tris.append((pts_prev[k], ring[kk], ring[k]))
        pts_prev = ring
    # 根本キャップ
    root_ring = ring_at(bz, r)
    for k in range(segs):
        kk = (k+1) % segs
        tris.append(((bx, by, bz), root_ring[kk], root_ring[k]))
    # 先端キャップ
    tip_center = (bx, by, bz + length)
    for k in range(segs):
        kk = (k+1) % segs
        tris.append((tip_center, pts_prev[k], pts_prev[kk]))
    return tris

def cylinder_segment_along_axis(c0, c1, r0, r1, axis_xy, segs):
    """axis_xy 方向を軸とする円柱セグメント (円は axis に垂直な平面、ここではZ軸を含む平面)"""
    ux, uy = axis_xy
    # 軸に垂直な2つの基底ベクトル: 1つはワールドZ、もう1つは axis×Z
    perp = (-uy, ux, 0.0)  # 水平面内で軸に垂直
    up = (0.0, 0.0, 1.0)   # 垂直方向
    tris = []
    pts0, pts1 = [], []
    for i in range(segs):
        a = 2*math.pi*i/segs
        ca, sa = math.cos(a), math.sin(a)
        ox = perp[0]*ca + up[0]*sa
        oy = perp[1]*ca + up[1]*sa
        oz = perp[2]*ca + up[2]*sa
        pts0.append((c0[0]+ox*r0, c0[1]+oy*r0, c0[2]+oz*r0))
        pts1.append((c1[0]+ox*r1, c1[1]+oy*r1, c1[2]+oz*r1))
    for i in range(segs):
        j = (i+1) % segs
        tris.append((pts0[i], pts0[j], pts1[j]))
        tris.append((pts0[i], pts1[j], pts1[i]))
    return tris

def disc_cap(center, axis_xy, r, segs, outward=True):
    ux, uy = axis_xy
    perp = (-uy, ux, 0.0)
    up = (0.0, 0.0, 1.0)
    pts = []
    for i in range(segs):
        a = 2*math.pi*i/segs
        ca, sa = math.cos(a), math.sin(a)
        ox = perp[0]*ca + up[0]*sa
        oy = perp[1]*ca + up[1]*sa
        oz = perp[2]*ca + up[2]*sa
        pts.append((center[0]+ox*r, center[1]+oy*r, center[2]+oz*r))
    tris = []
    for i in range(segs):
        j = (i+1) % segs
        if outward:
            tris.append((center, pts[i], pts[j]))
        else:
            tris.append((center, pts[j], pts[i]))
    return tris

# ---------------------------------------------------------------------------
# メイン形状生成
# ---------------------------------------------------------------------------

def generate(
    plate_w=75.0,       # 本体プレート幅 (コードバー分を確保するため拡幅)
    plate_h=100.0,      # 本体プレート高さ
    plate_t=4.0,        # 本体プレート厚さ
    plate_r=6.0,        # プレート角R
    hook_peg_r=7.5,      # アイロン用フックペグ半径 (拡大)
    hook_peg_len=32.0,   # アイロン用フックペグ長さ (拡大)
    hook_peg_y=55.0,     # フックペグの取り付け高さ (プレート下端からの距離)
    hook_peg_x_ratio=0.18,  # フックペグのX位置 (プレート幅に対する比率, 左寄せ)
    cord_bar_r=4.0,      # コードバー半径
    cord_bar_straight_len=32.0,  # 手前方向に伸びる直線部分の長さ
    cord_bar_curl_r=11.0,       # 先端の上向きカール半径
    cord_bar_y=72.0,     # コードバーの取り付け高さ (フックペグより上)
    cord_bar_x_ratio=0.85,  # コードバーのX位置 (プレート幅に対する比率, 右寄せ)
    slot_gap=3.0,        # 背面スロットの隙間 (カード2枚分の目安)
    slot_plate_t=3.0,    # 背面スロット板の厚さ
    slot_plate_h=32.0,   # 背面スロット板の高さ (上部のみ)
    slot_bridge_h=6.0,   # 上部の橋渡し部の高さ
):
    tris = []

    # --- 本体プレート (z: 0 〜 plate_t, 前面が z=plate_t 側) ---
    tris += rounded_plate_tris(0, 0, 0, plate_w, plate_h, plate_t, plate_r, segs=8)

    # --- 前面フックペグ (アイロンの持ち手の輪を掛ける, 大型化, 手前方向に90度倒した向き) ---
    peg_base = (plate_w * hook_peg_x_ratio, hook_peg_y, plate_t)
    tris += forward_peg_tris(peg_base, hook_peg_len, hook_peg_r, tip_r_scale=1.4)

    # --- コードバー (プレート面から手前(+Z)方向に伸び、先端が上向きにカールする) ---
    cord_base = (plate_w * cord_bar_x_ratio, cord_bar_y, plate_t)
    tris += forward_cord_bar_tris(cord_base, cord_bar_straight_len, cord_bar_curl_r, cord_bar_r)

    # --- 背面スロット (棚/カゴのへりを挟む板, プレート上部のみ) ---
    z_slot_front = -slot_gap             # 本体背面 (z=0) から slot_gap だけ離れた位置
    z_slot_back = z_slot_front - slot_plate_t
    y0 = plate_h - slot_plate_h
    y1 = plate_h
    tris += rounded_plate_tris(0, y0, z_slot_back, plate_w, y1, z_slot_front, 2.0, segs=6)

    # 上部の橋渡し (本体プレート上端とスロット板上端を繋ぐ)
    tris += rounded_plate_tris(0, plate_h - slot_bridge_h, z_slot_back, plate_w, plate_h, plate_t, 2.0, segs=6)

    return tris


def forward_cord_bar_tris(base, straight_len, curl_r, r, segs=20, n_straight=10, n_curl=10):
    """
    プレート面から手前 (+Z方向) にまっすぐ伸び、先端が上向き (+Y方向) に
    カールする丸棒 (コード抜け止め付き)。
    円の断面は Z軸 (棒の進行方向) に垂直な X-Y 平面上に生成する。
    """
    bx, by, bz = base
    tris = []

    def ring_at(cx, cy, cz, rad):
        return [(cx + rad*math.cos(2*math.pi*i/segs), cy + rad*math.sin(2*math.pi*i/segs), cz)
                for i in range(segs)]

    # --- 直線部分 (+Z方向) ---
    pts_prev = None
    for i in range(n_straight+1):
        t = straight_len * i / n_straight
        ring = ring_at(bx, by, bz + t, r)
        if pts_prev is not None:
            for k in range(segs):
                kk = (k+1) % segs
                tris.append((pts_prev[k], pts_prev[kk], ring[kk]))
                tris.append((pts_prev[k], ring[kk], ring[k]))
        pts_prev = ring
    # 根本キャップ
    root_ring = ring_at(bx, by, bz, r)
    for k in range(segs):
        kk = (k+1) % segs
        tris.append(((bx, by, bz), root_ring[kk], root_ring[k]))

    # --- 先端カール部分 (Y-Z平面内で上向きに曲げる) ---
    # 円弧中心: 直線部の終端から curl_r だけ +Y にオフセット
    z_straight_end = bz + straight_len
    cy_center, cz_center = by + curl_r, z_straight_end
    for i in range(1, n_curl+1):
        a = -math.pi/2 + (math.pi/2) * i / n_curl  # -90°(直線終端) -> 0°(真上向き)
        cy_ = cy_center + curl_r * math.sin(a)
        cz_ = cz_center + curl_r * math.cos(a)
        rad = r * (1.0 - 0.25 * (i / n_curl))
        ring = ring_at(bx, cy_, cz_, rad)
        for k in range(segs):
            kk = (k+1) % segs
            tris.append((pts_prev[k], pts_prev[kk], ring[kk]))
            tris.append((pts_prev[k], ring[kk], ring[k]))
        pts_prev = ring

    # 先端キャップ
    tip_center = (bx, cy_center + curl_r, cz_center)
    for k in range(segs):
        kk = (k+1) % segs
        tris.append((tip_center, pts_prev[k], pts_prev[kk]))

    return tris


if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "models")
    out_path = os.path.join(out_dir, "iron_wall_holder.stl")

    print("ヘアアイロン用 壁掛けホルダー を生成中...")
    tris = generate()
    write_stl(tris, out_path, name="iron_wall_holder")

    print("""
=== 印刷設定 (推奨) ===
  フィラメント : PETG (耐荷重性) または PLA
  レイヤー高さ : 0.20mm
  インフィル   : 30〜40%
  サポート     : なし (背面スロット側をベッドに接地させて印刷)
  壁ループ数   : 3〜4

=== 使い方 ===
  1. 前面のペグにアイロンの持ち手の輪 (ピボット部) を掛ける
  2. 右側のバーにコードを巻きつける
  3. 背面スロット (すき間 3mm, カード2枚分目安) に棚やカゴの薄いへりを
     上から挟み込んで掛ける

  ※ へりの厚みが 3mm と合わない場合は generate() の slot_gap 引数を調整して再生成してください。
""")
