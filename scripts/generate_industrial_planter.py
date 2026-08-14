#!/usr/bin/env python3
"""
黒/無骨系 塊根植物用 植木鉢 (Industrial Hammered-Facet Succulent Planter)
Bambu Lab A1 mini 向け STL生成スクリプト

設計仕様 (プロトタイプ v2):
  - 3号相当 (直径 90mm, 高さ 84mm)
  - 単色印刷想定 (黒 / ダークグレー)
  - 壁面: Voronoi風にばら撒いた種点ごとにランダムな傾斜平面を割り当て、
          隣接平面をブレンドする「ハンマード (鍛造/低ポリ)」テクスチャ。
          規則的なサイン波格子と違い、セルの大きさ・向きが不揃いなため
          光の当たり方が場所ごとに変わり、黒色フィラメントでも陰影が残る。
          (v1のサイン波干渉レリーフから、MakerWorldの人気デザインを参考に刷新)
  - シルエット: 単純な直線フラスタムに、緩やかなウエストの絞り込み・
          脚上部のリセスバンド・リム際の段差(カラー)を追加し、
          「スライサー原型」的な単調さを避けた輪郭にした
  - 鉢底: リム-ハブ間のスポーク+同心リングによる「メッシュ状」排水グレーチング
  - 脚: 壁の最下部に4箇所、半球アーチ状の切り欠き (自己支持形状、サポート不要)
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
    hammered_facet_height,
    smoothstep,
)


def generate(
    r_bottom=35.0,        # 鉢底の外半径 (mm) = 直径70mm
    r_top=45.0,           # 鉢上端の外半径 (mm) = 直径90mm (3号相当)
    height=84.0,          # 壁の高さ (mm, 脚を除く)
    wall_t=2.4,           # 壁の基本厚み (mm、テクスチャは常にこれより外側に加算)
    waist_amp=1.2,        # 胴の緩やかな絞り込み量 (mm、単調な直線フラスタムを避ける)
    tex_amp=1.35,         # ハンマードテクスチャの最大突出量 (mm)
    tex_cell_size=11.5,   # テクスチャのセルサイズ目安 (mm)
    tex_jitter=0.35,      # 種点グリッドのジッター量 (グリッド間隔に対する比率, <=0.4推奨)
    tex_beta=1.5,         # ファセットのブレンド急峻さ (大きいほど稜線がシャープ, 1/mm)
    tex_seed=42,          # 種点配置の乱数シード (再現性のため固定)
    n_feet=4,             # 脚 (アーチ切り欠き) の数
    foot_notch_h=4.0,     # 脚アーチの最大切り欠き高さ (mm)
    grate_z0=6.0,         # 排水グレーチングの取り付け高さ (mm, 脚アーチより上)
    grate_thick=1.6,      # 排水グレーチングの厚み (mm)
    grate_spokes=8,       # 排水グレーチングのスポーク数
    M=120,                # 外壁の垂直分割数
    N=250,                # 周方向の分割数
    M_inner=60,           # 内壁の垂直分割数
):
    H = height

    # --- シルエットの帯域定義 (脚アーチ上のリセス / テクスチャ全面表示域 /
    #     リム際のカラー段差 / 上端の無地リム) ---
    recess_band = (foot_notch_h, foot_notch_h + 6.0)
    tex_fade_in = (recess_band[1], recess_band[1] + 2.5)
    tex_fade_out = (H - 12.0, H - 8.0)
    collar_band = (tex_fade_out[1], tex_fade_out[1] + 4.0)

    def linear_taper(z):
        return r_bottom + (r_top - r_bottom) * (z / H)

    def waist_ease(z):
        # 胴の中央をわずかに絞り込む (外に開くフラスタム上の凹みは
        # オーバーハング的に安全な方向 = 半径が局所的に小さくなるだけ)
        return -waist_amp * math.sin(math.pi * z / H)

    def foot_recess(z):
        a, b = recess_band
        if a <= z <= b:
            t = (z - a) / (b - a)
            return -0.8 * math.sin(math.pi * t)
        return 0.0

    def rim_collar(z):
        a, b = collar_band
        if a <= z <= b:
            t = (z - a) / (b - a)
            return -0.35 * math.sin(math.pi * t)
        return 0.0

    def r_base(z):
        return linear_taper(z) + waist_ease(z) + foot_recess(z) + rim_collar(z)

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

    # --- ハンマード・ファセット種点の準備 (円周は中間半径で展開) ---
    r_mid = (r_bottom + r_top) / 2.0
    circumference = 2 * math.pi * r_mid
    seeds, seed_cols, _ = make_cell_seeds(
        circumference, tex_fade_in[0], tex_fade_out[1], tex_cell_size, tex_jitter, tex_seed
    )
    seed_grid = SeedGrid(seeds, circumference, tex_cell_size, seed_cols)

    def texture_dr(theta, z):
        s = theta * r_mid
        raw = hammered_facet_height(s, z, seed_grid, tex_amp, tex_beta, tex_cell_size, k=6)
        return raw * tex_fade(z)

    def r_outer(theta, z):
        return r_base(z) + texture_dr(theta, z)

    def r_inner(theta, z):
        return r_base(z) - wall_t

    def foot_z0(theta):
        # 4箇所のアーチ切り欠き: アーチ中心で最大高さ、脚(柱)の中心で0mmに収束する
        # なめらかな (C1連続) プロファイル。上にいくほど開口部が狭まるため
        # ブリッジ/サポートなしで印刷できる。
        phi = n_feet * theta
        c = math.cos(phi)
        return foot_notch_h * (max(0.0, c) ** 2)

    tris = []

    # --- 外壁 (ハンマード・テクスチャ + 脚アーチ) ---
    outer_tris, outer_bot, outer_top = revolve_side(
        r_outer, foot_z0, H, M, N, outward=True
    )
    tris += outer_tris

    # --- 内壁 (滑らか、脚アーチの開口部形状は外壁と共有し貫通させる) ---
    inner_tris, inner_bot, inner_top = revolve_side(
        r_inner, foot_z0, H, M_inner, N, outward=False
    )
    tris += inner_tris

    # --- 上端リム (外壁と内壁を結ぶ平らな縁) ---
    tris += annulus_cap(outer_top, inner_top, upward=True)

    # --- 鉢底の排水グレーチング (内壁に接続、リムからハブへスポークで橋渡し) ---
    inner_r_at_grate = r_base(grate_z0) - wall_t
    rim_r = inner_r_at_grate + 0.6  # 内壁にわずかにめり込ませて融着させる
    tris += spoke_wheel_grate(
        rim_r=rim_r,
        hub_r=4.0,
        z0=grate_z0,
        z1=grate_z0 + grate_thick,
        n_spokes=grate_spokes,
        spoke_half_angle=0.13,
        ring_radii=[rim_r * 0.55],
    )

    return tris, r_outer


def verify_overhang(r_outer, H, max_angle_deg=50.0, samples_theta=48, samples_z=200):
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
        print("  !! 警告: 安全域を超えています。tex_amp/waist_ampを下げてください。")
    return angle


if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "models")
    out_path = os.path.join(out_dir, "industrial_planter.stl")

    print("黒/無骨系 塊根植物用 植木鉢 (industrial_planter) を生成中...")
    tris, r_outer_func = generate()
    verify_overhang(r_outer_func, H=84.0)
    write_stl(tris, out_path, name="industrial_planter")

    print(
        """
=== 印刷設定 (推奨) ===
  フィラメント : PLA (黒 / ダークグレー、単色)
  レイヤー高さ : 0.20mm (Standard)
  壁ループ数   : 3 (排水/耐荷重強度のため)
  インフィル   : 15%
  サポート     : なし (脚のアーチ切り欠き・排水グレーチングとも自己支持形状)
  シーム位置   : 背面 (Rear) 推奨 (ファセットの継ぎ目を目立たせないため)
  ビルドプレート: Textured PEI Plate

=== 設計メモ (v2) ===
  外径: 下部70mm / 上部90mm (3号相当), 高さ 84mm
  壁面はVoronoi風にばら撒いた種点ごとのランダム傾斜平面をブレンドした
  「ハンマード」テクスチャ (v1のサイン波干渉レリーフから刷新)。
  シルエットにも緩やかなウエスト絞り込み・脚上部のリセスバンド・
  リム際のカラー段差を追加し、単調な直線フラスタムを避けている。
  鉢底はスポーク+同心リングのグレーチング構造で「メッシュ状」の排水口を再現。
  脚は壁最下部の半球アーチ状切り欠き (4箇所) で、サポート材不要。
"""
    )
