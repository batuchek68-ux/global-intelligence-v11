import json
import asyncio
import urllib.request
import websockets

async def check():
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
        
        js = """
        (function() {
            var url = window.location.href;
            var buttons = document.querySelectorAll('button');
            var btnTexts = [];
            buttons.forEach((b, i) => {
                var t = (b.innerText || b.textContent || '').trim().substring(0, 40);
                if (t) btnTexts.push(i + ':' + t);
            });
            var tabs = document.querySelectorAll('[role="tab"], [class*="tab"]');
            var tabTexts = [];
            tabs.forEach((t, i) => {
                var text = (t.innerText || t.textContent || '').trim().substring(0, 30);
                if (text) tabTexts.push(i + ':' + text);
            });
            var inputs = document.querySelectorAll('textarea, input[type="text"], [contenteditable="true"]');
            var inputInfo = [];
            inputs.forEach((inp, i) => {
                inputInfo.push(i + ':' + inp.tagName + ':' + (inp.placeholder || '').substring(0, 30) + ':val=' + (inp.value || inp.textContent || '').substring(0, 30));
            });
            return JSON.stringify({url: url, buttons: btnTexts.slice(0, 20), tabs: tabTexts.slice(0, 10), inputs: inputInfo.slice(0, 5)});
        })()
        """
        result = await evaluate(js)
        data = json.loads(result)
        print(f"URL: {data['url']}")
        print(f"\nButtons:")
        for b in data['buttons']:
            print(f"  {b}")
        print(f"\nTabs:")
        for t in data['tabs']:
            print(f"  {t}")
        print(f"\nInputs:")
        for i in data['inputs']:
            print(f"  {i}")

asyncio.run(check())
