import json
import asyncio
import urllib.request

async def get_cookies():
    data = urllib.request.urlopen('http://127.0.0.1:9222/json').read()
    tabs = json.loads(data)
    
    import websockets
    ws_url = tabs[0]['webSocketDebuggerUrl']
    
    async with websockets.connect(ws_url, max_size=10*1024*1024) as ws:
        await ws.send(json.dumps({"id": 1, "method": "Storage.getCookies"}))
        result = json.loads(await ws.recv())
        cookies = result.get('result', {}).get('cookies', [])
        
        for cookie in cookies:
            if cookie['name'] == 'sessionid' and 'jimeng' in cookie.get('domain', ''):
                print(f"SESSION_ID={cookie['value']}")
                return
        
        print(f"sessionid not found. Total cookies: {len(cookies)}")
        jimeng_cookies = [c for c in cookies if 'jimeng' in c.get('domain', '') or 'jianying' in c.get('domain', '')]
        print(f"jimeng cookies: {len(jimeng_cookies)}")
        for c in jimeng_cookies[:10]:
            print(f"  {c['domain']} -> {c['name']}")

asyncio.run(get_cookies())
