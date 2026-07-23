import json
import asyncio
import urllib.request
import websockets

async def check():
    data = urllib.request.urlopen('http://127.0.0.1:9222/json').read()
    tabs = json.loads(data)
    ws_url = tabs[0]['webSocketDebuggerUrl']
    
    async with websockets.connect(ws_url, max_size=10*1024*1024) as ws:
        js = """
        fetch('https://jimeng.jianying.com/mweb/v1/get_user_info', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: '{}',
            credentials: 'include'
        }).then(r => r.text()).then(t => t)
        """
        await ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate", "params": {"expression": js, "awaitPromise": True}}))
        r = json.loads(await ws.recv())
        val = r.get('result',{}).get('result',{}).get('value','')
        print(f"API response: {val[:500]}")

asyncio.run(check())
