"""
ComfyUI APIとの通信を担当するクライアント
"""
import time
import requests
from typing import Optional, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ComfyUIResponse:
    """ComfyUI APIレスポンスの統一型"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error_message: str = ""
    status_code: Optional[int] = None


class ComfyUIClient:
    """ComfyUI APIクライアント"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8188", timeout: int = 30):
        """
        Args:
            base_url: ComfyUIのベースURL
            timeout: リクエストタイムアウト（秒）
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()  # セッションを再利用して効率化
    
    def _make_url(self, endpoint: str) -> str:
        """エンドポイントURLを生成"""
        return f"{self.base_url}/{endpoint.lstrip('/')}"
    
    def _handle_request(
        self, 
        method: str, 
        endpoint: str, 
        **kwargs
    ) -> ComfyUIResponse:
        """
        HTTPリクエストを実行し、統一的なエラーハンドリングを行う
        
        Args:
            method: HTTPメソッド (GET, POST等)
            endpoint: APIエンドポイント
            **kwargs: requests.requestに渡す追加引数
        """
        url = self._make_url(endpoint)
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                timeout=self.timeout,
                **kwargs
            )
            response.raise_for_status()
            
            return ComfyUIResponse(
                success=True,
                data=response.json(),
                status_code=response.status_code
            )
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            return ComfyUIResponse(
                success=False,
                error_message=f"HTTP error: {e}",
                status_code=e.response.status_code if e.response else None
            )
            
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {e}")
            return ComfyUIResponse(
                success=False,
                error_message=f"Connection error: {e}. ComfyUIが起動していますか？"
            )
            
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout: {e}")
            return ComfyUIResponse(
                success=False,
                error_message=f"Request timeout after {self.timeout}s"
            )
            
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return ComfyUIResponse(
                success=False,
                error_message=f"Unexpected error: {e}"
            )
    
    # ====== 基本API ======
    
    def queue_prompt(self, workflow: Dict[str, Any]) -> ComfyUIResponse:
        """
        ワークフローをキューに投入
        
        Args:
            workflow: ワークフローの辞書（JSONワークフロー）
        
        Returns:
            ComfyUIResponse: prompt_idを含むレスポンス
        """
        logger.info("Queueing prompt to ComfyUI")
        return self._handle_request(
            method="POST",
            endpoint="/prompt",
            json={"prompt": workflow}
        )
    
    def get_history(self, prompt_id: str) -> ComfyUIResponse:
        """
        特定のプロンプトの実行履歴を取得
        
        Args:
            prompt_id: プロンプトID
        
        Returns:
            ComfyUIResponse: 実行履歴データ
        """
        return self._handle_request(
            method="GET",
            endpoint=f"/history/{prompt_id}"
        )
    
    def get_queue(self) -> ComfyUIResponse:
        """
        現在のキュー状態を取得
        
        Returns:
            ComfyUIResponse: キュー情報
        """
        return self._handle_request(
            method="GET",
            endpoint="/queue"
        )
    
    def interrupt(self) -> ComfyUIResponse:
        """
        現在の実行を中断
        
        Returns:
            ComfyUIResponse: 中断結果
        """
        logger.warning("Interrupting current execution")
        return self._handle_request(
            method="POST",
            endpoint="/interrupt"
        )
    
    # ====== 高レベルAPI ======
    
    def wait_for_completion(
        self, 
        prompt_id: str, 
        poll_interval: float = 1.0,
        max_wait_time: Optional[float] = None
    ) -> ComfyUIResponse:
        """
        プロンプトの実行完了を待つ
        
        Args:
            prompt_id: 待機対象のプロンプトID
            poll_interval: ポーリング間隔（秒）
            max_wait_time: 最大待機時間（秒）、Noneの場合は無制限
        
        Returns:
            ComfyUIResponse: 完了時の履歴データ、またはエラー
        """
        logger.info(f"Waiting for prompt {prompt_id} to complete")
        start_time = time.time()
        
        while True:
            # タイムアウトチェック
            if max_wait_time and (time.time() - start_time) > max_wait_time:
                logger.error(f"Timeout waiting for prompt {prompt_id}")
                return ComfyUIResponse(
                    success=False,
                    error_message=f"Timeout after {max_wait_time}s"
                )
            
            # 履歴を取得
            response = self.get_history(prompt_id)
            
            if not response.success:
                return response
            
            # 完了チェック
            history = response.data
            if prompt_id in history and "outputs" in history[prompt_id]:
                logger.info(f"Prompt {prompt_id} completed")
                return response
            
            # 待機
            time.sleep(poll_interval)
    
    def execute_and_wait(
        self, 
        workflow: Dict[str, Any],
        poll_interval: float = 1.0,
        max_wait_time: Optional[float] = None
    ) -> ComfyUIResponse:
        """
        ワークフローを実行して完了まで待つ（便利メソッド）
        
        Args:
            workflow: ワークフロー辞書
            poll_interval: ポーリング間隔（秒）
            max_wait_time: 最大待機時間（秒）
        
        Returns:
            ComfyUIResponse: 完了時の履歴データ、またはエラー
        """
        # キューに投入
        queue_response = self.queue_prompt(workflow)
        
        if not queue_response.success:
            return queue_response
        
        # prompt_idを取得
        prompt_id = queue_response.data.get("prompt_id")
        if not prompt_id:
            return ComfyUIResponse(
                success=False,
                error_message="Failed to get prompt_id from queue response"
            )
        
        # 完了を待つ
        return self.wait_for_completion(
            prompt_id=prompt_id,
            poll_interval=poll_interval,
            max_wait_time=max_wait_time
        )
    
    # ====== ヘルスチェック ======
    
    def is_alive(self) -> bool:
        """
        ComfyUIが起動しているかチェック
        
        Returns:
            bool: 起動していればTrue
        """
        try:
            response = self.session.get(
                self._make_url("/system_stats"),
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def get_system_stats(self) -> ComfyUIResponse:
        """
        システム統計情報を取得
        
        Returns:
            ComfyUIResponse: システム統計データ
        """
        return self._handle_request(
            method="GET",
            endpoint="/system_stats"
        )
    
    # ====== リソース管理 ======
    
    def close(self):
        """セッションをクローズ"""
        self.session.close()
    
    def __enter__(self):
        """コンテキストマネージャー対応"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャー対応"""
        self.close()


# ====== 使用例 ======

def example_usage():
    """使用例"""
    
    # 基本的な使い方
    client = ComfyUIClient(base_url="http://127.0.0.1:8188")
    
    # ヘルスチェック
    if not client.is_alive():
        print("ComfyUIが起動していません")
        return
    
    # ワークフローを読み込み（実際にはファイルから読む）
    workflow = {"1": {"inputs": {}, "class_type": "CheckpointLoaderSimple"}}
    
    # キューに投入
    response = client.queue_prompt(workflow)
    if response.success:
        prompt_id = response.data["prompt_id"]
        print(f"Queued: {prompt_id}")
        
        # 完了を待つ
        result = client.wait_for_completion(prompt_id)
        if result.success:
            print("完了しました")
        else:
            print(f"エラー: {result.error_message}")
    
    # コンテキストマネージャーを使った例
    with ComfyUIClient() as client:
        result = client.execute_and_wait(workflow)
        if result.success:
            print("生成完了")


if __name__ == "__main__":
    # ロギング設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    example_usage()