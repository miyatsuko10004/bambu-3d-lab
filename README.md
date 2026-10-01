# Bambu Lab A1 mini 用 3Dデータ・プロジェクト

Bambu Lab A1 mini で印刷するための 3D モデルを管理・生成するディレクトリです。  
テスト用に、A1 mini の精度や表現力を引き出す 4 種類のフィジェットトイ（Fidget Toy）のモデルを **すべてSTL形式** で用意しました。

---

## 📂 ディレクトリ構成

* **`models/`**: 3Dプリンター用モデルファイル（直接スライサーで開けます）
  * [`eima_emma_text_only.stl`](file:///Users/manyo/develop/bambu-3d-lab/models/eima_emma_text_only.stl): 提供PDFの筆文字「瑛万」と「emma」だけを厚み3.0mmにした、プレートなしの単色印刷向け文字モデル。
  * [`eima_emma_text_only_cursive.stl`](file:///Users/manyo/develop/bambu-3d-lab/models/eima_emma_text_only_cursive.stl): 上記の英字をBrush Script MTの接続筆記体にしたバリエーション。
  * [`industrial_planter.stl`](file:///Users/manyo/develop/bambu-3d-lab/models/industrial_planter.stl): 【新規・試作】黒/無骨系 塊根植物用 植木鉢（ハンマード/低ポリ風テクスチャ + メッシュ状排水グレーチング + 一体成形の脚）。
  * [`knit_planter.stl`](file:///Users/manyo/develop/bambu-3d-lab/models/knit_planter.stl): 【新規・試作】ナチュラル/パラメトリック系 観葉植物用 植木鉢（Voronoiセルテクスチャ + 統一感のある排水グレーチング）。
  * [`ichimatsu_planter.stl`](file:///Users/manyo/develop/bambu-3d-lab/models/ichimatsu_planter.stl): 【新規・試作】伝統文様シリーズ「市松」植木鉢。
  * [`asanoha_planter.stl`](file:///Users/manyo/develop/bambu-3d-lab/models/asanoha_planter.stl): 【新規・試作】伝統文様シリーズ「麻の葉」植木鉢。
  * [`shippou_planter.stl`](file:///Users/manyo/develop/bambu-3d-lab/models/shippou_planter.stl): 【新規・試作】伝統文様シリーズ「七宝」植木鉢。
  * `sample/`: MakerWorld からダウンロードしたCC0参考モデル (シルエット/プロポーションの参考用、形状そのものは製品に使用しない)。
  * [`veggie_slicer_lid.stl`](file:///Users/manyo/develop/bambu-3d-lab/models/veggie_slicer_lid.stl): 【新規】野菜スライサー用 抑えふた（スパイク16本付き）。
  * [`wave_coin.stl`](file:///Users/manyo/develop/bambu-3d-lab/models/wave_coin.stl): 波状テクスチャを持つフィジェット・コイン。
  * [`fidget_gyro.stl`](file:///Users/manyo/develop/bambu-3d-lab/models/fidget_gyro.stl): 一体成形（Print-in-Place）ジャイロスコープ。
  * [`fidget_button.stl`](file:///Users/manyo/develop/bambu-3d-lab/models/fidget_button.stl): サポート不要のタクタイル・プッシュボタン。
  * [`flexi_snake.stl`](file:///Users/manyo/develop/bambu-3d-lab/models/flexi_snake.stl): 【新規】グネグネ曲がる一体成形のフレキシブル・スネーク（背びれ・目付き）。
  * [`fidget_gyro.scad`](file:///Users/manyo/develop/bambu-3d-lab/models/fidget_gyro.scad): ジャイロスコープカスタマイズ用の OpenSCAD ソース。
* **`scripts/`**: 3Dモデル自動生成スクリプト（Python 3）
  * [`generate_nameplate.py`](file:///Users/manyo/develop/bambu-3d-lab/scripts/generate_nameplate.py): `assets/瑛万.pdf`の埋め込みベクター筆文字を直接抽出し、「emma」も高解像度で輪郭統合してSTLを生成する。
  * [`generate_industrial_planter.py`](file:///Users/manyo/develop/bambu-3d-lab/scripts/generate_industrial_planter.py): 黒/無骨系 植木鉢STL生成用。
  * [`generate_knit_planter.py`](file:///Users/manyo/develop/bambu-3d-lab/scripts/generate_knit_planter.py): ナチュラル/パラメトリック系 植木鉢STL生成用。
  * [`generate_ichimatsu_planter.py`](file:///Users/manyo/develop/bambu-3d-lab/scripts/generate_ichimatsu_planter.py): 市松文様 植木鉢STL生成用（ドナーメッシュ変位マッピング、要`pip install -r requirements.txt`）。
  * [`generate_asanoha_planter.py`](file:///Users/manyo/develop/bambu-3d-lab/scripts/generate_asanoha_planter.py): 麻の葉文様 植木鉢STL生成用（同上）。
  * [`generate_shippou_planter.py`](file:///Users/manyo/develop/bambu-3d-lab/scripts/generate_shippou_planter.py): 七宝文様 植木鉢STL生成用（同上）。
  * [`_pot_common.py`](file:///Users/manyo/develop/bambu-3d-lab/scripts/_pot_common.py): 植木鉢スクリプト群が共有するジオメトリ・テクスチャ生成ヘルパー（単体では実行しません、依存ライブラリなし）。
  * [`_mesh_pattern_common.py`](file:///Users/manyo/develop/bambu-3d-lab/scripts/_mesh_pattern_common.py): 伝統文様シリーズ3本が共有するドナーメッシュ変位マッピング・ヘルパー（単体では実行しません、trimesh/numpy/scipy依存）。
  * [`generate_veggie_slicer_lid.py`](file:///Users/manyo/develop/bambu-3d-lab/scripts/generate_veggie_slicer_lid.py): 野菜スライサー用 抑えふたSTL生成用。
  * [`generate_wave_coin.py`](file:///Users/manyo/develop/bambu-3d-lab/scripts/generate_wave_coin.py): ウェーブコイン生成用。
  * [`generate_fidget_gyro.py`](file:///Users/manyo/develop/bambu-3d-lab/scripts/generate_fidget_gyro.py): ジャイロスコープSTL生成用。
  * [`generate_fidget_button.py`](file:///Users/manyo/develop/bambu-3d-lab/scripts/generate_fidget_button.py): プッシュボタンSTL生成用。
  * [`generate_flexi_snake.py`](file:///Users/manyo/develop/bambu-3d-lab/scripts/generate_flexi_snake.py): フレキシブル・スネークSTL生成用。

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

### 4. フレキシブル・スネーク (`flexi_snake.stl`)
背骨のような関節を縦方向のピンで連結し、サポートなしで一体印刷（Print-in-Place）できるグネグネとよく動くヘビのおもちゃです。
* **特徴**: 頭部には目と頭びれがあり、胴体・尾に向けて徐々に細くなるリアルな設計です。各セグメントの間には強固なZピンジョイント（上下2枚プレートと中プレートの噛み合わせ）が施されており、印刷直後からグネグネと曲げて遊ぶことができます。
* **サイズ**: 全長 113mm、幅 12mm、高さ 10.8mm (背びれ含む)

---

## 🪴 植木鉢プロトタイプ（メルカリ / minne・Creema向け 試作）

いずれも単色印刷・完全オリジナル形状・サポート材不要で設計しています。量産前の試作(プロトタイプ)段階です。

> **v2 (現行)**: MakerWorldの人気植木鉢デザイン（Voronoi/ハンマード/樽型シルエット等）をベンチマークに、
> v1の規則的なサイン波干渉テクスチャから刷新。Voronoi風にばら撒いた種点による不規則なセル/ファセット
> テクスチャと、単調な直線・単純な回転体を避けたシルエット（ウエスト絞り・リムフレア等）を採用。

### A. 黒/無骨系 塊根植物用 植木鉢 (`industrial_planter.stl`)
インダストリアル・無骨系デザイン。Voronoi風の種点ごとにランダムな傾斜平面を割り当ててブレンドする「ハンマード（鍛造/低ポリ）」テクスチャを壁面全体に露出させています。
* **特徴**: セルの大きさ・向きが不揃いなため、黒色フィラメントでも陰影が残る。シルエットには緩やかなウエスト絞り込み・脚上部のリセスバンド・リム際のカラー段差を追加し、直線フラスタムの単調さを回避。鉢底はスポーク+同心リングによる「メッシュ状」排水グレーチング。脚は壁最下部の半球アーチ状切り欠き4箇所で表現し、浮いた支柱ではなく壁と一体の自己支持形状（サポート材不要）。オーバーハング角度は数値検証済み（約41°、45〜50°の安全域内）。
* **サイズ**: 直径 70mm(下)〜90mm(上、3号相当)、高さ 84mm
* **カラー**: 黒・ダークグレー想定（単色、同一STLで色違い運用）

### B. ナチュラル/パラメトリック系 観葉植物用 植木鉢 (`knit_planter.stl`)
Voronoi風にばら撒いた種点から「セル境界に溝、セル内部がプラトー」の有機的なセルテクスチャを全周に表現した、北欧ナチュラル寄りのデザイン。
* **特徴**: 規則的なヘリカル干渉（ゴルフボール状ディンプル）から、石垣/粘土の肌に近い不規則なセルテクスチャに刷新。丸みのある樽型プロファイルとリム際のわずかな外向きフレアでプロポーションを洗練。鉢底はセルテクスチャと統一感のあるスポーク+同心リングの排水グレーチング（脚なし、置き型専用）。オーバーハング角度は数値検証済み（約46°、45〜50°の安全域内）。
* **サイズ**: 最大径 120mm(4号相当)、リム開口部 96mm+フレア2mm、接地部 88mm、高さ 116mm
* **カラー**: マット白・テラコッタ想定（単色、同一STLで色違い運用）

---

## 🎎 伝統文様シリーズ（柄名=商品名、試作）

> **v2 (現行)**: 当初はMakerWorldのCC0参考モデル(`models/sample/`)から「シルエット/プロポーションだけ」を
> 抽出し、柄も排水穴・脚もゼロから再生成していたが、「排水穴などが実用的ではない」というフィードバックを
> 受けて方針転換した。参考モデルのうち柄が焼き込まれていない `Planter.3mf` (CC0) は実メッシュをそのまま
> 読み込み、排水穴・脚・リムなど印刷実績のある実用ディテールは一切変更せず、「滑らかな回転体の外壁」と
> 判定した頂点だけに柄を法線(半径)方向の変位として追加している(`scripts/_mesh_pattern_common.py`)。
> 柄が焼き込まれている`Maceta_Triángulo.3mf`/`einstein-planter.3mf`はこの手法の対象外(柄の二重写しになるため)。
> この処理には trimesh/numpy/scipy 等を使用する。セットアップ:
> ```bash
> python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
> ```

### C. 市松 (`ichimatsu_planter.stl`)
正方形セルが交互に凸/凹になる市松模様。セル境界の符号付き距離場を使っているため、パリティが反転する境界でも
テクスチャが連続しています(段差なし)。深さ控えめ(0.6mm)で陰影により柄を読ませます。ドナーメッシュの排水穴・
脚・リムはそのまま保持。オーバーハング角度は変位面のみを対象に数値検証済み(危険面0件)。

### D. 麻の葉 (`asanoha_planter.stl`)
正六角形タイリングの「辺」+「中心から各頂点への放射スポーク」を線分ネットワークとして持ち、線分までの距離が
近いほど盛り上がる細いリッジ(全幅約2mm、高さ0.4mm)で表現。格子線とスポークを同じ太さにすることで、
単なる六角グリッドではなく麻の葉として認識できる見た目にしています。細線パターンのためバイナリSTLで出力。
ドナーメッシュの排水穴・脚・リムはそのまま保持。オーバーハング角度は数値検証済み(危険面0件)。

### E. 七宝 (`shippou_planter.stl`)
正方格子上の円を重ねて描く「七宝つなぎ」模様。中心までの距離だけで書ける距離場のため、伝統文様3種の中で
最も軽量な実装です。ドナーメッシュの排水穴・脚・リムはそのまま保持。オーバーハング角度は数値検証済み(危険面0件)。

---

## 🚀 Bambu Studio / A1 mini 推奨印刷設定

モデルを Bambu Studio にインポートし、以下の設定でスライスしてください。

| 設定項目 | 推奨値 | 理由 |
| :--- | :--- | :--- |
| **フィラメント** | **PLA** / **PETG** | 標準的なPLAが最もシャープに造形でき、ピンやバネ、関節の強度も保てます。シルクPLAやマットPLAは層間接着力が弱く、可動部やバネが破損しやすいため推奨しません。 |
| **レイヤー高さ** | **0.12mm (Fine)** または **0.20mm (Standard)** | コインの波状テクスチャやボタンのバネ、スネークの関節のピン品質を保つために `0.12mm` または `0.20mm` が推奨されます。 |
| **サポート** | **なし (None)** | **重要！** ジャイロスコープやプッシュボタン、スネークの関節は、サポートを有効にすると隙間がサポートで埋まって動かなくなります。 |
| **インフィル** | **15%〜20%** (グリッド または ジャイロイド) | 構造的強度を確保します。 |
| **壁ループ数 (Walls)** | **3** | 関節ピンやバネ部分の強度を確保し、破損を防ぎます。 |
| **ビルドプレート** | Textured PEI Plate | A1 miniのPEIプレートで綺麗に定着します。印刷前にプレートを洗剤等で脱脂しておくと、反りを防止できます。 |

---

## 🔧 カスタマイズ方法（Python）

各生成スクリプトを実行することで、パラメータを変更した新しいSTLファイルを生成できます。
```bash
# 黒/無骨系 植木鉢の再生成
python3 scripts/generate_industrial_planter.py

# ナチュラル/パラメトリック系 植木鉢の再生成
python3 scripts/generate_knit_planter.py

# 伝統文様シリーズ (市松/麻の葉/七宝) はドナーメッシュ変位マッピングを使うため
# 事前に一度だけ venv セットアップが必要:
#   python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
source .venv/bin/activate

# 市松文様 植木鉢の再生成
python3 scripts/generate_ichimatsu_planter.py

# 麻の葉文様 植木鉢の再生成
python3 scripts/generate_asanoha_planter.py

# 七宝文様 植木鉢の再生成
python3 scripts/generate_shippou_planter.py

# ウェーブコインの再生成
python3 scripts/generate_wave_coin.py

# ジャイロスコープの再生成
python3 scripts/generate_fidget_gyro.py

# プッシュボタンの再生成
python3 scripts/generate_fidget_button.py

# フレキシブル・スネークの再生成（セグメント数やクリアランスの変更）
python3 scripts/generate_flexi_snake.py
```
> [!TIP]
> もしスネークの関節が固着して動かない場合は、`generate_flexi_snake.py` の `clearance` を `0.4` や `0.45` に変更して再生成してみてください。
