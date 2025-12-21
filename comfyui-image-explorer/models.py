"""
ComfyUI画像生成ツールのデータモデル定義
"""
from dataclasses import dataclass, field
from typing import Union, List, Tuple
from pathlib import Path


# ====== プロンプト関連 ======

@dataclass
class WeightedPrompt:
    """重み付きプロンプト"""
    text: str
    weight: float = 1.0
    
    def __str__(self) -> str:
        return self.text


@dataclass
class PromptAxis:
    """プロンプトの1つの軸（髪型、表情など）"""
    name: str
    choices: List[Union[str, WeightedPrompt]]
    
    def get_all_values(self) -> List[str]:
        """全選択肢の値を取得（重み情報は除く）"""
        return [
            c.text if isinstance(c, WeightedPrompt) else c
            for c in self.choices
        ]
    
    def is_weighted(self) -> bool:
        """重み付き軸かどうか"""
        return len(self.choices) > 0 and isinstance(self.choices[0], WeightedPrompt)


@dataclass
class PromptTemplate:
    """プロンプトテンプレート（固定部分+可変軸）"""
    fixed_positive: List[str]
    axes: List[PromptAxis]
    negative: List[str]
    
    def get_axis_by_name(self, name: str) -> PromptAxis:
        """名前で軸を取得"""
        for axis in self.axes:
            if axis.name == name:
                return axis
        raise ValueError(f"軸 '{name}' が見つかりません")
    
    def get_axis_names(self) -> List[str]:
        """全軸の名前リストを取得"""
        return [axis.name for axis in self.axes]


# ====== サンプリングパラメータ ======

@dataclass
class SamplerConfig:
    """KSamplerの設定"""
    steps: int
    cfg: float
    sampler_name: str
    scheduler: str
    seed: int = 0
    
    def __post_init__(self):
        if self.steps <= 0:
            raise ValueError("stepsは1以上である必要があります")
        if self.cfg <= 0:
            raise ValueError("cfgは正の値である必要があります")


@dataclass
class LoraConfig:
    """LoRAの設定"""
    name: str
    model_strength: float
    clip_strength: float
    
    def __post_init__(self):
        if not self.name.endswith('.safetensors'):
            raise ValueError("LoRAファイル名は.safetensorsで終わる必要があります")


# ====== 生成パラメータ（1回の生成に必要な全情報）======

@dataclass
class GenerationParams:
    """1回の画像生成に必要な全パラメータ"""
    # プロンプト
    positive_prompt: str
    negative_prompt: str
    
    # サンプラー
    sampler: SamplerConfig
    
    # LoRA
    lora: LoraConfig
    
    # メタ情報
    target_axis_name: str  # 今回探索している軸
    prompt_values: dict = field(default_factory=dict)  # 各軸の選択値
    
    def to_dict(self) -> dict:
        """メタデータとして保存するための辞書形式"""
        return {
            "axis": self.target_axis_name,
            "positive": self.positive_prompt,
            "negative": self.negative_prompt,
            "steps": self.sampler.steps,
            "cfg": self.sampler.cfg,
            "sampler": self.sampler.sampler_name,
            "scheduler": self.sampler.scheduler,
            "seed": self.sampler.seed,
            "lora": self.lora.name,
            "lora_model_strength": self.lora.model_strength,
            "lora_clip_strength": self.lora.clip_strength,
            "prompt_values": self.prompt_values
        }


# ====== ワークフロー設定 ======

@dataclass
class NodeMapping:
    """ComfyUIワークフローのノードID定義"""
    positive_prompt: str
    negative_prompt: str
    ksampler: str
    empty_latent: str
    save_image: str
    lora: str
    
    @classmethod
    def default(cls) -> 'NodeMapping':
        """デフォルトのノードマッピング"""
        return cls(
            positive_prompt="2",
            negative_prompt="3",
            ksampler="4",
            empty_latent="5",
            save_image="7",
        )


@dataclass
class WorkflowConfig:
    """ワークフロー全体の設定"""
    json_path: Path
    node_mapping: NodeMapping
    output_root: Path
    
    def __post_init__(self):
        if not self.json_path.exists():
            raise FileNotFoundError(f"ワークフローファイルが見つかりません: {self.json_path}")


# ====== 実行設定 ======

@dataclass
class ExecutionConfig:
    """実行時の設定"""
    repeats: int = 2  # 各パターンの繰り返し回数
    randomize_non_target: bool = True  # 非探索軸をランダム化するか
    comfy_url: str = "http://127.0.0.1:8188"
    state_file: Path = Path("axis_state.json")
    poll_interval: float = 1.0  # ポーリング間隔（秒）
    
    def __post_init__(self):
        if self.repeats <= 0:
            raise ValueError("repeatsは1以上である必要があります")
        if self.poll_interval <= 0:
            raise ValueError("poll_intervalは正の値である必要があります")


# ====== 実行結果 ======

@dataclass
class GenerationResult:
    """生成結果の情報"""
    run_id: str
    prompt_id: str
    params: GenerationParams
    output_dir: Path
    success: bool = True
    error_message: str = ""