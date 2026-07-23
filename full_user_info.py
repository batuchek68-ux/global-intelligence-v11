import json
import asyncio
import urllib.request
import websockets
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

async def check():
    data = urllib.request.urlopen('http://127.0.0.1:9222/json').read()
    tabs = json.loads(data)
    
    jimeng_tab = None
    for tab in tabs:
        url = tab.get('url', '')
        if 'jimeng.jianying.com' in url and 'helpdesk' not in url:
            jimeng_tab = tab
            break
    
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
        
        js = """
        (async function() {
            var resp = await fetch('/mweb/v1/get_user_info', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include'
            });
            var data = await resp.json();
            return JSON.stringify(data.data);
        })()
        """
        result = await evaluate(js)
        info = json.loads(result)
        print(json.dumps(info, indent=2, ensure_ascii=False))

asyncio.run(check())
