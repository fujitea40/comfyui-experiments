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

## [キャラ表情差分生成用ワークフロー](./doc/GenMaskAndInpaint.md)

入力したキャラクター画像の顔部分でマスクを生成し、
表情プリセットカスタムノード（次項参照）しておいた表情毎のパラメータをプロンプトとKsamplerにインプットし、
表情のみInpaintで生成しなおします。
本ワークフローと下記プリセットカスタムノードで表情パラメータをチューニングして[生成したデモ](https://fujitea40.github.io/comfyui_expression_demo/)を公開しました。

![example](doc/img/GenMaskAndInpaint.png)

## [表情プリセットカスタムノード](./expression_preset/README.md)

上記のワークフローで簡単に生成する表情を変更できるよう、あらかじめプリセットしておくためのカスタムノードです。
このカスタムノードで表情名、プロンプト、パラメータを保持しておき、ワークフローからは表情を選択するだけで適切なプロンプトを入力するようにします。

## [キャラ表情差分生成一括バッチツール](./comfyui-image-explorer/README.expression_batch_preset.md)

上記のキャラ表情差分生成ワークフローと表情プリセットカスタムノードを使用して、指定したフォルダ配下にある画像の表情差分を一括で生成します。
このとき、指定した回数を生成可能しているので、出来の良いものを選ぶことができます。

## Credits (Models)

Images in this repository were generated using the following model(s):

- MeinaMix — by Meina (Civitai) — Attribution required (per Civitai permissions)
- Pastel-Mix — by andite (Civitai)
- Counterfeit — by rpdwdw (Civitai)
- Anything — by Yuno779 (Civitai)

