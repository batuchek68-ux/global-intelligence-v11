import json
import asyncio
import urllib.request
import websockets

async def get_cookies():
    data = urllib.request.urlopen('http://127.0.0.1:9222/json').read()
    tabs = json.loads(data)
    ws_url = tabs[0]['webSocketDebuggerUrl']
    
    async with websockets.connect(ws_url, max_size=10*1024*1024) as ws:
        await ws.send(json.dumps({"id": 1, "method": "Network.getAllCookies"}))
        result = json.loads(await ws.recv())
        cookies = result.get('result', {}).get('cookies', [])
        
        jimeng_cookies = [c for c in cookies if 'jimeng' in c.get('domain', '') or 'jianying' in c.get('domain', '')]
        print(f"All jimeng/jianying cookies ({len(jimeng_cookies)}):")
        for c in jimeng_cookies:
            val_preview = c['value'][:30] + '...' if len(c['value']) > 30 else c['value']
            print(f"  {c['domain']:30s} {c['name']:25s} httpOnly={c.get('httpOnly',False)} secure={c.get('secure',False)} value={val_preview}")
        
        print(f"\nLooking for any cookie with 'session' in name:")
        for c in cookies:
            if 'session' in c['name'].lower():
                print(f"  {c['domain']} -> {c['name']} = {c['value'][:50]}")

asyncio.run(get_cookies())
