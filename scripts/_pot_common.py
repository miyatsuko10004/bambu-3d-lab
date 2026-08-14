#!/usr/bin/env python3
"""
植木鉢モデル共通ジオメトリ・ヘルパー
generate_industrial_planter.py / generate_knit_planter.py から import される。

三角形は全て (v1, v2, v3) の頂点タプルのリストとして表現し、
write_stl() が法線を頂点の巻き順から再計算して書き出す
（このリポジトリの他スクリプトと同じ流儀）。
"""

import math
import os
import random


# ---------------------------------------------------------------------------
# セル状 (Voronoi/ハンマード) テクスチャ・エンジン
# ---------------------------------------------------------------------------
#
# 円筒展開座標 s (= 円周方向の弧長, 0..circumference, 周期的) と z (高さ) の
# 平面上に、ジッター付きグリッドでVoronoi種点をばら撒き、各サンプル点ごとに
# 最近傍種点を検索する。用途に応じて2つのモードを提供する:
#   - groove モード: セル境界に溝、セル内部が平坦なプラトー (有機的な石垣/粘土風)
#   - facet モード : 種点ごとにランダムな傾斜平面を割り当てブレンド
#                    (ハンマード/低ポリ風、黒色フィラメントでも陰影が残る)
#
# 検索は種点をバケツ (セルサイズ幅) に分割し、周辺3x3バケツのみを走査する
# ことで、種点数百・サンプル数万でも実用的な時間で計算できるようにしている。


def smoothstep(edge0, edge1, x):
    if edge1 <= edge0:
        return 1.0 if x >= edge1 else 0.0
    t = min(1.0, max(0.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3 - 2 * t)


def wrapped_ds(s_a, s_b, circumference):
    """円周方向の符号付き最短差分 (-circumference/2 .. circumference/2)"""
    d = (s_a - s_b) % circumference
    if d > circumference / 2:
        d -= circumference
    return d


def make_cell_seeds(circumference, z0, z1, cell_size, jitter_frac, rng_seed):
    """
    ジッター付きグリッドで種点をばら撒く (完全ランダムだと種点が偏って
    大きすぎる/潰れたセルができるため、規則グリッド+小さな乱数ずらしで
    「意図的だが不規則」な配置にする)。各種点には facet モード用の
    ランダムな高さ・傾斜も付与する。
    """
    rng = random.Random(rng_seed)
    cols = max(4, round(circumference / cell_size))
    rows = max(2, round((z1 - z0) / cell_size))
    dx = circumference / cols
    dy = (z1 - z0) / rows

    seeds = []
    for c in range(cols):
        for r in range(rows):
            s = (c + 0.5) * dx + (rng.random() - 0.5) * 2 * jitter_frac * dx
            z = z0 + (r + 0.5) * dy + (rng.random() - 0.5) * 2 * jitter_frac * dy
            s %= circumference
            z = min(z1, max(z0, z))
            h = rng.uniform(0.3, 1.0)          # facetモード用: 相対的な高さ (0..1、後でamplitude倍する)
            gx = rng.uniform(-0.5, 0.5)         # facetモード用: s方向の傾斜
            gy = rng.uniform(-0.5, 0.5)         # facetモード用: z方向の傾斜
            seeds.append({"s": s, "z": z, "h": h, "gx": gx, "gy": gy})
    return seeds, cols, dy


class SeedGrid:
    """種点をバケツに分割し、近傍検索を高速化するための索引構造。"""

    def __init__(self, seeds, circumference, cell_size, ncols):
        self.seeds = seeds
        self.circumference = circumference
        self.ncols = ncols
        self.cell_size = cell_size
        self.buckets = {}
        for idx, sd in enumerate(seeds):
            c = int(sd["s"] / circumference * ncols) % ncols
            r = math.floor(sd["z"] / cell_size)
            self.buckets.setdefault((c, r), []).append(idx)

    def nearby_indices(self, s, z):
        c = int(s / self.circumference * self.ncols) % self.ncols
        r = math.floor(z / self.cell_size)
        out = []
        for dc in (-1, 0, 1):
            for dr in (-1, 0, 1):
                out.extend(self.buckets.get(((c + dc) % self.ncols, r + dr), []))
        return out

    def nearest(self, s, z, k):
        """(距離, 種点) のリストを距離昇順でk件返す (周辺バケツで足りなければ全走査にフォールバック)"""
        idxs = self.nearby_indices(s, z)
        if len(idxs) < k + 1:
            idxs = range(len(self.seeds))
        dists = []
        for i in idxs:
            sd = self.seeds[i]
            ds = wrapped_ds(s, sd["s"], self.circumference)
            dz = z - sd["z"]
            dists.append((math.hypot(ds, dz), sd, ds, dz))
        dists.sort(key=lambda x: x[0])
        return dists[:k]


def voronoi_groove_height(s, z, grid, amplitude, edge_width):
    """
    Voronoi溝モード: セル境界 (最近傍2点の距離差が0の場所) で0、
    セル内部に向かって滑らかにamplitudeまで盛り上がるプラトーを作る。
    """
    nearest2 = grid.nearest(s, z, 2)
    if len(nearest2) < 2:
        return amplitude
    d1 = nearest2[0][0]
    d2 = nearest2[1][0]
    return amplitude * smoothstep(0.0, edge_width, d2 - d1)


def hammered_facet_height(s, z, grid, amplitude, beta, cell_size, k=6):
    """
    facetモード: 近傍k種点それぞれに割り当てたランダム傾斜平面を、
    距離に応じたsoftmax重みでブレンドする。各セルの大部分は単一の
    種点の平面が支配的 (=平らなファセット)、境界付近だけ複数の平面が
    混ざり合い、面同士がぶつかる「稜線」ができる。

    sd["gx"]/sd["gy"] は無次元の傾き係数 (-0.5..0.5)。種点からセル境界
    相当の距離 (cell_size/2) 離れた場所でようやく ±0.5 (= h と同スケール)
    寄与するよう正規化することで、遠くの点を評価しても平面が暴走せず
    局所勾配が有界に保たれる。
    """
    nearest = grid.nearest(s, z, k)
    if not nearest:
        return 0.0
    weights = [math.exp(-beta * d[0]) for d in nearest]
    wsum = sum(weights)
    half_cell = max(cell_size * 0.5, 1e-6)
    total = 0.0
    for (dist, sd, ds, dz), w in zip(nearest, weights):
        plane = sd["h"] + (sd["gx"] * ds + sd["gy"] * dz) / half_cell
        total += w * plane
    blended = (total / wsum) * amplitude
    return min(amplitude, max(0.0, blended))


# ---------------------------------------------------------------------------
# 伝統文様 (市松 / 麻の葉 / 七宝) テクスチャ・エンジン
# ---------------------------------------------------------------------------
#
# Voronoi/ハンマードと違い、伝統文様は「意図的に規則的」であることが本質
# (不規則さは不要、むしろ規則性がそのまま柄の識別性になる)。
# 周方向は弧長近似ではなくtheta自体を整数分割で周期化し、theta=0の継ぎ目で
# 柄がずれないようにする。


def dist_point_to_segment(px, py, ax, ay, bx, by):
    """点(px,py)から線分(ax,ay)-(bx,by)までの最短距離"""
    dx, dy = bx - ax, by - ay
    l2 = dx * dx + dy * dy
    if l2 < 1e-12:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / l2))
    cx, cy = ax + t * dx, ay + t * dy
    return math.hypot(px - cx, py - cy)


def checkerboard_relief(col, row, cell_size_mm, amplitude, edge_width_mm):
    """
    市松 (いちまつ) 模様: col, row はセル単位の連続座標 (整数値がセルの境界)。
    チェビシェフ距離 (正方形の境界までの距離) に市松の符号 (パリティ) を
    掛けた符号付き距離を作り、それをsmoothstepするだけで境界を跨いでも
    連続 (パリティが反転する瞬間、距離が必ず0に収束するため)。
    col方向のセル数は必ず偶数にすること (奇数だとtheta=0の継ぎ目で
    同じパリティ同士が隣接し、市松の連続性が崩れる)。
    """
    fc = col - math.floor(col) - 0.5
    fr = row - math.floor(row) - 0.5
    d_edge = 0.5 - max(abs(fc), abs(fr))  # セル単位, 0 (境界) .. 0.5 (中心)
    parity = (math.floor(col) + math.floor(row))
    sign = 1.0 if parity % 2 == 0 else -1.0
    signed_d_mm = sign * d_edge * cell_size_mm
    return amplitude * smoothstep(-edge_width_mm, edge_width_mm, signed_d_mm)


def make_hex_centers(circumference, z0, z1, hex_r):
    """
    麻の葉パターン用の正六角形タイリングの中心点を、円周方向theta(弧長で近似)
    に沿って規則正しく (ジッターなし) 配置する。
    """
    spacing_s = hex_r * math.sqrt(3)
    spacing_z = hex_r * 1.5
    cols = max(4, round(circumference / spacing_s))
    spacing_s = circumference / cols  # 円周にちょうど整数個収まるよう補正
    rows = max(2, round((z1 - z0) / spacing_z))
    spacing_z = (z1 - z0) / rows

    seeds = []
    for r in range(rows + 1):
        row_offset = (spacing_s / 2.0) if (r % 2 == 1) else 0.0
        for c in range(cols):
            s = (c * spacing_s + row_offset) % circumference
            z = z0 + r * spacing_z
            seeds.append({"s": s, "z": z})
    return seeds, cols, spacing_z


def asanoha_height(s, z, grid, circumference, hex_r, amplitude, line_width, k=7):
    """
    麻の葉 (あさのは) 模様: 各正六角形の中心から6頂点への「放射スポーク」と
    六角形の「辺」を線分として持ち、最も近い線分までの距離が近いほど
    盛り上がるリッジを作る。周期境界(s方向)はwrapped_dsで最寄りのコピーに
    平行移動してから平面上の距離計算を行う。
    """
    nearest = grid.nearest(s, z, k)
    if not nearest:
        return 0.0
    min_dist = None
    for dist, sd, ds, dz in nearest:
        # このseed(六角形の中心)を、クエリ点に最も近い方の円周コピーへ平行移動
        cx = s - ds
        cy = sd["z"]
        verts = [
            (cx + hex_r * math.cos(math.pi / 3 * kk), cy + hex_r * math.sin(math.pi / 3 * kk))
            for kk in range(6)
        ]
        for kk in range(6):
            vx, vy = verts[kk]
            # スポーク: 中心 -> 頂点
            d = dist_point_to_segment(s, z, cx, cy, vx, vy)
            if min_dist is None or d < min_dist:
                min_dist = d
            # 辺: 頂点kk -> 頂点kk+1
            nx, ny = verts[(kk + 1) % 6]
            d = dist_point_to_segment(s, z, vx, vy, nx, ny)
            if min_dist is None or d < min_dist:
                min_dist = d
    return amplitude * (1.0 - smoothstep(0.0, line_width, min_dist))


def shippou_height(s, z, circumference, grid_spacing, radius, amplitude, line_width):
    """
    七宝 (しっぽう) 模様: 正方格子の各格子点を中心とする円を重ねて描き、
    円周線 (中心までの距離がradiusに近い場所) を盛り上げる。距離場が
    円との距離だけで書けるため、伝統文様の中では最も軽量。
    """
    cols = max(4, round(circumference / grid_spacing))
    spacing_s = circumference / cols
    ci = round(s / spacing_s)
    cj = round(z / grid_spacing)
    min_ring_dist = None
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            cs = ((ci + di) * spacing_s) % circumference
            cz = (cj + dj) * grid_spacing
            ds = wrapped_ds(s, cs, circumference)
            dz = z - cz
            d = math.hypot(ds, dz)
            ring_d = abs(d - radius)
            if min_ring_dist is None or ring_d < min_ring_dist:
                min_ring_dist = ring_d
    return amplitude * (1.0 - smoothstep(0.0, line_width, min_ring_dist))


# ---------------------------------------------------------------------------
# STL ユーティリティ
# ---------------------------------------------------------------------------

def cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def normalize(v):
    l = math.sqrt(sum(x * x for x in v))
    return (0.0, 0.0, 1.0) if l == 0 else tuple(x / l for x in v)


def facet_normal(v1, v2, v3):
    u = tuple(v2[i] - v1[i] for i in range(3))
    v = tuple(v3[i] - v1[i] for i in range(3))
    return normalize(cross(u, v))


def facet_area2(v1, v2, v3):
    """面積の2倍 (縮退三角形の判定用、実際のnormalize前のcross長)"""
    u = tuple(v2[i] - v1[i] for i in range(3))
    v = tuple(v3[i] - v1[i] for i in range(3))
    c = cross(u, v)
    return math.sqrt(sum(x * x for x in c))


def write_stl(triangles, filepath, name="model", min_area2=1e-9):
    """縮退三角形 (面積がほぼ0) を除外してASCII STLを書き出す"""
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    written = 0
    with open(filepath, "w") as f:
        f.write(f"solid {name}\n")
        for v1, v2, v3 in triangles:
            if facet_area2(v1, v2, v3) < min_area2:
                continue
            n = facet_normal(v1, v2, v3)
            f.write(f"  facet normal {n[0]:.6f} {n[1]:.6f} {n[2]:.6f}\n")
            f.write("    outer loop\n")
            for v in (v1, v2, v3):
                f.write(f"      vertex {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
            f.write("    endloop\n  endfacet\n")
            written += 1
        f.write(f"endsolid {name}\n")
    print(f"  -> {filepath} ({written} triangles)")
    return written


def write_stl_binary(triangles, filepath, name="model", min_area2=1e-9):
    """
    バイナリSTLを書き出す (依存ライブラリなし、標準structモジュールのみ)。
    ASCII形式に比べておよそ1/5のファイルサイズになるため、細線パターン
    (麻の葉など) で解像度を上げた際のファイル肥大化を避けるために使う。
    """
    import struct

    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    kept = [(v1, v2, v3) for v1, v2, v3 in triangles if facet_area2(v1, v2, v3) >= min_area2]

    with open(filepath, "wb") as f:
        header = name.encode("utf-8")[:80]
        header = header + b"\x00" * (80 - len(header))
        f.write(header)
        f.write(struct.pack("<I", len(kept)))
        for v1, v2, v3 in kept:
            n = facet_normal(v1, v2, v3)
            f.write(struct.pack("<3f", *n))
            f.write(struct.pack("<3f", *v1))
            f.write(struct.pack("<3f", *v2))
            f.write(struct.pack("<3f", *v3))
            f.write(struct.pack("<H", 0))
    print(f"  -> {filepath} ({len(kept)} triangles, binary)")
    return len(kept)


def signed_volume_cm3(triangles):
    """閉曲面 (watertight) な三角形リストの符号付き体積 [cm^3] を返す。
    法線の向きが正しく外向きなら正の値になる健全性チェック用。
    底面が開いているシェル (鉢の排水口など) には使わない。"""
    vol_mm3 = 0.0
    for v1, v2, v3 in triangles:
        vol_mm3 += (
            v1[0] * (v2[1] * v3[2] - v2[2] * v3[1])
            - v1[1] * (v2[0] * v3[2] - v2[2] * v3[0])
            + v1[2] * (v2[0] * v3[1] - v2[1] * v3[0])
        ) / 6.0
    return vol_mm3 / 1000.0


# ---------------------------------------------------------------------------
# 回転体 (revolve) ヘルパー
# ---------------------------------------------------------------------------

def revolve_side(r_func, z0_func, z1, M, N, outward=True):
    """
    r_func(theta, z) -> 半径, z0_func(theta) -> 局所的な下端Z (通常は0だが、
    脚のアーチ形状など角度依存の下端を表現できる) を使い、Z1 (上端, 一定) まで
    M分割・N分割で回転体側面を生成する。

    outward=True: 法線が半径方向外向き (外壁用)
    outward=False: 法線が半径方向内向き (内壁用)

    戻り値: (triangles, bottom_ring, top_ring)
    """
    rings = []
    for i in range(M + 1):
        t = i / M
        ring = []
        for j in range(N):
            theta = 2 * math.pi * j / N
            z0 = z0_func(theta)
            z = z0 + (z1 - z0) * t
            r = r_func(theta, z)
            ring.append((r * math.cos(theta), r * math.sin(theta), z))
        rings.append(ring)

    tris = []
    for i in range(M):
        for j in range(N):
            jn = (j + 1) % N
            a, b = rings[i][j], rings[i][jn]
            c, d = rings[i + 1][j], rings[i + 1][jn]
            if outward:
                tris.append((a, b, d))
                tris.append((a, d, c))
            else:
                tris.append((a, d, b))
                tris.append((a, c, d))
    return tris, rings[0], rings[-1]


def annulus_cap(outer_ring, inner_ring, upward):
    """同じ角度分割数Nを持つ2つの円環リング間を塞ぐ平面 (キャップ) を生成する。"""
    N = len(outer_ring)
    tris = []
    for j in range(N):
        jn = (j + 1) % N
        o, on = outer_ring[j], outer_ring[jn]
        ii, iin = inner_ring[j], inner_ring[jn]
        if upward:
            tris.append((o, iin, ii))
            tris.append((o, on, iin))
        else:
            tris.append((o, ii, iin))
            tris.append((o, iin, on))
    return tris


def extrude_polygon(poly2d, z0, z1):
    """
    反時計回り (CCW, +Zから見て) に並んだ2D多角形 poly2d を、
    重心からの扇形分割でZ方向 (z0..z1) に押し出す。
    (グレーチングのスポーク・ハブなど、星型/凸多角形に使う)
    """
    n = len(poly2d)
    cx = sum(p[0] for p in poly2d) / n
    cy = sum(p[1] for p in poly2d) / n
    top = [(p[0], p[1], z1) for p in poly2d]
    bot = [(p[0], p[1], z0) for p in poly2d]
    ctop = (cx, cy, z1)
    cbot = (cx, cy, z0)

    tris = []
    for i in range(n):
        j = (i + 1) % n
        tris.append((ctop, top[i], top[j]))       # 上面 (法線 上向き)
        tris.append((cbot, bot[j], bot[i]))        # 底面 (法線 下向き)
        tris.append((bot[i], bot[j], top[j]))      # 側面
        tris.append((bot[i], top[j], top[i]))      # 側面
    return tris


def frustum_triangles(cx, cy, z0, z1, r0, r1, segs=16):
    """円錐台 (r0==r1なら円柱)。上下キャップ込みの閉じたソリッドを返す。"""
    angles = [2 * math.pi * i / segs for i in range(segs)]
    bot = [(cx + r0 * math.cos(a), cy + r0 * math.sin(a), z0) for a in angles]
    top = [(cx + r1 * math.cos(a), cy + r1 * math.sin(a), z1) for a in angles]
    cbot = (cx, cy, z0)
    ctop = (cx, cy, z1)
    tris = []
    for i in range(segs):
        j = (i + 1) % segs
        tris.append((ctop, top[i], top[j]))
        tris.append((cbot, bot[j], bot[i]))
        tris.append((bot[i], bot[j], top[j]))
        tris.append((bot[i], top[j], top[i]))
    return tris


def annular_ring(r_outer, r_inner, z0, z1, N):
    """厚みのある円環 (ドーナツ状の短い筒)。グレーチングの同心円リング用。"""
    outer_tris, obot, otop = revolve_side(
        lambda th, z: r_outer, lambda th: z0, z1, 1, N, outward=True
    )
    inner_tris, ibot, itop = revolve_side(
        lambda th, z: r_inner, lambda th: z0, z1, 1, N, outward=False
    )
    tris = outer_tris + inner_tris
    tris += annulus_cap(obot, ibot, upward=False)
    tris += annulus_cap(otop, itop, upward=True)
    return tris


def spoke_wheel_grate(rim_r, hub_r, z0, z1, n_spokes, spoke_half_angle, ring_radii=()):
    """
    リム (rim_r) からハブ (hub_r) へ放射状スポークを渡す「グレーチング(排水口)」を生成。
    各スポークはリム側で固定支持され、ハブは全スポークが収束する中心で
    自己支持される (橋渡しはスポーク1本分の直線距離のみ、FDMで無支持印刷可能)。
    ring_radii: スポークに重ねる同心円リング (メッシュ感の演出、任意)。
    """
    tris = []

    # ハブ (中心の円盤)
    tris += frustum_triangles(0.0, 0.0, z0, z1, hub_r, hub_r, segs=max(12, n_spokes * 2))

    # スポーク (リムからハブへの放射状の帯)
    for k in range(n_spokes):
        angle = 2 * math.pi * k / n_spokes
        a0 = angle - spoke_half_angle
        a1 = angle + spoke_half_angle
        poly = [
            (hub_r * math.cos(a0), hub_r * math.sin(a0)),
            (rim_r * math.cos(a0), rim_r * math.sin(a0)),
            (rim_r * math.cos(a1), rim_r * math.sin(a1)),
            (hub_r * math.cos(a1), hub_r * math.sin(a1)),
        ]
        tris += extrude_polygon(poly, z0, z1)

    # 同心円リング (メッシュの見た目・強度補強、スポークと橋渡し不要な高さに配置)
    for r in ring_radii:
        if hub_r < r < rim_r:
            tris += annular_ring(r + 0.6, r - 0.6, z0, z1, N=max(48, n_spokes * 8))

    return tris


def build_planter_shell(
    r_body,
    texture_dr,
    foot_z0,
    height,
    wall_t,
    N,
    M,
    M_inner,
    grate_z0,
    grate_thick,
    grate_spokes,
    grate_hub_r=4.0,
    grate_spoke_half_angle=0.13,
    grate_ring_frac=0.55,
):
    """
    植木鉢の「外壁(テクスチャ付き)+内壁+リム+排水グレーチング」一式を組み立てる
    共通ビルダー。r_body(z)がシルエット、texture_dr(theta,z)が表面模様
    (常に0以上、外側にのみ加算)、foot_z0(theta)が脚アーチの局所下端高さ
    (脚なしの場合は `lambda theta: 0.0` を渡す)。

    industrial_planter.py / knit_planter.py は独自にこの組み立てをインライン
    で行っている (先に実装したv1/v2からの経緯) が、市松/麻の葉/七宝の3種は
    この共通ビルダー経由で組み立てる。
    """

    def r_outer(theta, z):
        return r_body(z) + texture_dr(theta, z)

    def r_inner(theta, z):
        return r_body(z) - wall_t

    tris = []
    outer_tris, outer_bot, outer_top = revolve_side(r_outer, foot_z0, height, M, N, outward=True)
    tris += outer_tris

    inner_tris, inner_bot, inner_top = revolve_side(r_inner, foot_z0, height, M_inner, N, outward=False)
    tris += inner_tris

    tris += annulus_cap(outer_top, inner_top, upward=True)

    inner_r_at_grate = r_body(grate_z0) - wall_t
    rim_r = inner_r_at_grate + 0.6
    tris += spoke_wheel_grate(
        rim_r=rim_r,
        hub_r=grate_hub_r,
        z0=grate_z0,
        z1=grate_z0 + grate_thick,
        n_spokes=grate_spokes,
        spoke_half_angle=grate_spoke_half_angle,
        ring_radii=[rim_r * grate_ring_frac],
    )

    return tris, r_outer


def verify_overhang(r_outer, height, max_angle_deg=50.0, samples_theta=200, samples_z=300):
    """profile+textureを合成した実際の外壁関数を有限差分でサンプルし、
    最大の「半径が広がる方向」の勾配が安全域に収まっているか数値検証する。
    細線パターン(麻の葉等)は最悪点が局所的なので、theta方向のサンプル数を
    多め (デフォルト200) に取る。"""
    dz = height / samples_z
    max_slope = 0.0
    worst = None
    for zi in range(samples_z):
        z = zi * dz
        for ti in range(samples_theta):
            theta = 2 * math.pi * ti / samples_theta
            r0 = r_outer(theta, z)
            r1 = r_outer(theta, min(height, z + dz))
            slope = (r1 - r0) / dz
            if slope > max_slope:
                max_slope = slope
                worst = (theta, z)
    angle = math.degrees(math.atan(max_slope))
    print(f"  オーバーハング検証: 最大勾配={max_slope:.3f} (角度 {angle:.1f}°, 安全域 <{max_angle_deg}°) at z≈{worst[1]:.1f}mm")
    if angle >= max_angle_deg:
        print("  !! 警告: 安全域を超えています。テクスチャ振幅/シルエットを調整してください。")
    return angle

    return tris
