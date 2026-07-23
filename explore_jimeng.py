import json
import asyncio
import urllib.request
import websockets

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
        print("No jimeng tab found. Tabs:")
        for t in tabs:
            print(f"  {t.get('url', '')[:80]}")
        return
    
    ws_url = jimeng_tab['webSocketDebuggerUrl']
    print(f"Using tab: {jimeng_tab['url'][:80]}")
    
    async with websockets.connect(ws_url, max_size=10*1024*1024) as ws:
        msg_id = 0
        
        async def evaluate(expr):
            nonlocal msg_id
            msg_id += 1
            await ws.send(json.dumps({"id": msg_id, "method": "Runtime.evaluate", "params": {
                "expression": expr, 
                "awaitPromise": True, 
                "returnByValue": True
            }}))
            while True:
                msg = json.loads(await ws.recv())
                if msg.get('id') == msg_id:
                    result = msg.get('result', {}).get('result', {})
                    if result.get('type') == 'string':
                        return result.get('value', '')
                    return json.dumps(result)
        
        await ws.send(json.dumps({"id": 0, "method": "Page.enable"}))
        await ws.recv()
        await ws.send(json.dumps({"id": 0, "method": "Network.enable"}))
        await ws.recv()
        
        js_check = """
        (function() {
            var url = window.location.href;
            var title = document.title;
            var bodyLen = document.body ? document.body.innerText.length : 0;
            return JSON.stringify({url: url, title: title, bodyLen: bodyLen});
        })()
        """
        page_info = json.loads(await evaluate(js_check))
        print(f"Page: {page_info['title'][:50]} (body: {page_info['bodyLen']} chars)")
        
        if 'jimeng' not in page_info['url']:
            print("Not on jimeng page!")
            return
        
        js = """
        (function() {
            var textareas = document.querySelectorAll('textarea');
            var inputs = document.querySelectorAll('[contenteditable="true"]');
            var result = {
                textareas: [],
                contentEditables: [],
                allClasses: []
            };
            
            textareas.forEach((t, i) => {
                result.textareas.push({
                    index: i,
                    placeholder: (t.placeholder || '').substring(0, 50),
                    className: (t.className || '').substring(0, 80),
                    value: (t.value || '').substring(0, 30),
                    id: t.id || '',
                    name: t.name || ''
                });
            });
            
            inputs.forEach((t, i) => {
                result.contentEditables.push({
                    index: i,
                    tag: t.tagName,
                    className: (t.className || '').substring(0, 80),
                    text: (t.textContent || '').substring(0, 30)
                });
            });
            
            var allText = document.body.innerText;
            var videoMatches = [];
            var keywords = ['视频', 'video', 'Seedance', 'seedance', '首帧', '尾帧', '文生视频', '图生视频', '生成'];
            keywords.forEach(kw => {
                var idx = allText.indexOf(kw);
                if (idx >= 0) {
                    videoMatches.push(kw + '->' + allText.substring(Math.max(0, idx-10), idx+30).replace(/\\n/g, ' '));
                }
            });
            result.videoKeywords = videoMatches.slice(0, 15);
            
            return JSON.stringify(result);
        })()
        """
        page_data = json.loads(await evaluate(js))
        
        print(f"\nTextareas: {len(page_data['textareas'])}")
        for t in page_data['textareas']:
            print(f"  [{t['index']}] placeholder='{t['placeholder']}' class='{t['className'][:50]}' id='{t['id']}'")
        
        print(f"\nContent Editables: {len(page_data['contentEditables'])}")
        for t in page_data['contentEditables']:
            print(f"  [{t['index']}] {t['tag']} class='{t['className'][:50]}'")
        
        print(f"\nVideo keywords found:")
        for k in page_data['videoKeywords']:
            print(f"  {k}")

asyncio.run(main())
