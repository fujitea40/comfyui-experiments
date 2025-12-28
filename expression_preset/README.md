# 表情プリセットカスタムノード

本カスタムノードは、smile, angryといった表情名に対して、あらかじめプロンプトとパラメータを設定しておき、表情名を選択するだけで接続したpositiveプロンプトとKsamplerにパラメータを入力するために使用します。

# 導入方法

+ リポジトリを(expression_presetフォルダ)をcustom_nodes配下に格納してください。
```
  ComfyUI/
    └──custom_nodes/
|        └─── expression_preset
```

+ 現時点では、パラメータはソースにハードコーディングしています。ソースの該当箇所を確認し、必要に応じて自分のモデルに適したパラメータに書き換えてください。
    + 表情用プロンプト部分
    ```
            expr_prompt = {
            "neutral": (
                "neutral expression, calm face, relaxed mouth, eyes open, relaxed eyes, "
                "emotionless, natural look, same eye color, consistent eye color"
            ),
            "smile": (
                "gentle smile, soft smile, slightly curved mouth, happy but calm expression, "
                "eyes relaxed"
            ),
    ```
    + パラメータ値部分
    ```
            params = {
            "neutral":     {"steps": 25, "cfg": 8.0, "denoise": 0.28},
            "smile":       {"steps": 25, "cfg": 8.0, "denoise": 0.48},
            "big_smile_closed_eyes": {"steps": 25, "cfg": 8.0, "denoise": 0.48},
    ```

+ 設定した**Expression Preset Selector**ノードからの出力は、以下のようにテキストエンコーダーとKsamplerノードに接続します。
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