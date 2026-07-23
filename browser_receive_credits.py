import json
import asyncio
import urllib.request
import websockets
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

async def receive():
    data = urllib.request.urlopen('http://127.0.0.1:9222/json').read()
    tabs = json.loads(data)
    
    jimeng_tab = None
    for tab in tabs:
        url = tab.get('url', '')
        if 'jimeng.jianying.com' in url and 'helpdesk' not in url:
            jimeng_tab = tab
            break
    
    if not jimeng_tab:
        print("No jimeng tab found")
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
        
        # Receive daily credits
        js = """
        (async function() {
            try {
                var resp = await fetch('/commerce/v1/benefits/credit_receive', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Referer': 'https://jimeng.jianying.com/ai-tool/image/generate'
                    },
                    credentials: 'include',
                    body: JSON.stringify({time_zone: 'Asia/Shanghai'})
                });
                var text = await resp.text();
                return text;
            } catch(e) {
                return 'Error: ' + e.message;
            }
        })()
        """
        result = await evaluate(js)
        print(f"Credit receive: {result}")
        
        # Check credit balance
        js2 = """
        (async function() {
            try {
                var resp = await fetch('/commerce/v1/benefits/user_credit', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Referer': 'https://jimeng.jianying.com/ai-tool/image/generate'
                    },
                    credentials: 'include',
                    body: JSON.stringify({})
                });
                var text = await resp.text();
                return text;
            } catch(e) {
                return 'Error: ' + e.message;
            }
        })()
        """
        result2 = await evaluate(js2)
        print(f"Credit balance: {result2}")

asyncio.run(receive())
