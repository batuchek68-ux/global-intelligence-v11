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
        (function() {
            var result = {};
            result.url = window.location.href;
            result.localStorage_keys = Object.keys(localStorage);
            result.sessionStorage_keys = Object.keys(sessionStorage);
            result.cookies = document.cookie;
            
            for (var i = 0; i < localStorage.length; i++) {
                var key = localStorage.key(i);
                if (key.toLowerCase().includes('user') || key.toLowerCase().includes('token') || key.toLowerCase().includes('session') || key.toLowerCase().includes('auth') || key.toLowerCase().includes('login')) {
                    result['ls_' + key] = localStorage.getItem(key).substring(0, 200);
                }
            }
            return JSON.stringify(result);
        })()
        """
        await ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate", "params": {"expression": js}}))
        r = json.loads(await ws.recv())
        val = r.get('result',{}).get('result',{}).get('value','')
        data = json.loads(val)
        print(f"URL: {data.get('url')}")
        print(f"LocalStorage keys: {data.get('localStorage_keys')}")
        print(f"SessionStorage keys: {data.get('sessionStorage_keys')}")
        print(f"Cookies: {data.get('cookies')[:200]}")
        for k, v in data.items():
            if k.startswith('ls_'):
                print(f"  {k}: {v}")

asyncio.run(check())
