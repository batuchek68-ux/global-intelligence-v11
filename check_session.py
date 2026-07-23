import json
import asyncio
import urllib.request
import websockets

async def check():
    data = urllib.request.urlopen('http://127.0.0.1:9222/json').read()
    tabs = json.loads(data)
    ws_url = tabs[0]['webSocketDebuggerUrl']
    
    async with websockets.connect(ws_url, max_size=10*1024*1024) as ws:
        await ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate", "params": {"expression": "window.location.href"}}))
        result = json.loads(await ws.recv())
        print(f"Current URL: {result.get('result',{}).get('result',{}).get('value','unknown')}")
        
        await ws.send(json.dumps({"id": 2, "method": "Runtime.evaluate", "params": {"expression": "document.cookie"}}))
        result = json.loads(await ws.recv())
        cookie_str = result.get('result',{}).get('result',{}).get('value','')
        
        if 'sessionid' in cookie_str:
            for part in cookie_str.split(';'):
                part = part.strip()
                if part.startswith('sessionid='):
                    sid = part.split('=', 1)[1]
                    print(f"SESSION_ID={sid}")
                    return
        else:
            print("sessionid not in document.cookie (httpOnly)")
            for part in cookie_str.split(';'):
                part = part.strip()
                if 'session' in part.lower() or 'passport' in part.lower():
                    print(f"  Found: {part[:80]}")

asyncio.run(check())
