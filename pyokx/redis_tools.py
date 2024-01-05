import asyncio
import json
import os

import dotenv

from pyokx.data_structures import *
from pyokx.okx.websocket.WsPprivateAsync import WsPrivateAsync
from pyokx.okx.websocket.WsPublicAsync import WsPublicAsync
from shared.tmp_shared import execute_function_calls

# Live
# Public WebSocket: wss://ws.okx.com:8443/ws/v5/public
# Private WebSocket: wss://ws.okx.com:8443/ws/v5/private
# wss://ws.okx.com:8443/ws/v5/business
# DEMO
# Public WebSocket：wss://wspap.okx.com:8443/ws/v5/public?brokerId=9999
# Private WebSocket：wss://wspap.okx.com:8443/ws/v5/private?brokerId=999
# wss://wspap.okx.com:8443/ws/v5/business?brokerId=9999
dotenv.load_dotenv(dotenv.find_dotenv())
apiKey = os.getenv('OKX_API_KEY')
passphrase = os.getenv('OKX_PASSPHRASE')
secretKey = os.getenv('OKX_SECRET_KEY')
sandbox_mode = os.getenv('OKX_SANDBOX_MODE')


# # Initialize FastAPI app
# app = FastAPI()

# # Initialize Redis client
# redis = aioredis.from_url("redis://localhost", encoding="utf-8", decode_responses=True)

class WebSocketConnectionConfig(BaseModel):
    channels: dict = {}
    wss_url: str


async def websockets_main_run(input_channel_models: list):
    if not input_channel_models:
        raise Exception("No channels provided")
    DEMO_TRADING_WS_EXTENSION = "?brokerId=9999"
    public_channels_config = WebSocketConnectionConfig(
        wss_url='wss://wspap.okx.com:8443/ws/v5/public',
        channels={
            "price-limit": PriceLimitChannel,
            "instruments": InstrumentsChannel,
            "mark-price": MarkPriceChannel,
            "index-tickers": IndexTickersChannel,
        }
    )
    business_channels_config = WebSocketConnectionConfig(
        wss_url='wss://wspap.okx.com:8443/ws/v5/business',
        channels={
            "mark-price-candle1m": MarkPriceCandleSticksChannel,
            "mark-price-candle3m": MarkPriceCandleSticksChannel,
            "mark-price-candle5m": MarkPriceCandleSticksChannel,
            "mark-price-candle15m": MarkPriceCandleSticksChannel,
            "mark-price-candle30m": MarkPriceCandleSticksChannel,
            "mark-price-candle1H": MarkPriceCandleSticksChannel,
            "mark-price-candle2H": MarkPriceCandleSticksChannel,
            "mark-price-candle4H": MarkPriceCandleSticksChannel,
            "mark-price-candle6H": MarkPriceCandleSticksChannel,
            "mark-price-candle12H": MarkPriceCandleSticksChannel,
            "mark-price-candle5D": MarkPriceCandleSticksChannel,
            "mark-price-candle3D": MarkPriceCandleSticksChannel,
            "mark-price-candle2D": MarkPriceCandleSticksChannel,
            "mark-price-candle1D": MarkPriceCandleSticksChannel,
            "mark-price-candle1W": MarkPriceCandleSticksChannel,
            "mark-price-candle1M": MarkPriceCandleSticksChannel,
            "mark-price-candle3M": MarkPriceCandleSticksChannel,
            "mark-price-candle1Yutc": MarkPriceCandleSticksChannel,
            "mark-price-candle3Mutc": MarkPriceCandleSticksChannel,
            "mark-price-candle1Mutc": MarkPriceCandleSticksChannel,
            "mark-price-candle1Wutc": MarkPriceCandleSticksChannel,
            "mark-price-candle1Dutc": MarkPriceCandleSticksChannel,
            "mark-price-candle2Dutc": MarkPriceCandleSticksChannel,
            "mark-price-candle3Dutc": MarkPriceCandleSticksChannel,
            "mark-price-candle5Dutc": MarkPriceCandleSticksChannel,
            "mark-price-candle12Hutc": MarkPriceCandleSticksChannel,
            "mark-price-candle6Hutc": MarkPriceCandleSticksChannel,
            #
            "index-candle1m": IndexCandleSticksChannel,
            "index-candle3m": IndexCandleSticksChannel,
            "index-candle5m": IndexCandleSticksChannel,
            "index-candle15m": IndexCandleSticksChannel,
            "index-candle30m": IndexCandleSticksChannel,
            "index-candle1H": IndexCandleSticksChannel,
            "index-candle2H": IndexCandleSticksChannel,
            "index-candle4H": IndexCandleSticksChannel,
            "index-candle6H": IndexCandleSticksChannel,
            "index-candle12H": IndexCandleSticksChannel,
            "index-candle5D": IndexCandleSticksChannel,
            "index-candle3D": IndexCandleSticksChannel,
            "index-candle2D": IndexCandleSticksChannel,
            "index-candle1D": IndexCandleSticksChannel,
            "index-candle1W": IndexCandleSticksChannel,
            "index-candle1M": IndexCandleSticksChannel,
            "index-candle3M": IndexCandleSticksChannel,
            "index-candle1Yutc": IndexCandleSticksChannel,
            "index-candle3Mutc": IndexCandleSticksChannel,
            "index-candle1Mutc": IndexCandleSticksChannel,
            "index-candle1Wutc": IndexCandleSticksChannel,
            "index-candle1Dutc": IndexCandleSticksChannel,
            "index-candle2Dutc": IndexCandleSticksChannel,
            "index-candle3Dutc": IndexCandleSticksChannel,
            "index-candle5Dutc": IndexCandleSticksChannel,
            "index-candle12Hutc": IndexCandleSticksChannel,
            "index-candle6Hutc": IndexCandleSticksChannel,
        }
    )

    private_channels_config = WebSocketConnectionConfig(
        wss_url='wss://wspap.okx.com:8443/ws/v5/private',
        channels={
            "account": AccountChannel,  # Missing coinUsdPrice
            "positions": PositionChannel,  # Missing pTime
            "balance_and_position": BalanceAndPositionsChannel,
        }
    )

    if sandbox_mode:
        public_channels_config.wss_url = f'{public_channels_config.wss_url}{DEMO_TRADING_WS_EXTENSION}'
        business_channels_config.wss_url = f'{business_channels_config.wss_url}{DEMO_TRADING_WS_EXTENSION}'
        private_channels_config.wss_url = f'{private_channels_config.wss_url}{DEMO_TRADING_WS_EXTENSION}'

    public_client = WsPublicAsync(url=public_channels_config.wss_url)
    business_client = WsPublicAsync(url=business_channels_config.wss_url)
    private_client = WsPrivateAsync(
        apiKey=apiKey,
        passphrase=passphrase,
        secretKey=secretKey,
        url=private_channels_config.wss_url,
        useServerTime=False,
    )


    available_channel_models = public_channels_config.channels | business_channels_config.channels | private_channels_config.channels

    def public_callback(message):
        message_data = json.loads(message)
        event = message_data.get("event", None)

        if event:
            if event == "error":
                print(f"Error: {message_data}")
                exit()
            print(f"Event: {message_data}")
            return  # TODO: Handle events, mostly subscribe and error

        message_args = message_data.get("arg")
        data = message_data.get("data")
        try:
            data_struct = available_channel_models[message_args.get("channel")]

            if hasattr(data_struct, "from_array"):
                structured_data = data_struct.from_array(args=message_args, data=data)
            else:
                structured_data = data_struct(args=message_args, data=data)
            print(f"Received Data: {structured_data}")

        except Exception as e:
            print(f"Exception: {e}")
            return

    public_channels = []
    business_channels = []
    private_channels = []
    for input_channel in input_channel_models:
        if input_channel.channel in public_channels_config.channels:
            public_channels.append(input_channel)
        elif input_channel.channel in business_channels_config.channels:
            business_channels.append(input_channel)
        elif input_channel.channel in private_channels_config.channels:
            private_channels.append(input_channel)
        else:
            raise Exception(f"Channel {input_channel.channel} not found in available channels")

    public_params = [channel.model_dump() for channel in public_channels]
    business_params = [channel.model_dump() for channel in business_channels]
    private_params = [channel.model_dump() for channel in private_channels]

    if public_params:
        print(f"Subscribing to public channels: {public_params}")
        await public_client.start()
        await public_client.subscribe(params=public_params, callback=public_callback)
    if business_params:
        print(f"Subscribing to business channels: {business_params}")
        await business_client.start()
        await business_client.subscribe(params=business_params, callback=public_callback)
    if private_params:
        print(f"Subscribing to private channels: {private_params}")
        await private_client.start()
        await private_client.subscribe(params=private_params, callback=public_callback)
    # Keep the loop running, or perform other tasks
    try:
        while True:
            await asyncio.sleep(2)  # Adjust the sleep duration as needed
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Exception: {e}")
    finally:
        await public_client.stop()
        await business_client.stop()
        await private_client.stop()


# Run the main coroutine
input_channel_models = [
    ### Public Channels
    InstrumentsChannelInputArgs(channel="instruments", instType="FUTURES"),
    PriceLimitChannelInputArgs(channel="price-limit", instId="BTC-USDT-240628"),
    MarkPriceChannelInputArgs(channel="mark-price", instId="BTC-USDT-240628"),
    IndexTickersChannelInputArgs(
        # Index with USD, USDT, BTC, USDC as the quote currency, e.g. BTC-USDT, e.g. not BTC-USDT-240628
        channel="index-tickers", instId="BTC-USDT"),

    ### Business Channels
    MarkPriceCandleSticksChannelInputArgs(channel="mark-price-candle1m", instId="BTC-USDT-240628"),
    IndexCandleSticksChannelInputArgs(channel="index-candle1m", instId="BTC-USDT"),

    ### Private Channels
    AccountChannelInputArgs(channel="account", ccy="BTC"),
    PositionChannelInputArgs(channel="positions", instType="FUTURES",
                             instFamily="BTC-USDT",
                             instId="BTC-USDT-240628"),
    BalanceAndPositionsChannelInputArgs(channel="balance_and_position")

]

asyncio.run(websockets_main_run(input_channel_models))
