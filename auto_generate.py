import json
import asyncio
import urllib.request
import websockets

async def generate_via_ui(prompt):
    data = urllib.request.urlopen('http://127.0.0.1:9222/json').read()
    tabs = json.loads(data)
    ws_url = tabs[0]['webSocketDebuggerUrl']
    
    async with websockets.connect(ws_url, max_size=10*1024*1024) as ws:
        msg_id = 0
        
        async def send_cmd(method, params={}):
            nonlocal msg_id
            msg_id += 1
            await ws.send(json.dumps({"id": msg_id, "method": method, "params": params}))
            while True:
                msg = json.loads(await ws.recv())
                if msg.get('id') == msg_id:
                    return msg
        
        async def evaluate(expr):
            r = await send_cmd("Runtime.evaluate", {"expression": expr, "awaitPromise": True, "returnByValue": True})
            return r.get('result', {}).get('result', {}).get('value', '')
        
        await send_cmd("Page.enable")
        await send_cmd("Network.enable")
        
        js = f"""
        (async function() {{
            var textarea = document.querySelector('textarea') || document.querySelector('[contenteditable="true"]') || document.querySelector('input[type="text"]');
            if (!textarea) return 'no textarea found';
            
            textarea.focus();
            textarea.value = '';
            
            var nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set || Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
            nativeInputValueSetter.call(textarea, '{prompt}');
            textarea.dispatchEvent(new Event('input', {{ bubbles: true }}));
            textarea.dispatchEvent(new Event('change', {{ bubbles: true }}));
            
            return 'text set to: ' + textarea.value;
        }})()
        """
        result = await evaluate(js)
        print(f"Step 1 - Set prompt: {result}")
        
        js2 = """
        (async function() {
            var buttons = document.querySelectorAll('button');
            var generateBtn = null;
            for (var btn of buttons) {
                var text = btn.innerText || btn.textContent || '';
                if (text.includes('生成') || text.includes('Generate') || text.includes('创作')) {
                    generateBtn = btn;
                    break;
                }
            }
            if (!generateBtn) {
                var allBtns = [];
                buttons.forEach(b => allBtns.push((b.innerText || b.textContent || '').substring(0, 20)));
                return 'no generate button found. Buttons: ' + allBtns.join(' | ');
            }
            generateBtn.click();
            return 'clicked: ' + (generateBtn.innerText || generateBtn.textContent || '').substring(0, 30);
        })()
        """
        result = await evaluate(js2)
        print(f"Step 2 - Click generate: {result}")

asyncio.run(generate_via_ui("成吉思汗骑马驰骋在辽阔草原上，自然光线，一镜到底，无大幅移动"))
