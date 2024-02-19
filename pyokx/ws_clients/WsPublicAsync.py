
import asyncio
import json
import logging
from typing import List, Set

from websockets import ConnectionClosedError

from pyokx.ws_clients.WebSocketFactory import WebSocketFactory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WsPublicAsync")


class WsPublicAsync:
    def __init__(self, url: str, callback):
        self.url = url
        # self.subscriptions = set()
        self.loop = asyncio.get_event_loop()
        self.factory = WebSocketFactory(url)
        self.callback = callback
        self.max_size = 2 ** 20
        self.websocket = None
        self.channel_params = []

    async def connect(self):
        self.websocket = await self.factory.connect(max_size=self.max_size)

    async def consume(self):
        try:
            async for message in self.websocket:
                logger.debug("Received message: {%s}", message)
                if self.callback:
                    await self.callback(message)
        except ConnectionClosedError as e:
            logger.error(f"WebSocket connection closed: {e}")
            # Handle reconnection logic here
            await self.restart()
        except Exception as e:
            logger.error(f"WebSocket unhandled error: {e}")
            await self.restart()

    async def subscribe(self, params: list):
        payload = json.dumps({
            "op": "subscribe",
            "args": params
        })
        await self.websocket.send(payload)
        self.channel_params = self.channel_params + params

    async def unsubscribe(self, params: List[dict]):
        payload = json.dumps({
            "op": "unsubscribe",
            "args": params
        })
        logger.info(f"unsubscribe: {payload}")
        await self.websocket.send(payload)
        self.channel_params = list(set(self.channel_params) - set(params))

    async def start(self):
        logger.info("Connecting to WebSocket...")
        await self.connect()
        self.loop.create_task(self.consume())

    async def restart(self):
        logger.info("Restarting WebSocket...")
        channel_params = self.channel_params
        for i in range(3):
            try:
                if self.websocket:
                    await self.factory.close()
                await self.start()
                await self.subscribe(channel_params)
                break
            except KeyboardInterrupt:
                logger.info("Keyboard Interrupt")
                try:
                    if self.websocket:
                        await self.factory.close()
                    self.stop_sync()
                except Exception as e:
                    logger.error(f"Error gracefully closing websocket: {e}")
                finally:
                    break
            except Exception as e:
                logger.error(f"Error restarting websocket: {e}")
                await asyncio.sleep(1)
                continue


    async def stop(self):
        await self.factory.close()
        self.loop.stop()

    def stop_sync(self):
        self.loop.run_until_complete(self.stop())
