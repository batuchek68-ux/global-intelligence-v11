from pathlib import Path

from batch_video import BatchVideoGenerator
from collect_urls import VideoURLCollector
from prompt_generator import TransitionPromptGenerator
from historical_prompt import HistoricalPromptGenerator
from genghis_khan_prompt import GenghisKhanPromptGenerator
from prompt_to_image import PromptToImageGenerator
from dreamina_image import DreaminaImageClient
from config import DREAMINA_API_KEY, DREAMINA_BASE_URL


def load_images_from_dir(image_dir: str) -> list[str]:
    image_dir = Path(image_dir)
    extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    images = sorted(
        [str(f) for f in image_dir.iterdir() if f.suffix.lower() in extensions],
        key=lambda x: Path(x).name,
    )
    print(f"Found {len(images)} images in {image_dir}")
    return images


def run_full_workflow(
    source_dir: str,
    output_dir: str = ".",
    scene_type: str = None,
    mood: str = None,
    mode: str = "default",
    figure_type: str = None,
    era: str = None,
    image_model: str = "4.0",
    resolution: str = "720p",
    skip_image_gen: bool = False,
):
    print("=" * 60)
    print("即梦图片 + 视频批量生成工作流")
    print("=" * 60)

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    image_gen = PromptToImageGenerator(
        api_key=DREAMINA_API_KEY,
        base_url=DREAMINA_BASE_URL,
        mode=mode,
    )

    prompts_json = output / "prompts.json"
    generated_images_json = output / "generated_images.json"
    video_results_json = output / "video_results.json"
    collected_urls_json = output / "collected_urls.json"

    if not skip_image_gen:
        print(f"\n[Step 1] Loading source images from: {source_dir}")
        images = load_images_from_dir(source_dir)
        if not images:
            print("  No source images found, generating images from prompts only")

        print(f"\n[Step 2] Generating prompts")
        prompts = []
        if images and len(images) >= 2:
            for i in range(len(images) - 1):
                from_img, to_img = images[i], images[i + 1]
                if isinstance(image_gen.prompt_generator, GenghisKhanPromptGenerator):
                    prompt = image_gen.prompt_generator.generate_prompt(from_img, to_img, scene_type, era, mood)
                elif isinstance(image_gen.prompt_generator, HistoricalPromptGenerator):
                    prompt = image_gen.prompt_generator.generate_prompt(from_img, to_img, figure_type, era, mood)
                else:
                    prompt = image_gen.prompt_generator.generate_prompt(from_img, to_img, scene_type, mood)
                prompts.append(prompt)
                print(f"  [{i + 1}] {prompt[:80]}...")
        else:
            prompts = [
                "A majestic warrior riding across endless grasslands, natural lighting, cinematic",
                "Ancient palace interior, golden light streaming through windows, peaceful",
                "Vast battlefield with armies, dramatic sky, epic scale, no sudden movements",
            ]
            print(f"  Using {len(prompts)} demo prompts")

        import json
        with open(prompts_json, "w", encoding="utf-8") as f:
            json.dump(prompts, f, ensure_ascii=False, indent=2)
        print(f"  Prompts saved to: {prompts_json}")

        print(f"\n[Step 3] Generating images from prompts")
        image_results = image_gen.generate_images_from_prompts(
            prompts,
            model=image_model,
            ratio="16:9",
            resolution="2k",
        )
        image_gen.save_results(str(generated_images_json))

        generated_image_dir = output / "generated_images"
        generated_image_dir.mkdir(exist_ok=True)

        print(f"\n[Step 4] Creating videos from generated images")
    else:
        print(f"\n[Step 1] Loading images from: {source_dir}")
        generated_image_dir = Path(source_dir)

        print(f"\n[Step 2] Generating transition prompts")
        img_prompt_gen = image_gen.prompt_generator
        images = load_images_from_dir(source_dir)
        prompts = []
        if images and len(images) >= 2:
            for i in range(len(images) - 1):
                from_img, to_img = images[i], images[i + 1]
                if isinstance(img_prompt_gen, GenghisKhanPromptGenerator):
                    prompt = img_prompt_gen.generate_prompt(from_img, to_img, scene_type, era, mood)
                elif isinstance(img_prompt_gen, HistoricalPromptGenerator):
                    prompt = img_prompt_gen.generate_prompt(from_img, to_img, figure_type, era, mood)
                else:
                    prompt = img_prompt_gen.generate_prompt(from_img, to_img, scene_type, mood)
                prompts.append(prompt)
        print(f"  Generated {len(prompts)} prompts")

        print(f"\n[Step 3] Skipping image generation (skip_image_gen=True)")
        print(f"\n[Step 4] Creating videos from source images")

    video_gen = BatchVideoGenerator(
        api_key=DREAMINA_API_KEY,
        base_url=DREAMINA_BASE_URL,
        mode=mode,
    )

    if skip_image_gen and images and len(images) >= 2:
        generator = video_gen.prompt_generator
        if isinstance(generator, GenghisKhanPromptGenerator):
            video_gen.prompts = [
                generator.generate_prompt(images[i], images[i + 1], scene_type, era, mood)
                for i in range(len(images) - 1)
            ]
        elif isinstance(generator, HistoricalPromptGenerator):
            video_gen.prompts = [
                generator.generate_prompt(images[i], images[i + 1], figure_type, era, mood)
                for i in range(len(images) - 1)
            ]
        else:
            video_gen.prompts = [
                generator.generate_prompt(images[i], images[i + 1], scene_type, mood)
                for i in range(len(images) - 1)
            ]

    video_gen.run(
        image_dir=str(generated_image_dir),
        output_path=str(video_results_json),
        resolution=resolution,
        ratio="16:9",
        duration=5,
        seed=-1,
        timeout=600,
        scene_type=scene_type,
        mood=mood,
        figure_type=figure_type,
        era=era,
    )

    print(f"\n[Step 5] Collecting video URLs")
    collector = VideoURLCollector()
    collector.collect_urls_from_file(str(video_results_json))
    collector.save_collected_urls(str(collected_urls_json))

    urls = collector.get_url_list()
    print(f"\n[Step 6] Summary")
    if not skip_image_gen:
        print(f"Prompts generated: {len(prompts)}")
        print(f"Images generated: {image_gen.results.__len__() if hasattr(image_gen, 'results') else 0}")
    print(f"Videos generated: {len(urls)}")
    print(f"Results: {video_results_json}")
    print(f"URLs: {collected_urls_json}")

    if urls:
        print(f"\nVideo URLs:")
        for i, url in enumerate(urls, 1):
            print(f"  {i}. {url}")

    return urls


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Full image + video generation workflow")
    parser.add_argument("--source-dir", "-i", required=True, help="Source images or generated images directory")
    parser.add_argument("--output-dir", "-o", default="output", help="Output directory")
    parser.add_argument("--mode", default="default", choices=["default", "historical", "genghis_khan"])
    parser.add_argument("--scene-type", "-s", default=None,
                        choices=["nature", "city", "portrait", "abstract", "cinematic",
                                 "steppe", "battle", "horseback", "strategy", "culture"])
    parser.add_argument("--mood", "-m", default=None,
                        choices=["calm", "dynamic", "mysterious", "romantic", "epic",
                                 "majestic", "heroic", "wise", "powerful", "cultural"])
    parser.add_argument("--figure-type", "-f", default=None,
                        choices=["emperor", "poet", "warrior", "scholar", "artist", "beauty"])
    parser.add_argument("--era", "-e", default=None,
                        choices=["ancient", "medieval", "modern", "rise", "conquest", "peak", "legacy"])
    parser.add_argument("--image-model", default="4.0", choices=["3.0", "3.1", "4.0", "4.6"])
    parser.add_argument("--resolution", default="720p", choices=["720p", "1080p"])
    parser.add_argument("--skip-image-gen", action="store_true", help="Skip image generation, use source images directly for video")
    args = parser.parse_args()

    run_full_workflow(
        args.source_dir,
        args.output_dir,
        args.scene_type,
        args.mood,
        args.mode,
        args.figure_type,
        args.era,
        args.image_model,
        args.resolution,
        args.skip_image_gen,
    )


if __name__ == "__main__":
    main()
