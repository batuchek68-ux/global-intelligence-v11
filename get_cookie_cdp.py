import json
import asyncio
import websockets

async def get_cookies_from_chrome():
    import urllib.request
    data = urllib.request.urlopen('http://127.0.0.1:9222/json').read()
    tabs = json.loads(data)
    ws_url = tabs[0]['webSocketDebuggerUrl']
    
    async with websockets.connect(ws_url) as ws:
        await ws.send(json.dumps({"id": 1, "method": "Network.getAllCookies"}))
        result = json.loads(await ws.recv())
        for cookie in result.get('result', {}).get('cookies', []):
            if cookie['name'] == 'sessionid' and 'jimeng' in cookie.get('domain', ''):
                print(f"SESSION_ID={cookie['value']}")
                return
        print("ERROR: sessionid not found")

asyncio.run(get_cookies_from_chrome())
