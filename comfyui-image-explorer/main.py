"""
ComfyUI画像生成ツール - メインプログラム
すべてのモジュールを統合し、画像生成を実行する
"""
import sys
import time
import random
import argparse
from pathlib import Path
from typing import Optional
import logging

from config_loader import ConfigLoader
from models import GenerationParams
from prompt_builder import PromptBuilder, ParameterCombinationGenerator
from workflow import WorkflowManager
from comfyui_client import ComfyUIClient
from state_manager import StateManager, print_progress
from utils import (
    generate_seed,
    generate_run_id,
    ensure_directory,
    format_duration,
    estimate_time_remaining,
    print_progress_bar,
    setup_logger
)

# ロガー
logger = logging.getLogger(__name__)


class ImageGenerationRunner:
    """
    画像生成の実行を管理するクラス
    各種マネージャーを統合してメインロジックを実行
    """
    
    def __init__(self, config_path: Path):
        """
        Args:
            config_path: 設定ファイルのパス
        """
        logger.info("=" * 60)
        logger.info("ComfyUI画像生成ツールを起動します")
        logger.info("=" * 60)
        
        # 設定を読み込み
        logger.info(f"設定ファイルを読み込み中: {config_path}")
        loader = ConfigLoader(config_path)
        self.config = loader.load_all()
        
        # 各種マネージャーを初期化
        self._initialize_managers()
        
        logger.info("初期化が完了しました")
    
    def _initialize_managers(self):
        """各種マネージャーを初期化"""
        # StateManager
        self.state_manager = StateManager(
            self.config["execution"].state_file
        )
        
        # WorkflowManager
        self.workflow_manager = WorkflowManager(
            self.config["workflow"]
        )
        
        # ComfyUIClient
        self.client = ComfyUIClient(
            base_url=self.config["execution"].comfy_url,
            timeout=30
        )
        
        # PromptBuilder
        self.prompt_builder = PromptBuilder(
            self.config["prompt_template"],
            randomize_non_target=self.config["execution"].randomize_non_target
        )
        
        # ParameterCombinationGenerator
        self.param_generator = ParameterCombinationGenerator(
            self.prompt_builder,
            self.config["sampler_choices"],
            self.config["lora_choices"]
        )
        
        logger.info("すべてのマネージャーを初期化しました")
    
    def check_comfyui_connection(self) -> bool:
        """
        ComfyUIへの接続を確認
        
        Returns:
            bool: 接続できればTrue
        """
        logger.info("ComfyUIへの接続を確認中...")
        
        if self.client.is_alive():
            logger.info("✓ ComfyUIに接続しました")
            return True
        else:
            logger.error("✗ ComfyUIに接続できません")
            logger.error(f"  URL: {self.config['execution'].comfy_url}")
            logger.error("  ComfyUIが起動しているか確認してください")
            return False
    
    def select_target_axis(self) -> Optional[str]:
        """
        探索する軸を選択
        
        Returns:
            str or None: 軸の名前、すべて使い切った場合はNone
        """
        all_axes = self.config["prompt_template"].get_axis_names()
        remaining = self.state_manager.get_remaining_axes(all_axes)
        
        if not remaining:
            logger.info("すべての軸を探索完了しました！")
            return None
        
        # ランダムに選択
        target_axis = random.choice(remaining)
        logger.info(f"探索軸を選択: {target_axis}")
        
        return target_axis
    
    def calculate_generation_count(self, target_axis: str) -> int:
        """
        生成される画像の総数を計算
        
        Args:
            target_axis: 探索対象の軸名
        
        Returns:
            int: 生成される画像の総数
        """
        base_count = self.param_generator.count_combinations(target_axis)
        repeats = self.config["execution"].repeats
        total = base_count * repeats
        
        logger.info(f"生成数: {base_count} パターン × {repeats} 回 = {total} 枚")
        
        return total
    
    def run_generation(self, target_axis: str):
        """
        画像生成を実行
        
        Args:
            target_axis: 探索対象の軸名
        """
        # 出力ルートを作成
        output_root = self.config["workflow"].output_root
        ensure_directory(output_root)
        
        # 生成数を計算
        base_count = self.param_generator.count_combinations(target_axis)
        repeats = self.config["execution"].repeats
        total_images = base_count * repeats
        
        logger.info("")
        logger.info("=" * 60)
        logger.info(f"画像生成を開始します")
        logger.info(f"  探索軸: {target_axis}")
        logger.info(f"  パターン数: {base_count}")
        logger.info(f"  繰り返し: {repeats}")
        logger.info(f"  合計生成数: {total_images}")
        logger.info("=" * 60)
        logger.info("")
        
        # 統計情報
        start_time = time.time()
        completed_images = 0
        failed_images = 0
        
        # パラメータを生成して実行
        for i, params in enumerate(
            self.param_generator.generate_combinations(target_axis),
            start=1
        ):
            run_id = generate_run_id(i)
            run_dir = ensure_directory(output_root / run_id)
            
            logger.info(f"パターン {i}/{base_count}: {run_id}")
            
            # メタデータを保存
            self._save_metadata(run_dir, params)
            
            # 繰り返し実行
            for r in range(repeats):
                # Seedを生成
                params.sampler.seed = generate_seed()
                
                # ワークフローを作成
                workflow = self.workflow_manager.create_configured_workflow(params)
                self.workflow_manager.set_filename_prefix(workflow, f"{run_id}/img")
                
                # ComfyUIに送信して実行
                logger.debug(f"  繰り返し {r+1}/{repeats} - Seed: {params.sampler.seed}")
                response = self.client.execute_and_wait(
                    workflow,
                    poll_interval=self.config["execution"].poll_interval
                )
                
                if response.success:
                    completed_images += 1
                    logger.debug(f"  ✓ 完了 ({r+1}/{repeats})")
                else:
                    failed_images += 1
                    logger.error(f"  ✗ エラー: {response.error_message}")
            
            logger.info(f"✓ {run_id} 完了")
            
            # 進捗を表示
            elapsed = time.time() - start_time
            remaining_time = estimate_time_remaining(
                completed_images,
                total_images,
                elapsed
            )
            
            print_progress_bar(
                completed_images,
                total_images,
                prefix="進捗:",
                suffix=f"完了 (残り約{remaining_time})"
            )
        
        # 完了
        total_time = time.time() - start_time
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("画像生成が完了しました")
        logger.info(f"  成功: {completed_images} 枚")
        logger.info(f"  失敗: {failed_images} 枚")
        logger.info(f"  所要時間: {format_duration(total_time)}")
        logger.info("=" * 60)
        
        # 軸を使用済みとしてマーク
        self.state_manager.mark_as_used(target_axis)
        logger.info(f"軸 '{target_axis}' を使用済みとしてマークしました")
    
    def _save_metadata(self, run_dir: Path, params: GenerationParams):
        """
        メタデータをJSONファイルに保存
        
        Args:
            run_dir: 実行ディレクトリ
            params: 生成パラメータ
        """
        import json
        
        metadata_path = run_dir / "params.json"
        metadata = params.to_dict()
        
        try:
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            logger.debug(f"メタデータを保存: {metadata_path}")
        except Exception as e:
            logger.error(f"メタデータの保存に失敗: {e}")
    
    def show_progress(self):
        """現在の進捗を表示"""
        all_axes = self.config["prompt_template"].get_axis_names()
        print_progress(self.state_manager, all_axes)
    
    def run(self) -> int:
        """
        メイン実行
        
        Returns:
            int: 終了コード (0: 成功, 1: エラー)
        """
        try:
            # 進捗を表示
            self.show_progress()
            
            # ComfyUI接続確認
            if not self.check_comfyui_connection():
                return 1
            
            # ワークフローを検証
            if not self.workflow_manager.validate_workflow(
                self.workflow_manager.get_base_workflow()
            ):
                logger.error("ワークフローの検証に失敗しました")
                return 1
            
            # 探索する軸を選択
            target_axis = self.select_target_axis()
            if target_axis is None:
                logger.info("すべての軸を探索完了しました！")
                return 0
            
            # 生成数を計算
            self.calculate_generation_count(target_axis)
            
            # 実行確認
            response = input("\n実行しますか？ (y/n): ")
            if response.lower() != 'y':
                logger.info("キャンセルされました")
                return 0
            
            # 画像生成を実行
            self.run_generation(target_axis)
            
            # 完了後の進捗を表示
            print("\n")
            self.show_progress()
            
            return 0
            
        except KeyboardInterrupt:
            logger.warning("\n中断されました")
            return 1
        except Exception as e:
            logger.error(f"予期しないエラーが発生しました: {e}", exc_info=True)
            return 1


# ====== コマンドライン引数の処理 ======

def parse_arguments():
    """コマンドライン引数をパース"""
    parser = argparse.ArgumentParser(
        description="ComfyUI画像生成ツール - 複数のプロンプトパラメータを探索"
    )
    
    parser.add_argument(
        "-c", "--config",
        type=Path,
        default=Path("config/config.yaml"),
        help="設定ファイルのパス (デフォルト: config.yaml)"
    )
    
    parser.add_argument(
        "-p", "--progress",
        action="store_true",
        help="進捗のみ表示して終了"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="詳細なログを表示"
    )
    
    parser.add_argument(
        "--log-file",
        type=Path,
        help="ログをファイルに出力"
    )
    
    return parser.parse_args()


# ====== エントリーポイント ======

def main():
    """メインエントリーポイント"""
    # コマンドライン引数をパース
    args = parse_arguments()
    
    # ロギング設定
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = setup_logger(
        name="image_generator",
        level=log_level,
        log_file=args.log_file
    )
    
    # 設定ファイルの存在確認
    if not args.config.exists():
        logger.error(f"設定ファイルが見つかりません: {args.config}")
        return 1
    
    try:
        # Runnerを作成
        runner = ImageGenerationRunner(args.config)
        
        # 進捗のみ表示モード
        if args.progress:
            runner.show_progress()
            return 0
        
        # メイン実行
        return runner.run()
        
    except FileNotFoundError as e:
        logger.error(f"ファイルが見つかりません: {e}")
        return 1
    except ValueError as e:
        logger.error(f"設定エラー: {e}")
        return 1
    except Exception as e:
        logger.error(f"予期しないエラー: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())