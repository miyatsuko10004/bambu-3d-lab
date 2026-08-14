#!/usr/bin/env python3
"""
ナチュラル/パラメトリック系 観葉植物用 植木鉢 (Organic Voronoi-cell Planter)
Bambu Lab A1 mini 向け STL生成スクリプト

設計仕様 (プロトタイプ v2):
  - 4号相当 (最大直径 120mm, 高さ 116mm)
  - 単色印刷想定 (マット白 / テラコッタ)
  - 壁面: Voronoi風にばら撒いた種点から「セル境界に溝、セル内部が
          プラトー」の有機的なセルテクスチャを生成 (v1の規則的な
          ヘリカル干渉=ゴルフボール状ディンプルから、MakerWorldの
          人気デザイン(Voronoi)を参考に刷新。「編み目/ニット」というより
          石垣・粘土の肌に近い、不規則で有機的な質感)
  - シルエット: 丸みのある樽型プロファイル (下部から膨らみ、リムに向けて
          すぼまる)。膨らみのピーク位置とセルテクスチャの遷移幅は、
          プロファイル勾配+テクスチャ勾配の合成オーバーハングを数値検証
          しながら決定 (安全マージンを優先し、胴の膨らみをやや高め・
          遷移をやや広めに調整)。リム際にわずかな外向きフレア(鍔)を追加
  - 鉢底: セルテクスチャと統一感のあるスポーク+同心リングの排水グレーチング
          (脚なし、置き型専用。ハンギング非対応)
  - サポート不要, PLA推奨, 完全オリジナル形状
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _pot_common import (
    write_stl,
    revolve_side,
    annulus_cap,
    spoke_wheel_grate,
    make_cell_seeds,
    SeedGrid,
    voronoi_groove_height,
    smoothstep,
)


def generate(
    r_bottom=44.0,        # 接地部の外半径 (mm) = 直径88mm
    r_max=60.0,           # 胴の最大膨らみ半径 (mm) = 直径120mm (4号相当)
    r_top=48.0,           # リム開口部の外半径 (mm、フレア追加前) = 直径96mm
    height=116.0,         # 全高 (mm)
    z_peak=64.0,          # 胴の膨らみが最大になる高さ (mm)
    rim_flare=2.0,        # リム際の外向きフレア量 (mm)
    wall_t=2.4,           # 壁の基本厚み (mm、テクスチャは常にこれより外側に加算)
    tex_amp=1.8,          # セルテクスチャの最大突出量 (mm、溝底からプラトーまで)
    tex_cell_size=20.0,   # テクスチャのセルサイズ目安 (mm)
    tex_jitter=0.35,      # 種点グリッドのジッター量 (グリッド間隔に対する比率, <=0.4推奨)
    tex_edge_width=7.5,   # セル境界の溝からプラトーへの遷移幅 (mm、プロファイル勾配との
                          # 合成オーバーハングが安全域に収まるよう数値検証の上で選定)
    tex_seed=7,           # 種点配置の乱数シード (再現性のため固定)
    grate_thick=1.8,      # 排水グレーチングの厚み (mm)
    grate_spokes=10,      # 排水グレーチングのスポーク数
    M=150,                # 外壁の垂直分割数
    N=300,                # 周方向の分割数
    M_inner=40,           # 内壁の垂直分割数 (曲面追従のためやや細かめ)
):
    H = height

    floor_clear = 6.0
    tex_fade_in = (floor_clear, floor_clear + 7.0)
    tex_fade_out = (H - 16.0, H - 9.0)
    flare_band = (H - 4.0, H)

    def r_body(z):
        # 樽型プロファイル: 下部からz_peakまで滑らかに膨らみ (sinイージング)、
        # そこからリムまで滑らかにすぼまる (すぼまる側はオーバーハングにならない)
        if z <= z_peak:
            t = z / z_peak
            return r_bottom + (r_max - r_bottom) * math.sin(math.pi / 2 * t)
        else:
            s = (H - z) / (H - z_peak)
            return r_top + (r_max - r_top) * math.sin(math.pi / 2 * s)

    def flare(z):
        a, b = flare_band
        if a <= z <= b:
            t = (z - a) / (b - a)
            return rim_flare * smoothstep(0.0, 1.0, t)
        return 0.0

    def r_base(z):
        return r_body(z) + flare(z)

    def tex_fade(z):
        if z < tex_fade_in[0]:
            return 0.0
        if z < tex_fade_in[1]:
            return smoothstep(tex_fade_in[0], tex_fade_in[1], z)
        if z <= tex_fade_out[0]:
            return 1.0
        if z < tex_fade_out[1]:
            return 1.0 - smoothstep(tex_fade_out[0], tex_fade_out[1], z)
        return 0.0

    # --- Voronoi種点の準備 (円周は中間半径で展開) ---
    r_mid = (r_bottom + r_max + r_top) / 3.0
    circumference = 2 * math.pi * r_mid
    seeds, seed_cols, _ = make_cell_seeds(
        circumference, tex_fade_in[0], tex_fade_out[1], tex_cell_size, tex_jitter, tex_seed
    )
    seed_grid = SeedGrid(seeds, circumference, tex_cell_size, seed_cols)

    def texture_dr(theta, z):
        s = theta * r_mid
        raw = voronoi_groove_height(s, z, seed_grid, tex_amp, tex_edge_width)
        return raw * tex_fade(z)

    def r_outer(theta, z):
        return r_base(z) + texture_dr(theta, z)

    def r_inner(theta, z):
        return r_base(z) - wall_t

    zero_z0 = lambda theta: 0.0  # 脚なし・置き型専用: 鉢底は接地面と同じ高さ

    tris = []

    # --- 外壁 (Voronoiセルテクスチャ付き) ---
    outer_tris, outer_bot, outer_top = revolve_side(
        r_outer, zero_z0, H, M, N, outward=True
    )
    tris += outer_tris

    # --- 内壁 (滑らか) ---
    inner_tris, inner_bot, inner_top = revolve_side(
        r_inner, zero_z0, H, M_inner, N, outward=False
    )
    tris += inner_tris

    # --- 上端リム ---
    tris += annulus_cap(outer_top, inner_top, upward=True)

    # --- 鉢底の排水グレーチング (接地面と同じ高さ、橋渡し不要) ---
    inner_r_at_base = r_base(0.0) - wall_t
    rim_r = inner_r_at_base + 0.6  # 内壁にわずかにめり込ませて融着させる
    tris += spoke_wheel_grate(
        rim_r=rim_r,
        hub_r=4.0,
        z0=0.0,
        z1=grate_thick,
        n_spokes=grate_spokes,
        spoke_half_angle=0.12,
        ring_radii=[rim_r * 0.6],
    )

    return tris, r_outer


def verify_overhang(r_outer, H, max_angle_deg=50.0, samples_theta=48, samples_z=250):
    """profile+textureを合成した実際の外壁関数を有限差分でサンプルし、
    最大の「半径が広がる方向」の勾配が安全域に収まっているか数値検証する。"""
    dz = H / samples_z
    max_slope = 0.0
    worst = None
    for zi in range(samples_z):
        z = zi * dz
        for ti in range(samples_theta):
            theta = 2 * math.pi * ti / samples_theta
            r0 = r_outer(theta, z)
            r1 = r_outer(theta, min(H, z + dz))
            slope = (r1 - r0) / dz
            if slope > max_slope:
                max_slope = slope
                worst = (theta, z)
    angle = math.degrees(math.atan(max_slope))
    print(f"  オーバーハング検証: 最大勾配={max_slope:.3f} (角度 {angle:.1f}°, 安全域 <{max_angle_deg}°) at z≈{worst[1]:.1f}mm")
    if angle >= max_angle_deg:
        print("  !! 警告: 安全域を超えています。tex_amp/z_peak/rim_flareを調整してください。")
    return angle


if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "models")
    out_path = os.path.join(out_dir, "knit_planter.stl")

    print("ナチュラル/パラメトリック系 観葉植物用 植木鉢 (knit_planter) を生成中...")
    tris, r_outer_func = generate()
    verify_overhang(r_outer_func, H=116.0)
    write_stl(tris, out_path, name="knit_planter")

    print(
        """
=== 印刷設定 (推奨) ===
  フィラメント : PLA (マット白 / テラコッタ、単色)
  レイヤー高さ : 0.20mm (Standard)
  壁ループ数   : 3 (排水/耐荷重強度のため)
  インフィル   : 15%
  サポート     : なし (樽型の膨らみ+セルテクスチャ+リムフレアは勾配を数値検証済み、
                 底面グレーチングも接地面と同じ高さのため橋渡し不要)
  シーム位置   : 背面 (Rear) 推奨 (セルの継ぎ目を目立たせないため)
  ビルドプレート: Textured PEI Plate

=== 設計メモ (v2) ===
  最大径120mm(4号相当) / リム開口部96mm+フレア2mm / 接地部88mm、高さ116mm
  壁面はVoronoi風にばら撒いた種点による「セル境界に溝、セル内部がプラトー」の
  有機的なセルテクスチャ (v1の規則的なヘリカル干渉パターンから刷新)。
  胴の膨らみのピーク位置とセルの遷移幅は、プロファイル勾配+テクスチャ勾配の
  合成オーバーハングを数値検証しながら安全マージンを優先して決定した。
  リム際にはわずかな外向きフレアを追加しプロポーションを洗練した。
  鉢底はセルテクスチャと統一感のあるスポーク+同心リングの排水グレーチング。
  ハンギング/壁掛け用途は非対応 (置き型専用)。
"""
    )
