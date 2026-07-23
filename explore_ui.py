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
        
        js = """
        (function() {
            var body = document.body.innerText;
            var lines = body.split('\\n').filter(l => l.trim()).slice(0, 50);
            
            var buttons = [];
            document.querySelectorAll('button').forEach((b, i) => {
                var text = (b.innerText || b.textContent || '').trim();
                var cls = (b.className || '').substring(0, 60);
                if (text && text.length < 40) {
                    buttons.push(i + ': ' + text + ' [' + cls + ']');
                }
            });
            
            var links = [];
            document.querySelectorAll('a').forEach((a, i) => {
                var text = (a.innerText || a.textContent || '').trim();
                var href = a.href || '';
                if (text && text.length < 40 && (href.includes('video') || href.includes('ai-tool') || text.includes('视频') || text.includes('创作'))) {
                    links.push(i + ': ' + text + ' -> ' + href.substring(0, 80));
                }
            });
            
            var editables = [];
            document.querySelectorAll('[contenteditable="true"]').forEach((el, i) => {
                var parent = el.parentElement;
                var siblingText = parent ? (parent.innerText || '').substring(0, 100) : '';
                editables.push({
                    index: i,
                    text: (el.textContent || '').substring(0, 50),
                    parentText: siblingText.substring(0, 80),
                    className: (el.className || '').substring(0, 50)
                });
            });
            
            return JSON.stringify({
                bodyLines: lines.slice(0, 30),
                buttons: buttons.slice(0, 30),
                links: links.slice(0, 15),
                editables: editables
            });
        })()
        """
        result = json.loads(await evaluate(js))
        
        print("=== BODY TEXT ===")
        for line in result['bodyLines']:
            print(f"  {line[:80]}")
        
        print("\\n=== BUTTONS ===")
        for b in result['buttons']:
            print(f"  {b}")
        
        print("\\n=== LINKS ===")
        for l in result['links']:
            print(f"  {l}")
        
        print("\\n=== EDITABLES ===")
        for e in result['editables']:
            print(f"  [{e['index']}] text='{e['text']}' parent='{e['parentText'][:60]}'")

asyncio.run(main())
