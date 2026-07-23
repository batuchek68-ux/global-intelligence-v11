import json
import time
import requests
from pathlib import Path

from config import get_auth_header, DREAMINA_BASE_URL


class DreaminaFreeClient:
    def __init__(self, session_id: str = None, region: str = "cn"):
        if session_id:
            from config import REGION_PREFIXES
            prefix = REGION_PREFIXES.get(region, "")
            self.auth_header = f"Bearer {prefix}{session_id}"
        else:
            self.auth_header = get_auth_header()
        
        self.base_url = DREAMINA_BASE_URL
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": self.auth_header,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }

    def _post(self, endpoint: str, data: dict) -> dict:
        url = f"{self.base_url}{endpoint}"
        resp = requests.post(url, json=data, headers=self.headers, timeout=60)
        resp.raise_for_status()
        return resp.json()

    def _get(self, endpoint: str) -> dict:
        url = f"{self.base_url}{endpoint}"
        resp = requests.get(url, headers=self.headers, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def text2image(
        self,
        prompt: str,
        model: str = "jimeng-5.0",
        ratio: str = "16:9",
        resolution: str = "2k",
        num_images: int = 1,
    ) -> dict:
        data = {
            "model": model,
            "prompt": prompt,
            "ratio": ratio,
            "resolution": resolution,
            "num_images": num_images,
        }
        return self._post("/mweb/v1/aigc_draft/generate", data)

    def image2video(
        self,
        prompt: str,
        image_urls: list[str],
        model: str = "jimeng-video-seedance-2.0",
        duration: int = 5,
        resolution: str = "720p",
    ) -> dict:
        material_list = []
        for url in image_urls:
            material_list.append({
                "type": "image",
                "url": url,
            })
        
        data = {
            "model": model,
            "prompt": prompt,
            "material_list": material_list,
            "duration": duration,
            "resolution": resolution,
        }
        return self._post("/mweb/v1/aigc_draft/generate", data)

    def query_task(self, history_id: str) -> dict:
        data = {"history_id": history_id}
        return self._post("/mweb/v1/get_history_by_ids", data)

    def wait_result(self, history_id: str, timeout: int = 300, interval: int = 5) -> dict:
        elapsed = 0
        while elapsed < timeout:
            result = self.query_task(history_id)
            
            status = result.get("status", "")
            if status == "success" or status == "completed":
                return result
            if status == "failed":
                raise RuntimeError(f"Task failed: {result.get('error', 'unknown')}")
            
            time.sleep(interval)
            elapsed += interval
        
        raise TimeoutError(f"Task {history_id} timed out after {timeout}s")

    def get_credits(self) -> dict:
        return self._get("/mweb/v1/get_user_credits")
