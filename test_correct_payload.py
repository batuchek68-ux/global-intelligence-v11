import json
import asyncio
import uuid
import urllib.request
import websockets
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

async def test_correct_payload():
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
        
        prompt = "成吉思汗骑马驰骋在辽阔草原上，阳光洒落，自然光线"
        
        js = f"""
        (async function() {{
            try {{
                var uid = crypto.randomUUID();
                var compId = crypto.randomUUID();
                var metaId = crypto.randomUUID();
                var submitId = crypto.randomUUID();
                
                var payload = {{
                    "extend": {{
                        "root_model": "dreamina_ic_generate_video_model_vgfm_3.5_pro",
                        "m_video_commerce_info": {{
                            "benefit_type": "basic_video_operation_vgfm_v_three",
                            "resource_id": "generate_video",
                            "resource_id_type": "str",
                            "resource_sub_type": "aigc"
                        }},
                        "m_video_commerce_info_list": [{{
                            "benefit_type": "basic_video_operation_vgfm_v_three",
                            "resource_id": "generate_video",
                            "resource_id_type": "str",
                            "resource_sub_type": "aigc"
                        }}]
                    }},
                    "submit_id": submitId,
                    "metrics_extra": JSON.stringify({{
                        "enterFrom": "click",
                        "isDefaultSeed": 1,
                        "promptSource": "custom",
                        "isRegenerate": false,
                        "originSubmitId": uid
                    }}),
                    "draft_content": JSON.stringify({{
                        "type": "draft",
                        "id": uid,
                        "min_version": "3.0.5",
                        "is_from_tsn": true,
                        "version": "3.3.4",
                        "main_component_id": compId,
                        "component_list": [{{
                            "type": "video_base_component",
                            "id": compId,
                            "min_version": "1.0.0",
                            "metadata": {{
                                "type": "",
                                "id": metaId,
                                "created_platform": 3,
                                "created_platform_version": "",
                                "created_time_in_ms": Date.now(),
                                "created_did": ""
                            }},
                            "generate_type": "gen_video",
                            "aigc_mode": "workbench",
                            "abilities": {{
                                "type": "",
                                "id": crypto.randomUUID(),
                                "gen_video": {{
                                    "id": crypto.randomUUID(),
                                    "type": "",
                                    "text_to_video_params": {{
                                        "type": "",
                                        "id": crypto.randomUUID(),
                                        "model_req_key": "dreamina_ic_generate_video_model_vgfm_3.5_pro",
                                        "priority": 0,
                                        "seed": Math.floor(Math.random() * 100000000) + 2500000000,
                                        "video_aspect_ratio": "16:9",
                                        "video_gen_inputs": [{{
                                            "duration_ms": 5000,
                                            "first_frame_image": undefined,
                                            "end_frame_image": undefined,
                                            "fps": 24,
                                            "id": crypto.randomUUID(),
                                            "min_version": "3.0.5",
                                            "prompt": "{prompt}",
                                            "resolution": "720p",
                                            "type": "",
                                            "video_mode": 2
                                        }}]
                                    }},
                                    "video_task_extra": JSON.stringify({{
                                        "enterFrom": "click",
                                        "isDefaultSeed": 1,
                                        "promptSource": "custom",
                                        "isRegenerate": false,
                                        "originSubmitId": uid
                                    }})
                                }}
                            }}
                        }}]
                    }}),
                    "http_common_info": {{
                        "aid": 513695
                    }}
                }};
                
                var resp = await fetch('/mweb/v1/aigc_draft/generate?os=windows&aid=513695&web_version=7.5.0&da_version=3.3.4&aigc_features=app_lip_sync', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    credentials: 'include',
                    body: JSON.stringify(payload)
                }});
                
                var text = await resp.text();
                return text.substring(0, 1500);
            }} catch(e) {{
                return 'Error: ' + e.message;
            }}
        }})()
        """
        print("Testing with correct payload format...")
        result = await evaluate(js)
        print(result)

asyncio.run(test_correct_payload())
