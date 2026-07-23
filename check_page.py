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
        r = json.loads(await ws.recv())
        print(f"URL: {r.get('result',{}).get('result',{}).get('value','?')}")
        
        await ws.send(json.dumps({"id": 2, "method": "Runtime.evaluate", "params": {"expression": "document.title"}}))
        r = json.loads(await ws.recv())
        print(f"Title: {r.get('result',{}).get('result',{}).get('value','?')}")
        
        await ws.send(json.dumps({"id": 3, "method": "Runtime.evaluate", "params": {"expression": "document.body.innerText.substring(0, 500)"}}))
        r = json.loads(await ws.recv())
        text = r.get('result',{}).get('result',{}).get('value','')
        print(f"Page text (first 500): {text[:500]}")

asyncio.run(check())
