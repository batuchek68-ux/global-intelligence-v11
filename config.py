import os
from dotenv import load_dotenv

load_dotenv()

BYTEPLUS_ACCESS_KEY_ID = os.getenv("BYTEPLUS_ACCESS_KEY_ID", "")
BYTEPLUS_SECRET_ACCESS_KEY = os.getenv("BYTEPLUS_SECRET_ACCESS_KEY", "")
BYTEPLUS_SERVICE = "cv"
BYTEPLUS_REGION = "ap-singapore-1"
BYTEPLUS_API_URL = "https://cv.byteplusapi.com"

DREAMINA_API_KEY = os.getenv("DREAMINA_API_KEY", "")
DREAMINA_SESSION_ID = os.getenv("DREAMINA_SESSION_ID", "")
DREAMINA_REGION = os.getenv("DREAMINA_REGION", "cn")

REGION_PREFIXES = {
    "cn": "",
    "us": "us-",
    "hk": "hk-",
    "jp": "jp-",
    "sg": "sg-",
}

def get_auth_header():
    prefix = REGION_PREFIXES.get(DREAMINA_REGION, "")
    return f"Bearer {prefix}{DREAMINA_SESSION_ID}"

DREAMINA_BASE_URL = "https://jimeng.jianying.com"
