from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from kafka.consumer import start_consumer
from internal import enums
from collections import defaultdict
import uvicorn
import settings
import json

app = FastAPI()

class ConnectionManager:
    subscriptions: dict[str, list[WebSocket]] = defaultdict(lambda: [])

    async def connect(self, account_id:str, websocket: WebSocket):
        websocket.account_id = account_id
        websocket.channels = []
        await websocket.accept()
        ConnectionManager.subscriptions[account_id].append(websocket)

    def disconnect(self, websocket: WebSocket):
        ConnectionManager.subscriptions[websocket.account_id].remove(websocket)
        if not ConnectionManager.subscriptions[websocket.account_id]:
            del ConnectionManager.subscriptions[websocket.account_id]

    async def subscribe(self, channel:str, websocket: WebSocket):
        print("new subscriptions")
        if channel not in websocket.channels:
            msg = f"{channel} subscribed"
            print("subsed")
            websocket.channels.append(channel)
            ConnectionManager.subscriptions[channel].append(websocket)
        else:
            msg = f"{channel} already subscribed"
        await self.send_message(msg, websocket)

    async def unsubscribe(self, channel:str, websocket: WebSocket):
        msg = f"{channel} unsubscribed"
        if channel in websocket.channels:
            websocket.channels.remove(channel)
        ConnectionManager.subscriptions[channel].remove(websocket)
        if not ConnectionManager.subscriptions[channel]:
            del ConnectionManager.subscriptions[channel]
        await self.send_message(msg, websocket)

    async def publish(self, subscription_key: str="", message: str=""):
        print(ConnectionManager.subscriptions[subscription_key])
        for websocket in ConnectionManager.subscriptions[subscription_key]:
            await self.send_message(message=message, websocket=websocket)

    async def send_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    # async def broadcast(self, message: str):
    #     for _, connections in ConnectionManager.active_connections.items():
    #         for connection in connections:
    #             await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/{account_id}")
async def websocket_endpoint(websocket: WebSocket, account_id: str):
    await manager.connect(account_id, websocket)
    try:
        while True:
            try:
                data = await websocket.receive_text()
                params = json.loads(data)
                if params['method'] == "SUBSCRIBE":
                    for channel in params['channels']:
                        await manager.subscribe(channel, websocket)
            except Exception as e:
                print(e)
                await manager.send_message(
                    json.dumps({
                        "event": "ERROR",
                        "msg": "invalid format"
                    }),
                    websocket
                    )
    except WebSocketDisconnect:
        print("disconnect")
        manager.disconnect(websocket)

@app.get("/")
async def root():
    return {"message": "OK!"}

@app.on_event("startup")
async def startup():
    start_consumer(manager.publish)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=settings.SERVICE_PORT)
