import json
import asyncio
import urllib.request
import websockets
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

async def get_session():
    data = urllib.request.urlopen('http://127.0.0.1:9222/json').read()
    tabs = json.loads(data)
    
    jimeng_tab = None
    for tab in tabs:
        url = tab.get('url', '')
        if 'jimeng.jianying.com' in url and 'helpdesk' not in url:
            jimeng_tab = tab
            break
    
    if not jimeng_tab:
        print("No jimeng tab found. Tabs:")
        for t in tabs:
            print(f"  {t.get('url', '')[:80]}")
        return
    
    ws_url = jimeng_tab['webSocketDebuggerUrl']
    
    async with websockets.connect(ws_url, max_size=10*1024*1024) as ws:
        msg_id = 0
        async def evaluate(expr):
            nonlocal msg_id
            msg_id += 1
            await ws.send(json.dumps({"id": msg_id, "method": "Runtime.evaluate", "params": {
                "expression": expr, "awaitPromise": True, "returnByValue": True
            }}))
            while True:
                msg = json.loads(await ws.recv())
                if msg.get('id') == msg_id:
                    result = msg.get('result', {}).get('result', {})
                    return result.get('value', '')
        
        # Get cookies
        await ws.send(json.dumps({"id": 0, "method": "Network.enable"}))
        await ws.recv()
        
        await ws.send(json.dumps({"id": 1, "method": "Network.getCookies", "params": {"urls": ["https://jimeng.jianying.com"]}}))
        r = json.loads(await ws.recv())
        cookies = r.get('result', {}).get('cookies', [])
        
        for c in cookies:
            if c.get('name') == 'sessionid':
                print(f"SessionID: {c.get('value')}")
                print(f"Domain: {c.get('domain')}")
                print(f"HttpOnly: {c.get('httpOnly')}")
                print(f"Expires: {c.get('expires')}")
                return
        
        print("No sessionid cookie found!")
        print("Available cookies:")
        for c in cookies[:10]:
            print(f"  {c.get('name')}: {c.get('value', '')[:30]}...")

asyncio.run(get_session())
