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

## [Workflow for Generating Character Expression Variations](./doc/GenMaskAndInpaint.en.md)

This workflow generates a mask around the face area of an input character image, then feeds per-expression presets (see the next section) into both the prompt and KSampler parameters, and regenerates **only the expression** via inpainting.

![example](doc/img/GenMaskAndInpaint.png)

## [Expression Preset Custom Node](./expression_preset/README.en.md)

This is a custom node for predefining presets so you can easily switch expressions when using the workflow above.

The node stores the expression name, prompt, and parameters. From the workflow, you only need to select the expression, and the appropriate prompt/parameters will be applied automatically.

## [Character Expression Variation Batch Tool](./comfyui-image-explorer/README.expression_batch_preset.md)

Using the expression-variation workflow and the ExpressionPresetNode custom node described above, this tool generates expression variations in bulk for all images under the specified folder.

You can also generate multiple variations per expression by setting the number of repeats, making it easy to pick the best results.


## Credits (Models)

Images in this repository were generated using the following model(s):

- MeinaMix — by Meina (Civitai) — Attribution required (per Civitai permissions)
- Pastel-Mix — by andite (Civitai)
- Counterfeit — by rpdwdw (Civitai)
- Anything — by Yuno779 (Civitai)
