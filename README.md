# comfyui-experiments

日本語 | [English](README.en.md)

ComfyUI用に何か作ったものを入れてます。
いずれも実験的に作ったもので、十分なデータでテストしたものではありません。
もし要望やうまくいかない点があればIssueで挙げてもらえると助かります。
（必ずしも対応するかはわかりません）

## [プロンプト探索ツール](./comfyui-image-explorer/README.image_explorer.md)

プロンプトの候補をカテゴリ毎に設定ファイルに書くと、
探索軸以外は固定、探索軸とcfgやLoRAは全パターン実行といったリクエストパターンを作成し、APIから実行できます。
プロンプト全通り実行するとすぐに億や兆といった桁にいってしまうのを防ぎ、数百～千程度の現実的なパターン数を狙うことができます。

## ~~キャラ表情差分生成用ワークフロー~~
キャラ表情差分生成用ワークフローは、[comfy_exp_preset](https://github.com/fujitea40/comfy_exp_preset)に移しました

## ~~表情プリセットカスタムノード~~
表情プリセットカスタムノードは、[comfy_exp_preset](https://github.com/fujitea40/comfy_exp_preset)に移しました

## [キャラ表情差分生成一括バッチツール](./comfyui-image-explorer/README.expression_batch_preset.md)

上記のキャラ表情差分生成ワークフローと表情プリセットカスタムノードを使用して、指定したフォルダ配下にある画像の表情差分を一括で生成します。
このとき、指定した回数を生成可能しているので、出来の良いものを選ぶことができます。

## [キャラ立ち絵生成ワークフロー](./doc/CharacterSpriteWorkflow.md)

キャラクターの立ち絵差分を生成するためのワークフローです。
衣装LoRAであらかじめ目的の衣装の直立画像を生成しておき、それに対してIP-Adapterで参照することでより服装を固定化します。
加えて、OpenPose ControlNetを用いて姿勢を固定化することで、ある程度一貫性のある立ち絵を生成できます。
Qwen-Image-Editのような高性能、高負荷なモデルには及びませんが、低コスト、ローエンドGPUでも動作可能となることを目指しています。

![image](doc/img/StandingImage.png)

## Credits (Models)

Images in this repository were generated using the following model(s):

- MeinaMix — by Meina (Civitai) — Attribution required (per Civitai permissions)
- Pastel-Mix — by andite (Civitai)
- Counterfeit — by rpdwdw (Civitai)
- Anything — by Yuno779 (Civitai)

