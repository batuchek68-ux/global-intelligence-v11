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
        captured = []
        
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
        
        js_intercept = """
        (function() {
            window._capturedBodies = [];
            var origFetch = window.fetch;
            window.fetch = function() {
                var url = typeof arguments[0] === 'string' ? arguments[0] : (arguments[0] ? arguments[0].url : '');
                var opts = arguments[1] || {};
                if (url.includes('generate') || url.includes('aigc')) {
                    window._capturedBodies.push({
                        url: url,
                        method: opts.method || 'GET',
                        body: opts.body || null,
                        headers: opts.headers ? JSON.stringify(opts.headers) : null,
                        time: Date.now()
                    });
                }
                return origFetch.apply(this, arguments);
            };
            
            var origSend = XMLHttpRequest.prototype.send;
            var origOpen = XMLHttpRequest.prototype.open;
            XMLHttpRequest.prototype.open = function(m, u) {
                this._m = m; this._u = u;
                return origOpen.apply(this, arguments);
            };
            XMLHttpRequest.prototype.send = function(body) {
                if (this._u && (this._u.includes('generate') || this._u.includes('aigc'))) {
                    window._capturedBodies.push({
                        url: this._u, method: this._m, body: body,
                        time: Date.now()
                    });
                }
                return origSend.apply(this, arguments);
            };
            return 'ok';
        })()
        """
        print("Installing interceptor:", await evaluate(js_intercept))
        
        print("Typing prompt...")
        js_type = f"""
        (async function() {{
            var editor = document.querySelector('.tiptap.ProseMirror');
            if (!editor) return 'no editor found';
            
            editor.focus();
            
            editor.innerHTML = '<p>{PROMPT}</p>';
            editor.dispatchEvent(new Event('input', {{ bubbles: true }}));
            
            await new Promise(r => setTimeout(r, 500));
            
            return 'typed: ' + editor.textContent.substring(0, 50);
        }})()
        """
        print("Type result:", await evaluate(js_type))
        
        await asyncio.sleep(1)
        
        print("Looking for generate button...")
        js_gen = """
        (function() {
            var allEls = document.querySelectorAll('*');
            for (var el of allEls) {
                var text = (el.textContent || '').trim();
                if (text === '生成' && el.tagName === 'DIV' && el.children.length === 0) {
                    var btn = el.closest('[class*="button"], [class*="btn"], button') || el.parentElement;
                    btn.click();
                    return 'clicked parent: ' + btn.tagName + ' class=' + (btn.className || '').substring(0, 60);
                }
            }
            return 'generate button not found';
        })()
        """
        gen_result = await evaluate(js_gen)
        print(f"Generate click: {gen_result}")
        
        print("Waiting for network request (30s)...")
        for i in range(30):
            await asyncio.sleep(1)
            captured = json.loads(await evaluate("JSON.stringify(window._capturedBodies || [])"))
            if captured:
                print(f"\n=== CAPTURED {len(captured)} REQUEST(S) ===")
                for req in captured:
                    print(f"\nURL: {req.get('url', '')[:120]}")
                    print(f"Method: {req.get('method', '')}")
                    body = req.get('body', '')
                    if body:
                        try:
                            parsed = json.loads(body)
                            print(f"Body: {json.dumps(parsed, indent=2, ensure_ascii=False)[:2000]}")
                        except:
                            print(f"Body (raw): {body[:2000]}")
                break
            if i % 5 == 0:
                print(f"  waiting... {i}s")
        
        if not captured:
            print("\nNo requests captured. Checking current page state...")
            js_state = """
            (function() {
                var url = window.location.href;
                var modals = document.querySelectorAll('[class*="modal"], [class*="dialog"], [class*="popup"]');
                var modalTexts = [];
                modals.forEach(m => {
                    var text = (m.innerText || '').trim();
                    if (text) modalTexts.push(text.substring(0, 100));
                });
                return JSON.stringify({url: url, modals: modalTexts});
            })()
            """
            state = json.loads(await evaluate(js_state))
            print(f"URL: {state['url'][:80]}")
            print(f"Modals: {state['modals']}")

asyncio.run(main())
