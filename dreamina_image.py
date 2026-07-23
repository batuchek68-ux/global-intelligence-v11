import time
import requests


class DreaminaImageClient:
    MODELS = {
        "4.0": "jimeng-4.0",
        "4.6": "jimeng-4.6",
        "3.0": "jimeng-3.0",
        "3.1": "jimeng-3.1",
    }

    RATIOS = ["1:1", "4:3", "3:4", "16:9", "9:16", "3:2", "2:3", "21:9"]
    RESOLUTIONS = ["1k", "2k", "4k"]

    def __init__(self, api_key: str, base_url: str = "https://api.xxx.com"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

    def _post(self, endpoint: str, data: dict) -> dict:
        url = f"{self.base_url}{endpoint}"
        resp = requests.post(url, json=data, headers=self.headers, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def text_to_image(
        self,
        prompt: str,
        model: str = "4.0",
        ratio: str = "16:9",
        resolution: str = "2k",
        seed: int = -1,
    ) -> str:
        data = {
            "model": self.MODELS.get(model, model),
            "prompt": prompt,
            "ratio": ratio,
            "resolution": resolution,
        }
        if seed != -1:
            data["seed"] = seed
        result = self._post("/v1/images/generations", data)
        return result.get("task_id", result.get("id", ""))

    def image_to_image(
        self,
        prompt: str,
        image_url: str = None,
        image_base64: str = None,
        model: str = "3.0",
        ratio: str = "16:9",
        resolution: str = "2k",
        seed: int = -1,
    ) -> str:
        data = {
            "model": self.MODELS.get(model, model),
            "prompt": prompt,
            "ratio": ratio,
            "resolution": resolution,
        }
        if image_url:
            data["image_urls"] = [image_url]
        if image_base64:
            data["binary_data_base64"] = [image_base64]
        if seed != -1:
            data["seed"] = seed
        result = self._post("/v1/images/generations", data)
        return result.get("task_id", result.get("id", ""))

    def query_task(self, task_id: str) -> dict:
        url = f"{self.base_url}/v1/images/generations/{task_id}"
        resp = requests.get(url, headers=self.headers, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def wait_result(self, task_id: str, timeout: int = 300, interval: int = 3) -> dict:
        elapsed = 0
        while elapsed < timeout:
            result = self.query_task(task_id)
            status = (
                result.get("status")
                or result.get("data", {}).get("status")
                or result.get("data", {}).get("data", {}).get("status")
                or ""
            )
            if status in ("SUCCESS", "succeeded", "completed"):
                return result
            if status in ("FAILED", "failed"):
                fail_reason = (
                    result.get("fail_reason")
                    or result.get("error")
                    or result.get("data", {}).get("fail_reason")
                    or "unknown"
                )
                raise RuntimeError(f"Task failed: {fail_reason}")
            time.sleep(interval)
            elapsed += interval
        raise TimeoutError(f"Task {task_id} timed out after {timeout}s")
