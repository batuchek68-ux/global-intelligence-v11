import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def check_env():
    print("Checking environment...")
    print("=" * 40)
    
    session_id = os.getenv("DREAMINA_SESSION_ID", "")
    region = os.getenv("DREAMINA_REGION", "cn")
    
    if not session_id or session_id == "your_session_id_here":
        print("❌ DREAMINA_SESSION_ID not set!")
        print("\nHow to get it:")
        print("1. Open: https://jimeng.jianying.com/")
        print("2. Login to your account")
        print("3. Press F12 → Console")
        print("4. Paste: document.cookie.split(';').find(c => c.trim().startsWith('sessionid=')).split('=')[1]")
        print("5. Copy the output")
        print("6. Add to .env: DREAMINA_SESSION_ID=your_value")
        return False
    
    print(f"✓ DREAMINA_SESSION_ID: {session_id[:10]}...")
    print(f"✓ DREAMINA_REGION: {region}")
    return True

def test_api():
    print("\nTesting API connection...")
    print("=" * 40)
    
    try:
        from dreamina_free_client import DreaminaFreeClient
        client = DreaminaFreeClient()
        
        print("\n1. Testing credits...")
        credits = client.get_credits()
        print(f"   Credits: {credits}")
        
        print("\n2. Testing image generation...")
        result = client.text2image(
            prompt="A beautiful sunset",
            model="jimeng-4.0",
            ratio="16:9",
            resolution="2k",
        )
        print(f"   Result: {result}")
        
        print("\n✅ API is working!")
        return True
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

if __name__ == "__main__":
    if check_env():
        test_api()
    else:
        print("\nPlease set up your session ID first.")
