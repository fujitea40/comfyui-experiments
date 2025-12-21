"""
汎用ユーティリティ関数
"""
import random
import time
import uuid
import math
from typing import List, Union, Tuple, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


# ====== ランダム選択 ======

def weighted_choice(items: List[Tuple[str, float]]) -> str:
    """
    重み付きランダム選択
    
    Args:
        items: [(value, weight), ...] 形式のリスト
    
    Returns:
        str: 選択された値
    
    Examples:
        >>> items = [("a", 2.0), ("b", 1.0), ("c", 0.5)]
        >>> result = weighted_choice(items)
        >>> result in ["a", "b", "c"]
        True
    """
    if not items:
        return ""
    
    values = [v for v, _ in items]
    weights = [w for _, w in items]
    
    # weightsがすべて0の場合は等確率
    if all(w == 0 for w in weights):
        return random.choice(values)
    
    return random.choices(values, weights=weights, k=1)[0]


def pick_from_choices(
    choices: List[Union[str, Tuple[str, float]]]
) -> str:
    """
    選択肢から1つ選ぶ（重み付き/等確率を自動判定）
    
    Args:
        choices: 文字列リスト or (文字列, 重み) のタプルリスト
    
    Returns:
        str: 選択された値
    
    Examples:
        >>> pick_from_choices(["a", "b", "c"])
        'a'  # or 'b' or 'c'
        
        >>> pick_from_choices([("a", 2.0), ("b", 1.0)])
        'a'  # or 'b'
    """
    if not choices:
        return ""
    
    first = choices[0]
    
    # 重み付きタプルの場合
    if isinstance(first, tuple):
        return weighted_choice(choices)
    
    # 等確率の場合
    return random.choice(choices)


# ====== ID生成 ======

def generate_run_id(index: int = 0) -> str:
    """
    実行IDを生成（一意性保証）
    
    Args:
        index: 連番（オプション）
    
    Returns:
        str: 実行ID（例: "0001_a3f5b2"）
    
    Examples:
        >>> run_id = generate_run_id(1)
        >>> len(run_id)
        11
        >>> run_id.startswith("0001_")
        True
    """
    if index > 0:
        return f"{index:04d}_{uuid.uuid4().hex[:6]}"
    else:
        return f"{uuid.uuid4().hex[:8]}"


def generate_seed() -> int:
    """
    シード値を生成（現在時刻ベース）
    
    Returns:
        int: シード値（0 ~ 1,999,999,999）
    
    Examples:
        >>> seed = generate_seed()
        >>> 0 <= seed < 2_000_000_000
        True
    """
    return int(time.time() * 1000) % 2_000_000_000


# ====== 組み合わせ計算 ======

def calculate_combinations_count(
    target_axis_size: int,
    *other_sizes: int
) -> int:
    """
    組み合わせの総数を計算
    
    Args:
        target_axis_size: 探索軸のサイズ
        *other_sizes: その他の軸のサイズ
    
    Returns:
        int: 組み合わせの総数
    
    Examples:
        >>> calculate_combinations_count(5, 2, 3, 4)
        120
    """
    sizes = [target_axis_size] + list(other_sizes)
    return math.prod(sizes)


def estimate_total_images(
    axis_size: int,
    sampler_combinations: int,
    lora_combinations: int,
    repeats: int = 1
) -> int:
    """
    生成される画像の総数を見積もる
    
    Args:
        axis_size: 探索軸のサイズ
        sampler_combinations: サンプラーの組み合わせ数
        lora_combinations: LoRAの組み合わせ数
        repeats: 繰り返し回数
    
    Returns:
        int: 生成される画像の総数
    
    Examples:
        >>> estimate_total_images(10, 4, 2, repeats=2)
        160
    """
    return axis_size * sampler_combinations * lora_combinations * repeats


# ====== 時間・期間 ======

def format_duration(seconds: float) -> str:
    """
    秒数を人間が読みやすい形式に変換
    
    Args:
        seconds: 秒数
    
    Returns:
        str: フォーマット済み文字列
    
    Examples:
        >>> format_duration(65)
        '1分5秒'
        >>> format_duration(3665)
        '1時間1分5秒'
        >>> format_duration(45)
        '45秒'
    """
    if seconds < 60:
        return f"{int(seconds)}秒"
    
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    
    if minutes < 60:
        return f"{minutes}分{secs}秒"
    
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}時間{mins}分{secs}秒"


def estimate_time_remaining(
    completed: int,
    total: int,
    elapsed_seconds: float
) -> str:
    """
    残り時間を見積もる
    
    Args:
        completed: 完了した数
        total: 全体の数
        elapsed_seconds: 経過時間（秒）
    
    Returns:
        str: 残り時間の見積もり
    
    Examples:
        >>> estimate_time_remaining(25, 100, 60.0)
        '3分0秒'
    """
    if completed == 0:
        return "不明"
    
    avg_time_per_item = elapsed_seconds / completed
    remaining_items = total - completed
    remaining_seconds = avg_time_per_item * remaining_items
    
    return format_duration(remaining_seconds)


# ====== ファイル・ディレクトリ ======

def ensure_directory(path: Path) -> Path:
    """
    ディレクトリが存在することを保証（なければ作成）
    
    Args:
        path: ディレクトリパス
    
    Returns:
        Path: 作成されたディレクトリパス
    
    Examples:
        >>> p = ensure_directory(Path("test_dir"))
        >>> p.exists()
        True
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_filename(text: str, max_length: int = 50) -> str:
    """
    安全なファイル名に変換（特殊文字を除去）
    
    Args:
        text: 元のテキスト
        max_length: 最大文字数
    
    Returns:
        str: 安全なファイル名
    
    Examples:
        >>> safe_filename("hello/world:test")
        'hello_world_test'
        >>> safe_filename("a" * 100, max_length=10)
        'aaaaaaaaaa'
    """
    # 特殊文字を置換
    safe = text.replace("/", "_").replace("\\", "_")
    safe = safe.replace(":", "_").replace("*", "_")
    safe = safe.replace("?", "_").replace('"', "_")
    safe = safe.replace("<", "_").replace(">", "_")
    safe = safe.replace("|", "_")
    
    # 連続するアンダースコアを1つに
    while "__" in safe:
        safe = safe.replace("__", "_")
    
    # 前後の空白・アンダースコアを削除
    safe = safe.strip("_ ")
    
    # 長さ制限
    if len(safe) > max_length:
        safe = safe[:max_length]
    
    return safe


# ====== プロンプト操作 ======

def join_prompts(prompts: List[str]) -> str:
    """
    プロンプトのリストをカンマ区切りで結合
    空文字列は除外する
    
    Args:
        prompts: プロンプトのリスト
    
    Returns:
        str: 結合されたプロンプト
    
    Examples:
        >>> join_prompts(["1girl", "smile", "", "long hair"])
        '1girl, smile, long hair'
    """
    # 空文字列を除外
    filtered = [p.strip() for p in prompts if p.strip()]
    return ", ".join(filtered)


def clean_prompt(prompt: str) -> str:
    """
    プロンプトをクリーンアップ（余分な空白・カンマを除去）
    
    Args:
        prompt: 元のプロンプト
    
    Returns:
        str: クリーンアップされたプロンプト
    
    Examples:
        >>> clean_prompt("1girl,  , smile,  long hair")
        '1girl, smile, long hair'
    """
    # カンマで分割
    parts = [p.strip() for p in prompt.split(",")]
    # 空文字列を除外
    parts = [p for p in parts if p]
    # 再結合
    return ", ".join(parts)


# ====== 進捗表示 ======

def print_progress_bar(
    current: int,
    total: int,
    prefix: str = "",
    suffix: str = "",
    bar_length: int = 50
):
    """
    プログレスバーを表示
    
    Args:
        current: 現在の進捗
        total: 全体の数
        prefix: 前置きテキスト
        suffix: 後置きテキスト
        bar_length: バーの長さ
    
    Examples:
        >>> print_progress_bar(25, 100, prefix="Progress:", suffix="Complete")
        Progress: |████████████▌                                       | 25/100 Complete
    """
    if total == 0:
        return
    
    filled_length = int(bar_length * current // total)
    bar = "█" * filled_length + "▌" * (1 if current < total else 0)
    bar = bar.ljust(bar_length)
    
    percent = 100 * (current / float(total))
    
    print(f"\r{prefix} |{bar}| {current}/{total} {suffix}", end="", flush=True)
    
    if current == total:
        print()  # 改行


# ====== データ検証 ======

def validate_positive_int(value: int, name: str = "value"):
    """
    正の整数であることを検証
    
    Args:
        value: 検証する値
        name: パラメータ名（エラーメッセージ用）
    
    Raises:
        ValueError: 正の整数でない場合
    """
    if not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} は正の整数である必要があります: {value}")


def validate_positive_float(value: float, name: str = "value"):
    """
    正の浮動小数点数であることを検証
    
    Args:
        value: 検証する値
        name: パラメータ名（エラーメッセージ用）
    
    Raises:
        ValueError: 正の浮動小数点数でない場合
    """
    if not isinstance(value, (int, float)) or value <= 0:
        raise ValueError(f"{name} は正の数である必要があります: {value}")


def validate_range(value: float, min_val: float, max_val: float, name: str = "value"):
    """
    値が範囲内にあることを検証
    
    Args:
        value: 検証する値
        min_val: 最小値
        max_val: 最大値
        name: パラメータ名（エラーメッセージ用）
    
    Raises:
        ValueError: 範囲外の場合
    """
    if not (min_val <= value <= max_val):
        raise ValueError(f"{name} は {min_val} から {max_val} の範囲である必要があります: {value}")


# ====== ロギングヘルパー ======

def setup_logger(
    name: str = __name__,
    level: int = logging.INFO,
    log_file: Path = None
) -> logging.Logger:
    """
    ロガーをセットアップ
    
    Args:
        name: ロガー名
        level: ログレベル
        log_file: ログファイルパス（Noneの場合はコンソールのみ）
    
    Returns:
        logging.Logger: 設定されたロガー
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # ハンドラーをクリア
    logger.handlers.clear()
    
    # フォーマッター
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # コンソールハンドラー
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # ファイルハンドラー（オプション）
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# ====== 使用例 ======

def example_usage():
    """使用例"""
    
    print("=== ランダム選択 ===")
    choices = [("a", 2.0), ("b", 1.0), ("c", 0.5)]
    print(f"重み付き選択: {weighted_choice(choices)}")
    
    print("\n=== ID生成 ===")
    print(f"実行ID: {generate_run_id(1)}")
    print(f"シード: {generate_seed()}")
    
    print("\n=== 組み合わせ計算 ===")
    count = calculate_combinations_count(10, 2, 3, 4)
    print(f"組み合わせ数: {count}")
    
    total_images = estimate_total_images(10, 4, 2, repeats=2)
    print(f"総画像数: {total_images}")
    
    print("\n=== 時間フォーマット ===")
    print(f"65秒 = {format_duration(65)}")
    print(f"3665秒 = {format_duration(3665)}")
    
    print("\n=== 残り時間見積もり ===")
    remaining = estimate_time_remaining(25, 100, 60.0)
    print(f"残り時間: {remaining}")
    
    print("\n=== ファイル名 ===")
    safe = safe_filename("hello/world:test*?")
    print(f"安全なファイル名: {safe}")
    
    print("\n=== プロンプト操作 ===")
    prompts = ["1girl", "", "smile", "  ", "long hair"]
    joined = join_prompts(prompts)
    print(f"結合: {joined}")
    
    dirty = "1girl,  , smile,  long hair"
    clean = clean_prompt(dirty)
    print(f"クリーンアップ: {clean}")
    
    print("\n=== プログレスバー ===")
    for i in range(101):
        print_progress_bar(i, 100, prefix="Progress:", suffix="Complete")
        time.sleep(0.01)


if __name__ == "__main__":
    example_usage()