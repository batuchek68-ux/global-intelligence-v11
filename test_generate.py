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
                'App-Sdk-Version': '2.0.0'
            }},
            body: JSON.stringify({payload}),
            credentials: 'include'
        }});
        var text = await resp.text();
        return JSON.stringify({{status: resp.status, body: text.substring(0, 1000)}});
    }} catch(e) {{
        return JSON.stringify({{error: e.message}});
    }}
}})()
"""

async def generate_video(prompt):
    data = urllib.request.urlopen('http://127.0.0.1:9222/json').read()
    tabs = json.loads(data)
    ws_url = tabs[0]['webSocketDebuggerUrl']
    
    payload = {
        "model": "dreamina_seedance_40",
        "prompt": prompt,
        "duration": 5,
        "ratio": "16:9",
        "resolution": "720p",
        "video_gen_type": 1,
    }
    
    js = JS_TEMPLATE.format(payload=json.dumps(payload))
    
    async with websockets.connect(ws_url, max_size=10*1024*1024) as ws:
        await ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate", "params": {"expression": js, "awaitPromise": True}}))
        r = json.loads(await ws.recv())
        val = r.get('result', {}).get('result', {}).get('value', '')
        print(f"Response: {val}")

asyncio.run(generate_video("成吉思汗骑马驰骋在辽阔草原上，自然光线，一镜到底，无大幅移动"))
