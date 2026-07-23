import json
import asyncio
import urllib.request
import websockets

async def test():
    data = urllib.request.urlopen('http://127.0.0.1:9222/json').read()
    tabs = json.loads(data)
    ws_url = tabs[0]['webSocketDebuggerUrl']
    
    async with websockets.connect(ws_url, max_size=10*1024*1024) as ws:
        await ws.send(json.dumps({"id": 0, "method": "Page.navigate", "params": {"url": "https://jimeng.jianying.com/ai-tool/home"}}))
        await ws.recv()
        await asyncio.sleep(5)
        
        js = """
        (async function() {
            try {
                var r = await fetch('/mweb/v1/get_user_credits', {
                    method: 'GET',
                    credentials: 'include'
                });
                var t = await r.text();
                return 'credits: ' + t.substring(0, 300);
            } catch(e) {
                return 'error: ' + e.message;
            }
        })()
        """
        await ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate", "params": {"expression": js, "awaitPromise": True}}))
        r = json.loads(await ws.recv())
        print(r.get('result',{}).get('result',{}).get('value',''))
        
        js2 = """
        (async function() {
            try {
                var r = await fetch('/mweb/v1/get_new_user_guide', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({}),
                    credentials: 'include'
                });
                var t = await r.text();
                return 'guide: ' + t.substring(0, 300);
            } catch(e) {
                return 'error: ' + e.message;
            }
        })()
        """
        await ws.send(json.dumps({"id": 2, "method": "Runtime.evaluate", "params": {"expression": js2, "awaitPromise": True}}))
        r = json.loads(await ws.recv())
        print(r.get('result',{}).get('result',{}).get('value',''))
        
        js3 = """
        (async function() {
            try {
                var r = await fetch('/mweb/v1/get_credit_balance', {
                    method: 'GET',
                    credentials: 'include'
                });
                var t = await r.text();
                return 'balance: ' + t.substring(0, 300);
            } catch(e) {
                return 'error: ' + e.message;
            }
        })()
        """
        await ws.send(json.dumps({"id": 3, "method": "Runtime.evaluate", "params": {"expression": js3, "awaitPromise": True}}))
        r = json.loads(await ws.recv())
        print(r.get('result',{}).get('result',{}).get('value',''))

asyncio.run(test())
