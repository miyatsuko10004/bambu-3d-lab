# Bambu Lab A1 mini 用 3Dデータ・プロジェクト

Bambu Lab A1 mini で印刷するための 3D モデルを管理・生成するディレクトリです。  
テスト用に、A1 mini の精度や表現力を引き出す 2 種類のフィジェットトイ（Fidget Toy）のモデルを用意しました。

---

## 📂 ディレクトリ構成

* **`models/`**: 3Dプリンター用モデルファイル
  * [`wave_coin.stl`](file:///Users/manyo/develop/bambu-3d-lab/models/wave_coin.stl): Pythonで生成された波状テクスチャを持つフィジェット・コイン。
  * [`fidget_gyro.scad`](file:///Users/manyo/develop/bambu-3d-lab/models/fidget_gyro.scad): OpenSCAD用のパラメータ調整可能なジャイロスコープ。
* **`scripts/`**: 3Dモデル生成スクリプト
  * [`generate_wave_coin.py`](file:///Users/manyo/develop/bambu-3d-lab/scripts/generate_wave_coin.py): ウェーブコインのSTLを自動計算して出力するPythonスクリプト。

---

## 🛠️ テストモデルの紹介

### 1. 数学ウェーブ・フィジェットコイン (`wave_coin.stl`)
親指でなぞると心地よい、エルゴノミックな凹みと数学的な波（サイン波）を組み合わせたコインです。
* **特徴**: 
  * 中央部が親指にフィットするよう緩やかに凹んでいます（Worry Stone形状）。
  * 表面には細かい干渉波パターンの微細なテクスチャを施しており、A1 mini の高精細な印刷品質をテストできます。
  * 外周には滑り止めのローレット加工（ギザギザ）があり、エクストルーダーの押し出し・引き戻し（リトラクション）の精度をテストできます。
* **サイズ**: 直径 40mm、高さ 5mm

### 2. Print-in-Place ジャイロスコープ (`fidget_gyro.scad`)
組み立て不要（Print-in-Place）で、印刷完了後すぐに回転させて遊べる同心円状のジャイロスコープです。
* **特徴**: 
  * 4層のリングが45度オーバーハングのピンで連結されており、サポート材なしで一体印刷できます。
  * A1 mini の優れた精度を活かし、**クリアランス 0.35mm** で設計されています。印刷後に少しひねるだけで、ピンが穴の中でスムーズに回転するようになります。
  * 外側のリングには滑り止めのテクスチャが施されています。
* **サイズ**: 直径 約56mm、高さ 8mm

---

## 🚀 Bambu Studio / A1 mini 推奨印刷設定

モデルを Bambu Studio にインポートし、以下の設定でスライスしてください。

| 設定項目 | 推奨値 | 理由 |
| :--- | :--- | :--- |
| **フィラメント** | **PLA** / **PETG** | 標準的なPLAが最もシャープに造形でき、ピンの強度も保てます。シルクPLAは層間接着力が弱くピンが折れやすいため、避けるのが無難です。 |
| **レイヤー高さ** | **0.12mm (Fine)** または **0.20mm (Standard)** | コインの波状テクスチャを美しく表現するには `0.12mm` が最も推奨されます。 |
| **サポート** | **なし (None)** | **重要！** ジャイロスコープにサポートを適用すると、可動部がサポートで埋まって回転しなくなります。 |
| **インフィル** | **15%〜20%** (グリッド または ジャイロイド) | ジャイロスコープの耐久性を高めるために、ある程度のインフィルと壁厚が必要です。 |
| **壁ループ数 (Walls)** | **3** | ピンの強度を十分に確保し、回した時に破損するのを防ぎます。 |
| **ビルドプレート** | Textured PEI Plate | A1 mini 付属のテクスチャPEIプレートは、下面に美しいザラザラ感を付与でき、定着力も良好です。プレートの汚れ（油分）はIPAや食器用洗剤でよく落としておいてください。 |

---

## 🔧 カスタマイズ方法

### 1. コインの形状を変更する
Pythonスクリプト [`scripts/generate_wave_coin.py`](file:///Users/manyo/develop/bambu-3d-lab/scripts/generate_wave_coin.py) のパラメータ（半径、波の周波数、深さなど）を変更し、ターミナルで以下を実行すると新しい STL ファイルが再生成されます。
```bash
python3 scripts/generate_wave_coin.py
```

### 2. ジャイロスコープのサイズやクリアランスを変更する
[OpenSCAD](https://openscad.org/)（無料）をインストールし、[`models/fidget_gyro.scad`](file:///Users/manyo/develop/bambu-3d-lab/models/fidget_gyro.scad) を開きます。
* プリンターの個体差やフィラメントの種類でピンが固着する場合は、`clearance` を `0.4` や `0.45` に増やしてください。
* リングの数 (`num_rings`) や高さ (`ring_height`) を自由に変更して、STLファイルとしてエクスポートできます。
