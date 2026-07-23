import json
import asyncio
import urllib.request
import websockets

JS_TEMPLATE = """
(async function() {{
    try {{
        var resp = await fetch('/mweb/v1/aigc_draft/generate', {{
            method: 'POST',
            headers: {{
                'Content-Type': 'application/json',
                'Lan': 'zh',
                'Loc': 'cn',
            }},
            body: JSON.stringify({payload}),
            credentials: 'include'
        }});
        var text = await resp.text();
        return JSON.stringify({{status: resp.status, body: text}});
    }} catch(e) {{
        return JSON.stringify({{error: e.message}});
    }}
}})()
"""

async def test():
    data = urllib.request.urlopen('http://127.0.0.1:9222/json').read()
    tabs = json.loads(data)
    ws_url = tabs[0]['webSocketDebuggerUrl']
    
    payloads = [
        {
            "type": "video",
            "model": "dreamina_seedance_40",
            "prompt": "草原",
            "duration": 5,
            "ratio": "16:9",
            "resolution": "720p",
        },
        {
            "metrics": {"extra": {"air": "1"}},
            "model": "dreamina_seedance_40",
            "prompt": "草原",
            "duration": 5,
            "video_gen_type": 1,
            "video_ratio": "16:9",
            "video_resolution": "720p",
            "type": "video",
        },
        {
            "model_version": "dreamina_seedance_40",
            "prompt": "草原",
            "video_gen_type": 1,
            "video_ratio": "16:9",
            "video_resolution": "720p",
            "duration": 5,
        },
    ]
    
    async with websockets.connect(ws_url, max_size=10*1024*1024) as ws:
        for i, payload in enumerate(payloads):
            js = JS_TEMPLATE.format(payload=json.dumps(payload, ensure_ascii=False))
            await ws.send(json.dumps({"id": i+1, "method": "Runtime.evaluate", "params": {"expression": js, "awaitPromise": True}}))
            r = json.loads(await ws.recv())
            val = r.get('result', {}).get('result', {}).get('value', '')
            d = json.loads(val)
            print(f"\n[Payload {i+1}] status={d.get('status')}")
            print(f"  body={d.get('body', d.get('error', ''))[:200]}")

asyncio.run(test())
