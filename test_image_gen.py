import json
import asyncio
import urllib.request
import websockets
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

async def check():
    data = urllib.request.urlopen('http://127.0.0.1:9222/json').read()
    tabs = json.loads(data)
    
    jimeng_tab = None
    for tab in tabs:
        url = tab.get('url', '')
        if 'jimeng.jianying.com' in url and 'helpdesk' not in url:
            jimeng_tab = tab
            break
    
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
        
        # Try image generation to see if it works (costs 3 credits per image)
        js = """
        (async function() {
            try {
                var uid = crypto.randomUUID();
                var compId = crypto.randomUUID();
                var metaId = crypto.randomUUID();
                var submitId = crypto.randomUUID();
                
                var payload = {
                    "extend": {
                        "root_model": "high_aes_general_v50"
                    },
                    "submit_id": submitId,
                    "metrics_extra": JSON.stringify({
                        "enterFrom": "click",
                        "isDefaultSeed": 1,
                        "promptSource": "custom",
                        "isRegenerate": false,
                        "originSubmitId": uid
                    }),
                    "draft_content": JSON.stringify({
                        "type": "draft",
                        "id": uid,
                        "min_version": "3.0.5",
                        "is_from_tsn": true,
                        "version": "3.3.9",
                        "main_component_id": compId,
                        "component_list": [{
                            "type": "image_base_component",
                            "id": compId,
                            "min_version": "1.0.0",
                            "metadata": {
                                "type": "",
                                "id": metaId,
                                "created_platform": 3,
                                "created_platform_version": "",
                                "created_time_in_ms": Date.now(),
                                "created_did": ""
                            },
                            "generate_type": "normal",
                            "aigc_mode": "workbench",
                            "abilities": {
                                "type": "",
                                "id": crypto.randomUUID(),
                                "generate_image": {
                                    "id": crypto.randomUUID(),
                                    "type": "",
                                    "image_gen_inputs": [{
                                        "type": "",
                                        "id": crypto.randomUUID(),
                                        "model_req_key": "high_aes_general_v50",
                                        "prompt": "a beautiful sunset over mountains",
                                        "resolution": "2k",
                                        "seed": Math.floor(Math.random() * 100000000),
                                        "image_num": 1,
                                        "image_height": 1440,
                                        "image_width": 2560,
                                        "use_hyper": false
                                    }],
                                    "task_extra": JSON.stringify({
                                        "enterFrom": "click",
                                        "isDefaultSeed": 1,
                                        "promptSource": "custom",
                                        "isRegenerate": false,
                                        "originSubmitId": uid
                                    })
                                }
                            }
                        }]
                    }),
                    "http_common_info": {
                        "aid": 513695
                    }
                };
                
                var resp = await fetch('/mweb/v1/aigc_draft/generate?os=windows&aid=513695&web_version=7.5.0&da_version=3.3.9&aigc_features=app_lip_sync', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify(payload)
                });
                
                var text = await resp.text();
                return text.substring(0, 1500);
            } catch(e) {
                return 'Error: ' + e.message;
            }
        })()
        """
        print("Testing image generation...")
        result = await evaluate(js)
        print(result)

asyncio.run(check())
