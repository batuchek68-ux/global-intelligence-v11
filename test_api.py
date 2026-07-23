import json
import sys
from dreamina_free_client import DreaminaFreeClient
from config import DREAMINA_SESSION_ID


def main():
    if not DREAMINA_SESSION_ID or DREAMINA_SESSION_ID == "your_session_id_here":
        print("Error: Please set DREAMINA_SESSION_ID in .env file")
        print("\nHow to get session ID:")
        print("1. Open https://jimeng.jianying.com/")
        print("2. Login to your account")
        print("3. Press F12 -> Application -> Cookies")
        print("4. Find 'sessionid' and copy its value")
        print("5. Add to .env: DREAMINA_SESSION_ID=your_value")
        return

    client = DreaminaFreeClient()

    print("Testing Dreamina Free API...")
    print("=" * 40)

    print("\n1. Checking credits...")
    try:
        credits = client.get_credits()
        print(f"Credits: {json.dumps(credits, indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"Credits error: {e}")

    print("\n2. Testing image generation...")
    try:
        result = client.text2image(
            prompt="A beautiful sunset over mountains",
            model="jimeng-5.0",
            ratio="16:9",
            resolution="2k",
        )
        print(f"Image result: {json.dumps(result, indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"Image error: {e}")


if __name__ == "__main__":
    main()
