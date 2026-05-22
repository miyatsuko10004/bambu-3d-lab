# Bambu Lab A1 mini 用 3Dデータ・プロジェクト

Bambu Lab A1 mini で印刷するための 3D モデルを管理・生成するディレクトリです。  
テスト用に、A1 mini の精度や表現力を引き出す 3 種類のフィジェットトイ（Fidget Toy）のモデルを **すべてSTL形式** で用意しました。

---

## 📂 ディレクトリ構成

* **`models/`**: 3Dプリンター用モデルファイル（直接スライサーで開けます）
  * [`wave_coin.stl`](file:///Users/manyo/develop/bambu-3d-lab/models/wave_coin.stl): 波状テクスチャを持つフィジェット・コイン。
  * [`fidget_gyro.stl`](file:///Users/manyo/develop/bambu-3d-lab/models/fidget_gyro.stl): 【新規】一体成形（Print-in-Place）ジャイロスコープ。
  * [`fidget_button.stl`](file:///Users/manyo/develop/bambu-3d-lab/models/fidget_button.stl): 【新規】サポート不要のタクタイル・プッシュボタン。
  * [`fidget_gyro.scad`](file:///Users/manyo/develop/bambu-3d-lab/models/fidget_gyro.scad): ジャイロスコープカスタマイズ用の OpenSCAD ソース。
* **`scripts/`**: 3Dモデル自動生成スクリプト（Python 3）
  * [`generate_wave_coin.py`](file:///Users/manyo/develop/bambu-3d-lab/scripts/generate_wave_coin.py): ウェーブコイン生成用。
  * [`generate_fidget_gyro.py`](file:///Users/manyo/develop/bambu-3d-lab/scripts/generate_fidget_gyro.py): ジャイロスコープSTL生成用。
  * [`generate_fidget_button.py`](file:///Users/manyo/develop/bambu-3d-lab/scripts/generate_fidget_button.py): プッシュボタンSTL生成用。

---

## 🛠️ テストモデルの紹介

### 1. 数学ウェーブ・フィジェットコイン (`wave_coin.stl`)
親指でなぞると心地よい、エルゴノミックな凹みと数学的な波（サイン波）を組み合わせたコインです。
* **特徴**: 中央が緩やかに凹んでおり、表面に干渉波パターンの微細なテクスチャを施しています。外周には滑り止めのローレット加工（ギザギザ）があり、A1 miniの押し出し・引き戻し（リトラクション）精度をテストできます。
* **サイズ**: 直径 40mm、高さ 5mm

### 2. Print-in-Place ジャイロスコープ (`fidget_gyro.stl`)
組み立て不要（Print-in-Place）で、印刷完了後すぐに回転させて遊べる同心円状のジャイロスコープです。
* **特徴**: 4層のリングが45度オーバーハングのピンで連結されており、サポート材なしで一体印刷できます。A1 miniの精度に最適化された **クリアランス 0.35mm** で設計されています。印刷後に軽くひねるだけでスムーズに回転します。
* **サイズ**: 直径 約56mm、高さ 8mm

### 3. スパイラル・プッシュボタン (`fidget_button.stl`)
追加パーツ（金属スプリングなど）を一切使用せず、3Dプリントされたプラスチックの弾性を利用した「カチカチ」と押せるプッシュボタンです。
* **特徴**: ボタンと外枠を3本のスパイラル（らせん）状のプラスチックバネで接続しており、完全にサポート材なしで底面密着で印刷できます。印刷ベッドから剥がすだけでそのままボタンとして機能します。
* **サイズ**: 直径 50mm、高さ 11mm (外枠高さ 8mm)

---

## 🚀 Bambu Studio / A1 mini 推奨印刷設定

モデルを Bambu Studio にインポートし、以下の設定でスライスしてください。

| 設定項目 | 推奨値 | 理由 |
| :--- | :--- | :--- |
| **フィラメント** | **PLA** / **PETG** | 標準的なPLAが最もシャープに造形でき、ピンやバネの強度も保てます。シルクPLAやマットPLAは層間接着力が弱く、可動部やバネが破損しやすいため推奨しません。 |
| **レイヤー高さ** | **0.12mm (Fine)** または **0.20mm (Standard)** | コインの波状テクスチャやボタンのバネ、ジャイロのピンの積層品質を保つために `0.12mm` または `0.20mm` が推奨されます。 |
| **サポート** | **なし (None)** | **重要！** ジャイロスコープやプッシュボタンはサポートを有効にすると、可動部や隙間がサポートで埋まって動かなくなります。 |
| **インフィル** | **15%〜20%** (グリッド または ジャイロイド) | 構造的強度を確保します。 |
| **壁ループ数 (Walls)** | **3** | ジャイロのピンやプッシュボタンのバネ部分の強度を確保し、破損を防ぎます。 |
| **ビルドプレート** | Textured PEI Plate | A1 miniのPEIプレートで綺麗に定着します。印刷前にプレートを洗剤等で脱脂しておくと、反りを防止できます。 |

---

## 🔧 カスタマイズ方法（Python）

各生成スクリプトを実行することで、パラメータを変更した新しいSTLファイルを生成できます。
```bash
# ウェーブコインの再生成
python3 scripts/generate_wave_coin.py

# ジャイロスコープの再生成（クリアランスの微調整など）
python3 scripts/generate_fidget_gyro.py

# プッシュボタンの再生成（バネの強さやボタンの高さ調整）
python3 scripts/generate_fidget_button.py
```
> [!TIP]
> もしジャイロスコープの可動部が固着して動かない場合は、`generate_fidget_gyro.py` の `clearance` を `0.4` に変更して再生成してみてください。
