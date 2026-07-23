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
        
        print("监听中... 请在即梦页面上生成一个【视频】（不是图片）")
        
        start = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start < 90:
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
                data = json.loads(msg)
                method = data.get('method', '')
                
                if method == 'Network.requestWillBeSent':
                    req = data['params']['request']
                    url = req.get('url', '')
                    if req.get('method') == 'POST' and 'jianying' in url:
                        body = req.get('postData', '')
                        if 'aigc_draft' in url or 'video' in url.lower() or 'seedance' in body.lower():
                            print(f"\n>>> POST {url[:200]}")
                            print(f"Body: {body[:3000]}")
                            print()
                            
            except asyncio.TimeoutError:
                continue
            except websockets.exceptions.ConnectionClosed:
                break
            except Exception:
                continue
        
        print("\n监听结束")

asyncio.run(intercept())
