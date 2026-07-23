import json
import asyncio
import urllib.request
import websockets

async def navigate():
    data = urllib.request.urlopen('http://127.0.0.1:9222/json').read()
    tabs = json.loads(data)
    ws_url = tabs[0]['webSocketDebuggerUrl']
    
    async with websockets.connect(ws_url, max_size=10*1024*1024) as ws:
        await ws.send(json.dumps({"id": 1, "method": "Page.navigate", "params": {"url": "https://jimeng.jianying.com/"}}))
        resp = json.loads(await ws.recv())
        print(f"Navigated: {resp}")

asyncio.run(navigate())
print("请在Chrome中登录即梦账号，登录完成后告诉我")
