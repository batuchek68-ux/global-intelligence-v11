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
        
        print("请在即梦页面上点击【生成】一个视频，等待20秒...")
        
        captured = []
        start = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start < 25:
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=1.0)
                data = json.loads(msg)
                method = data.get('method', '')
                if method == 'Network.requestWillBeSent':
                    url = data.get('params', {}).get('request', {}).get('url', '')
                    if 'aigc_draft' in url or 'generate' in url:
                        req = data['params']['request']
                        body = req.get('postData', '')
                        captured.append({
                            'url': url,
                            'method': req.get('method', ''),
                            'body': body[:2000],
                            'headers': dict(list(req.get('headers', {}).items())[:10])
                        })
                        print(f"\n[CAPTURED] {req.get('method','')} {url}")
                        print(f"Body: {body[:1000]}")
                elif method == 'Network.responseReceived':
                    url = data.get('params', {}).get('response', {}).get('url', '')
                    if 'aigc_draft' in url or 'generate' in url:
                        req_id = data['params']['requestId']
                        await ws.send(json.dumps({"id": 999, "method": "Network.getResponseBody", "params": {"requestId": req_id}}))
                        resp = json.loads(await ws.recv())
                        body = resp.get('result', {}).get('body', '')
                        print(f"\n[RESPONSE] {url}")
                        print(f"Body: {body[:1000]}")
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Error: {e}")
                continue
        
        if not captured:
            print("\n没有捕获到生成请求。请确认你在即梦页面上操作了。")
        else:
            print(f"\n共捕获 {len(captured)} 个请求")

asyncio.run(intercept())
