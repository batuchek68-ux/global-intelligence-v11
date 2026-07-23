import hashlib
import time
import uuid
import json
import urllib.request
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SESSION_ID = 'db33fc325c5966e358a283b663f2f0c3'

def md5(text):
    return hashlib.md5(text.encode()).hexdigest()

def generate_sign(uri):
    device_time = str(int(time.time()))
    sign = md5(f'9e2c|{uri[-7:]}|7|8.4.0|{device_time}||11ac')
    return device_time, sign

uri = '/mweb/v1/aigc_draft/generate'
device_time, sign = generate_sign(uri)

url = 'https://jimeng.jianying.com' + uri + '?os=windows&aid=513695&web_version=7.5.0&da_version=3.3.9&aigc_features=app_lip_sync'

uid = str(uuid.uuid4())
comp_id = str(uuid.uuid4())
meta_id = str(uuid.uuid4())
submit_id = str(uuid.uuid4())
abilities_id = str(uuid.uuid4())
gen_image_id = str(uuid.uuid4())
image_input_id = str(uuid.uuid4())

payload = {
    "extend": {
        "root_model": "high_aes_general_v50"
    },
    "submit_id": submit_id,
    "metrics_extra": json.dumps({
        "enterFrom": "click",
        "isDefaultSeed": 1,
        "promptSource": "custom",
        "isRegenerate": False,
        "originSubmitId": uid
    }),
    "draft_content": json.dumps({
        "type": "draft",
        "id": uid,
        "min_version": "3.0.5",
        "is_from_tsn": True,
        "version": "3.3.9",
        "main_component_id": comp_id,
        "component_list": [{
            "type": "image_base_component",
            "id": comp_id,
            "min_version": "1.0.0",
            "metadata": {
                "type": "",
                "id": meta_id,
                "created_platform": 3,
                "created_platform_version": "",
                "created_time_in_ms": int(time.time() * 1000),
                "created_did": ""
            },
            "generate_type": "normal",
            "aigc_mode": "workbench",
            "abilities": {
                "type": "",
                "id": abilities_id,
                "generate_image": {
                    "id": gen_image_id,
                    "type": "",
                    "image_gen_inputs": [{
                        "type": "",
                        "id": image_input_id,
                        "model_req_key": "high_aes_general_v50",
                        "prompt": "成吉思汗骑马驰骋在辽阔草原上，金色阳光洒落，一镜到底",
                        "resolution": "2k",
                        "seed": 123456789,
                        "image_num": 1,
                        "image_height": 1440,
                        "image_width": 2560,
                        "use_hyper": False
                    }],
                    "task_extra": json.dumps({
                        "enterFrom": "click",
                        "isDefaultSeed": 1,
                        "promptSource": "custom",
                        "isRegenerate": False,
                        "originSubmitId": uid
                    })
                }
            }
        }]
    }),
    "http_common_info": {
        "aid": 513695
    }
}

headers = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Content-Type': 'application/json',
    'Origin': 'https://jimeng.jianying.com',
    'Referer': 'https://jimeng.jianying.com/ai-tool/image/generate',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
    'Cookie': f'sessionid={SESSION_ID}',
    'Device-Time': device_time,
    'Sign': sign,
    'Sign-Ver': '1',
    'Appid': '513695',
    'Appvr': '8.4.0',
    'Pf': '7',
    'Lan': 'zh-Hans',
    'Loc': 'cn',
    'Tdid': '',
    'App-Sdk-Version': '48.0.0',
}

body = json.dumps(payload).encode()
req = urllib.request.Request(url, data=body, headers=headers, method='POST')

try:
    resp = urllib.request.urlopen(req, timeout=30)
    result = json.loads(resp.read().decode())
    print(f'Result: {json.dumps(result, indent=2, ensure_ascii=False)[:3000]}')
except Exception as e:
    print(f'Error: {e}')
