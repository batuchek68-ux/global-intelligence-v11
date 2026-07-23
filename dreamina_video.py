import time
import requests


class DreaminaVideoClient:
    MODELS = {
        "v30": "jimeng_v30",
        "v30_pro": "jimeng_v30_pro",
    }

    RATIOS = ["16:9", "4:3", "1:1", "3:4", "9:16", "21:9"]
    RESOLUTIONS = ["720p", "1080p"]
    DURATIONS = [5, 10]

    CAMERA_TEMPLATES = {
        "hitchcock_dolly_in": "希区柯克推进",
        "hitchcock_dolly_out": "希区柯克拉远",
        "robo_arm": "机械臂",
        "dynamic_orbit": "动感环绕",
        "central_orbit": "中心环绕",
        "crane_push": "起重机",
        "quick_pull_back": "超级拉远",
        "counterclockwise_swivel": "逆时针回旋",
        "clockwise_swivel": "顺时针回旋",
        "handheld": "手持运镜",
        "rapid_push_pull": "快速推拉",
    }

    CAMERA_STRENGTHS = ["weak", "medium", "strong"]

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

    def _get(self, endpoint: str) -> dict:
        url = f"{self.base_url}{endpoint}"
        resp = requests.get(url, headers=self.headers, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def text_to_video(
        self,
        prompt: str,
        model: str = "v30",
        resolution: str = "720p",
        ratio: str = "16:9",
        duration: int = 5,
        seed: int = -1,
    ) -> str:
        data = {
            "model": self.MODELS.get(model, model),
            "prompt": prompt,
            "resolution": resolution,
            "ratio": ratio,
            "duration": duration,
            "seed": seed,
        }
        result = self._post("/v1/video/generations", data)
        return result["task_id"]

    def image_to_video(
        self,
        prompt: str,
        images: list[str],
        model: str = "v30",
        resolution: str = "720p",
        ratio: str = "16:9",
        duration: int = 5,
        seed: int = -1,
    ) -> str:
        data = {
            "model": self.MODELS.get(model, model),
            "prompt": prompt,
            "images": images,
            "resolution": resolution,
            "ratio": ratio,
            "duration": duration,
            "seed": seed,
        }
        result = self._post("/v1/video/generations", data)
        return result["task_id"]

    def camera_video(
        self,
        prompt: str,
        images: list[str],
        template_id: str,
        camera_strength: str = "medium",
        model: str = "v30",
        resolution: str = "720p",
        ratio: str = "16:9",
        duration: int = 5,
        seed: int = -1,
    ) -> str:
        data = {
            "model": self.MODELS.get(model, model),
            "prompt": prompt,
            "images": images,
            "resolution": resolution,
            "ratio": ratio,
            "duration": duration,
            "template_id": template_id,
            "camera_strength": camera_strength,
            "seed": seed,
        }
        result = self._post("/v1/video/generations", data)
        return result["task_id"]

    def query_task(self, task_id: str) -> dict:
        return self._get(f"/v1/video/generations/{task_id}")

    def wait_result(self, task_id: str, timeout: int = 300, interval: int = 5) -> dict:
        elapsed = 0
        while elapsed < timeout:
            result = self.query_task(task_id)
            status = (
                result.get("data", {}).get("status")
                or result.get("status")
                or result.get("data", {}).get("data", {}).get("status")
                or ""
            )
            if status in ("SUCCESS", "succeeded", "completed"):
                return result
            if status in ("FAILED", "failed"):
                fail_reason = (
                    result.get("data", {}).get("fail_reason")
                    or result.get("error")
                    or result.get("data", {}).get("data", {}).get("fail_reason")
                    or "unknown"
                )
                raise RuntimeError(f"Task failed: {fail_reason}")
            time.sleep(interval)
            elapsed += interval
        raise TimeoutError(f"Task {task_id} timed out after {timeout}s")
