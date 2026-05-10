import asyncio
import websockets
import json

async def test():
    uri = "ws://localhost:3001/ws/chat"
    try:
        async with websockets.connect(uri) as ws:
            payload = {
                "message": "Hello, say 'TEST SUCCESSFUL' if you can hear me.",
                "model": "qwen2.5:0.5b",
                "system": "You are a helpful assistant.",
                "temperature": 0.7,
                "max_tokens": 100,
                "use_gpu": True
            }
            await ws.send(json.dumps(payload))
            print("Sent prompt to Qwen. Waiting for stream...")
            
            while True:
                resp = await ws.recv()
                data = json.loads(resp)
                if "token" in data:
                    print(data["token"], end="", flush=True)
                if data.get("done"):
                    print("\n\n[Finished stream]")
                    break
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(test())
