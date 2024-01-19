import asyncio
import logging
import ssl

import certifi
import websockets

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WstFactory")

class WebSocketFactory:

    def __init__(self, url):
        self.url = url
        self.websocket = None
        self.callback = None

    async def connect(self, max_size=None):
        ssl_context = ssl.create_default_context()
        ssl_context.load_verify_locations(certifi.where())
        try:
            # Add the max_size argument here
            self.websocket = await websockets.connect(self.url, ssl=ssl_context, max_size=max_size)
            logger.info("WebSocket connection established.")
            return self.websocket
        except Exception as e:
            logger.error(f"Error connecting to WebSocket: {e}")
            return None
    async def close(self):
        if self.websocket:
            await self.websocket.close()
            self.websocket = None

