import requests
import json

session_id = "db33fc325c5966e358a283b663f2f0c3"
base_url = "https://jimeng.jianying.com"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {session_id}",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://jimeng.jianying.com/ai-tool/home",
    "Origin": "https://jimeng.jianying.com",
}

resp = requests.get(f"{base_url}/mweb/v1/get_user_credits", headers=headers, timeout=30)
print(f"Status: {resp.status_code}")
print(f"Response: {resp.text[:500]}")
