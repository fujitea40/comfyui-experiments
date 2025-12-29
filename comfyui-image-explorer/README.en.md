# ComfyUI Image Generation Exploration Tool

[日本語](README.md) | English

A tool that automates image generation by combining multiple prompt parameters via the ComfyUI API.
You specify an exploration axis (e.g., hairstyle, expression) and generate all candidates along that axis exhaustively.

## Features

- ✨ **Exploratory image generation**: Automatically generate all patterns for a single axis (e.g., hairstyle, expression)
- 🎯 **Flexible configuration**: Easy customization with YAML/JSON config files
- 📊 **Progress tracking**: Records used axes and tracks them until all axes have been exhausted
- 🔄 **Reproducibility**: Saves metadata for each generation so you can reproduce results later
- 🛡️ **Error handling**: Properly handles ComfyUI API connection errors and timeouts
- 📈 **Progress display**: Shows a real-time progress bar and estimated remaining time

## Requirements

### ComfyUI
- ComfyUI must be installed and running
- Default URL: `http://127.0.0.1:8188`

### Python
- Python 3.10 or later

### Python dependencies

In addition to the standard library, you’ll need:

```bash
requests>=2.31.0
pyyaml>=6.0.0
```

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd comfyui-experiments/comfyui-image-explorer
```

### 2. Install dependencies

#### Using pip

```bash
pip install -r requirements.txt
```

#### Manual install

```bash
pip install requests pyyaml
```

### 3. Prepare the config file

Edit `config/config.yaml` to match your environment:

```bash
cp config/config.example.yaml config/config.yaml
# then edit config/config.yaml with your favorite editor
```

Prepare and place your workflow JSON file yourself:
- Enable **Developer mode** in ComfyUI
- Export via **File → Export (API)**

A sample workflow JSON is included in the `workflow/` folder.
Specify the workflow file name in `config.yaml`.

> Note: The `workflow/` folder is just a storage location the author uses.  
> You can store workflow JSON files in a different folder as well—this tool will work as long as `workflow.json_path` points to the right file.

## Project structure

```text
comfyui-experiments/
├─project/
|   ├── main.py                # Entry point
|   ├── config_loader.py       # Loads config files
|   ├── models.py              # Dataclasses
|   ├── prompt_builder.py      # Builds prompts / generates combinations
|   ├── workflow.py            # Workflow JSON manipulation
|   ├── comfyui_client.py      # ComfyUI API client
|   ├── state_manager.py       # Axis state tracking
|   ├── utils.py               # Utility helpers
|   ├── requirements.txt       # Dependencies
|   ├── DESIGN.md              # Design doc
|   ├── README.md              # Japanese README
|   └── config/
|       └── config.yaml        # Config file (create it)
└─workflow/                    # Workflow storage
  └── workflow.json            # Workflow JSON (create/prepare it)
```

## Usage

### Basic usage

```bash
# Run with the default config
python main.py

# Specify a config file explicitly
python main.py -c config.yaml
```

### CLI arguments

```bash
python main.py --help
```

Example output:

```text
usage: main.py [-h] [-c CONFIG] [-p] [-v] [--log-file LOG_FILE]

ComfyUI Image Generation Tool - Explore multiple prompt parameters

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        config file path (default: config.yaml)
  -p, --progress        show progress only and exit
  -v, --verbose         enable verbose logging
  --log-file LOG_FILE   write logs to a file
```

### Example run

#### 1. Normal run

```text
============================================================
Starting ComfyUI Image Generation Tool
============================================================

==================================================
Exploration progress: 3/10 (30.0%)
==================================================

Used axes:
  ✓ breasts
  ✓ hair_style
  ✓ expression

Unused axes:
  ○ hair_color
  ○ gaze
  ○ pose
  ○ outfit
  ○ state
  ○ angle
  ○ accessory
==================================================

✓ Connected to ComfyUI
Selected exploration axis: hair_color
Count: 40 patterns × 2 repeats = 80 images

Proceed? (y/n): y

============================================================
Starting generation
  Axis: hair_color
  Patterns: 40
  Repeats: 2
  Total: 80
============================================================

Progress: |████████████████████████████████████████████████  | 75/80 done (about 30s remaining)
```

#### 2. Check progress only

```bash
python main.py -p
```

#### 3. Verbose logging + log file

```bash
python main.py -v --log-file generation.log
```

## Config file (`config.yaml`)

### Basic structure

```yaml
# Execution settings
execution:
  repeats: 2                          # Repeats per pattern
  randomize_non_target: true          # Randomize non-target axes
  comfy_url: "http://127.0.0.1:8188"  # ComfyUI URL
  state_file: "axis_state.json"       # State file path
  poll_interval: 1.0                  # Poll interval (seconds)

# Workflow settings
workflow:
  json_path: "../workflow/illust_image.json"  # Workflow JSON file
  output_root: "C:/ComfyUI/output"            # Output root
  node_mapping:                               # Node ID mapping
    positive_prompt: "2"
    negative_prompt: "3"
    ksampler: "4"
    empty_latent: "5"
    save_image: "7"
    lora: "18"
    perky_breasts_lora: "19"

# Prompt templates
prompt_template:
  fixed_positive:                     # Fixed positive prompts
    - "1girl"
    - "anime style"
    - "cute face"

  axes:                               # Variable axes
    - name: "hair_style"
      choices:
        - "long hair"
        - "short hair"
        - "bob cut"

    - name: "angle"                   # Weighted axis
      choices:
        - {text: "front view", weight: 2.0}
        - {text: "side view", weight: 0.3}
        - {text: "back view", weight: 0.0}

  negative:                           # Negative prompts
    - "bad anatomy"
    - "blurry"

# Sampler choices
sampler_choices:
  steps: [20, 25]
  cfg: [6.0, 7.0]
  sampler_name: ["euler", "dpmpp_2m"]
  scheduler: ["karras", "normal"]

# LoRA choices
lora_choices:
  names: ["frilled_bikini.safetensors"]
  model_strength: [0.4, 0.8]
  clip_strength: [0.8, 1.2]
```

### Key settings

#### `execution`
| Setting | Description | Default |
|---|---|---|
| `repeats` | Repeats per pattern | 2 |
| `randomize_non_target` | Randomize non-target axes | true |
| `comfy_url` | ComfyUI URL | http://127.0.0.1:8188 |
| `state_file` | File to record used axes | axis_state.json |
| `poll_interval` | Poll interval (seconds) | 1.0 |

#### `workflow.node_mapping`
Set node IDs from your ComfyUI workflow JSON.
Create a workflow in ComfyUI, then check each node ID and fill them in here.

#### `prompt_template.axes`
Define exploration axes. Two supported formats:

- **Uniform choices**: a list of strings
  ```yaml
  - name: "hair_style"
    choices:
      - "long hair"
      - "short hair"
  ```

- **Weighted choices**: `{text: "...", weight: ...}`
  ```yaml
  - name: "angle"
    choices:
      - {text: "front view", weight: 2.0}
      - {text: "side view", weight: 0.3}
      - {text: "", weight: 0.2}  # Empty is allowed
  ```

## Output

### Directory structure

```text
output/
├── 0001_a3f5b2/              # Run ID
│   ├── params.json           # Metadata
│   ├── img_00001_.png        # Image 1
│   └── img_00002_.png        # Image 2
├── 0002_b4c7d3/
│   ├── params.json
│   ├── img_00001_.png
│   └── img_00002_.png
...
```

### Metadata (`params.json`)

Example metadata saved per run:

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
    "expression": "smile"
  }
}
```

## State management

### `axis_state.json`

A file that records which axes have been used:

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

### Reset

To reset all axes to unused:

```bash
# Delete axis_state.json
rm axis_state.json

# Or via Python
python -c "from state_manager import StateManager; StateManager('axis_state.json').reset()"
```

## Troubleshooting

### Cannot connect to ComfyUI

```text
✗ Cannot connect to ComfyUI
  URL: http://127.0.0.1:8188
  Make sure ComfyUI is running
```

**Fix**:
1. Confirm ComfyUI is running
2. Confirm the URL in `config.yaml` (`execution.comfy_url`)
3. Check firewall settings

### Config file not found

```text
Config file not found: config.yaml
```

**Fix**:
1. Confirm the file exists
2. Use `-c` to specify the correct path

### Workflow JSON not found

```text
Workflow file not found: illust_image.json
```

**Fix**:
1. Export the workflow from ComfyUI
2. Check `workflow.json_path` in `config.yaml`

### Node ID not found

```text
Node ID 2 not found
```

**Fix**:
1. Check node IDs in your ComfyUI workflow
2. Update `workflow.node_mapping` in `config.yaml`

## For developers

### Module responsibilities

| Module | Responsibility |
|---|---|
| `main.py` | Orchestration / entry point |
| `config_loader.py` | Load YAML/JSON config |
| `models.py` | Dataclass definitions |
| `prompt_builder.py` | Build prompts / generate combinations |
| `workflow.py` | Edit workflow JSON |
| `comfyui_client.py` | Communicate with ComfyUI API |
| `state_manager.py` | Track used axes |
| `utils.py` | Shared utilities |

> `DESIGN.md` is referenced in the Japanese README, but may not exist yet.

### Unit test example

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

### Log levels

```python
import logging

# DEBUG: detailed debug info
# INFO: general info
# WARNING: warnings
# ERROR: errors

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
```

## License

Copyright (c) 2025 fuji-tea  
Released under the MIT License.

## Contributing

Bug reports and feature requests are welcome via Issues.
Pull requests are also welcome.

## Changelog

### v1.0.0
- Initial release
