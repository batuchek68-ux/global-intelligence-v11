import json
import subprocess
import time
from pathlib import Path


class DreaminaCLIClient:
    def __init__(self, cli_path: str = r"C:\Users\Surface\.dreamina_cli\dreamina.exe"):
        self.cli_path = cli_path
        self._verify_cli()

    def _verify_cli(self):
        if not Path(self.cli_path).exists():
            raise FileNotFoundError(f"Dreamina CLI not found at {self.cli_path}")

    def _run(self, args: list[str], timeout: int = 300) -> dict:
        cmd = [self.cli_path] + args
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode != 0:
            raise RuntimeError(f"CLI error: {result.stderr or result.stdout}")
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {"raw_output": result.stdout}

    def login(self, headless: bool = False) -> dict:
        args = ["login"]
        if headless:
            args.append("--headless")
        return self._run(args, timeout=60)

    def check_login(self, device_code: str = None) -> dict:
        args = ["login", "checklogin"]
        if device_code:
            args.append(f"--device_code={device_code}")
        return self._run(args, timeout=30)

    def user_credit(self) -> dict:
        return self._run(["user_credit"], timeout=30)

    def text2image(
        self,
        prompt: str,
        model_version: str = "5.0",
        ratio: str = "16:9",
        resolution_type: str = "2k",
        generate_num: int = 1,
        poll: int = 60,
    ) -> dict:
        args = [
            "text2image",
            f"--prompt={prompt}",
            f"--model_version={model_version}",
            f"--ratio={ratio}",
            f"--resolution_type={resolution_type}",
            f"--generate_num={generate_num}",
            f"--poll={poll}",
        ]
        return self._run(args, timeout=poll + 30)

    def image2video(
        self,
        image_path: str,
        prompt: str,
        model_version: str = "seedance2.0_vip",
        video_resolution: str = "720p",
        duration: int = 5,
        poll: int = 180,
    ) -> dict:
        args = [
            "image2video",
            f"--image={image_path}",
            f"--prompt={prompt}",
            f"--model_version={model_version}",
            f"--video_resolution={video_resolution}",
            f"--duration={duration}",
            f"--poll={poll}",
        ]
        return self._run(args, timeout=poll + 30)

    def frames2video(
        self,
        first_image: str,
        last_image: str,
        prompt: str,
        model_version: str = "seedance2.0_vip",
        video_resolution: str = "720p",
        duration: int = 5,
        poll: int = 180,
    ) -> dict:
        args = [
            "frames2video",
            f"--first={first_image}",
            f"--last={last_image}",
            f"--prompt={prompt}",
            f"--model_version={model_version}",
            f"--video_resolution={video_resolution}",
            f"--duration={duration}",
            f"--poll={poll}",
        ]
        return self._run(args, timeout=poll + 30)

    def query_result(self, submit_id: str) -> dict:
        return self._run(["query_result", f"--submit_id={submit_id}"], timeout=30)

    def list_tasks(self, gen_status: str = None) -> dict:
        args = ["list_task"]
        if gen_status:
            args.append(f"--gen_status={gen_status}")
        return self._run(args, timeout=30)
