import json
import asyncio
import urllib.request
import websockets
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PROMPT = "成吉思汗骑马驰骋在辽阔草原上，阳光洒落，自然光线，一镜到底，无大幅移动，镜头跟随平稳"

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
        
        await ws.send(json.dumps({"id": 0, "method": "Network.enable"}))
        await ws.recv()
        
        # Install network interceptor
        await evaluate("""
        (function() {
            window._cap = [];
            var of = window.fetch;
            window.fetch = function() {
                var u = typeof arguments[0] === 'string' ? arguments[0] : '';
                var o = arguments[1] || {};
                if (u.includes('mweb') || u.includes('aigc') || u.includes('generate')) {
                    window._cap.push({url: u, method: o.method||'GET', body: o.body||null, time: Date.now()});
                }
                return of.apply(this, arguments);
            };
            var os = XMLHttpRequest.prototype.send;
            var oo = XMLHttpRequest.prototype.open;
            XMLHttpRequest.prototype.open = function(m,u) { this._m=m; this._u=u; return oo.apply(this,arguments); };
            XMLHttpRequest.prototype.send = function(b) {
                if (this._u && (this._u.includes('mweb') || this._u.includes('aigc') || this._u.includes('generate'))) {
                    window._cap.push({url:this._u, method:this._m, body:b, time:Date.now()});
                }
                return os.apply(this,arguments);
            };
            return 'ok';
        })()
        """)
        
        # Click on "视频生成" option
        print("Clicking 视频生成...")
        result = await evaluate("""
        (function() {
            var all = document.querySelectorAll('.home-type-select-option-yv5WfC');
            for (var el of all) {
                if ((el.textContent||'').trim() === '视频生成') {
                    el.click();
                    return 'clicked option';
                }
            }
            return 'not found';
        })()
        """)
        print(f"Click: {result}")
        
        await asyncio.sleep(3)
        
        # Check what page shows now
        body = await evaluate("document.body.innerText.substring(0, 2000)")
        print(f"\nBody:\n{body[:1000]}")
        
        # Find all input areas
        inputs = await evaluate("""
        (function() {
            var result = [];
            document.querySelectorAll('textarea, [contenteditable="true"], input[type="text"]').forEach((el, i) => {
                var rect = el.getBoundingClientRect();
                result.push({
                    index: i, tag: el.tagName,
                    placeholder: (el.placeholder || el.getAttribute('data-placeholder') || '').substring(0, 50),
                    text: (el.textContent || el.value || '').substring(0, 30),
                    visible: rect.width > 0 && rect.height > 0,
                    rect: {w: Math.round(rect.width), h: Math.round(rect.height), x: Math.round(rect.x), y: Math.round(rect.y)}
                });
            });
            return JSON.stringify(result);
        })()
        """)
        print(f"\nInputs: {inputs}")

asyncio.run(main())
