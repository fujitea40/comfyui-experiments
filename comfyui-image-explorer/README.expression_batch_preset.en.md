# Expression Preset Batch

[日本語](README.expression_batch_preset.md) | English

This is a batch tool for ComfyUI that assumes the custom node **[ExpressionPresetNode](../expression_preset/README.en.md)**.
It processes multiple images in a folder and runs generations in bulk for:

**expression × seed (repeats)**

It can:

* (Optional) Upload images to ComfyUI
* Replace the workflow **LoadImage (input image)** reference
* Replace the workflow **ExpressionPresetNode (expression)** input
* (Optional) Replace **seed**
* (Optional) Replace SaveImage `filename_prefix`
* Save execution metadata (`meta.json`) locally

---

## Features

* ✅ **Batch processing for a folder**: Automatically processes all images in the input folder
* ✅ **Preset-based expression management**: Centralize expression prompts & parameters in ExpressionPresetNode presets (YAML)
* ✅ **Seed variations**: Repeat `repeats` times per expression (supports multiple seed strategies)
* ✅ **Metadata logging**: Saves run details as `meta.json` for reproducibility and tracking

---

## Requirements

### ComfyUI

* ComfyUI must be installed and running
* Default URL: `http://127.0.0.1:8188`

### Python

* Python 3.10+

### Required Python packages

You need the following packages (besides the standard library):

```bash
requests>=2.31.0
pyyaml>=6.0.0
```

---

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd comfyui-experiments/comfyui-image-explorer
```

### 2. Install dependencies

#### Using `requirements.txt`

```bash
pip install -r requirements.txt
```

#### Install manually

```bash
pip install requests pyyaml
```

---

## Setup (Important)

### 1) Export the ComfyUI workflow in API format

Enable Developer Mode in ComfyUI, then export via:
`File -> Export (API)` and save the JSON anywhere you like.

This tool assumes an **API-format workflow JSON** (a dict mapping `node_id -> node definition`).

### 2) Required nodes in the workflow

At minimum, your workflow must include:

* **A LoadImage-equivalent node** (a node that stores the input image filename in `inputs["image"]`)
* **ExpressionPresetNode** (a custom node that receives `expression` as input)

Optional (supported if present/configured):

* **SaveImage**: if you want to override `filename_prefix` externally
* **KSampler (etc.)**: if you want to override the seed externally (useful when the workflow uses a fixed seed)

### 3) Record node IDs

Since the config file requires node IDs, check the `node_id` in ComfyUI (or in the exported JSON).
In the exported JSON, keys like `"10": { ... }` represent the `node_id`.

---

## Usage

### Basic run

```bash
python scripts/expression_preset_batch.py -i <input-images-folder> -c <config-file>
```

Example:

```bash
python scripts/expression_preset_batch.py -i ./input_images -c ./config/config.epb.yaml
```

### Options

* `--recursive`: Search subfolders as well
* `--limit N`: Process only the first N images
* `--dry-run`: Do not call the ComfyUI API (only show planned actions and generate metadata)
* `--verbose`: Enable debug logging

---

## Output

### Generated images

Generated images are saved according to **ComfyUI’s output settings**.

If you set `save_image.filename_prefix_template`, the tool will override SaveImage’s `filename_prefix`, which makes output organization easier.

### meta.json (local)

The tool also saves `meta.json` under `output_root` as a local execution log (for reproducibility and tracking).

Example:

```
outputs_epb/
  alice/
    neutral/
      0001_ab12cd/
        meta.json
```

---

## Config file (YAML)

### Example: `config/config.epb.example.yaml`

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

### Config fields

#### Root

* `comfy_url`: ComfyUI base URL
* `workflow_json`: API-exported workflow JSON
* `output_root`: Local root directory for metadata logs

#### `input_image`

* `node_id`: Node ID of LoadImage (or equivalent)
* `input_name`: Usually `"image"`
* `upload`: If `true`, uploads images to ComfyUI before execution
* `upload_type`: Usually `"input"`
* `overwrite`: Whether to overwrite if the same filename exists (recommended: `false`)
* `upload_subfolder`: Recommended to keep empty (some LoadImage setups are limited regarding subfolders)

#### `expression_preset`

* `node_id`: Node ID of ExpressionPresetNode
* `expression_input_name`: Usually `"expression"`
* `expressions`: List of expressions to run (executed in this order)

#### `save_image` (optional)

* `node_id`: SaveImage node ID (only if you want to override the prefix)
* `filename_prefix_template`: Template for `filename_prefix`

  * Available variables: `{image}` `{expr}` `{run}` `{seed}`

#### `seed_node` (optional)

* `node_id`: Node ID of KSampler (or equivalent) for seed override
* `input_name`: Usually `"seed"`

#### `run`

* `repeats`: Number of repetitions per image × expression (seed variations)
* `poll_interval`: Polling interval in seconds for completion checks
* `timeout_sec`: Max wait time in seconds (`null` for unlimited)
* `seed_strategy`:

  * `time`: Time-based random seed
  * `increment`: `seed_base + counter`
  * `fixed`: Always `seed_base`
* `seed_base`: Base seed used by `increment/fixed`

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'yaml'`

`pip install yaml` is not correct. Install **PyYAML** instead:

```bash
pip install PyYAML
```

### `ComfyUI is not reachable`

* Make sure ComfyUI is running
* Confirm `comfy_url` is correct (e.g. `http://127.0.0.1:8188`)

### “Image not found / cannot load image”

* If `input_image.upload: true`: check whether the upload step failed
* If `upload: false`: the file must already exist in the ComfyUI server’s `input/` directory with the same name

---

## License

Copyright (c) 2025 fuji-tea
Released under the MIT License.

---

## Contributing

Bug reports and feature requests are welcome via Issues.
Pull requests are also welcome.

---

## Changelog

### v1.0.0

* Initial release

