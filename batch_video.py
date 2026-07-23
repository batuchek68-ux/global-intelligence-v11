import json
import os
import time
from pathlib import Path

from dreamina_video import DreaminaVideoClient
from prompt_generator import TransitionPromptGenerator
from historical_prompt import HistoricalPromptGenerator
from genghis_khan_prompt import GenghisKhanPromptGenerator
from config import DREAMINA_API_KEY, DREAMINA_BASE_URL


class BatchVideoGenerator:
    def __init__(self, api_key: str = None, base_url: str = None, mode: str = "default"):
        self.client = DreaminaVideoClient(
            api_key=api_key or DREAMINA_API_KEY,
            base_url=base_url or DREAMINA_BASE_URL,
        )
        if mode == "genghis_khan":
            self.prompt_generator = GenghisKhanPromptGenerator()
        elif mode == "historical":
            self.prompt_generator = HistoricalPromptGenerator()
        else:
            self.prompt_generator = TransitionPromptGenerator()
        self.mode = mode
        self.results = []

    def load_images(self, image_dir: str) -> list[str]:
        image_dir = Path(image_dir)
        extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
        images = sorted(
            [
                str(f)
                for f in image_dir.iterdir()
                if f.suffix.lower() in extensions
            ],
            key=lambda x: Path(x).name,
        )
        print(f"Found {len(images)} images in {image_dir}")
        return images

    def create_video_tasks(
        self,
        images: list[str],
        resolution: str = "720p",
        ratio: str = "16:9",
        duration: int = 5,
        seed: int = -1,
        scene_type: str = None,
        mood: str = None,
        figure_type: str = None,
        era: str = None,
    ) -> list[str]:
        task_ids = []
        total = len(images) - 1

        for i in range(total):
            if isinstance(self.prompt_generator, GenghisKhanPromptGenerator):
                prompt = self.prompt_generator.generate_prompt(
                    images[i], images[i + 1], scene_type, era, mood
                )
            elif isinstance(self.prompt_generator, HistoricalPromptGenerator):
                prompt = self.prompt_generator.generate_prompt(
                    images[i], images[i + 1], figure_type, era, mood
                )
            else:
                prompt = self.prompt_generator.generate_prompt(
                    images[i], images[i + 1], scene_type, mood
                )
            pair = [images[i], images[i + 1]]

            print(f"\n[{i + 1}/{total}] Creating video:")
            print(f"  From: {Path(pair[0]).name}")
            print(f"  To:   {Path(pair[1]).name}")
            print(f"  Prompt: {prompt}")

            task_id = self.client.image_to_video(
                prompt=prompt,
                images=pair,
                model="v30",
                resolution=resolution,
                ratio=ratio,
                duration=duration,
                seed=seed,
            )
            task_ids.append(task_id)
            print(f"  Task ID: {task_id}")

            time.sleep(0.5)

        return task_ids

    def wait_and_collect_results(
        self, task_ids: list[str], images: list[str], timeout: int = 600
    ) -> list[dict]:
        results = []
        total = len(task_ids)

        for i, task_id in enumerate(task_ids):
            print(f"\n[{i + 1}/{total}] Waiting for task {task_id}...")
            try:
                result = self.client.wait_result(task_id, timeout=timeout)
                video_url = (
                    result.get("data", {}).get("data", {}).get("content", {}).get("video_url")
                    or result.get("data", {}).get("content", {}).get("video_url")
                    or result.get("response", {}).get("videoUrl")
                    or result.get("response", {}).get("video_url")
                    or ""
                )
                status = "SUCCESS" if video_url else "FAILED"
                if video_url:
                    print(f"  Video URL: {video_url}")
                else:
                    print(f"  Warning: No video URL in response")
            except Exception as e:
                video_url = ""
                status = "FAILED"
                print(f"  Error: {e}")

            entry = {
                "index": i,
                "task_id": task_id,
                "from_image": images[i],
                "to_image": images[i + 1],
                "video_url": video_url,
                "status": status,
            }
            results.append(entry)
            self.results.append(entry)

        return results

    def save_results(self, output_path: str = "video_results.json"):
        output = {
            "total": len(self.results),
            "success": sum(1 for r in self.results if r["status"] == "SUCCESS"),
            "failed": sum(1 for r in self.results if r["status"] == "FAILED"),
            "results": self.results,
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"\nResults saved to {output_path}")
        return output

    def run(
        self,
        image_dir: str,
        output_path: str = "video_results.json",
        resolution: str = "720p",
        ratio: str = "16:9",
        duration: int = 5,
        seed: int = -1,
        timeout: int = 600,
        scene_type: str = None,
        mood: str = None,
        figure_type: str = None,
        era: str = None,
    ) -> dict:
        images = self.load_images(image_dir)
        if len(images) < 2:
            raise ValueError("Need at least 2 images to create videos")

        task_ids = self.create_video_tasks(
            images,
            resolution=resolution,
            ratio=ratio,
            duration=duration,
            seed=seed,
            scene_type=scene_type,
            mood=mood,
            figure_type=figure_type,
            era=era,
        )
        self.wait_and_collect_results(task_ids, images, timeout=timeout)
        return self.save_results(output_path)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Batch video generation from images")
    parser.add_argument("--image-dir", "-i", required=True, help="Directory with images")
    parser.add_argument("--output", "-o", default="video_results.json", help="Output JSON path")
    parser.add_argument("--resolution", "-r", default="720p", choices=["720p", "1080p"])
    parser.add_argument("--ratio", default="16:9")
    parser.add_argument("--duration", "-d", type=int, default=5, choices=[5, 10])
    parser.add_argument("--seed", type=int, default=-1)
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--mode", default="default", choices=["default", "historical", "genghis_khan"], help="Prompt generation mode")
    parser.add_argument("--scene-type", "-s", default=None, choices=["nature", "city", "portrait", "abstract", "cinematic", "steppe", "battle", "horseback", "strategy", "culture"])
    parser.add_argument("--mood", "-m", default=None, choices=["calm", "dynamic", "mysterious", "romantic", "epic", "majestic", "heroic", "wise", "powerful", "cultural"])
    parser.add_argument("--figure-type", "-f", default=None, choices=["emperor", "poet", "warrior", "scholar", "artist", "beauty"])
    parser.add_argument("--era", "-e", default=None, choices=["ancient", "medieval", "modern", "rise", "conquest", "peak", "legacy"])
    args = parser.parse_args()

    generator = BatchVideoGenerator(mode=args.mode)
    generator.run(
        image_dir=args.image_dir,
        output_path=args.output,
        resolution=args.resolution,
        ratio=args.ratio,
        duration=args.duration,
        seed=args.seed,
        timeout=args.timeout,
        scene_type=args.scene_type,
        mood=args.mood,
        figure_type=args.figure_type,
        era=args.era,
    )


if __name__ == "__main__":
    main()
