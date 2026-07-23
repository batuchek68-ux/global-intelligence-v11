import json
import asyncio
import urllib.request
import websockets
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

async def test_api():
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
        
        js = """
        (async function() {
            try {
                var resp = await fetch('/mweb/v1/get_user_info', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include'
                });
                var text = await resp.text();
                return text.substring(0, 500);
            } catch(e) {
                return 'Error: ' + e.message;
            }
        })()
        """
        print("Testing user info...")
        result = await evaluate(js)
        print(result[:500])
        
        js2 = """
        (async function() {
            try {
                var resp = await fetch('/mweb/v1/get_credit_balance', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include'
                });
                var text = await resp.text();
                return text.substring(0, 500);
            } catch(e) {
                return 'Error: ' + e.message;
            }
        })()
        """
        print("\nTesting credit balance...")
        result2 = await evaluate(js2)
        print(result2[:500])

asyncio.run(test_api())
