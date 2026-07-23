import json
import os
from pathlib import Path

from dreamina_video import DreaminaVideoClient
from config import DREAMINA_API_KEY, DREAMINA_BASE_URL


class VideoURLCollector:
    def __init__(self, api_key: str = None, base_url: str = None):
        self.client = DreaminaVideoClient(
            api_key=api_key or DREAMINA_API_KEY,
            base_url=base_url or DREAMINA_BASE_URL,
        )
        self.collected_urls = []

    def collect_urls_from_file(self, json_path: str) -> list[str]:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        urls = []
        for result in data.get("results", []):
            url = result.get("video_url", "")
            if url and result.get("status") == "SUCCESS":
                urls.append(url)
                self.collected_urls.append(
                    {
                        "from": result.get("from_image", ""),
                        "to": result.get("to_image", ""),
                        "url": url,
                    }
                )

        print(f"Collected {len(urls)} video URLs from {json_path}")
        return urls

    def collect_urls_from_results(self, results: list[dict]) -> list[str]:
        urls = []
        for result in results:
            url = result.get("video_url", "")
            if url and result.get("status") == "SUCCESS":
                urls.append(url)
                self.collected_urls.append(
                    {
                        "from": result.get("from_image", ""),
                        "to": result.get("to_image", ""),
                        "url": url,
                    }
                )
        return urls

    def save_collected_urls(self, output_path: str = "collected_urls.json"):
        output = {
            "total": len(self.collected_urls),
            "urls": self.collected_urls,
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(self.collected_urls)} URLs to {output_path}")
        return output

    def get_url_list(self) -> list[str]:
        return [item["url"] for item in self.collected_urls]


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Collect video URLs from results")
    parser.add_argument("--input", "-i", required=True, help="Input JSON file with results")
    parser.add_argument("--output", "-o", default="collected_urls.json", help="Output JSON path")
    args = parser.parse_args()

    collector = VideoURLCollector()
    collector.collect_urls_from_file(args.input)
    collector.save_collected_urls(args.output)


if __name__ == "__main__":
    main()
