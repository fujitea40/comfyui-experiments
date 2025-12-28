# 表情差分作成ワークフロー（ComfyUI）

[キャラ表情差分生成用ワークフロー](../workflow/GenmaskAndInpaint.json)は、**立ち絵素材から表情差分を安定して生成するための ComfyUI ワークフローおよびカスタムノード構成**をまとめたものです。

- 顔のみを inpaint で差し替え
- 同一性（髪・服・輪郭）を最大限維持
- 表情ごとに最適な denoise / cfg をプリセット化

を目的としています。
workflowとカスタムノードを適用することで、expression_presetカスタムノードからプルダウンで生成する表情を選択し、
生成することで、表情変更した画像を生成します。

![workflow](img/GenMaskAndInpaint_Workflow.png)

![画像サンプル](img/GenMaskAndInpaint2.png)
---

## 使用カスタムノード

### マスク生成

- **comfyui_segment_anything**
  - https://github.com/storyicon/comfyui_segment_anything?tab=readme-ov-file#groundingdino

- **expression_preset**
  - https://github.com/fujitea40/comfyui-experiments/tree/main/expression_preset


#### 導入方法
**comfyui_segment_anything**の導入については、記載のサイトを確認してください。
**expression_preset**は、本リポジトリよりチェックアウトして配置すればOK
```
  ComfyUI/
    └──custom_nodes/
        └─── expression_preset
```

workflowには上記カスタムノードの他、実際に動作確認したモデルが設定されてしまっています。自身で使っているモデルに差し替え、プリセットも調整の上使用してください。
expression_preset内でプリセットされているパラメータの変更方法は、[README](../expression_preset/README.md)を参照してください。

SD1.5系のモデルで生成した画像は比較的表情がきれいに生成されました(上画像)が、SDXLはいまいち表情が出ません。基本的にはSD1.5系が前提としてください。

### 確認済みモデル
+ [MeinaMix v12](https://civitai.com/models/7240/meinamix)
+ [Anything V3](https://civitai.com/models/66?modelVersionId=75)
  + BigSmileは閉じた目が崩れやすいので、denoise低め推奨
+ [Counterfeit-V3.0](https://civitai.com/models/4468?modelVersionId=57618)
  + 崩れやすいのでランダムシードで何度か生成必要
+ [Pastel-Mix](https://civitai.com/models/5414?modelVersionId=6297)

## 今後の更新予定

反響が高いほど対応優先度が上がりますので、興味がある方はIssueからご要望ください。

+ 顔のみの差分画像も保存対象とする可能性あり。立ち絵差分の用途と考えると現状の差分含んだ全身画像で十分かと思っているが、要望があれば。
+ 一発で全表情を出力可能にする。
+ 実用向けに、[comfyui-image-explorer](../comfyui-image-explorer/)の機構を利用して、複数パラメータパターンの差し替えをAPI実行し、一回で同一表情を複数パターン生成、取捨選択可能にする。
+ その他の箇所（ポーズ、髪型、アクセサリー）の差分生成自動化
+ ControlNet併用で安定感向上（現状SDXLモデル試したところdenoise上げないと弱いし、上げるとかなり崩れる）

## 生成サンプル
+ MeinaMix
  ![MeinaMix](../doc/img/GenMaskAndInpaint.png)
+ Anything
  ![Anything](../doc/img/GenMaskAndInpaint_anything.png)
+ Counterfeit
  ![Counterfeit](../doc/img/GenMaskAndInpaint_counterfate.png)
+ Pastel-Mix
  ![Pastel-Mix](../doc/img/GenMaskAndInpaint_pastelMix.png)

## ライセンス

Copyright (c) 2025 fuji-tea
Released under the MIT License.

## 貢献

バグ報告や機能要望は Issue で受け付けています。
プルリクエストも歓迎します。

## 更新履歴

### v1.0.0
- 2025/12/28 初回リリース
