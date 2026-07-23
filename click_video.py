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
                    if result.get('type') == 'string':
                        return result.get('value', '')
                    elif result.get('type') == 'object':
                        return result.get('value', json.dumps(result))
                    return json.dumps(result)
        
        await ws.send(json.dumps({"id": 0, "method": "Network.enable"}))
        await ws.recv()
        
        captured_requests = []
        
        js_intercept = """
        (function() {
            if (window._interceptInstalled) return 'already installed';
            window._interceptInstalled = true;
            window._capturedRequests = [];
            
            var origFetch = window.fetch;
            window.fetch = function() {
                var url = arguments[0];
                if (typeof url === 'string' && url.includes('aigc_draft')) {
                    var options = arguments[1] || {};
                    window._capturedRequests.push({
                        url: url,
                        method: options.method || 'GET',
                        body: options.body || null,
                        time: Date.now()
                    });
                }
                return origFetch.apply(this, arguments);
            };
            
            var origXHR = XMLHttpRequest.prototype.open;
            var origXHRSend = XMLHttpRequest.prototype.send;
            XMLHttpRequest.prototype.open = function(method, url) {
                this._url = url;
                this._method = method;
                return origXHR.apply(this, arguments);
            };
            XMLHttpRequest.prototype.send = function(body) {
                if (this._url && this._url.includes('aigc_draft')) {
                    window._capturedRequests.push({
                        url: this._url,
                        method: this._method,
                        body: body,
                        time: Date.now()
                    });
                }
                return origXHRSend.apply(this, arguments);
            };
            
            return 'intercept installed';
        })()
        """
        print(await evaluate(js_intercept))
        
        js = """
        (function() {
            var body = document.body.innerText;
            var allSpans = document.querySelectorAll('span, div, p');
            var videoRelated = [];
            for (var el of allSpans) {
                var text = (el.textContent || '').trim();
                if (text === '视频生成' || text === '文生视频' || text === '视频生') {
                    videoRelated.push({
                        tag: el.tagName,
                        text: text,
                        clickable: el.closest('button, a, [role="tab"], [role="menuitem"]') !== null,
                        className: (el.className || '').substring(0, 60)
                    });
                }
            }
            
            var allBtns = [];
            document.querySelectorAll('button, [role="tab"], [role="menuitem"]').forEach((b, i) => {
                var text = (b.innerText || b.textContent || '').trim();
                if (text.includes('视频') || text.includes('生成') || text.includes('创作') || text.includes('video')) {
                    allBtns.push(i + ': ' + text.substring(0, 30) + ' tag=' + b.tagName);
                }
            });
            
            return JSON.stringify({videoElements: videoRelated, buttons: allBtns});
        })()
        """
        result = json.loads(await evaluate(js))
        
        print("Video-related elements:")
        for v in result['videoElements']:
            print(f"  {v}")
        
        print("\nRelevant buttons:")
        for b in result['buttons']:
            print(f"  {b}")
        
        js_click_video = """
        (function() {
            var allElements = document.querySelectorAll('*');
            for (var el of allElements) {
                var text = (el.textContent || '').trim();
                if (text === '视频生成' && (el.tagName === 'SPAN' || el.tagName === 'DIV' || el.tagName === 'A')) {
                    var clickTarget = el.closest('button, a, [role="tab"], [class*="menu"], [class*="nav"], [class*="tab"]') || el;
                    clickTarget.click();
                    return 'clicked: ' + clickTarget.tagName + ' text=' + (clickTarget.textContent || '').trim().substring(0, 30);
                }
            }
            return 'not found';
        })()
        """
        click_result = await evaluate(js_click_video)
        print(f"\nClick result: {click_result}")
        
        await asyncio.sleep(3)
        
        js_after = """
        (function() {
            var url = window.location.href;
            var bodyText = document.body.innerText.substring(0, 800);
            var textareas = [];
            document.querySelectorAll('textarea, [contenteditable="true"]').forEach((el, i) => {
                textareas.push({
                    index: i,
                    tag: el.tagName,
                    placeholder: (el.placeholder || el.getAttribute('data-placeholder') || '').substring(0, 50),
                    text: (el.textContent || el.value || '').substring(0, 30),
                    class: (el.className || '').substring(0, 50)
                });
            });
            return JSON.stringify({url: url, bodySnippet: bodyText.substring(0, 500), textareas: textareas});
        })()
        """
        after = json.loads(await evaluate(js_after))
        print(f"\nURL after click: {after['url'][:80]}")
        print(f"\nTextareas after: {json.dumps(after['textareas'], indent=2, ensure_ascii=False)}")

asyncio.run(main())
