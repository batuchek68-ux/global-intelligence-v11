import json
import asyncio
import urllib.request
import websockets

async def check():
    data = urllib.request.urlopen('http://127.0.0.1:9222/json').read()
    tabs = json.loads(data)
    ws_url = tabs[0]['webSocketDebuggerUrl']
    
    async with websockets.connect(ws_url, max_size=10*1024*1024) as ws:
        js = """
        (function() {
            var body = document.body.innerText;
            var hasLogin = body.includes('登录') || body.includes('login');
            var hasAvatar = !!document.querySelector('img[src*="avatar"]') || !!document.querySelector('[class*="avatar"]') || !!document.querySelector('[class*="user"]');
            var hasCreate = body.includes('立即创作') || body.includes('开始创作');
            var headerText = '';
            var header = document.querySelector('header') || document.querySelector('nav') || document.querySelector('[class*="header"]');
            if (header) headerText = header.innerText.substring(0, 200);
            return JSON.stringify({hasLogin: hasLogin, hasAvatar: hasAvatar, hasCreate: hasCreate, headerText: headerText, bodySnippet: body.substring(0, 300)});
        })()
        """
        await ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate", "params": {"expression": js}}))
        r = json.loads(await ws.recv())
        val = r.get('result',{}).get('result',{}).get('value','')
        d = json.loads(val)
        print(f"Has login button: {d['hasLogin']}")
        print(f"Has avatar: {d['hasAvatar']}")
        print(f"Has create button: {d['hasCreate']}")
        print(f"Header: {d['headerText']}")
        print(f"Body: {d['bodySnippet']}")

asyncio.run(check())
