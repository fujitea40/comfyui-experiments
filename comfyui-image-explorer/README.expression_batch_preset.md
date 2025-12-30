# Expression Preset Batch

日本語 | [English](README.expression_batch_preset.en.md)

ComfyUI の カスタムノード [**ExpressionPresetNode**](../expression_preset/README.md) を前提に、入力フォルダ内の画像（複数）に対して
**表情（expression）× seed（repeats）** をまとめて実行するバッチツールです。

* 画像を ComfyUI にアップロード（任意）
* workflow の **LoadImage（入力画像）** を差し替え
* workflow の **ExpressionPresetNode（expression）** を差し替え
* （任意）seed を差し替え
* （任意）SaveImage の `filename_prefix` を差し替え
* 実行メタデータ（meta.json）をローカルに保存

---

## 特徴

* ✅ **フォルダ一括処理**：入力画像フォルダの全画像に対して自動実行
* ✅ **表情プリセット運用**：ExpressionPresetNode の preset（YAML）で表情プロンプト＆パラメータを集中管理
* ✅ **seedバリエーション生成**：1表情あたり `repeats` 回繰り返し（seed戦略も選択）
* ✅ **メタ保存**：各実行の情報を `meta.json` に保存（再現・追跡が容易）

---

## 必要な環境

### ComfyUI

* ComfyUI がインストールされ、起動していること
* デフォルトURL: `http://127.0.0.1:8188`

### Python
- Python 3.10 以上

### 必要なPythonパッケージ

標準ライブラリ以外に以下のパッケージが必要です：

```bash
requests>=2.31.0
pyyaml>=6.0.0
```

## インストール

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd comfyui-experiments/comfyui-image-explorer
```

### 2. 依存パッケージのインストール

#### pip を使用する場合

```bash
pip install -r requirements.txt
```

#### 手動でインストールする場合

```bash
pip install requests pyyaml
```
---

## 準備（重要）

### 1) ComfyUI workflow を API 形式でエクスポート

ComfyUI の開発者モードをONにして、`File -> Export (API)` で JSON を出力し、任意の場所に保存します。

このツールは **API形式の workflow JSON**（node_id → node定義の辞書形式）を前提とします。

### 2) workflow に必要なノード

最低限、次のノードが workflow 内に存在する必要があります。

* **LoadImage 相当**（入力画像のファイル名を `inputs["image"]` に持つノード）
* **ExpressionPresetNode**（`expression` を入力として受けるカスタムノード）

任意で対応：

* **SaveImage**：`filename_prefix` を外部から差し替えたい場合
* **KSampler 等**：seed を外部から差し替えたい場合（workflow側で固定seedのときに便利）

### 3) node_id を控える

config で node_id を指定するため、ComfyUI で該当ノードの node_id を確認してください。
（ExportしたJSON内で `"10": {...}` のようなキーが node_id です）

### おまけ

立ち絵の作成には、併せて公開している[ComfyUI画像生成探索ツール](README.image_explorer.md)も使用してみてください。
ある程度立ち絵用に合わせた設定ファイルも含めています。

`python scripts/image_explorer.py -c config/explorer_standingpicture.yaml`

---

## 使い方

### 基本実行

```bash
python scripts/expression_preset_batch.py -i <入力画像フォルダ> -c <設定ファイル>
```

例：

```bash
python scripts/expression_preset_batch.py -i ./input_images -c ./config/config.epb.yaml
```

### オプション

* `--recursive`：サブフォルダも探索
* `--limit N`：先頭N枚のみ処理
* `--dry-run`：ComfyUIに投げず、予定動作（メタ生成など）だけ行う
* `--verbose`：デバッグログ

---

## 出力

### 生成画像

生成画像は **ComfyUI 側の output 設定**に従って保存されます。

`save_image.filename_prefix_template` を設定している場合は、SaveImage ノードの `filename_prefix` が差し替わるので、出力の整理がしやすくなります。

### meta.json（ローカル）

ローカル側にも `output_root` 配下に `meta.json` を保存します（実行ログ・再現用）。

例：

```
outputs_epb/
  alice/
    neutral/
      0001_ab12cd/
        meta.json
```

---

## 設定ファイル（YAML）

### サンプル：`config/config.epb.example.yaml`

```yaml
comfy_url: "http://127.0.0.1:8188"
workflow_json: "./workflows/expression_preset_batch_api.json"
output_root: "./outputs_epb"

input_image:
  node_id: "10"
  input_name: "image"
  upload: true
  upload_type: "input"
  upload_subfolder: ""
  overwrite: false

expression_preset:
  node_id: "123"
  expression_input_name: "expression"
  expressions:
    - neutral
    - smile
    - angry
    - sad

save_image:
  node_id: "999"
  filename_prefix_template: "{image}/{expr}/{run}/img"

seed_node:
  node_id: "6"
  input_name: "seed"

run:
  repeats: 3
  poll_interval: 1.0
  timeout_sec: 600
  seed_strategy: "time"   # time | increment | fixed
  seed_base: 0
```

### 設定項目の説明

#### ルート

* `comfy_url`：ComfyUI のURL
* `workflow_json`：API形式でエクスポートした workflow JSON
* `output_root`：ローカルに保存するメタ情報のルート

#### `input_image`

* `node_id`：LoadImage 等の node_id
* `input_name`：通常 `"image"`
* `upload`：`true` の場合、実行前に画像を ComfyUI にアップロードします
* `upload_type`：通常 `"input"`
* `overwrite`：同名がある場合に上書きするか（基本 `false` 推奨）
* `upload_subfolder`：基本は空推奨（LoadImage側がサブフォルダ参照に弱い場合があるため）

#### `expression_preset`

* `node_id`：ExpressionPresetNode の node_id
* `expression_input_name`：通常 `"expression"`
* `expressions`：実行する表情の一覧（ここに書いた順で実行）

#### `save_image`（任意）

* `node_id`：SaveImage ノードID（prefix差し替えをしたい場合のみ）
* `filename_prefix_template`：`filename_prefix` に入れるテンプレ

  * 使える変数：`{image}` `{expr}` `{run}` `{seed}`

#### `seed_node`（任意）

* `node_id`：KSampler 等の node_id（seed差し替えしたい場合のみ）
* `input_name`：通常 `"seed"`

#### `run`

* `repeats`：1画像×1表情あたりの繰り返し回数（seedバリエーション数）
* `poll_interval`：完了待ちポーリング間隔（秒）
* `timeout_sec`：最大待ち時間（秒）。`null` で無制限
* `seed_strategy`：

  * `time`：時刻ベースでランダム
  * `increment`：`seed_base + 連番`
  * `fixed`：常に `seed_base`
* `seed_base`：`increment/fixed` の基準 seed

---

## よくあるエラーと対処

### `ModuleNotFoundError: No module named 'yaml'`

`pip install yaml` では入らず、正しくは **`PyYAML`** です。

```bash
pip install PyYAML
```

### `ComfyUI is not reachable`

* ComfyUI が起動しているか
* `comfy_url` が正しいか（`http://127.0.0.1:8188` 等）

### 画像が見つからない / 読み込めない

* `input_image.upload: true` の場合：アップロードに失敗していないか
* `upload: false` の場合：ComfyUI サーバ側の `input/` に該当ファイルが存在するか

---

## ライセンス

Copyright (c) 2025 fuji-tea
Released under the MIT License.

## 貢献

バグ報告や機能要望は Issue で受け付けています。
プルリクエストも歓迎します。

## 更新履歴

### v1.0.0
- 初回リリース
