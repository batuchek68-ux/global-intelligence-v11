import json
import os
from pathlib import Path

from dreamina_image import DreaminaImageClient
from genghis_khan_prompt import GenghisKhanPromptGenerator
from historical_prompt import HistoricalPromptGenerator
from prompt_generator import TransitionPromptGenerator
from config import DREAMINA_API_KEY, DREAMINA_BASE_URL


class PromptToImageGenerator:
    def __init__(self, api_key: str = None, base_url: str = None, mode: str = "default"):
        self.client = DreaminaImageClient(
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

    def generate_image_from_prompt(
        self,
        prompt: str,
        model: str = "4.0",
        ratio: str = "16:9",
        resolution: str = "2k",
        seed: int = -1,
    ) -> dict:
        print(f"\nGenerating image:")
        print(f"  Prompt: {prompt}")

        task_id = self.client.text_to_image(
            prompt=prompt,
            model=model,
            ratio=ratio,
            resolution=resolution,
            seed=seed,
        )
        print(f"  Task ID: {task_id}")

        result = self.client.wait_result(task_id)
        return result

    def generate_images_from_prompts(
        self,
        prompts: list[str],
        model: str = "4.0",
        ratio: str = "16:9",
        resolution: str = "2k",
        seed: int = -1,
    ) -> list[dict]:
        results = []
        total = len(prompts)

        for i, prompt in enumerate(prompts):
            print(f"\n[{i + 1}/{total}] Generating image")
            try:
                result = self.generate_image_from_prompt(
                    prompt=prompt,
                    model=model,
                    ratio=ratio,
                    resolution=resolution,
                    seed=seed,
                )
                image_url = result.get("data", {}).get("url", "")
                status = "SUCCESS"
                print(f"  Image URL: {image_url}")
            except Exception as e:
                image_url = ""
                status = "FAILED"
                print(f"  Error: {e}")

            entry = {
                "index": i,
                "prompt": prompt,
                "image_url": image_url,
                "status": status,
            }
            results.append(entry)
            self.results.append(entry)

        return results

    def generate_images_from_pairs(
        self,
        image_pairs: list[tuple[str, str]],
        scene_type: str = None,
        mood: str = None,
        figure_type: str = None,
        era: str = None,
        model: str = "4.0",
        ratio: str = "16:9",
        resolution: str = "2k",
        seed: int = -1,
    ) -> list[dict]:
        prompts = []
        for from_image, to_image in image_pairs:
            if isinstance(self.prompt_generator, GenghisKhanPromptGenerator):
                prompt = self.prompt_generator.generate_prompt(
                    from_image, to_image, scene_type, era, mood
                )
            elif isinstance(self.prompt_generator, HistoricalPromptGenerator):
                prompt = self.prompt_generator.generate_prompt(
                    from_image, to_image, figure_type, era, mood
                )
            else:
                prompt = self.prompt_generator.generate_prompt(
                    from_image, to_image, scene_type, mood
                )
            prompts.append(prompt)

        return self.generate_images_from_prompts(
            prompts, model=model, ratio=ratio, resolution=resolution, seed=seed
        )

    def save_results(self, output_path: str = "image_results.json"):
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


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Generate images from prompts")
    parser.add_argument("--prompts", "-p", nargs="+", help="List of prompts")
    parser.add_argument("--prompt-file", "-f", help="File with prompts (one per line)")
    parser.add_argument("--output", "-o", default="image_results.json", help="Output JSON path")
    parser.add_argument("--mode", default="default", choices=["default", "historical", "genghis_khan"])
    parser.add_argument("--model", default="4.0", choices=["3.0", "3.1", "4.0", "4.6"])
    parser.add_argument("--ratio", default="16:9")
    parser.add_argument("--resolution", default="2k", choices=["1k", "2k", "4k"])
    parser.add_argument("--seed", type=int, default=-1)
    args = parser.parse_args()

    generator = PromptToImageGenerator(mode=args.mode)

    if args.prompt_file:
        with open(args.prompt_file, "r", encoding="utf-8") as f:
            prompts = [line.strip() for line in f if line.strip()]
    elif args.prompts:
        prompts = args.prompts
    else:
        print("Error: Must provide --prompts or --prompt-file")
        return

    generator.generate_images_from_prompts(
        prompts,
        model=args.model,
        ratio=args.ratio,
        resolution=args.resolution,
        seed=args.seed,
    )
    generator.save_results(args.output)


if __name__ == "__main__":
    main()
