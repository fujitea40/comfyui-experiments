# comfyui-experiments

[日本語](README.md) | English

This repository contains various things I built for ComfyUI.
All of them are experimental and have **not** been tested with sufficient data.

If you have requests or run into issues, I'd appreciate it if you could open an Issue.
(I may not always be able to respond.)

## [Prompt Exploration Tool](./comfyui-image-explorer/README.image_explorer.en.md)

By writing prompt candidates per category in a config file, you can generate request patterns such as:

- Keep everything fixed except the exploration axis
- Execute all combinations for the exploration axis plus CFG and LoRA settings

…and then run them via the API.

This helps avoid the “combinatorial explosion” where running every possible prompt combination quickly reaches astronomical numbers, and instead aims for a realistic number of patterns (hundreds to around a thousand).

## ~~Workflow for Generating Character Expression Variations~~

Workflow for Generating Character Expression Variations has been moved to [comfy_exp_preset](https://github.com/fujitea40/comfy_exp_preset/blob/main/README.en.md)

## ~~Expression Preset Custom Node~~

Expression Preset Custom Node has been moved to [comfy_exp_preset](https://github.com/fujitea40/comfy_exp_preset/blob/main/README.en.md)

## [Character Expression Variation Batch Tool](./comfyui-image-explorer/README.expression_batch_preset.md)

Using the expression-variation workflow and the ExpressionPresetNode custom node described above, this tool generates expression variations in bulk for all images under the specified folder.

You can also generate multiple variations per expression by setting the number of repeats, making it easy to pick the best results.


## Credits (Models)

Images in this repository were generated using the following model(s):

- MeinaMix — by Meina (Civitai) — Attribution required (per Civitai permissions)
- Pastel-Mix — by andite (Civitai)
- Counterfeit — by rpdwdw (Civitai)
- Anything — by Yuno779 (Civitai)
