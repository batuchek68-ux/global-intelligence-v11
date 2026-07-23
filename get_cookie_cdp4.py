import json
import asyncio
import urllib.request
import websockets

async def get_cookies():
    data = urllib.request.urlopen('http://127.0.0.1:9222/json').read()
    tabs = json.loads(data)
    ws_url = tabs[0]['webSocketDebuggerUrl']
    
    async with websockets.connect(ws_url, max_size=10*1024*1024) as ws:
        await ws.send(json.dumps({"id": 1, "method": "Page.navigate", "params": {"url": "https://jimeng.jianying.com/"}}))
        await ws.recv()
        
        print("Waiting for page to load...")
        await asyncio.sleep(15)
        
        await ws.send(json.dumps({"id": 2, "method": "Network.getAllCookies"}))
        result = json.loads(await ws.recv())
        cookies = result.get('result', {}).get('cookies', [])
        
        jimeng_cookies = [c for c in cookies if 'jimeng' in c.get('domain', '') or 'jianying' in c.get('domain', '')]
        print(f"Total cookies: {len(cookies)}, jimeng: {len(jimeng_cookies)}")
        
        for c in jimeng_cookies:
            print(f"  {c['domain']} -> {c['name']}")
        
        for cookie in cookies:
            if cookie['name'] == 'sessionid':
                print(f"\nSESSION_ID={cookie['value']}")
                return
        
        print("\nNo sessionid found - user may not be logged in")

asyncio.run(get_cookies())
