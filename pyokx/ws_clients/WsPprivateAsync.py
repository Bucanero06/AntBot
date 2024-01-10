import asyncio
import json
import logging

from pyokx.ws_clients import WsUtils
from pyokx.ws_clients.WebSocketFactory import WebSocketFactory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WsPrivate")


class WsPrivateAsync:
    def __init__(self, apikey: str, passphrase: str, secretkey: str, url: str, use_servertime: bool):
        self.url = url
        # self.subscriptions = set()
        self.loop = asyncio.get_event_loop()
        self.factory = WebSocketFactory(url)
        self.callback = self.factory.callback
        self.apiKey = apikey
        self.passphrase = passphrase
        self.secretKey = secretkey
        self.useServerTime = use_servertime

    async def connect(self):
        self.websocket = await self.factory.connect()

    async def consume(self):
        async for message in self.websocket:
            logger.debug("Received message: {%s}", message)
            if self.callback:
                self.callback(message)

    async def subscribe(self, params: list, callback):

        self.callback = callback

        logRes = await self.login()
        await asyncio.sleep(5)
        if logRes:
            payload = json.dumps({
                "op": "subscribe",
                "args": params
            })
            await self.websocket.send(payload)
        else:
            logger.error(f"Could not login to websocket")
            # TODO handle edge case ... exit?

    async def login(self):
        loginPayload = WsUtils.initLoginParams(
            useServerTime=self.useServerTime,
            apiKey=self.apiKey,
            passphrase=self.passphrase,
            secretKey=self.secretKey
        )
        await self.websocket.send(loginPayload)
        return True

    async def unsubscribe(self, params: list, callback):
        self.callback = callback
        payload = json.dumps({
            "op": "unsubscribe",
            "args": params
        })
        logger.info(f"unsubscribe: {payload}")
        await self.websocket.send(payload)
        # for param in params:
        #     self.subscriptions.discard(param)

    async def start(self):
        logger.info("Connecting to WebSocket...")
        await self.connect()
        self.loop.create_task(self.consume())

    async def stop(self):
        await self.factory.close()
        self.loop.stop()

    def stop_sync(self):
        self.loop.run_until_complete(self.stop())
