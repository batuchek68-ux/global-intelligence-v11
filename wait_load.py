import json
import asyncio
import urllib.request
import websockets

async def wait_and_check():
    data = urllib.request.urlopen('http://127.0.0.1:9222/json').read()
    tabs = json.loads(data)
    ws_url = tabs[0]['webSocketDebuggerUrl']
    
    async with websockets.connect(ws_url, max_size=10*1024*1024) as ws:
        msg_id = 0
        async def evaluate(expr):
            nonlocal msg_id
            msg_id += 1
            await ws.send(json.dumps({"id": msg_id, "method": "Runtime.evaluate", "params": {"expression": expr, "awaitPromise": True, "returnByValue": True}}))
            while True:
                msg = json.loads(await ws.recv())
                if msg.get('id') == msg_id:
                    return msg.get('result', {}).get('result', {}).get('value', '')
        
        print("等待页面加载...")
        await asyncio.sleep(5)
        
        url = await evaluate("window.location.href")
        print(f"URL: {url}")
        
        title = await evaluate("document.title")
        print(f"Title: {title}")
        
        js = """
        (function() {
            var body = document.body;
            if (!body) return 'no body';
            var text = body.innerText || '';
            return text.substring(0, 1000);
        })()
        """
        body_text = await evaluate(js)
        print(f"Body text length: {len(body_text)}")
        print(f"Body text: {body_text[:500]}")

asyncio.run(wait_and_check())
