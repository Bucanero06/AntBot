# Copyright (c) 2024 Carbonyl LLC & Carbonyl R&D
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import asyncio
import json
import logging
from typing import List, Set

from websockets import ConnectionClosedError

from pyokx.ws_clients import WsUtils
from pyokx.ws_clients.WebSocketFactory import WebSocketFactory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WsPrivate")


class WsPrivateAsync:
    def __init__(self, apikey: str, passphrase: str, secretkey: str, url: str, use_servertime: bool,
                 callback):
        self.url = url
        self.loop = asyncio.get_event_loop()
        self.factory = WebSocketFactory(url)
        self.callback = callback
        self.apiKey = apikey
        self.passphrase = passphrase
        self.secretKey = secretkey
        self.useServerTime = use_servertime
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
            # Handle reconnection logic here
            await self.restart()


    async def subscribe(self, params: List[dict]):
        logRes = await self.login()
        await asyncio.sleep(5)
        try:
            if logRes:
                payload = json.dumps({
                    "op": "subscribe",
                    "args": params
                })
                await self.websocket.send(payload)
            else:
                logger.error(f"Could not login to websocket")
                raise Exception("Could not login to websocket")
            self.channel_params = self.channel_params + params
        except Exception as e:
            logger.error(f"Error subscribing to websocket: {e}")
            raise Exception(f"Error subscribing to websocket: {e}")

    async def login(self):
        loginPayload = WsUtils.initLoginParams(
            useServerTime=self.useServerTime,
            apiKey=self.apiKey,
            passphrase=self.passphrase,
            secretKey=self.secretKey
        )
        await self.websocket.send(loginPayload)
        return True

    async def unsubscribe(self, params: list):
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
