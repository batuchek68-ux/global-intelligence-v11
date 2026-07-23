import json
import asyncio
import urllib.request
import websockets

async def open_new_tab():
    data = urllib.request.urlopen('http://127.0.0.1:9222/json').read()
    tabs = json.loads(data)
    
    target_ws = None
    for tab in tabs:
        if 'jimeng' in tab.get('url', ''):
            target_ws = tab['webSocketDebuggerUrl']
            print(f"Found jimeng tab: {tab['url']}")
            break
    
    if not target_ws:
        urllib.request.urlopen('http://127.0.0.1:9222/json/new?https://jimeng.jianying.com/ai-tool/home')
        data = urllib.request.urlopen('http://127.0.0.1:9222/json').read()
        tabs = json.loads(data)
        for tab in tabs:
            if 'jimeng' in tab.get('url', ''):
                target_ws = tab['webSocketDebuggerUrl']
                print(f"Opened jimeng tab: {tab['url']}")
                break
    
    if not target_ws:
        print("Cannot find jimeng tab")
        return
    
    await asyncio.sleep(8)
    
    async with websockets.connect(target_ws, max_size=10*1024*1024) as ws:
        msg_id = 0
        async def evaluate(expr):
            nonlocal msg_id
            msg_id += 1
            await ws.send(json.dumps({"id": msg_id, "method": "Runtime.evaluate", "params": {"expression": expr, "awaitPromise": True, "returnByValue": True}}))
            while True:
                msg = json.loads(await ws.recv())
                if msg.get('id') == msg_id:
                    return msg.get('result', {}).get('result', {}).get('value', '')
        
        url = await evaluate("window.location.href")
        print(f"Current URL: {url}")
        
        title = await evaluate("document.title")
        print(f"Title: {title}")

asyncio.run(open_new_tab())
