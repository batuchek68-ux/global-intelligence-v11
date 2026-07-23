import json
import asyncio
import urllib.request
import websockets

async def check():
    data = urllib.request.urlopen('http://127.0.0.1:9222/json').read()
    tabs = json.loads(data)
    ws_url = tabs[0]['webSocketDebuggerUrl']
    
    async with websockets.connect(ws_url, max_size=10*1024*1024) as ws:
        await ws.send(json.dumps({"id": 1, "method": "Page.navigate", "params": {"url": "https://jimeng.jianying.com/ai-tool/home"}}))
        await ws.recv()
        
        await asyncio.sleep(10)
        
        await ws.send(json.dumps({"id": 2, "method": "Network.getAllCookies"}))
        result = json.loads(await ws.recv())
        cookies = result.get('result', {}).get('cookies', [])
        
        for c in cookies:
            if c['name'] == 'sessionid':
                print(f"SESSION_ID={c['value']}")
                return
        
        jimeng = [c for c in cookies if 'jimeng' in c.get('domain','')]
        print(f"No sessionid. jimeng cookies: {len(jimeng)}")
        for c in jimeng:
            print(f"  {c['name']}")
        
        await ws.send(json.dumps({"id": 3, "method": "Runtime.evaluate", "params": {"expression": "document.querySelector('[class*=avatar]') ? 'logged in' : 'not logged in'"}}))
        r = json.loads(await ws.recv())
        print(f"Login status: {r.get('result',{}).get('result',{}).get('value','unknown')}")

asyncio.run(check())
