from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import threading
from internal import enums
from uuid import uuid4
from collections import defaultdict
from celery_config.celery_app import app as celery_app
# from celery import app as celery_app
import time
import uvicorn
import settings
import json
import logging

logger = logging.getLogger("uvicorn.error")


class ConnectionManager:
    # subscriptions: dict[str, list[WebSocket]] = defaultdict(lambda: [])
    connections: dict[str, dict[str, WebSocket]] = defaultdict(lambda: {})
    channel_subscriptions: dict[str, list[str]] = defaultdict(lambda: [])
    tid = str(uuid4())
    @classmethod
    def get_subscription_msg(cls, event):
        msg = {"topic": "subscription", "timestampe": int(time.time() * 1000), "event": event}
        return json.dumps(msg)
    @classmethod
    async def connect(cls, account_id:str, websocket: WebSocket):
        # logger.warning(f"new account_id {account_id}")
        websocket.connection_id = str(uuid4())
        websocket.account_id = account_id
        websocket.channels = []
        await websocket.accept()
        # ConnectionManager.subscriptions[account_id].append(websocket)
        ConnectionManager.connections[websocket.account_id][websocket.connection_id] = websocket
        # logger.warning(ConnectionManager.connections)

    @classmethod
    def disconnect(cls, websocket: WebSocket):
        # ConnectionManager.subscriptions[websocket.account_id].remove(websocket)
        # ConnectionManager.connections[websocket.account_id][websocket.connection_id].remove(websocket)
        del ConnectionManager.connections[websocket.account_id][websocket.connection_id]
        if not ConnectionManager.connections[websocket.account_id]:
            del ConnectionManager.connections[websocket.account_id]
        # if not ConnectionManager.subscriptions[websocket.account_id]:
        #     del ConnectionManager.subscriptions[websocket.account_id]
        # logger.warning(f"connection closed {websocket.account_id}")
        ## logger.warning(ConnectionManager.connections)

    @classmethod
    async def subscribe(cls, channel:str, websocket: WebSocket):
        # logger.warning("new subscriptions")
        msg = ConnectionManager.get_subscription_msg({"channel": channel, "action": "subscribed"})
        if channel not in websocket.channels:
            # logger.warning("subsed")
            websocket.channels.append(channel)
            ConnectionManager.channel_subscriptions[channel].append(f"{websocket.account_id}@@{websocket.connection_id}")
            # ConnectionManager.subscriptions[channel].append(websocket)
        # else:
        #     msg = json.dumps({"topic": "subscription", "channel": channel})
        #logger.warning(ConnectionManager.connections)
        await cls.send_message(msg, websocket)

    @classmethod
    async def unsubscribe(cls, channel:str, websocket: WebSocket):
        msg = ConnectionManager.get_subscription_msg({"channel": channel, "action": "unsubscribed"})
        if channel in websocket.channels:
            websocket.channels.remove(channel)
        # ConnectionManager.subscriptions[channel].remove(websocket)
        ConnectionManager.channel_subscriptions[channel].remove(f"{websocket.account_id}@@{websocket.connection_id}")
        await cls.send_message(msg, websocket)
        if not websocket.channels:
            cls.disconnect(websocket=websocket)
        # if not ConnectionManager.subscriptions[channel]:
        #     del ConnectionManager.subscriptions[channel]
        #logger.warning(ConnectionManager.connections)

    @classmethod
    async def publish(cls, subscription_key: str="", message: str="", account_update: bool=True):
        # logger.warning(ConnectionManager.channel_subscriptions)
        # logger.warning(ConnectionManager.connections)
        if account_update:
            if subscription_key in ConnectionManager.connections:
                for connection_id, websocket in ConnectionManager.connections[subscription_key].items():
                    await cls.send_message(message=message, websocket=websocket)
        else:
            for websocket_info in ConnectionManager.channel_subscriptions[subscription_key]:
                account_id, connection_id = websocket_info.split('@@')
                if account_id in ConnectionManager.connections:
                    if connection_id in ConnectionManager.connections[account_id]:
                        websocket = ConnectionManager.connections[account_id][connection_id]
                        await cls.send_message(message=message, websocket=websocket)

    @classmethod
    async def send_message(cls, message: str, websocket: WebSocket):
        await websocket.send_text(message)  

    # async def broadcast(cls, message: str):
    #     for _, connections in ConnectionManager.active_connections.items():
    #         for connection in connections:
    #             await connection.send_text(message)
# manager = ConnectionManager