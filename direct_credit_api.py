import hashlib
import time
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
    platform_code = '7'
    version_code = '8.4.0'
    sign = md5(f'9e2c|{uri[-7:]}|{platform_code}|{version_code}|{device_time}||11ac')
    return device_time, sign

# Step 1: Check credits
uri_credit = '/commerce/v1/benefits/user_credit'
device_time, sign = generate_sign(uri_credit)

url_credit = 'https://jimeng.jianying.com' + uri_credit + '?aid=513695&device_platform=web&region=cn&da_version=3.3.9&os=windows&web_component_open_flag=1&web_version=7.5.0&aigc_features=app_lip_sync'

headers_credit = {
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

req = urllib.request.Request(url_credit, data=b'{}', headers=headers_credit, method='POST')
try:
    resp = urllib.request.urlopen(req, timeout=15)
    result = json.loads(resp.read().decode())
    print(f'Credits: {json.dumps(result, indent=2, ensure_ascii=False)}')
except Exception as e:
    print(f'Credit error: {e}')

# Step 2: Receive daily credits
uri_receive = '/commerce/v1/benefits/credit_receive'
device_time2, sign2 = generate_sign(uri_receive)

url_receive = 'https://jimeng.jianying.com' + uri_receive + '?aid=513695&device_platform=web&region=cn&da_version=3.3.9&os=windows&web_component_open_flag=1&web_version=7.5.0&aigc_features=app_lip_sync'

headers_receive = headers_credit.copy()
headers_receive['Device-Time'] = device_time2
headers_receive['Sign'] = sign2

body_receive = json.dumps({"time_zone": "Asia/Shanghai"}).encode()
req2 = urllib.request.Request(url_receive, data=body_receive, headers=headers_receive, method='POST')
try:
    resp2 = urllib.request.urlopen(req2, timeout=15)
    result2 = json.loads(resp2.read().decode())
    print(f'Receive: {json.dumps(result2, indent=2, ensure_ascii=False)}')
except Exception as e:
    print(f'Receive error: {e}')
