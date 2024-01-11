import asyncio
import json
import os

import dotenv

from pyokx.ws_clients.WsPprivateAsync import WsPrivateAsync
from pyokx.ws_clients.WsPublicAsync import WsPublicAsync
from pyokx.ws_data_structures import PositionChannelInputArgs, InstrumentsChannelInputArgs, PriceLimitChannelInputArgs, \
    MarkPriceChannelInputArgs, IndexTickersChannelInputArgs, MarkPriceCandleSticksChannelInputArgs, \
    IndexCandleSticksChannelInputArgs, BalanceAndPositionsChannelInputArgs, PriceLimitChannel, InstrumentsChannel, \
    MarkPriceChannel, IndexTickersChannel, MarkPriceCandleSticksChannel, IndexCandleSticksChannel, AccountChannel, \
    PositionChannel, BalanceAndPositionsChannel, AccountChannelInputArgs, WebSocketConnectionConfig

# # Initialize FastAPI app
# app = FastAPI()

# # Initialize Redis client
# redis = aioredis.from_url("redis://localhost", encoding="utf-8", decode_responses=True)
import redis

OKX_WEBSOCKET_URLS = dict(
    public="wss://ws.okx.com:8443/ws/v5/public",
    private="wss://ws.okx.com:8443/ws/v5/private",
    business="wss://ws.okx.com:8443/ws/v5/business",
    public_aws="wss://wsaws.okx.com:8443/ws/v5/public",
    private_aws="wss://wsaws.okx.com:8443/ws/v5/private",
    business_aws="wss://wsaws.okx.com:8443/ws/v5/business",
    public_demo="wss://wspap.okx.com:8443/ws/v5/public?brokerId=9999",
    private_demo="wss://wspap.okx.com:8443/ws/v5/private?brokerId=9999",
    business_demo="wss://wspap.okx.com:8443/ws/v5/business?brokerId=9999",
)


async def okx_websockets_main_run(input_channel_models: list,
                                  apikey: str = None, passphrase: str = None, secretkey: str = None,
                                  sandbox_mode: bool = True):
    if not input_channel_models:
        raise Exception("No channels provided")

    public_channels_config = WebSocketConnectionConfig(
        wss_url=OKX_WEBSOCKET_URLS["public"] if not sandbox_mode else OKX_WEBSOCKET_URLS["public_demo"],
        channels={
            "price-limit": PriceLimitChannel,
            "instruments": InstrumentsChannel,
            "mark-price": MarkPriceChannel,
            "index-tickers": IndexTickersChannel,
        }
    )
    business_channels_config = WebSocketConnectionConfig(
        wss_url=OKX_WEBSOCKET_URLS["business"] if not sandbox_mode else OKX_WEBSOCKET_URLS["business_demo"],
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
        wss_url=OKX_WEBSOCKET_URLS["private"] if not sandbox_mode else OKX_WEBSOCKET_URLS["private_demo"],
        channels={
            "account": AccountChannel,  # Missing coinUsdPrice
            "positions": PositionChannel,  # Missing pTime
            "balance_and_position": BalanceAndPositionsChannel,
        }
    )

    available_channel_models = public_channels_config.channels | business_channels_config.channels | private_channels_config.channels

    def ws_callback(message):
        message_data = json.loads(message)
        event = message_data.get("event", None)

        if event:
            if event == "error":
                print(f"Error: {message_data}")
                return  # TODO: Handle events, mostly subscribe and error
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
            return  # TODO: Handle exceptions

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
        public_client = WsPublicAsync(url=public_channels_config.wss_url)
        print(f"Subscribing to public channels: {public_params}")
        await public_client.start()
        await public_client.subscribe(params=public_params, callback=ws_callback)
    if business_params:
        business_client = WsPublicAsync(url=business_channels_config.wss_url)
        print(f"Subscribing to business channels: {business_params}")
        await business_client.start()
        await business_client.subscribe(params=business_params, callback=ws_callback)
    if private_params:
        assert apikey, f"API key was not provided"
        assert secretkey, f"API secret key was not provided"
        assert passphrase, f"Passphrase was not provided"

        private_client = WsPrivateAsync(apikey=apikey, passphrase=passphrase, secretkey=secretkey,
                                        url=private_channels_config.wss_url, use_servertime=False)
        print(f"Subscribing to private channels: {private_params}")
        await private_client.start()
        await private_client.subscribe(params=private_params, callback=ws_callback)

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


if __name__ == '__main__':
    # ticker = get_ticker_with_higher_volume('BTC-USDT')
    # instId = ticker.instId
    # instType = ticker.instType
    instId = "BTC-USDT-240329"
    instType = "FUTURES"
    #
    instId_split = instId.split("-")
    instFamily = "-".join(instId_split[:-1])
    ccy = instId_split[0]

    dotenv.load_dotenv(dotenv.find_dotenv())

    # Run the main coroutine with asyncio
    asyncio.run(okx_websockets_main_run(
        apikey=os.getenv('OKX_API_KEY'),
        passphrase=os.getenv('OKX_PASSPHRASE'),
        secretkey=os.getenv('OKX_SECRET_KEY'),
        sandbox_mode=os.getenv('OKX_SANDBOX_MODE', True),
        input_channel_models=[
            # ### Public Channels
            # InstrumentsChannelInputArgs(channel="instruments", instType=instType),
            # PriceLimitChannelInputArgs(channel="price-limit", instId=instId),
            # MarkPriceChannelInputArgs(channel="mark-price", instId=instId),
            # IndexTickersChannelInputArgs(
            #     # Index with USD, USDT, BTC, USDC as the quote currency, e.g. BTC-USDT, e.g. not BTC-USDT-240628
            #     channel="index-tickers", instId=instFamily),
            #
            # ### Business Channels
            # MarkPriceCandleSticksChannelInputArgs(channel="mark-price-candle1m", instId=instId),
            # IndexCandleSticksChannelInputArgs(channel="index-candle1m", instId=instFamily),

            ### Private Channels
            # AccountChannelInputArgs(channel="account", ccy=ccy),
            PositionChannelInputArgs(channel="positions", instType=instType,
                                     instFamily=instFamily,
                                     instId=instId),
            BalanceAndPositionsChannelInputArgs(channel="balance_and_position")
        ]
    ))
