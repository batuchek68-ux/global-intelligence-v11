import hashlib
import hmac
import json
import time
from datetime import datetime, timezone
from urllib.parse import quote

import requests


class BytePlusAuth:
    def __init__(self, access_key_id: str, secret_access_key: str, service: str, region: str):
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.service = service
        self.region = region

    def _sha256(self, data: str) -> str:
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    def _hmac_sha256(self, key: bytes, msg: str) -> bytes:
        return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

    def _get_signing_key(self, short_date: str) -> bytes:
        k_date = self._hmac_sha256(self.secret_access_key.encode("utf-8"), short_date)
        k_region = self._hmac_sha256(k_date, self.region)
        k_service = self._hmac_sha256(k_region, self.service)
        k_signing = self._hmac_sha256(k_service, "request")
        return k_signing

    def sign(self, method: str, body: str, timestamp: str) -> dict:
        now = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        short_date = now.strftime("%Y%m%d")
        date_str = now.strftime("%Y%m%dT%H%M%SZ")

        payload_hash = self._sha256(body)

        signed_headers = "content-type;host;x-date"
        canonical_headers = f"content-type:application/json\nhost:cv.byteplusapi.com\nx-date:{date_str}\n"
        canonical_request = f"{method}\n/\n\n{canonical_headers}\n{signed_headers}\n{payload_hash}"

        credential_scope = f"{short_date}/{self.region}/{self.service}/request"
        string_to_sign = f"HMAC-SHA256\n{date_str}\n{credential_scope}\n{self._sha256(canonical_request)}"

        signing_key = self._get_signing_key(short_date)
        signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

        auth_header = (
            f"HMAC-SHA256 Credential={self.access_key_id}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, Signature={signature}"
        )

        return {
            "Authorization": auth_header,
            "Content-Type": "application/json",
            "Host": "cv.byteplusapi.com",
            "X-Date": date_str,
        }


class SubjectRecognitionClient:
    REQ_KEY = "realman_avatar_picture_create_role_omni_cv"
    VERSION = "2024-06-06"

    def __init__(self, access_key_id: str, secret_access_key: str):
        self.auth = BytePlusAuth(
            access_key_id=access_key_id,
            secret_access_key=secret_access_key,
            service="cv",
            region="ap-singapore-1",
        )
        self.base_url = "https://cv.byteplusapi.com"

    def _request(self, action: str, body: dict) -> dict:
        url = f"{self.base_url}?Action={action}&Version={self.VERSION}"
        body_str = json.dumps(body)
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        headers = self.auth.sign("POST", body_str, timestamp)
        resp = requests.post(url, data=body_str, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def submit_task(self, image_url: str, callback_url: str = None) -> dict:
        body = {
            "req_key": self.REQ_KEY,
            "image_url": image_url,
        }
        if callback_url:
            body["callback_url"] = callback_url
        return self._request("CVSubmitTask", body)

    def query_result(self, task_id: str) -> dict:
        body = {
            "req_key": self.REQ_KEY,
            "task_id": task_id,
        }
        return self._request("CVGetResult", body)

    def wait_result(self, task_id: str, timeout: int = 60, interval: int = 2) -> dict:
        elapsed = 0
        while elapsed < timeout:
            result = self.query_result(task_id)
            data = result.get("data", {})
            status = data.get("status", "")
            if status == "done":
                return result
            if status in ("not_found", "expired"):
                raise RuntimeError(f"Task {task_id} {status}")
            time.sleep(interval)
            elapsed += interval
        raise TimeoutError(f"Task {task_id} timed out after {timeout}s")
