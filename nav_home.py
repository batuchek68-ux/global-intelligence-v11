import json
import asyncio
import urllib.request
import websockets
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

async def main():
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
        
        await ws.send(json.dumps({"id": 0, "method": "Page.enable"}))
        await ws.recv()
        
        # Navigate back to home
        await ws.send(json.dumps({"id": 1, "method": "Page.navigate", "params": {
            "url": "https://jimeng.jianying.com/ai-tool/home"
        }}))
        await ws.recv()
        
        await asyncio.sleep(8)
        
        url = await evaluate("window.location.href")
        print(f"URL: {url}")
        
        js = """
        (function() {
            var body = document.body.innerText || '';
            return body.substring(0, 2000);
        })()
        """
        body = await evaluate(js)
        print(f"Body:\n{body[:1000]}")

asyncio.run(main())
