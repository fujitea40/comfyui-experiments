import os, json, time, itertools, uuid, random, math
from pathlib import Path
import requests

COMFY = "http://127.0.0.1:8188"

# ====== 環境設定 ======
WORKFLOW_JSON = "illust_image.json"

POS_NODE_ID = "2"
NEG_NODE_ID = "3"
KSAMPLER_ID = "4"
EMPTY_LATENT_ID = "5"
SAVE_NODE_ID = "7"
PERKY_BREASTS_ID = "19"
LORA_ID = "18"

RUN_ROOT = Path(r"C:\ComfyUI\ComfyUI_windows_portable_nvidia\ComfyUI_windows_portable\ComfyUI\output")

AXIS_STATE_FILE = Path("axis_state.json")
# 一つの選択に対して何度実行するか
repeats = 2
# 軸以外をランダムで選ぶか
RANDOMIZE_NON_TARGET = True
# ======================


# ====== プロンプト候補（探索軸）======
POS_PARTS = [
    [("breasts out",1.0), 
    ("one breast out",1.0), 
    ("nipple slip", 0.5),
    ("sideboob", 0.5),
    ("underboob", 0.5), 
    ("areola slip", 0.3),
    ("breasts slip", 0.7),
    ("",0.2)],                         # breasts
    ["long hair", "short hair", "bob cut", "twin tails",
     "ponytail", "side ponytail", "wavy hair", "straight hair",
     "messy hair", "ahoge"],                                   # hair_style
    ["black hair", "brown hair", "blonde hair", "blue hair",
     "pink hair", "silver hair", "white hair", "red hair",
     "purple hair", "green hair"],                             # hair_color
    ["smile", "gentle smile", "closed eyes smile",
     "shy smile", "neutral expression", "serious expression",
     "surprised", "embarrassed", "angry", "sad expression"],   # expression
    ["looking at viewer", "looking away", "looking down",
     "looking up", "head tilt", "face close-up"],              # gaze
    ["standing", "sitting", "leaning forward", "leaning back",
     "arms behind back", "hands on hips", "crossed arms"],     # pose
    ["nude", "bikini", "frilled bikini", "micro bikini",
     "casual outfit", "yukata", "lingerie", "negligee"],       # outfit
    [("wet clothes", 0.2),
     ("oversized clothes",0.7), 
     ("",3.0)],                  # state
    [                                                          # angle
    ("front view",2.0),              # 正面
    ("side view",0.3),               # 横から
    ("back view",0.0),               # 後ろから
    ("three-quarter view",3.0),      # 斜め（定番・安定）
    ("from above",0.0),              # 上から見下ろし
    ("from below",0.0),              # 下から見上げ
    ("low angle",0.7),               # ローアングル
    ("high angle",0.7),              # ハイアングル
    ("overhead view",0.0),           # 真上
    ("close-up",1.5),                # クローズアップ
    ("upper body",2.5),              # 上半身
    ("portrait",3.0),                # バストアップ寄り
    ("full body",1.5),               # 全身
    ("cowboy shot",0.7),             # 太もも〜上
    ("extreme close-up",0.2)         # 顔アップ（破綻しやすいので注意）
    ],
    [                                                           # accessory
    ("",3.0),                         # なし（重要：ランダム用）
    ("glasses",1.0),                  # 眼鏡
    ("round glasses",0.2),            # 丸眼鏡
    ("rimless glasses",0.2),          # 縁なし眼鏡
    ("sunglasses",0.1),               # サングラス
    ("earrings",0.8),                 # ピアス
    ("hoop earrings",0.4),            # フープピアス
    ("stud earrings",0.7),            # 小さなピアス
    ("necklace",1.0),                 # ネックレス
    ("choker",2.0),                   # チョーカー（効きやすい）
    ("hair ribbon",1.0),              # 髪リボン
    ("hair clip",1.0),                # ヘアピン
    ("hairband",1.0),                 # カチューシャ
    ("bow",1.0),                      # リボン
    ("flower hair ornament",0.7),     # 花飾り
    ("earphones",0.3),                # イヤホン
    ("headphones",0.3),               # ヘッドホン
    ("bracelet",1.0),                 # ブレスレット
    ("ring",1.0)                      # 指輪
    ]
]

AXIS_NAMES = [
    "breasts",
    "hair_style",
    "hair_color",
    "expression",
    "gaze",
    "pose",
    "outfit",
    "state",
    "angle",
    "accessory"
]
# =====================================


# ====== 固定プロンプト ======
POS_PARTS_FIX = [
    "1girl",
    "anime style",
    "cute face",
    "big eyes",
    "soft lighting",
    "simple background"
]

NEG_PARTS = [
    "bad anatomy",
    "bad face",
    "deformed",
    "extra limbs",
    "low quality",
    "worst quality",
    "blurry",
    "realistic",
    "photo"
]
# ============================


# ====== KSampler ======
STEPS_LIST = [20, 25]
CFG_LIST = [6.0, 7.0]
SAMPLER_LIST = ["euler", "dpmpp_2m"]
SCHEDULER_LIST = ["karras", "normal"]
# ======================


# ====== LoRA ======
LORA_LIST = ["OneBreastOutLoRA_V1_1rank8.safetensors"]
LORA_MODEL_STRENGTH = [0.0]
LORA_CLIP_STRENGTH = [0.0]

PERKY_BREASTS_LOAR_MODEL_STRENGTH = [0.4, 0.8]
PERKY_BREASTS_LOAR_CLIP_STRENGTH = [0.8, 1.2]
# ===================


# ====== 状態管理 ======
def load_used_axes():
    if AXIS_STATE_FILE.exists():
        return set(json.loads(AXIS_STATE_FILE.read_text())["used_axes"])
    return set()

def save_used_axes(used_axes: set):
    AXIS_STATE_FILE.write_text(
        json.dumps({"used_axes": sorted(used_axes)}, indent=2),
        encoding="utf-8"
    )
# ====================


# ====== ComfyUI API ======
def queue_prompt(prompt: dict) -> str:
    r = requests.post(f"{COMFY}/prompt", json={"prompt": prompt})
    r.raise_for_status()
    return r.json()["prompt_id"]

def get_history(prompt_id: str) -> dict:
    r = requests.get(f"{COMFY}/history/{prompt_id}")
    r.raise_for_status()
    return r.json()

def wait_done(prompt_id: str, poll_sec=1.0):
    while True:
        h = get_history(prompt_id)
        if prompt_id in h and "outputs" in h[prompt_id]:
            return
        time.sleep(poll_sec)

def load_workflow() -> dict:
    with open(WORKFLOW_JSON, "r", encoding="utf-8") as f:
        return json.load(f)
# ======================

def pick_from_axis(axis):
    """
    axis:
      - ["a", "b", "c"] → 等確率
      - [("a", 2.0), ("b", 1.0)] → 重み付き
    """
    if not axis:
        return ""

    first = axis[0]

    # 重み付き
    if isinstance(first, tuple):
        return weighted_choice(axis)

    # 従来（等確率）
    return random.choice(axis)



#def pick_axis(idx):
#    if idx == target_axis_index:
#        return POS_PARTS[idx]
#    if RANDOMIZE_NON_TARGET:
#        return pick_random(POS_PARTS[idx])
#    return [POS_PARTS[idx][0]]

def pick_axis(idx, target_axis_index):
    if idx == target_axis_index:
        # 探索軸は全候補（値だけ取り出す）
        axis = POS_PARTS[idx]
        if isinstance(axis[0], tuple):
            return [v for v, _ in axis]
        return axis

    # 非探索軸は重み付きランダム1個
    return [pick_from_axis(POS_PARTS[idx])]


def weighted_choice(items: list[tuple[str, float]]) -> str:
    """
    items: [(value, weight), ...]
    """
    values = [v for v, _ in items]
    weights = [w for _, w in items]
    return random.choices(values, weights=weights, k=1)[0]


def calc_generation_count(
    target_axis: list,
    *other_axes: list[list]
) -> int:
    """
    target_axis : 探索軸（全候補を回す）
    other_axes  : itertools.product に入る他の軸
    """
    sizes = [len(target_axis)]

    for axis in other_axes:
        sizes.append(len(axis))

    return math.prod(sizes)


def set_inputs(prompt: dict, pos: str, neg: str,
               steps: int, cfg: float,
               sampler: str, scheduler: str, seed: int,
               lora: str, lomo: float, locl: float,
               pblomo: float, pblocl: float,
               filename_prefix: str):

    prompt[POS_NODE_ID]["inputs"]["text"] = pos
    prompt[NEG_NODE_ID]["inputs"]["text"] = neg

    prompt[LORA_ID]["inputs"]["lora_name"] = lora
    prompt[LORA_ID]["inputs"]["strength_model"] = lomo
    prompt[LORA_ID]["inputs"]["strength_clip"] = locl

    prompt[PERKY_BREASTS_ID]["inputs"]["strength_model"] = pblomo
    prompt[PERKY_BREASTS_ID]["inputs"]["strength_clip"] = pblocl

    ks = prompt[KSAMPLER_ID]["inputs"]
    ks["steps"] = steps
    ks["cfg"] = cfg
    ks["sampler_name"] = sampler
    ks["scheduler"] = scheduler
    ks["seed"] = seed

    if SAVE_NODE_ID in prompt:
        prompt[SAVE_NODE_ID]["inputs"]["filename_prefix"] = filename_prefix


# ====== main ======
def main():
    RUN_ROOT.mkdir(parents=True, exist_ok=True)

    used_axes = load_used_axes()
    remaining = [(i, n) for i, n in enumerate(AXIS_NAMES) if n not in used_axes]

    if not remaining:
        print("すべての探索軸を使い切りました")
        return

    target_axis_index, target_axis_name = random.choice(remaining)
    print(f"今回探索する軸: {target_axis_name}")

    count = calc_generation_count(
        POS_PARTS[target_axis_index],
        STEPS_LIST,
        CFG_LIST,
        SAMPLER_LIST,
        SCHEDULER_LIST,
        LORA_LIST,
        LORA_MODEL_STRENGTH,
        LORA_CLIP_STRENGTH,
        PERKY_BREASTS_LOAR_MODEL_STRENGTH,
        PERKY_BREASTS_LOAR_CLIP_STRENGTH
    )
    
    print(f"今回の生成回数: {count*repeats}")

    base = load_workflow()

    for i, combo in enumerate(
        itertools.product(

            #*[
            #     POS_PARTS[idx] if idx == target_axis_index else pick_random(POS_PARTS[idx])
            #     for idx in range(len(POS_PARTS))
            # ],
             *[pick_axis(idx, target_axis_index) for idx in range(len(POS_PARTS))],

            #*[
            #    pick_axis(idx)
            #    for idx in range(len(POS_PARTS))
            #],
            STEPS_LIST,
            CFG_LIST,
            SAMPLER_LIST,
            SCHEDULER_LIST,
            LORA_LIST,
            LORA_MODEL_STRENGTH,
            LORA_CLIP_STRENGTH,
            PERKY_BREASTS_LOAR_MODEL_STRENGTH,
            PERKY_BREASTS_LOAR_CLIP_STRENGTH
        ),
        start=1
    ):
        (*pos_vals,
         steps, cfg, sampler, sched,
         lora, lomo, locl, pblomo, pblocl) = combo

        pos = ", ".join(POS_PARTS_FIX + list(pos_vals))
        neg = ", ".join(NEG_PARTS)

        run_id = f"{i:04d}_{uuid.uuid4().hex[:6]}"
        run_dir = RUN_ROOT / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        meta = {
            "axis": target_axis_name,
            "positive": pos,
            "steps": steps,
            "cfg": cfg,
            "sampler": sampler,
            "scheduler": sched,
            "lora": lora,
            "lora model strength": lomo,
            "lora clip strength": locl,
            "perky breasts model strength": pblomo,
            "perky breasts clip strength": pblocl

        }
        (run_dir / "params.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        prompt = json.loads(json.dumps(base))
        seed = int(time.time() * 1000) % 2_000_000_000

        for r in range(repeats):
            seed = int(time.time() * 1000) % 2_000_000_000  # 雑にランダム
            set_inputs(
                prompt, pos, neg,
                steps, cfg, sampler, sched, seed,
                lora, lomo, locl,
                pblomo, pblocl,
                f"{run_id}/img"
            )

            pid = queue_prompt(prompt)
            wait_done(pid)

        print(f"done {run_id}")

    used_axes.add(target_axis_name)
    save_used_axes(used_axes)


if __name__ == "__main__":
    main()
