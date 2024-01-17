import asyncio
import json
import os

import dotenv

from pyokx.okx_market_maker.market_data_service.WssMarketDataService import on_orderbook_snapshot_or_update
from pyokx.okx_market_maker.market_data_service.model.OrderBook import OrderBook
from pyokx.signal_handling import get_ticker_with_higher_volume
from pyokx.ws_clients.WsPprivateAsync import WsPrivateAsync
from pyokx.ws_clients.WsPublicAsync import WsPublicAsync
from pyokx.ws_data_structures import PriceLimitChannel, InstrumentsChannel, \
    MarkPriceChannel, IndexTickersChannel, MarkPriceCandleSticksChannel, IndexCandleSticksChannel, AccountChannel, \
    PositionChannel, BalanceAndPositionsChannel, WebSocketConnectionConfig, OrdersChannel, OrderBookChannel, \
    MarkPriceChannelInputArgs, TickersChannelInputArgs, TickersChannel, OrderBookInputArgs, AccountChannelInputArgs, \
    PositionChannelInputArgs, BalanceAndPositionsChannelInputArgs, OrdersChannelInputArgs
from redis_tools.utils import serialize_for_redis, connect_to_aioredis

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
                                  sandbox_mode: bool = True, redis_store: bool = True):
    if not input_channel_models:
        raise Exception("No channels provided")

    public_channels_config = WebSocketConnectionConfig(
        name='okx_public',
        wss_url=OKX_WEBSOCKET_URLS["public"] if not sandbox_mode else OKX_WEBSOCKET_URLS["public_demo"],
        channels={
            "price-limit": PriceLimitChannel,
            "instruments": InstrumentsChannel,
            "mark-price": MarkPriceChannel,
            "index-tickers": IndexTickersChannel,
            "tickers": TickersChannel,
            "books5": OrderBookChannel,
            "books": OrderBookChannel,
            "bbo-tbt": OrderBookChannel,
            "books50-l2-tbt": OrderBookChannel,
            "books-l2-tbt": OrderBookChannel,
        }
    )
    business_channels_config = WebSocketConnectionConfig(
        name='okx_business',
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
        name='okx_private',
        wss_url=OKX_WEBSOCKET_URLS["private"] if not sandbox_mode else OKX_WEBSOCKET_URLS["private_demo"],
        channels={
            "account": AccountChannel,  # Missing coinUsdPrice
            "positions": PositionChannel,  # Missing pTime
            "balance_and_position": BalanceAndPositionsChannel,
            "orders": OrdersChannel
        }
    )

    available_channel_models: WebSocketConnectionConfig.channels = (
            public_channels_config.channels | business_channels_config.channels | private_channels_config.channels
    )
    if redis_store:
        async_redis = await connect_to_aioredis()
    else:
        async_redis = None

    async def ws_callback(message):
        message_json = json.loads(message)
        event = message_json.get("event", None)

        if event:
            if event == "error":
                print(f"Error: {message_json}")
                return  # TODO: Handle events, mostly subscribe and error
            print(f"Event: {message_json}")
            return  # TODO: Handle events, mostly subscribe and error

        try:
            '''
            ----------------------------------------------------
            Send out the Supported Models to their messages stream channel 
            (verifies the channel message has a pydantic model)
            ----------------------------------------------------
            '''
            message_args = message_json.get("arg")
            message_channel = message_args.get("channel")

            data_struct = available_channel_models[message_channel]
            if hasattr(data_struct, "from_array"):  # only applicatble to a few scenarios with candlesticks
                structured_message = data_struct.from_array(**message_json)
            else:
                structured_message = data_struct(**message_json)
            print(f"Received Data: {structured_message}")

            if redis_store and async_redis:
                redis_ready_message = serialize_for_redis(structured_message.model_dump())
                await async_redis.xadd(f'okx:messages@{message_channel}', redis_ready_message, maxlen=1000)

                '''
                ----------------------------------------------------
                Handle supported channels data (can be moved to listen to the redistributed redis channel -from-above-)
                ----------------------------------------------------
                '''

                # Position Management Service
                if message_channel == "balance_and_position":
                    from pyokx.okx_market_maker.position_management_service.WssPositionManagementService import \
                        on_balance_and_position
                    from pyokx.okx_market_maker.position_management_service.model.BalanceAndPosition import \
                        BalanceAndPosition
                    balance_and_position: BalanceAndPosition = on_balance_and_position(message_json)
                    redis_ready_message = serialize_for_redis(balance_and_position.to_dict())
                    await async_redis.xadd(f'okx:{message_channel}', redis_ready_message, maxlen=1000)
                if message_channel == "account":
                    from pyokx.okx_market_maker.position_management_service.WssPositionManagementService import \
                        on_account
                    from pyokx.okx_market_maker.position_management_service.model.Account import Account
                    account: Account = on_account(message_json)
                    redis_ready_message = serialize_for_redis(account.to_dict())
                    await async_redis.xadd(f'okx:{message_channel}', redis_ready_message, maxlen=1000)
                if message_channel == "positions":
                    from pyokx.okx_market_maker.position_management_service.WssPositionManagementService import \
                        on_position
                    from pyokx.okx_market_maker.position_management_service.model.Positions import Positions
                    positions: Positions = on_position(message_json)
                    redis_ready_message = serialize_for_redis(positions.to_dict())
                    await async_redis.xadd(f'okx:{message_channel}', redis_ready_message, maxlen=1000)

                # Order Management Service
                if message_channel == "orders":
                    from pyokx.okx_market_maker.order_management_service.WssOrderManagementService import \
                        on_orders_update
                    from pyokx.okx_market_maker.order_management_service.model.Order import Orders
                    orders: Orders = on_orders_update(message_json)
                    redis_ready_message = serialize_for_redis(orders.to_dict())
                    await async_redis.xadd(f'okx:{message_channel}', redis_ready_message, maxlen=1000)

                # Market Data Service
                if message_channel in ["books5", "books", "bbo-tbt", "books50-l2-tbt", "books-l2-tbt"]:
                    books: OrderBook = on_orderbook_snapshot_or_update(message_json)
                    redis_ready_message = serialize_for_redis(books.to_dict())
                    await async_redis.xadd(f'okx:{message_channel}@{message_args.get("instId")}', redis_ready_message,
                                           maxlen=1000)

                if message_channel == "mark-price":
                    from pyokx.okx_market_maker.market_data_service.WssMarketDataService import on_mark_price_update
                    from pyokx.okx_market_maker.market_data_service.model.MarkPx import MarkPxCache
                    mark_px: MarkPxCache = on_mark_price_update(message_json)
                    redis_ready_message = serialize_for_redis(mark_px.to_dict())
                    await async_redis.xadd(f'okx:{message_channel}@{message_args.get("instId")}', redis_ready_message,
                                           maxlen=1000)

                if message_channel == "tickers":
                    from pyokx.okx_market_maker.market_data_service.WssMarketDataService import on_ticker_update
                    from pyokx.okx_market_maker.market_data_service.model.Tickers import Tickers
                    tickers: Tickers = on_ticker_update(message_json)
                    redis_ready_message = serialize_for_redis(tickers.to_dict())
                    await async_redis.xadd(f'okx:{message_channel}@{message_args.get("instId")}', redis_ready_message,
                                           maxlen=1000)


        except Exception as e:
            print(f"Exception: {e} \n {message_json}")
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

    public_client = None
    business_client = None
    private_client = None
    if public_params:
        public_client = WsPublicAsync(url=public_channels_config.wss_url, callback=ws_callback)
        print(f"Subscribing to public channels: {public_params}")
        await public_client.start()
        await public_client.subscribe(params=public_params)
    if business_params:
        business_client = WsPublicAsync(url=business_channels_config.wss_url, callback=ws_callback)
        print(f"Subscribing to business channels: {business_params}")
        await business_client.start()
        await business_client.subscribe(params=business_params)
    if private_params:
        assert apikey, f"API key was not provided"
        assert secretkey, f"API secret key was not provided"
        assert passphrase, f"Passphrase was not provided"

        private_client = WsPrivateAsync(apikey=apikey, passphrase=passphrase, secretkey=secretkey,
                                        url=private_channels_config.wss_url, use_servertime=False, callback=ws_callback)
        print(f"Subscribing to private channels: {private_params}")
        await private_client.start()
        await private_client.subscribe(params=private_params)

    # Keep the loop running, or perform other tasks
    try:
        while True:
            await asyncio.sleep(2)  # Adjust the sleep duration as needed
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Exception: {e}")
    finally:
        if public_client:
            try:
                if public_params:
                    await public_client.unsubscribe(params=public_params)
                await public_client.stop()
            except Exception as e:
                print(f"Exception: {e}")
        if business_client:
            try:
                if business_params:
                    await business_client.unsubscribe(params=business_params)
                await business_client.stop()
            except Exception as e:
                print(f"Exception: {e}")
        if private_client:
            try:
                if private_params:
                    await private_client.unsubscribe(params=private_params)
                await private_client.stop()
            except Exception as e:
                print(f"Exception: {e}")
        if redis_store and async_redis:
            try:
                await async_redis.close()
            except Exception as e:
                print(f"Exception: {e}")
        print("Exiting")


if __name__ == '__main__':
    dotenv.load_dotenv(dotenv.find_dotenv())

    # from pyokx.signal_handling import get_ticker_with_higher_volume
    btc_ = get_ticker_with_higher_volume("BTC-USDT",
                                         instrument_type="FUTURES",
                                         top_n=2)
    eth_ = get_ticker_with_higher_volume("ETH-USDT",
                                         instrument_type="FUTURES",
                                         top_n=2)
    ltc = get_ticker_with_higher_volume("LTC-USDT",
                                        instrument_type="FUTURES",
                                        top_n=2)

    instruments_to_listen_to = btc_ + eth_ + ltc
    instrument_specific_channels = []

    for instrument in instruments_to_listen_to:
        instrument_specific_channels.append(OrderBookInputArgs(channel="books5", instId=instrument.instId))
        instrument_specific_channels.append(OrderBookInputArgs(channel="books", instId=instrument.instId))
        instrument_specific_channels.append(OrderBookInputArgs(channel="bbo-tbt", instId=instrument.instId))
        instrument_specific_channels.append(MarkPriceChannelInputArgs(channel="mark-price", instId=instrument.instId))
        instrument_specific_channels.append(TickersChannelInputArgs(channel="tickers", instId=instrument.instId))

    input_channel_models = [
                               ### Business Channels
                               # MarkPriceCandleSticksChannelInputArgs(channel="mark-price-candle1m", instId=instId),
                               # IndexCandleSticksChannelInputArgs(channel="index-candle1m", instId=instFamily),

                               ### Public Channels
                               # # InstrumentsChannelInputArgs(channel="instruments", instType="FUTURES"), # todo handle data
                               # PriceLimitChannelInputArgs(channel="price-limit", instId=instId),# todo handle data
                               # IndexTickersChannelInputArgs( # todo handle data
                               #     # Index with USD, USDT, BTC, USDC as the quote currency, e.g. BTC-USDT, e.g. not BTC-USDT-240628
                               #     channel="index-tickers", instId=instFamily),

                               ### Private Channels
                               AccountChannelInputArgs(channel="account", ccy=None),
                               PositionChannelInputArgs(channel="positions", instType="ANY", instFamily=None,
                                                        instId=None),
                               BalanceAndPositionsChannelInputArgs(channel="balance_and_position"),
                               OrdersChannelInputArgs(channel="orders", instType="FUTURES", instFamily=None,
                                                      instId=None)
                           ] + instrument_specific_channels

    asyncio.run(okx_websockets_main_run(input_channel_models=input_channel_models,
                                        apikey=os.getenv('OKX_API_KEY'), passphrase=os.getenv('OKX_PASSPHRASE'),
                                        secretkey=os.getenv('OKX_SECRET_KEY'),
                                        sandbox_mode=os.getenv('OKX_SANDBOX_MODE', True),
                                        redis_store=True
                                        )
                )
