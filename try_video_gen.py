import json
import asyncio
import urllib.request
import websockets

JS = """
(async function() {
    try {
        var resp = await fetch('/mweb/v1/aigc_draft/generate?os=windows&aid=513695&web_version=7.5.0&da_version=3.3.21&aigc_features=app_lip_sync', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                "metrics": {"extra": {"air": "1"}},
                "model": "dreamina_seedance_40",
                "prompt": "成吉思汗骑马驰骋在辽阔草原上，自然光线，一镜到底",
                "duration": 5,
                "video_gen_type": 1,
                "video_ratio": "16:9",
                "video_resolution": "720p",
                "type": "video"
            }),
            credentials: 'include'
        });
        var text = await resp.text();
        return JSON.stringify({status: resp.status, body: text});
    } catch(e) {
        return JSON.stringify({error: e.message});
    }
})()
"""

async def test():
    data = urllib.request.urlopen('http://127.0.0.1:9222/json').read()
    tabs = json.loads(data)
    ws_url = tabs[0]['webSocketDebuggerUrl']
    
    async with websockets.connect(ws_url, max_size=10*1024*1024) as ws:
        await ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate", "params": {"expression": JS, "awaitPromise": True}}))
        r = json.loads(await ws.recv())
        val = r.get('result', {}).get('result', {}).get('value', '')
        print(val)

asyncio.run(test())
