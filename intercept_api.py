import json
import asyncio
import urllib.request
import websockets

async def intercept():
    data = urllib.request.urlopen('http://127.0.0.1:9222/json').read()
    tabs = json.loads(data)
    ws_url = tabs[0]['webSocketDebuggerUrl']
    
    async with websockets.connect(ws_url, max_size=10*1024*1024) as ws:
        await ws.send(json.dumps({"id": 1, "method": "Network.enable"}))
        await ws.recv()
        
        await ws.send(json.dumps({"id": 2, "method": "Page.navigate", "params": {"url": "https://jimeng.jianying.com/ai-tool/home"}}))
        await ws.recv()
        
        print("Listening for API requests for 15 seconds...")
        api_requests = []
        import time
        start = time.time()
        
        while time.time() - start < 15:
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=1.0)
                data = json.loads(msg)
                method = data.get('method', '')
                if method == 'Network.requestWillBeSent':
                    url = data.get('params', {}).get('request', {}).get('url', '')
                    if 'mweb' in url or 'api' in url or 'aigc' in url:
                        req = data['params']['request']
                        api_requests.append({
                            'url': url,
                            'method': req.get('method', ''),
                            'headers': {k: v for k, v in req.get('headers', {}).items() if k.lower() in ('cookie', 'authorization', 'content-type')},
                        })
            except asyncio.TimeoutError:
                continue
        
        print(f"\nFound {len(api_requests)} API requests:")
        for r in api_requests:
            print(f"  {r['method']} {r['url']}")
            for k, v in r['headers'].items():
                if k.lower() == 'cookie':
                    print(f"    Cookie: {v[:100]}...")
                else:
                    print(f"    {k}: {v[:80]}")

asyncio.run(intercept())
