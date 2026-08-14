#!/usr/bin/env python3
"""
ドナーメッシュ(models/sample/*.3mf)に対する法線方向変位マッピング・ヘルパー。

このリポジトリの他のジェネレータ(_pot_common.py)はゼロから回転体を
数式生成するが、こちらは「実績のある機能的な形状(排水穴・脚・リム等)を
そのまま活かし、模様だけを新規に載せる」という別方針専用のモジュール。
trimesh/numpy に依存する (requirements.txt 参照、venv推奨)。

パイプライン:
  1. load_donor_mesh(): 3MFからジオメトリを読み込み、シーングラフの変換
     行列をそのまま適用 (軸を手動でスワップしない = 反転/法線崩れのリスクを排除)。
  2. subdivide_uniform(): 一様midpoint分割を複数回 (subdivide_to_sizeは
     非適合分割でwatertightを壊すため使わない)。
  3. build_wall_mask(): 「滑らかな回転体の外壁」に該当する頂点だけを検出し、
     排水穴・脚・リムなどの非回転体ディテールは変位対象から除外する。
  4. displace_radial(): 選択した頂点だけを半径方向外側に変位。
  5. flag_new_overhangs(): 変位によって新たに急勾配になった面を検出。
"""

import math
import os

import numpy as np
import trimesh


def load_donor_mesh(path, geometry_key, zero_xy_translation=True):
    """
    3MFファイルから指定ジオメトリを読み込み、シーングラフのビルド変換行列を
    そのまま適用する (回転行列を自前で組み立てない=手動軸スワップによる
    鏡像化/法線反転のリスクを避ける)。zero_xy_translation=True で
    ビルドプレート中央寄せの並進だけ除去し、原点中心に揃える。
    """
    scene = trimesh.load(path)
    mesh = scene.geometry[geometry_key].copy()
    T, _ = scene.graph[geometry_key]
    T = T.copy()
    if zero_xy_translation:
        T[0, 3] = 0.0
        T[1, 3] = 0.0
    mesh.apply_transform(T)
    return mesh


def subdivide_uniform(mesh, times=2):
    """
    全面一様midpoint分割 (頂点位置は動かさない、トポロジのみ細分化)。
    subdivide_to_size は不適合分割(T-junction)を作りwatertightを壊すため
    使わない。細線パターン(麻の葉等)を潰さない解像度を得るために使う。
    """
    for _ in range(times):
        verts, faces = trimesh.remesh.subdivide(mesh.vertices, mesh.faces)
        mesh = trimesh.Trimesh(vertices=verts, faces=faces, process=False)
    return mesh


def _smoothstep(edge0, edge1, x):
    if edge1 <= edge0:
        return np.where(x >= edge1, 1.0, 0.0)
    t = np.clip((x - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def build_wall_mask(
    mesh,
    axis=2,
    profile_bin=1.0,
    profile_tolerance=0.8,
    coverage_bin=1.5,
    z_floor_margin=(3.0, 7.0),
    z_ceiling_margin=(4.0, 2.0),
):
    """
    「滑らかな回転体の外壁」に該当する頂点だけを検出するマスク (0..1) を返す。
    axis: 回転軸のインデックス (0=X, 1=Y, 2=Z)。load_donor_mesh適用後は
    通常2 (Z軸) でよい。

    3条件のANDで判定:
      1. 法線の径方向成分が大きい (内壁やリム上面を除外)
      2. 外側プロファイルr_outer(h)に近い (脚/排水穴の局所的な半径ズレを除外)
      3. その高さ帯における「条件1&2を満たす頂点の割合」(coverage) を
         なめらかにブレンドし、脚/排水部やリム際で自動的にフェードアウトする
         (手動でZ帯を決め打ちしない、データドリブンな遷移)

    上記3条件だけでは、排水穴のフチのように局所的に「外向き・プロファイル
    近傍」に見えてしまう箇所を排除しきれないことが実測でわかったため
    (穴のフチ自体は元の設計で急勾配になっていることがあり、条件1/2は
    そこを誤って安全と判定してしまう)、安全側の追加ゲートとして下端付近
    z_floor_margin=(fade開始, fade完了) と上端付近 z_ceiling_margin=(同) の
    範囲でマスクを強制的に0へフェードさせる (advisorの元提案通りの
    ハードな高さ帯フェードを、データドリブン判定の「保険」として併用する)。

    戻り値: (mask[0..1] per vertex, h (回転軸方向座標) per vertex,
             theta (周方向角度) per vertex, r_ref (中間半径、テクスチャ座標用))
    """
    other_axes = [i for i in range(3) if i != axis]
    a0, a1 = other_axes
    x = mesh.vertices[:, a0]
    y = mesh.vertices[:, a1]
    h = mesh.vertices[:, axis]
    r = np.hypot(x, y)
    theta = np.arctan2(y, x)

    normals = mesh.vertex_normals
    rhat_x = np.divide(x, r, out=np.zeros_like(x), where=r > 1e-9)
    rhat_y = np.divide(y, r, out=np.zeros_like(y), where=r > 1e-9)
    radial_component = normals[:, a0] * rhat_x + normals[:, a1] * rhat_y
    cond1 = radial_component > 0.6

    # 外向き頂点だけを使って高さ帯ごとの外側プロファイル r_outer(h) を作る
    h_min, h_max = h.min(), h.max()
    n_bins = max(1, int(math.ceil((h_max - h_min) / profile_bin)))
    bin_idx = np.clip(((h - h_min) / profile_bin).astype(int), 0, n_bins - 1)

    r_outer_profile = np.full(n_bins, np.nan)
    for b in range(n_bins):
        sel = cond1 & (bin_idx == b)
        if np.any(sel):
            r_outer_profile[b] = np.percentile(r[sel], 90)
    # NaNのビンは前後の有効なビンから補間
    valid = ~np.isnan(r_outer_profile)
    if valid.sum() >= 2:
        r_outer_profile = np.interp(
            np.arange(n_bins), np.where(valid)[0], r_outer_profile[valid]
        )
    elif valid.sum() == 1:
        r_outer_profile[:] = r_outer_profile[valid][0]
    else:
        r_outer_profile[:] = r.max()

    r_outer_of_vertex = r_outer_profile[bin_idx]
    cond2 = np.abs(r - r_outer_of_vertex) < profile_tolerance

    both = cond1 & cond2

    # coverage: 高さ帯ごとに「外向き(cond1)頂点のうち条件2も満たす割合」を
    # 求め、脚/排水部やリム際で自動的に0へフェードするブレンド係数にする。
    # 分母は全頂点ではなくcond1頂点数にする (内壁頂点が分母に混ざると
    # 健全な壁面でもcoverageが~0.5程度に頭打ちになってしまうため)。
    n_cov_bins = max(1, int(math.ceil((h_max - h_min) / coverage_bin)))
    cov_idx = np.clip(((h - h_min) / coverage_bin).astype(int), 0, n_cov_bins - 1)
    coverage = np.zeros(n_cov_bins)
    for b in range(n_cov_bins):
        sel = cov_idx == b
        denom = np.sum(cond1[sel])
        if denom > 0:
            coverage[b] = np.sum(both[sel]) / denom
    # 滑らかに: coverageが低い帯を隣接帯まで少しにじませる (単純な移動平均)
    if n_cov_bins >= 3:
        kernel = np.array([0.25, 0.5, 0.25])
        coverage = np.convolve(coverage, kernel, mode="same")
    coverage_of_vertex = coverage[cov_idx]
    coverage_blend = _smoothstep(0.3, 0.7, coverage_of_vertex)

    mask = np.where(both, 1.0, 0.0) * coverage_blend

    floor_lo, floor_hi = h_min + z_floor_margin[0], h_min + z_floor_margin[1]
    ceil_lo, ceil_hi = h_max - z_ceiling_margin[0], h_max - z_ceiling_margin[1]
    z_gate = _smoothstep(floor_lo, floor_hi, h) * (1.0 - _smoothstep(ceil_lo, ceil_hi, h))
    mask = mask * z_gate

    r_ref = float(np.median(r_outer_profile))
    return mask, h, theta, r_ref


def displace_radial(mesh, mask, h, theta, r_ref, pattern_func, axis=2):
    """
    mask(0..1)で選択した頂点だけを、pattern_func(s, z) [常に>=0mm] だけ
    半径方向外側へ変位する。s = theta * r_ref (弧長近似), z = h。
    トポロジ(面)は変更しないため watertight は保たれる
    (Trimeshはprocess=Falseで再構築し、頂点マージ等による縮退を避ける)。
    """
    other_axes = [i for i in range(3) if i != axis]
    a0, a1 = other_axes
    verts = mesh.vertices.copy()
    x = verts[:, a0]
    y = verts[:, a1]
    r = np.hypot(x, y)

    disp = np.array([
        pattern_func(theta[i] * r_ref, h[i]) if mask[i] > 1e-6 else 0.0
        for i in range(len(mask))
    ])
    disp = disp * mask

    new_r = r + disp
    scale = np.divide(new_r, r, out=np.ones_like(r), where=r > 1e-9)
    verts[:, a0] = x * scale
    verts[:, a1] = y * scale

    new_mesh = trimesh.Trimesh(vertices=verts, faces=mesh.faces, process=False)
    return new_mesh, disp


def flag_new_overhangs(mesh, disp, max_angle_deg=50.0, axis=2):
    """
    変位によって新たに急勾配になった面を検出する。変位量が非ゼロの面のみを
    対象にする (ドナー由来の面=排水グレート底面やアーチ等は印刷実績が
    あるものとして対象外、変位で新たに触れた面だけを厳しくチェックする)。
    """
    face_disp = disp[mesh.faces].max(axis=1)
    touched = face_disp > 1e-6
    normals = mesh.face_normals
    down_component = normals[:, axis]
    threshold = -math.sin(math.radians(max_angle_deg))
    flagged = touched & (down_component < threshold)
    n_flagged = int(np.sum(flagged))
    print(f"  オーバーハング検証(変位面のみ): 危険面 {n_flagged} / {int(np.sum(touched))} (変位面中)")
    if n_flagged > 0:
        worst_idx = np.argmin(np.where(touched, down_component, 1.0))
        worst_angle = math.degrees(math.asin(-normals[worst_idx, axis]))
        print(f"  !! 警告: 最大 {worst_angle:.1f}° の急勾配面があります (安全域 <{max_angle_deg}°)")
    return n_flagged


def export_binary_stl(mesh, filepath, name="model"):
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    mesh.export(filepath, file_type="stl")
    size_mb = os.path.getsize(filepath) / (1024 * 1024)
    print(f"  -> {filepath} ({len(mesh.faces)} triangles, {size_mb:.1f} MB)")
