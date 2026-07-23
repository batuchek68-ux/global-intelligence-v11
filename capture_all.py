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
        
        print("监听中... 请在即梦页面上生成一个视频")
        
        start = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start < 60:
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
                data = json.loads(msg)
                method = data.get('method', '')
                
                if method == 'Network.requestWillBeSent':
                    req = data['params']['request']
                    url = req.get('url', '')
                    if req.get('method') == 'POST' and ('jianying' in url or 'jimeng' in url):
                        body = req.get('postData', '')
                        print(f"\n>>> POST {url}")
                        print(f"Body: {body[:2000]}")
                        print(f"Headers: {json.dumps({k:v for k,v in req.get('headers',{}).items() if k.lower() in ('content-type','authorization','cookie')}, indent=2)}")
                
                if method == 'Network.responseReceived':
                    resp = data['params']['response']
                    url = resp.get('url', '')
                    status = resp.get('status', 0)
                    if status == 200 and ('jianying' in url or 'jimeng' in url) and 'generate' in url.lower():
                        req_id = data['params']['requestId']
                        await ws.send(json.dumps({"id": 999, "method": "Network.getResponseBody", "params": {"requestId": req_id}}))
                        resp_data = json.loads(await ws.recv())
                        body = resp_data.get('result', {}).get('body', '')
                        print(f"\n<<< Response {url}: {body[:1000]}")
                        
            except asyncio.TimeoutError:
                continue
            except websockets.exceptions.ConnectionClosed:
                print("Connection closed, reconnecting...")
                break
            except Exception as e:
                continue
        
        print("\n监听结束")

asyncio.run(intercept())
