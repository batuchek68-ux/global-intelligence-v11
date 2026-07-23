import json
import time
from pathlib import Path

from dreamina_cli_client import DreaminaCLIClient
from prompt_generator import TransitionPromptGenerator
from historical_prompt import HistoricalPromptGenerator
from genghis_khan_prompt import GenghisKhanPromptGenerator


class DreaminaCLIWorkflow:
    def __init__(self, mode: str = "default"):
        self.client = DreaminaCLIClient()
        if mode == "genghis_khan":
            self.prompt_generator = GenghisKhanPromptGenerator()
        elif mode == "historical":
            self.prompt_generator = HistoricalPromptGenerator()
        else:
            self.prompt_generator = TransitionPromptGenerator()
        self.mode = mode

    def login(self, headless: bool = False) -> dict:
        print("Logging in to Dreamina...")
        return self.client.login(headless=headless)

    def check_login(self, device_code: str = None) -> dict:
        return self.client.check_login(device_code)

    def get_credits(self) -> dict:
        return self.client.user_credit()

    def generate_image(
        self,
        prompt: str,
        model_version: str = "5.0",
        ratio: str = "16:9",
        resolution_type: str = "2k",
        generate_num: int = 1,
    ) -> dict:
        print(f"\nGenerating image:")
        print(f"  Prompt: {prompt}")
        print(f"  Model: {model_version}, Resolution: {resolution_type}")

        result = self.client.text2image(
            prompt=prompt,
            model_version=model_version,
            ratio=ratio,
            resolution_type=resolution_type,
            generate_num=generate_num,
            poll=60,
        )
        print(f"  Result: {result}")
        return result

    def generate_video_from_image(
        self,
        image_path: str,
        prompt: str,
        model_version: str = "seedance2.0_vip",
        video_resolution: str = "720p",
        duration: int = 5,
    ) -> dict:
        print(f"\nGenerating video from image:")
        print(f"  Image: {image_path}")
        print(f"  Prompt: {prompt}")

        result = self.client.image2video(
            image_path=image_path,
            prompt=prompt,
            model_version=model_version,
            video_resolution=video_resolution,
            duration=duration,
            poll=180,
        )
        print(f"  Result: {result}")
        return result

    def generate_video_from_frames(
        self,
        first_image: str,
        last_image: str,
        prompt: str,
        model_version: str = "seedance2.0_vip",
        video_resolution: str = "720p",
        duration: int = 5,
    ) -> dict:
        print(f"\nGenerating video from frames:")
        print(f"  First: {first_image}")
        print(f"  Last: {last_image}")
        print(f"  Prompt: {prompt}")

        result = self.client.frames2video(
            first_image=first_image,
            last_image=last_image,
            prompt=prompt,
            model_version=model_version,
            video_resolution=video_resolution,
            duration=duration,
            poll=180,
        )
        print(f"  Result: {result}")
        return result

    def batch_images_to_videos(
        self,
        image_dir: str,
        output_dir: str = "output",
        resolution: str = "720p",
        model_version: str = "seedance2.0_vip",
        duration: int = 5,
        scene_type: str = None,
        mood: str = None,
        figure_type: str = None,
        era: str = None,
    ) -> list[dict]:
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)

        images = self._load_images(image_dir)
        if len(images) < 2:
            print("Error: Need at least 2 images")
            return []

        results = []
        total = len(images) - 1

        for i in range(total):
            from_img, to_img = images[i], images[i + 1]

            if isinstance(self.prompt_generator, GenghisKhanPromptGenerator):
                prompt = self.prompt_generator.generate_prompt(from_img, to_img, scene_type, era, mood)
            elif isinstance(self.prompt_generator, HistoricalPromptGenerator):
                prompt = self.prompt_generator.generate_prompt(from_img, to_img, figure_type, era, mood)
            else:
                prompt = self.prompt_generator.generate_prompt(from_img, to_img, scene_type, mood)

            print(f"\n[{i + 1}/{total}] Generating video:")
            print(f"  From: {Path(from_img).name}")
            print(f"  To: {Path(to_img).name}")
            print(f"  Prompt: {prompt}")

            try:
                result = self.generate_video_from_frames(
                    first_image=from_img,
                    last_image=to_img,
                    prompt=prompt,
                    model_version=model_version,
                    video_resolution=resolution,
                    duration=duration,
                )
                status = "SUCCESS"
            except Exception as e:
                result = {"error": str(e)}
                status = "FAILED"
                print(f"  Error: {e}")

            entry = {
                "index": i,
                "from_image": from_img,
                "to_image": to_img,
                "prompt": prompt,
                "status": status,
                "result": result,
            }
            results.append(entry)

            time.sleep(1)

        results_path = output / "video_results.json"
        with open(results_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\nResults saved to {results_path}")

        urls = [r["result"].get("video_url", "") for r in results if r["status"] == "SUCCESS"]
        urls_path = output / "collected_urls.json"
        with open(urls_path, "w", encoding="utf-8") as f:
            json.dump(urls, f, ensure_ascii=False, indent=2)
        print(f"URLs saved to {urls_path}")

        return results

    def _load_images(self, image_dir: str) -> list[str]:
        image_dir = Path(image_dir)
        extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
        images = sorted(
            [str(f) for f in image_dir.iterdir() if f.suffix.lower() in extensions],
            key=lambda x: Path(x).name,
        )
        print(f"Found {len(images)} images in {image_dir}")
        return images


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Dreamina CLI Workflow")
    parser.add_argument("command", choices=["login", "credits", "image", "video", "batch"])
    parser.add_argument("--prompt", "-p", help="Prompt for generation")
    parser.add_argument("--image", "-i", help="Image path")
    parser.add_argument("--first", help="First frame image path")
    parser.add_argument("--last", help="Last frame image path")
    parser.add_argument("--image-dir", help="Directory with images for batch")
    parser.add_argument("--output-dir", "-o", default="output", help="Output directory")
    parser.add_argument("--model", default="5.0", help="Model version")
    parser.add_argument("--video-model", default="seedance2.0_vip", help="Video model")
    parser.add_argument("--resolution", default="720p", help="Video resolution")
    parser.add_argument("--duration", type=int, default=5, help="Video duration")
    parser.add_argument("--ratio", default="16:9", help="Image ratio")
    parser.add_argument("--resolution-type", default="2k", help="Image resolution type")
    parser.add_argument("--mode", default="default", choices=["default", "historical", "genghis_khan"])
    parser.add_argument("--scene-type", "-s", default=None)
    parser.add_argument("--mood", "-m", default=None)
    parser.add_argument("--figure-type", "-f", default=None)
    parser.add_argument("--era", "-e", default=None)
    parser.add_argument("--device-code", help="Device code for login check")
    parser.add_argument("--headless", action="store_true")
    args = parser.parse_args()

    workflow = DreaminaCLIWorkflow(mode=args.mode)

    if args.command == "login":
        result = workflow.login(headless=args.headless)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.command == "credits":
        result = workflow.get_credits()
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.command == "image":
        if not args.prompt:
            print("Error: --prompt required")
            return
        result = workflow.generate_image(
            prompt=args.prompt,
            model_version=args.model,
            ratio=args.ratio,
            resolution_type=args.resolution_type,
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.command == "video":
        if not args.prompt:
            print("Error: --prompt required")
            return
        if args.first and args.last:
            result = workflow.generate_video_from_frames(
                first_image=args.first,
                last_image=args.last,
                prompt=args.prompt,
                model_version=args.video_model,
                video_resolution=args.resolution,
                duration=args.duration,
            )
        elif args.image:
            result = workflow.generate_video_from_image(
                image_path=args.image,
                prompt=args.prompt,
                model_version=args.video_model,
                video_resolution=args.resolution,
                duration=args.duration,
            )
        else:
            print("Error: --image or --first/--last required")
            return
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.command == "batch":
        if not args.image_dir:
            print("Error: --image-dir required")
            return
        workflow.batch_images_to_videos(
            image_dir=args.image_dir,
            output_dir=args.output_dir,
            resolution=args.resolution,
            model_version=args.video_model,
            duration=args.duration,
            scene_type=args.scene_type,
            mood=args.mood,
            figure_type=args.figure_type,
            era=args.era,
        )


if __name__ == "__main__":
    main()
