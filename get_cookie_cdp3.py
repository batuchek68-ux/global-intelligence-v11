import json
import asyncio
import urllib.request

async def get_cookies():
    data = urllib.request.urlopen('http://127.0.0.1:9222/json').read()
    tabs = json.loads(data)
    
    import websockets
    ws_url = tabs[0]['webSocketDebuggerUrl']
    
    async with websockets.connect(ws_url, max_size=10*1024*1024) as ws:
        await ws.send(json.dumps({"id": 1, "method": "Network.enable"}))
        await ws.recv()
        
        await ws.send(json.dumps({"id": 2, "method": "Network.getAllCookies"}))
        result = json.loads(await ws.recv())
        cookies = result.get('result', {}).get('cookies', [])
        
        print(f"Total cookies: {len(cookies)}")
        for c in cookies:
            print(f"  {c['domain']} -> {c['name']} (httpOnly={c.get('httpOnly',False)})")
        
        for cookie in cookies:
            if cookie['name'] == 'sessionid':
                print(f"\nSESSION_ID={cookie['value']}")
                return
        
        print("\nNo sessionid found in any domain")

asyncio.run(get_cookies())
