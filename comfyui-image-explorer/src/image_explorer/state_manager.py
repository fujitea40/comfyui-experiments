"""
使用済み軸の状態管理
探索済みの軸を記録し、すべての軸を使い切るまで管理する
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Set

logger = logging.getLogger(__name__)


class StateManager:
    """使用済み軸の状態を管理するクラス"""

    def __init__(self, state_file: Path):
        """
        Args:
            state_file: 状態を保存するJSONファイルのパス
        """
        self.state_file = state_file
        self._used_axes: Set[str] = set()
        self._load()

    def _load(self):
        """状態ファイルから使用済み軸を読み込む"""
        if not self.state_file.exists():
            logger.info(
                f"状態ファイルが存在しません。新規作成します: {self.state_file}"
            )
            self._used_axes = set()
            return

        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # バージョンチェック（将来の拡張用）
            version = data.get("version", "1.0")
            if version != "1.0":
                logger.warning(
                    f"未知のバージョン: {version}。互換性の問題が発生する可能性があります"  # noqa: E501
                )

            self._used_axes = set(data.get("used_axes", []))
            logger.info(
                f"状態ファイルを読み込みました: {len(self._used_axes)} 個の軸が使用済み"
            )

        except json.JSONDecodeError as e:
            logger.error(f"状態ファイルの読み込みに失敗しました: {e}")
            logger.warning("新しい状態ファイルを作成します")
            self._used_axes = set()
        except Exception as e:
            logger.error(f"予期しないエラー: {e}")
            raise

    def _save(self):
        """使用済み軸を状態ファイルに保存"""
        try:
            # 親ディレクトリが存在しない場合は作成
            self.state_file.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "version": "1.0",
                "used_axes": sorted(self._used_axes),  # ソートして保存（可読性向上）
                "last_updated": datetime.now().isoformat(),
                "total_used": len(self._used_axes),
            }

            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"状態ファイルを保存しました: {self.state_file}")

        except Exception as e:
            logger.error(f"状態ファイルの保存に失敗しました: {e}")
            raise

    # ====== 公開メソッド ======

    def get_used_axes(self) -> Set[str]:
        """
        使用済み軸のセットを取得

        Returns:
            Set[str]: 使用済み軸の名前セット
        """
        return self._used_axes.copy()  # コピーを返して不変性を保つ

    def is_used(self, axis_name: str) -> bool:
        """
        指定された軸が使用済みかどうかを判定

        Args:
            axis_name: 軸の名前

        Returns:
            bool: 使用済みならTrue
        """
        return axis_name in self._used_axes

    def mark_as_used(self, axis_name: str):
        """
        軸を使用済みとしてマーク

        Args:
            axis_name: 軸の名前
        """
        if axis_name in self._used_axes:
            logger.warning(f"軸 '{axis_name}' は既に使用済みです")
        else:
            self._used_axes.add(axis_name)
            logger.info(f"軸 '{axis_name}' を使用済みとしてマークしました")

        self._save()

    def get_remaining_axes(self, all_axis_names: List[str]) -> List[str]:
        """
        未使用の軸のリストを取得

        Args:
            all_axis_names: すべての軸の名前リスト

        Returns:
            List[str]: 未使用の軸の名前リスト
        """
        remaining = [name for name in all_axis_names if name not in self._used_axes]
        logger.info(f"残り {len(remaining)} 個の軸が未使用です")
        return remaining

    def is_all_used(self, all_axis_names: List[str]) -> bool:
        """
        すべての軸が使用済みかどうかを判定

        Args:
            all_axis_names: すべての軸の名前リスト

        Returns:
            bool: すべて使用済みならTrue
        """
        return len(self.get_remaining_axes(all_axis_names)) == 0

    def reset(self):
        """
        状態をリセット（すべての軸を未使用に戻す）
        """
        logger.warning("状態をリセットします")
        self._used_axes.clear()
        self._save()

    def remove_axis(self, axis_name: str):
        """
        特定の軸を未使用に戻す

        Args:
            axis_name: 軸の名前
        """
        if axis_name not in self._used_axes:
            logger.warning(f"軸 '{axis_name}' は使用済みリストに存在しません")
        else:
            self._used_axes.remove(axis_name)
            logger.info(f"軸 '{axis_name}' を未使用に戻しました")
            self._save()

    def get_progress(self, all_axis_names: List[str]) -> dict:
        """
        進捗情報を取得

        Args:
            all_axis_names: すべての軸の名前リスト

        Returns:
            dict: 進捗情報 {used: int, total: int, percentage: float, remaining: List[str]}
        """  # noqa: E501
        total = len(all_axis_names)
        used = len(self._used_axes)
        remaining = self.get_remaining_axes(all_axis_names)
        percentage = (used / total * 100) if total > 0 else 0

        return {
            "used": used,
            "total": total,
            "percentage": percentage,
            "remaining": remaining,
            "used_axes": sorted(self._used_axes),
        }

    # ====== コンテキストマネージャー対応 ======

    def __enter__(self):
        """コンテキストマネージャー対応"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャー対応（終了時に保存）"""
        if exc_type is None:
            self._save()


# ====== 便利な関数 ======


def create_state_manager(state_file: Path) -> StateManager:
    """
    StateManagerのファクトリ関数

    Args:
        state_file: 状態ファイルのパス

    Returns:
        StateManager: StateManagerインスタンス
    """
    return StateManager(state_file)


def print_progress(state_manager: StateManager, all_axis_names: List[str]):
    """
    進捗を見やすく表示

    Args:
        state_manager: StateManagerインスタンス
        all_axis_names: すべての軸の名前リスト
    """
    progress = state_manager.get_progress(all_axis_names)

    print("=" * 50)
    print(
        f"探索進捗: {progress['used']}/{progress['total']} ({progress['percentage']:.1f}%)"  # noqa: E501
    )
    print("=" * 50)

    if progress["used_axes"]:
        print("\n使用済み軸:")
        for axis in progress["used_axes"]:
            print(f"  ✓ {axis}")

    if progress["remaining"]:
        print("\n未使用軸:")
        for axis in progress["remaining"]:
            print(f"  ○ {axis}")
    else:
        print("\n✨ すべての軸を探索完了しました！")

    print("=" * 50)


# ====== 使用例 ======


def example_usage():
    """使用例"""

    # StateManagerを作成
    state_file = Path("axis_state.json")
    state_manager = StateManager(state_file)

    # すべての軸
    all_axes = ["hair_style", "hair_color", "expression", "pose"]

    # 進捗を表示
    print_progress(state_manager, all_axes)

    # 未使用の軸を取得
    remaining = state_manager.get_remaining_axes(all_axes)
    print(f"\n未使用の軸: {remaining}")

    # 軸を使用済みとしてマーク
    if remaining:
        axis_to_use = remaining[0]
        print(f"\n軸 '{axis_to_use}' を使用します")
        state_manager.mark_as_used(axis_to_use)

    # 再度進捗を表示
    print_progress(state_manager, all_axes)

    # すべて使用済みかチェック
    if state_manager.is_all_used(all_axes):
        print("\nすべての軸を使い切りました！")
        print("リセットしますか？")
        # state_manager.reset()

    # コンテキストマネージャーを使った例
    print("\n--- コンテキストマネージャーの例 ---")
    with StateManager(state_file) as sm:
        progress = sm.get_progress(all_axes)
        print(f"進捗: {progress['percentage']:.1f}%")
        # 終了時に自動保存される


def example_reset():
    """リセットの例"""
    state_file = Path("axis_state.json")
    state_manager = StateManager(state_file)

    print("現在の状態:")
    all_axes = ["hair_style", "hair_color", "expression", "pose"]
    print_progress(state_manager, all_axes)

    # リセット
    response = input("\nリセットしますか？ (y/n): ")
    if response.lower() == "y":
        state_manager.reset()
        print("\nリセット後:")
        print_progress(state_manager, all_axes)


if __name__ == "__main__":
    # ロギング設定
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    example_usage()
    # example_reset()
