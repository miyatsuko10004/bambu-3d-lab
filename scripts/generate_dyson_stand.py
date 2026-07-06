#!/usr/bin/env python3
"""
Dyson Supersonic ドライヤースタンド (置き型・ハンドル下向き)
Bambu Lab A1 mini 向け STL生成スクリプト

パーツ構成:
  Part 1: ベースプレート (150x150x10mm) → dyson_stand_base.stl
  Part 2: ポスト + ハンドルソケット    → dyson_stand_post.stl

結合方法: ベース中央のボスにポスト底部のペグを差し込み、
          M3 ネジ x2 で固定 (ネジ穴径 3.2mm)

Dyson Supersonic ハンドル外径: 約 78mm
ソケット内径: 82mm (2mm クリアランス)
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

def ring_pts(cx, cy, z, r, segs):
    a = [2*math.pi*i/segs for i in range(segs)]
    return [(cx+r*math.cos(t), cy+r*math.sin(t), z) for t in a]

def cylinder_tris(cx, cy, z0, z1, r, segs=32, cap_bot=True, cap_top=True):
    tris = []
    pb = ring_pts(cx, cy, z0, r, segs)
    pt = ring_pts(cx, cy, z1, r, segs)
    cb = (cx, cy, z0)
    ct = (cx, cy, z1)
    for i in range(segs):
        j = (i+1) % segs
        if cap_bot:
            tris.append((cb, pb[j], pb[i]))
        if cap_top:
            tris.append((ct, pt[i], pt[j]))
        tris.append((pb[i], pb[j], pt[j]))
        tris.append((pb[i], pt[j], pt[i]))
    return tris

def tube_tris(cx, cy, z0, z1, r_in, r_out, segs=48):
    """中空円筒 (チューブ)"""
    tris = []
    po = ring_pts(cx, cy, z0, r_out, segs)
    pi = ring_pts(cx, cy, z0, r_in, segs)
    Po = ring_pts(cx, cy, z1, r_out, segs)
    Pi = ring_pts(cx, cy, z1, r_in, segs)
    for i in range(segs):
        j = (i+1) % segs
        # 底面 (アニュラス)
        tris.append((po[i], pi[i], po[j]))
        tris.append((pi[i], pi[j], po[j]))
        # 上面
        tris.append((Po[i], Po[j], Pi[i]))
        tris.append((Pi[i], Po[j], Pi[j]))
        # 外側面
        tris.append((po[i], po[j], Po[j]))
        tris.append((po[i], Po[j], Po[i]))
        # 内側面
        tris.append((pi[j], pi[i], Pi[i]))
        tris.append((pi[j], Pi[i], Pi[j]))
    return tris

def box_tris(x0, y0, z0, x1, y1, z1):
    def q(a, b, c, d): return [(a,b,c),(a,c,d)]
    tris = []
    tris += q((x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1))  # top
    tris += q((x0,y1,z0),(x1,y1,z0),(x1,y0,z0),(x0,y0,z0))  # bot
    tris += q((x0,y0,z0),(x1,y0,z0),(x1,y0,z1),(x0,y0,z1))  # front
    tris += q((x1,y1,z0),(x0,y1,z0),(x0,y1,z1),(x1,y1,z1))  # back
    tris += q((x0,y1,z0),(x0,y0,z0),(x0,y0,z1),(x0,y1,z1))  # left
    tris += q((x1,y0,z0),(x1,y1,z0),(x1,y1,z1),(x1,y0,z1))  # right
    return tris

def rounded_plate_tris(x0, y0, z0, x1, y1, z1, r, segs=8):
    """上下フラット・四隅R付き板"""
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

def subtract_cylinder_from_plate(plate_tris, cx, cy, z0, z1, r, segs=32):
    """
    板からの円柱くり抜きを近似: 実際のCSGは使えないため
    穴の縁にチューブを追加し、内側面で表現する簡易実装。
    ここでは穴の内壁 + 上面アニュラスのみ生成 (板の底面は閉じたまま)。
    """
    tris = []
    pi_pts = ring_pts(cx, cy, z0, r, segs)
    po_pts_top = ring_pts(cx, cy, z1, r+0.01, segs)  # 上面外縁
    pi_pts_top = ring_pts(cx, cy, z1, r, segs)
    center_top = (cx, cy, z1)
    # 穴の内壁 (下から上)
    pi_bot = ring_pts(cx, cy, z0, r, segs)
    pi_top = ring_pts(cx, cy, z1, r, segs)
    for i in range(segs):
        j = (i+1) % segs
        tris.append((pi_bot[j], pi_bot[i], pi_top[i]))
        tris.append((pi_bot[j], pi_top[i], pi_top[j]))
    return tris

# ---------------------------------------------------------------------------
# Part 1: ベースプレート
# ---------------------------------------------------------------------------

def generate_base(
    bw=150.0,    # 幅
    bd=150.0,    # 奥行き
    bh=10.0,     # 高さ
    br=8.0,      # コーナーR
    boss_r=15.0, # ポスト受けボス外径
    boss_h=8.0,  # ボス高さ
    peg_r=9.0,   # アライメントペグ穴内径
    hole_r=1.6,  # M3 ネジ穴半径 (3.2mm 径)
    hole_offset=25.0, # ネジ穴の中心からの距離
):
    tris = []
    cx, cy = bw/2, bd/2

    # ベース板 (底面 z=0 〜 bh)
    tris += rounded_plate_tris(0, 0, 0, bw, bd, bh, br, segs=8)

    # 中央ボス (ポスト受け): z=bh 〜 bh+boss_h
    # ボス外筒
    tris += cylinder_tris(cx, cy, bh, bh+boss_h, boss_r, segs=32, cap_bot=False, cap_top=False)
    # ボス上面アニュラス (peg穴)
    tris += tube_tris(cx, cy, bh+boss_h, bh+boss_h+0.001, peg_r, boss_r, segs=32)

    # ボスと板の間を閉じる底面アニュラス
    tris += tube_tris(cx, cy, bh, bh+0.001, peg_r, boss_r, segs=32)

    # ペグ穴の内壁
    tris += [t for t in cylinder_tris(cx, cy, bh, bh+boss_h, peg_r, segs=32, cap_bot=True, cap_top=True)
             if True]  # 穴なので内壁は外側向きの法線を反転
    # 穴の内壁 (法線を内向きに: v1,v2,v3 を逆順)
    peg_inner = cylinder_tris(cx, cy, bh, bh+boss_h, peg_r, segs=32, cap_bot=False, cap_top=False)
    tris += [(v3, v2, v1) for v1, v2, v3 in peg_inner]

    # ネジ穴 (M3): ベース板を貫通する穴の内壁
    for dx, dy in [(hole_offset, 0), (-hole_offset, 0)]:
        hx, hy = cx+dx, cy+dy
        inner = cylinder_tris(hx, hy, 0, bh, hole_r, segs=16, cap_bot=False, cap_top=False)
        tris += [(v3, v2, v1) for v1, v2, v3 in inner]
        # 穴の上面 (皿部) - 小さいアニュラス
        tris += tube_tris(hx, hy, bh-0.001, bh, hole_r, hole_r+0.001, segs=16)

    # 底面の滑り止めフット (四隅に小さいバンプ)
    foot_r = 5.0
    foot_h = 1.5
    for fx, fy in [(br+5, br+5), (bw-br-5, br+5), (bw-br-5, bd-br-5), (br+5, bd-br-5)]:
        tris += cylinder_tris(fx, fy, 0, foot_h, foot_r, segs=16, cap_bot=False, cap_top=True)
        side = cylinder_tris(fx, fy, 0, foot_h, foot_r, segs=16, cap_bot=False, cap_top=False)
        tris += side

    return tris


# ---------------------------------------------------------------------------
# Part 2: ポスト + ハンドルソケット
# ---------------------------------------------------------------------------

def generate_post(
    post_r=22.5,     # ポスト外径 (45mm)
    post_h=80.0,     # ポスト高さ
    peg_r=8.5,       # アライメントペグ半径 (ベース穴 9mm - 0.5mm クリアランス)
    peg_h=8.0,       # ペグ高さ (ベースボスと同じ)
    socket_r_in=41.0,  # ソケット内径 (82mm / 2)
    socket_r_out=52.0, # ソケット外径 (104mm / 2)
    socket_h=45.0,   # ソケット深さ
    hole_r=1.6,      # M3 ネジ穴半径
    hole_offset=25.0,
):
    tris = []
    cx, cy = 0.0, 0.0
    z_peg_top = peg_h
    z_post_top = peg_h + post_h

    # --- アライメントペグ (下方向) ---
    tris += cylinder_tris(cx, cy, 0, z_peg_top, peg_r, segs=32)

    # --- ポスト本体 ---
    tris += cylinder_tris(cx, cy, z_peg_top, z_post_top, post_r, segs=32)

    # --- ハンドルソケット (チューブ状) ---
    # ソケット下面 (プレート): ポスト上部と繋がるアニュラス
    tris += tube_tris(cx, cy, z_post_top, z_post_top + socket_h, socket_r_in, socket_r_out, segs=48)

    # ソケット底面 (ハンドル先端が当たる面) = ソケット上面アニュラスは既に tube_tris に含まれる
    # ソケット底面のアニュラスとポストの上面をつなぐ
    # post外縁 (r=post_r) → socket外縁 (r=socket_r_out) の肩部分
    pb_out = ring_pts(cx, cy, z_post_top, socket_r_out, 48)
    pb_post = ring_pts(cx, cy, z_post_top, post_r, 48)
    # 肩 (アニュラス on z_post_top, from post_r to socket_r_out)
    for i in range(48):
        j = (i+1) % 48
        tris.append((pb_post[i], pb_post[j], pb_out[j]))
        tris.append((pb_post[i], pb_out[j], pb_out[i]))

    # ポスト上面 (post_r 内側の円)
    ct = (cx, cy, z_post_top)
    pp = ring_pts(cx, cy, z_post_top, post_r, 32)
    for i in range(32):
        j = (i+1) % 32
        tris.append((ct, pp[i], pp[j]))

    # --- ネジ穴 (M3) ペグ部分を貫通 ---
    for dx, dy in [(hole_offset, 0), (-hole_offset, 0)]:
        hx, hy = cx+dx, cy+dy
        inner = cylinder_tris(hx, hy, 0, peg_h, hole_r, segs=16, cap_bot=True, cap_top=False)
        tris += [(v3, v2, v1) for v1, v2, v3 in inner]

    # --- ケーブル逃げ溝 (ソケット側面に切り欠き) ---
    # ポスト正面に 15mm 幅 x 30mm 高さの切り欠きを近似 (box で追加、CSGなし)
    # 代わりにケーブルガイドリブを追加
    notch_w = 8.0
    notch_h = 20.0
    notch_z0 = z_post_top + socket_h * 0.3
    # ソケット外壁のケーブル逃げ用リブ (ガイド)
    for sign in [1, -1]:
        rx = cx + sign * (socket_r_out + 2)
        ry = cy
        tris += box_tris(rx - 3, ry - notch_w/2, notch_z0,
                         rx + 3, ry + notch_w/2, notch_z0 + notch_h)

    return tris


# ---------------------------------------------------------------------------
# エントリポイント
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "models")

    print("Dyson Supersonic スタンド - ベース 生成中...")
    tris_base = generate_base()
    write_stl(tris_base, os.path.join(out_dir, "dyson_stand_base.stl"), "dyson_stand_base")

    print("Dyson Supersonic スタンド - ポスト+ソケット 生成中...")
    tris_post = generate_post()
    write_stl(tris_post, os.path.join(out_dir, "dyson_stand_post.stl"), "dyson_stand_post")

    print("""
=== パーツ一覧 ===
  dyson_stand_base.stl : ベースプレート (150x150x10mm + ボス)
  dyson_stand_post.stl : ポスト+ソケット (高さ約133mm, 最大幅104mm)

=== 組み立て方法 ===
  1. ポストのペグをベースのボス穴に差し込む
  2. M3 x 12mm ネジ x2 本でベース裏から固定
  3. Dyson Supersonic のハンドルをソケットに差し込んで完成

=== 印刷設定 (推奨) ===
  フィラメント : PETG (強度・耐久性) または PLA
  レイヤー高さ : 0.20mm
  インフィル   : 40% (ジャイロイド)
  サポート     : なし (ベース・ポストとも不要)
  壁ループ数   : 4 (ソケット強度のため)
""")
