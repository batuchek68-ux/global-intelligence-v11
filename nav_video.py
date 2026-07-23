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
        await ws.send(json.dumps({"id": 0, "method": "Network.enable"}))
        await ws.recv()
        
        print("Navigating to video generation page...")
        await ws.send(json.dumps({"id": 1, "method": "Page.navigate", "params": {
            "url": "https://jimeng.jianying.com/ai-tool/video-gen"
        }}))
        r = json.loads(await ws.recv())
        
        await asyncio.sleep(8)
        
        url = await evaluate("window.location.href")
        print(f"URL: {url}")
        
        js = """
        (function() {
            var body = document.body.innerText.substring(0, 1500);
            var textareas = [];
            document.querySelectorAll('textarea, [contenteditable="true"]').forEach((el, i) => {
                textareas.push({
                    index: i, tag: el.tagName,
                    placeholder: (el.placeholder || el.getAttribute('data-placeholder') || '').substring(0, 50),
                    text: (el.textContent || el.value || '').substring(0, 50),
                    class: (el.className || '').substring(0, 60)
                });
            });
            var buttons = [];
            document.querySelectorAll('button, [role="button"]').forEach((b, i) => {
                var text = (b.innerText || b.textContent || '').trim();
                if (text.length < 40 && text.length > 0) {
                    buttons.push(i + ': ' + text.substring(0, 30));
                }
            });
            return JSON.stringify({bodyLen: body.length, bodySnippet: body.substring(0, 800), textareas: textareas, buttons: buttons.slice(0, 30)});
        })()
        """
        page = json.loads(await evaluate(js))
        print(f"Body length: {page['bodyLen']}")
        print(f"\nBody snippet:\n{page['bodySnippet'][:600]}")
        print(f"\nTextareas: {json.dumps(page['textareas'], indent=2, ensure_ascii=False)}")
        print(f"\nButtons: {page['buttons']}")

asyncio.run(main())
