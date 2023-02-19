from __future__ import absolute_import, unicode_literals
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import threading
from internal import enums
from uuid import uuid4
from collections import defaultdict
from kafka.consumer import start_consumer
import uvicorn
import settings
import json
import logging
from connections import ConnectionManager as manager

logger = logging.getLogger("uvicorn.error")

app = FastAPI()


# manager = ConnectionManager()

@app.websocket("/ws/{account_id}")
async def websocket_endpoint(websocket: WebSocket, account_id: str):
    # logger.warning(f"connect {manager.tid}")
    await manager.connect(account_id, websocket)
    try:
        while True:
            try:
                data = await websocket.receive_text()
                params = json.loads(data)
                if params['method'] == "SUBSCRIBE":
                    for channel in params['channels']:
                        await manager.subscribe(channel, websocket)
            except WebSocketDisconnect:
                logger.warning("disconnect")
                manager.disconnect(websocket)
                break
            except Exception as e:
                logger.warning(e)
                await manager.send_message(
                    json.dumps({
                        "event": "ERROR",
                        "msg": "invalid format"
                    }),
                    websocket
                    )
    except WebSocketDisconnect:
        # print("disconnect")
        logger.error(e)
        manager.disconnect(websocket)
    except Exception as e:
        # print("disconnect")
        logger.error(e)

@app.get("/")
async def root():
    return {"message": "Websocket service is runing."}

# def f():
#     while True:
#         time.sleep(20)
#         logger.warning(f"f {manager.connections}")

@app.on_event("startup")
async def startup():
    start_consumer(manager.publish)
    
if __name__ == "__main__":
    logger.warning(f"starting server {manager.tid}")
    uvicorn.run("main:app", host="0.0.0.0", port=settings.SERVICE_PORT)
