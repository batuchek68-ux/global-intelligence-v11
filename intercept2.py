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
        r = json.loads(await ws.recv())
        print(f"Network enable: {r}")
        
        print("监听中... 请在浏览器里刷新即梦页面")
        api_requests = []
        
        start = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start < 20:
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
                data = json.loads(msg)
                method = data.get('method', '')
                if method == 'Network.requestWillBeSent':
                    url = data.get('params', {}).get('request', {}).get('url', '')
                    if 'jimeng' in url or 'jianying' in url:
                        req = data['params']['request']
                        cookie = req.get('headers', {}).get('Cookie', req.get('headers', {}).get('cookie', ''))
                        auth = req.get('headers', {}).get('Authorization', req.get('headers', {}).get('authorization', ''))
                        if cookie or auth:
                            api_requests.append({
                                'url': url[:150],
                                'method': req.get('method', ''),
                                'has_cookie': bool(cookie),
                                'has_auth': bool(auth),
                                'content_type': req.get('headers', {}).get('Content-Type', req.get('headers', {}).get('content-type', '')),
                            })
            except asyncio.TimeoutError:
                continue
            except websockets.exceptions.ConnectionClosed:
                print("Connection closed")
                break
        
        print(f"\nFound {len(api_requests)} jimeng/jianying requests:")
        for r in api_requests:
            print(f"  {r['method']} {r['url']}")
            print(f"    cookie={r['has_cookie']} auth={r['has_auth']} ct={r['content_type']}")

asyncio.run(intercept())
