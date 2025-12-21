# ComfyUI画像生成探索ツール

ComfyUI APIを使用して、複数のプロンプトパラメータを組み合わせた画像生成を自動化するツールです。
探索軸（髪型、表情など）を指定し、その軸の全候補を網羅的に生成します。

## 特徴

- ✨ **探索的な画像生成**: 1つの軸（髪型、表情など）の全パターンを自動生成
- 🎯 **柔軟な設定**: YAML/JSON形式の設定ファイルで簡単カスタマイズ
- 📊 **進捗管理**: 使用済み軸を記録し、すべての軸を使い切るまで追跡
- 🔄 **再現性**: 各生成のメタデータを保存し、後から再現可能
- 🛡️ **エラーハンドリング**: ComfyUI APIの接続エラーやタイムアウトを適切に処理
- 📈 **進捗表示**: リアルタイムで進捗バーと残り時間を表示

## 必要な環境

### ComfyUI
- ComfyUI がインストールされ、起動していること
- デフォルトURL: `http://127.0.0.1:8188`

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

### 3. 設定ファイルの準備

`config/config.yaml`を編集して、環境に合わせて設定します：

```bash
cp config/config.example.yaml comfig/config.yaml
nano config/config.yaml  # または任意のエディタで編集
```

ワークフローファイルは、自身で準備して格納してください。
開発者モードをONにして、File->Export(API)で出力します。
サンプルとしてworkflowフォルダに１ファイル入れています。
`config.yaml`にワークフローファイル名を指定してください。
`workflow`フォルダは、自分の蓄積用に作ったものなので、
違うフォルダに格納しても動作に問題ありません。

## ファイル構成

```
comfyui-experiments/
├─project/
|   ├── main.py                # メインプログラム
|   ├── config_loader.py       # 設定ファイル読み込み
|   ├── models.py              # データクラス定義
|   ├── prompt_builder.py      # プロンプト構築
|   ├── workflow.py            # ワークフロー操作
|   ├── comfyui_client.py      # ComfyUI API通信
|   ├── state_manager.py       # 状態管理
|   ├── utils.py               # 汎用ユーティリティ
|   ├── requirements.txt       # 依存パッケージ一覧
|   ├── DESIGN.md              # 設計ドキュメント
|   ├── README.md              # このファイル
|   └── config/                # このファイル
|       └── config.yaml        # 設定ファイル（要作成）
└─workflow/                    # ワークフロー置き場
  └── workflow.json            # ワークフローファイル（要作成）
   
```

## 使い方

### 基本的な使い方

```bash
# デフォルト設定で実行
python main.py

# 設定ファイルを指定
python main.py -c config.yaml
```

### コマンドライン引数

```bash
python main.py --help
```

```
usage: main.py [-h] [-c CONFIG] [-p] [-v] [--log-file LOG_FILE]

ComfyUI画像生成ツール - 複数のプロンプトパラメータを探索

optional arguments:
  -h, --help            ヘルプを表示
  -c CONFIG, --config CONFIG
                        設定ファイルのパス (デフォルト: config.yaml)
  -p, --progress        進捗のみ表示して終了
  -v, --verbose         詳細なログを表示
  --log-file LOG_FILE   ログをファイルに出力
```

### 実行例

#### 1. 通常実行

```bash
$ python main.py

============================================================
ComfyUI画像生成ツールを起動します
============================================================

==================================================
探索進捗: 3/10 (30.0%)
==================================================

使用済み軸:
  ✓ breasts
  ✓ hair_style
  ✓ expression

未使用軸:
  ○ hair_color
  ○ gaze
  ○ pose
  ○ outfit
  ○ state
  ○ angle
  ○ accessory
==================================================

✓ ComfyUIに接続しました
探索軸を選択: hair_color
生成数: 40 パターン × 2 回 = 80 枚

実行しますか？ (y/n): y

============================================================
画像生成を開始します
  探索軸: hair_color
  パターン数: 40
  繰り返し: 2
  合計生成数: 80
============================================================

進捗: |████████████████████████████████████████████████  | 75/80 完了 (残り約30秒)
```

#### 2. 進捗のみ確認

```bash
python main.py -p
```

#### 3. 詳細ログ付きで実行

```bash
python main.py -v --log-file generation.log
```

## 設定ファイル（config.yaml）

### 基本構造

```yaml
# 実行設定
execution:
  repeats: 2                          # 各パターンの繰り返し回数
  randomize_non_target: true          # 非探索軸をランダム化
  comfy_url: "http://127.0.0.1:8188"  # ComfyUI URL
  state_file: "axis_state.json"       # 状態ファイルパス
  poll_interval: 1.0                  # ポーリング間隔（秒）

# ワークフロー設定
workflow:
  json_path: "../workflow/illust_image.json"      # ワークフローJSONファイル
  output_root: "C:/ComfyUI/output"    # 出力ルート
  node_mapping:                       # ノードIDマッピング
    positive_prompt: "2"
    negative_prompt: "3"
    ksampler: "4"
    empty_latent: "5"
    save_image: "7"
    lora: "18"
    perky_breasts_lora: "19"

# プロンプトテンプレート
prompt_template:
  fixed_positive:                     # 固定ポジティブプロンプト
    - "1girl"
    - "anime style"
    - "cute face"
  
  axes:                               # 可変軸
    - name: "hair_style"
      choices:
        - "long hair"
        - "short hair"
        - "bob cut"

    - name: "angle"                   # 重みづけ軸
      choices:
        - {text: "front view", weight: 2.0}
        - {text: "side view", weight: 0.3}
        - {text: "back view", weight: 0.0}
  
  negative:                           # ネガティブプロンプト
    - "bad anatomy"
    - "blurry"

# サンプラーの選択肢
sampler_choices:
  steps: [20, 25]
  cfg: [6.0, 7.0]
  sampler_name: ["euler", "dpmpp_2m"]
  scheduler: ["karras", "normal"]

# LoRAの選択肢
lora_choices:
  names: ["frilled_bikini.safetensors"]
  model_strength: [0.4, 0.8]
  clip_strength: [0.8, 1.2]
```

### 主要設定の説明

#### `execution`
| 設定 | 説明 | デフォルト |
|-----|------|-----------|
| `repeats` | 各パターンの繰り返し回数 | 2 |
| `randomize_non_target` | 非探索軸をランダム化するか | true |
| `comfy_url` | ComfyUIのURL | http://127.0.0.1:8188 |
| `state_file` | 使用済み軸を記録するファイル | axis_state.json |
| `poll_interval` | 完了チェックの間隔（秒） | 1.0 |

#### `workflow.node_mapping`
ComfyUIワークフローのノードIDを指定します。
ComfyUIでワークフローを作成し、各ノードのIDを確認して設定してください。

#### `prompt_template.axes`
探索する軸を定義します。各軸には以下の形式があります：

- **等確率選択**: 文字列のリスト
  ```yaml
  - name: "hair_style"
    choices:
      - "long hair"
      - "short hair"
  ```

- **重み付き選択**: `{text: "...", weight: ...}` 形式
  ```yaml
    - name: "angle"
      choices:
        - {text: "front view", weight: 2.0}
        - {text: "side view", weight: 0.3}
        - {text: "", weight: 0.2}  # 空も可能
  ```

## 出力

### ディレクトリ構造

```
output/
├── 0001_a3f5b2/              # 実行ID
│   ├── params.json           # メタデータ
│   ├── img_00001_.png        # 生成画像1
│   └── img_00002_.png        # 生成画像2
├── 0002_b4c7d3/
│   ├── params.json
│   ├── img_00001_.png
│   └── img_00002_.png
...
```

### メタデータ（params.json）

各実行ディレクトリに保存されるメタデータの例：

```json
{
  "axis": "hair_color",
  "positive": "1girl, anime style, cute face, big eyes, black hair, smile",
  "negative": "bad anatomy, blurry",
  "steps": 20,
  "cfg": 7.0,
  "sampler": "euler",
  "scheduler": "karras",
  "seed": 1234567890,
  "lora": "OneBreastOut.safetensors",
  "lora_model_strength": 0.0,
  "lora_clip_strength": 0.0,
  "perky_breasts_model_strength": 0.8,
  "perky_breasts_clip_strength": 1.2,
  "prompt_values": {
    "hair_style": "long hair",
    "hair_color": "black hair",
    "expression": "smile",
    ...
  }
}
```

## 状態管理

### axis_state.json

使用済み軸を記録するファイル：

```json
{
  "version": "1.0",
  "used_axes": [
    "breasts",
    "hair_style",
    "expression"
  ],
  "last_updated": "2025-12-21T10:30:00.123456",
  "total_used": 3
}
```

### リセット方法

すべての軸を未使用に戻す場合：

```bash
# axis_state.jsonを削除
rm axis_state.json

# または、Pythonで
python -c "from state_manager import StateManager; StateManager('axis_state.json').reset()"
```

## トラブルシューティング

### ComfyUIに接続できない

```
✗ ComfyUIに接続できません
  URL: http://127.0.0.1:8188
  ComfyUIが起動しているか確認してください
```

**解決方法**:
1. ComfyUIが起動しているか確認
2. URLが正しいか確認（`config.yaml`の`comfy_url`）
3. ファイアウォールの設定を確認

### 設定ファイルが見つからない

```
設定ファイルが見つかりません: config.yaml
```

**解決方法**:
1. `config.yaml`が存在するか確認
2. `-c`オプションで正しいパスを指定

### ワークフローJSONが見つからない

```
ワークフローファイルが見つかりません: illust_image.json
```

**解決方法**:
1. ComfyUIでワークフローを保存
2. `config.yaml`の`workflow.json_path`を確認

### ノードIDが見つからない

```
ノードID 2 が見つかりません
```

**解決方法**:
1. ComfyUIのワークフローでノードIDを確認
2. `config.yaml`の`workflow.node_mapping`を更新

## 開発者向け情報

### モジュール構成

各モジュールの責務：

| モジュール | 責務 |
|----------|------|
| `main.py` | メインプログラム、全体のオーケストレーション |
| `config_loader.py` | 設定ファイル（YAML/JSON）の読み込み |
| `models.py` | データクラス定義 |
| `prompt_builder.py` | プロンプト構築、パラメータ組み合わせ生成 |
| `workflow.py` | ワークフローJSONの操作 |
| `comfyui_client.py` | ComfyUI APIとの通信 |
| `state_manager.py` | 使用済み軸の状態管理 |
| `utils.py` | 汎用ユーティリティ関数 |

<! -- 作成してません。
詳細は[DESIGN.md](DESIGN.md)を参照してください。
-->

### 単体テスト（例）

```python
# test_prompt_builder.py
import pytest
from prompt_builder import PromptBuilder

def test_build_positive_prompt():
    template = create_test_template()
    builder = PromptBuilder(template, randomize_non_target=False)
    
    axis_values = {
        "hair_style": "long hair",
        "expression": "smile"
    }
    
    positive, negative = builder.build_prompts(axis_values)
    
    assert "1girl" in positive
    assert "long hair" in positive
    assert "smile" in positive
    assert "bad anatomy" in negative
```

### ログレベル

```python
# ログレベルの設定
import logging

# DEBUG: 詳細なデバッグ情報
# INFO: 一般的な情報メッセージ
# WARNING: 警告メッセージ
# ERROR: エラーメッセージ

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
```

## ライセンス

Copyright (c) 2025 fuji-tea
Released under the MIT License.

## 貢献

バグ報告や機能要望は Issue で受け付けています。
プルリクエストも歓迎します。

## 更新履歴

### v1.0.0
- 初回リリース