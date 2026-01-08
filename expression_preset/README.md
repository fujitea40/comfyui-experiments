# 表情プリセットカスタムノード

日本語 | [English](README.en.md)

本カスタムノードは、smile, angryといった表情名に対して、あらかじめプロンプトとパラメータを設定しておき、表情名を選択するだけで接続したpositiveプロンプトとKsamplerにパラメータを入力するために使用します。

# 導入方法

+ リポジトリを(expression_presetフォルダ)をcustom_nodes配下に格納してください。
```
  ComfyUI/
    └──custom_nodes/
|        └─── expression_preset
              ├─── __init__.py
              ├─── expression_preset.py
              └─── expression_presets.yaml   # 設定ファイル
```
+ expression_presets.yamlに各プロンプト、パラメータを好み、モデルに合わせて設定してください。
    + パラメータはデフォルト値があるので、上書きしたい場合だけ入力
```
defaults:
  params:
    steps: 25
    cfg: 8.0
    denoise: 0.48
    scheduler: karras
    sampler: dpmpp_2m_sde

expressions:
  neutral:
    expr_prompt: "neutral expression, calm face, relaxed mouth, eyes open, relaxed eyes, emotionless, natural look, same eye color, consistent eye color"
    params:
      denoise: 0.28
      scheduler: karras
      sampler: dpmpp_2m_sde
```

+ 設定した**Expression Preset Selector**ノードからの出力は、以下のようにテキストエンコーダーとKsamplerノードに接続します。
+ expression, expr_prompt, meta_jsonは設定値を確認するためのデバッグ用です。必要ならPreview as Textで確認できます。
![usage](../doc/img/Expression_Preset_Selector_usage.png)

## ライセンス

Copyright (c) 2025 fuji-tea
Released under the MIT License.

## 貢献

バグ報告や機能要望は Issue で受け付けています。
プルリクエストも歓迎します。

## 更新履歴

### v1.0.0
- 2025/12/28 初回リリース

### v1.0.1
- 2026/01/08 scheduler、samplerを読み込めるように更新