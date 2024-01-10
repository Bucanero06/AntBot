import asyncio
import json
import logging

from pyokx.ws_clients.WebSocketFactory import WebSocketFactory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WsPublicAsync")

class WsPublicAsync:
    def __init__(self, url: str):
        self.url = url
        # self.subscriptions = set()
        self.loop = asyncio.get_event_loop()
        self.factory = WebSocketFactory(url)
        self.callback = self.factory.callback


    async def connect(self):
        self.websocket = await self.factory.connect()

    async def consume(self):
        async for message in self.websocket:
            logger.debug("Received message: {%s}", message)
            if self.callback:
                self.callback(message)

    async def subscribe(self, params: list, callback):
        self.callback = callback
        payload = json.dumps({
            "op": "subscribe",
            "args": params
        })
        await self.websocket.send(payload)

    async def unsubscribe(self, params: list, callback):
        self.callback = callback
        payload = json.dumps({
            "op": "unsubscribe",
            "args": params
        })
        logger.info(f"unsubscribe: {payload}")
        await self.websocket.send(payload)

    async def start(self):
        logger.info("Connecting to WebSocket...")
        await self.connect()
        self.loop.create_task(self.consume())

    async def stop(self):
        await self.factory.close()
        self.loop.stop()

    def stop_sync(self):
        self.loop.run_until_complete(self.stop())
