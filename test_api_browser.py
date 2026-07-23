import json
import asyncio
import urllib.request
import websockets

async def test_api():
    data = urllib.request.urlopen('http://127.0.0.1:9222/json').read()
    tabs = json.loads(data)
    ws_url = tabs[0]['webSocketDebuggerUrl']
    
    async with websockets.connect(ws_url, max_size=10*1024*1024) as ws:
        js = """
        fetch('/mweb/v1/get_user_info', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({}),
            credentials: 'include'
        }).then(r => r.text())
        """
        await ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate", "params": {"expression": js, "awaitPromise": True}}))
        r = json.loads(await ws.recv())
        print(f"get_user_info: {r.get('result',{}).get('result',{}).get('value','')[:500]}")
        
        js2 = """
        fetch('/mweb/v1/get_user_credits', {
            method: 'GET',
            credentials: 'include'
        }).then(r => r.text())
        """
        await ws.send(json.dumps({"id": 2, "method": "Runtime.evaluate", "params": {"expression": js2, "awaitPromise": True}}))
        r = json.loads(await ws.recv())
        print(f"get_user_credits: {r.get('result',{}).get('result',{}).get('value','')[:500]}")

asyncio.run(test_api())
