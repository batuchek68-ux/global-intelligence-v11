import json
import asyncio
import urllib.request
import websockets
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

async def check_credits():
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
            try {
                var resp = await fetch('/mweb/v1/user/get_user_credit', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include'
                });
                var text = await resp.text();
                return text;
            } catch(e) {
                return 'Error: ' + e.message;
            }
        })()
        """
        result = await evaluate(js)
        print(f"User credit: {result[:500]}")
        
        js2 = """
        (async function() {
            try {
                var resp = await fetch('/mweb/v1/get_user_info', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include'
                });
                var data = await resp.json();
                var info = data.data || {};
                return JSON.stringify({
                    name: info.name,
                    uid: info.uid,
                    total_credit: info.total_credit,
                    vip_type: info.vip_type,
                    vip_level: info.vip_level
                });
            } catch(e) {
                return 'Error: ' + e.message;
            }
        })()
        """
        result2 = await evaluate(js2)
        print(f"User info: {result2}")

asyncio.run(check_credits())
