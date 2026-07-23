import json
import asyncio
import urllib.request
import websockets
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

async def test_image_gen():
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
        (async function() {
            try {
                var resp = await fetch('/mweb/v1/aigc_draft/generate?os=windows&aid=513695&web_version=7.5.0&da_version=3.3.21&aigc_features=app_lip_sync', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({
                        "metrics": {"extra": {"air": "1"}},
                        "model": "dreamina_ic_generate_video_model_vgfm_3.5_pro",
                        "prompt": "test video",
                        "duration": 5,
                        "video_gen_type": 1,
                        "video_ratio": "16:9",
                        "video_resolution": "720p",
                        "type": "video"
                    })
                });
                var text = await resp.text();
                return text.substring(0, 1000);
            } catch(e) {
                return 'Error: ' + e.message;
            }
        })()
        """
        print("Testing video generation...")
        result = await evaluate(js)
        print(result[:1000])

asyncio.run(test_image_gen())
