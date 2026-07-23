import json
import asyncio
import urllib.request
import websockets

async def inspect_and_generate():
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
            var result = {};
            
            var allElements = document.querySelectorAll('*');
            var textAreas = [];
            var videoRelated = [];
            for (var el of allElements) {
                var text = (el.innerText || el.textContent || '').trim();
                if (el.tagName === 'TEXTAREA' || (el.contentEditable === 'true')) {
                    textAreas.push(el.tagName + ':' + (el.placeholder || '').substring(0,50) + ':class=' + (el.className || '').substring(0,50));
                }
                if (text && (text.includes('视频') || text.includes('video') || text.includes('Seedance') || text.includes('首帧') || text.includes('尾帧'))) {
                    if (el.children.length === 0 || el.tagName === 'SPAN' || el.tagName === 'DIV') {
                        videoRelated.push(el.tagName + ':' + text.substring(0, 60) + ':class=' + (el.className || '').substring(0, 40));
                    }
                }
            }
            
            result.textAreas = textAreas.slice(0, 10);
            result.videoElements = videoRelated.slice(0, 20);
            result.bodyText = document.body.innerText.substring(0, 500);
            
            return JSON.stringify(result);
        })()
        """
        result = await evaluate(js)
        data = json.loads(result)
        print("TextAreas:", data['textAreas'])
        print("\nVideo-related elements:")
        for v in data['videoElements']:
            print(f"  {v}")
        print(f"\nBody text: {data['bodyText'][:300]}")

asyncio.run(inspect_and_generate())
