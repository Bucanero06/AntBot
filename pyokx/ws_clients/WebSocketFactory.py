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

