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
        
        # Install fetch interceptor
        await evaluate("""
        (function() {
            window._cap = [];
            var of = window.fetch;
            window.fetch = function() {
                var u = typeof arguments[0] === 'string' ? arguments[0] : '';
                var o = arguments[1] || {};
                if (u.includes('mweb')) {
                    window._cap.push({url: u, method: o.method||'GET', body: o.body||null});
                }
                return of.apply(this, arguments);
            };
            return 'ok';
        })()
        """)
        
        # Click "生成" nav item
        print("Clicking 生成 nav...")
        result = await evaluate("""
        (function() {
            var spans = document.querySelectorAll('span, div, a');
            for (var s of spans) {
                if ((s.textContent||'').trim() === '生成' && s.offsetParent !== null) {
                    var clickable = s.closest('a, [role="tab"], [role="button"], button') || s.parentElement;
                    clickable.click();
                    return 'clicked: ' + clickable.tagName + ' ' + (clickable.className||'').substring(0,60);
                }
            }
            return 'not found';
        })()
        """)
        print(f"Click result: {result}")
        
        await asyncio.sleep(3)
        
        # Now look at what appeared
        body = await evaluate("document.body.innerText.substring(0, 2000)")
        print(f"\nBody after click:\n{body[:1200]}")
        
        # Find the video generation option
        result2 = await evaluate("""
        (function() {
            var all = document.querySelectorAll('*');
            var found = [];
            for (var el of all) {
                var t = (el.textContent||'').trim();
                if (t.includes('视频生成') || t.includes('文生视频') || t.includes('Seedance') || t.includes('一镜到底')) {
                    if (el.children.length < 3 && t.length < 50) {
                        found.push({tag: el.tagName, text: t.substring(0,40), class: (el.className||'').substring(0,50)});
                    }
                }
            }
            return JSON.stringify(found.slice(0, 15));
        })()
        """)
        video_options = json.loads(result2)
        print(f"\nVideo options:")
        for v in video_options:
            print(f"  {v}")
        
        # Check for tabs/options
        tabs_result = await evaluate("""
        (function() {
            var all = document.querySelectorAll('[role="tab"], [class*="tab"], [class*="option"], [class*="select"]');
            var items = [];
            all.forEach((el, i) => {
                var t = (el.textContent||'').trim();
                if (t.length > 0 && t.length < 30) {
                    items.push(i + ': ' + el.tagName + ' text=' + t + ' class=' + (el.className||'').substring(0,40));
                }
            });
            return items.slice(0, 20).join('\\n');
        })()
        """)
        print(f"\nTabs/Options:\n{tabs_result}")

asyncio.run(main())
