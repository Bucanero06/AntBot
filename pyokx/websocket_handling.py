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
import os
from pprint import pprint

import dotenv

from pyokx.okx_market_maker.market_data_service.WssMarketDataService import on_orderbook_snapshot_or_update
from pyokx.okx_market_maker.market_data_service.model.OrderBook import OrderBook
from pyokx.rest_handling import get_ticker_with_higher_volume
from pyokx.ws_clients.WsPprivateAsync import WsPrivateAsync
from pyokx.ws_clients.WsPublicAsync import WsPublicAsync
from pyokx.ws_data_structures import PriceLimitChannel, InstrumentsChannel, \
    MarkPriceChannel, IndexTickersChannel, MarkPriceCandleSticksChannel, IndexCandleSticksChannel, AccountChannel, \
    PositionsChannel, BalanceAndPositionsChannel, WebSocketConnectionConfig, OrdersChannel, OrderBookChannel, \
    TickersChannel, IndexTickersChannelInputArgs, OrderBookInputArgs, MarkPriceChannelInputArgs, \
    TickersChannelInputArgs, OrdersChannelInputArgs, OKX_WEBSOCKET_URLS, public_channels_available, \
    business_channels_available, private_channels_available, available_channel_models
from redis_tools.utils import serialize_for_redis, init_async_redis

REDIS_STREAM_MAX_LEN = int(os.getenv('REDIS_STREAM_MAX_LEN', 1000))

async def okx_websockets_main_run(input_channel_models: list,
                                  apikey: str = None, passphrase: str = None, secretkey: str = None,
                                  sandbox_mode: bool = True, redis_store: bool = True):
    print(f"Starting OKX Websocket Connections ")
    if not input_channel_models:
        raise Exception("No channels provided")

    public_channels_config = WebSocketConnectionConfig(
        name='okx_public',
        wss_url=OKX_WEBSOCKET_URLS["public"] if not sandbox_mode else OKX_WEBSOCKET_URLS["public_demo"],
        channels=public_channels_available
    )
    business_channels_config = WebSocketConnectionConfig(
        name='okx_business',
        wss_url=OKX_WEBSOCKET_URLS["business"] if not sandbox_mode else OKX_WEBSOCKET_URLS["business_demo"],
        channels=business_channels_available
    )

    private_channels_config = WebSocketConnectionConfig(
        name='okx_private',
        wss_url=OKX_WEBSOCKET_URLS["private"] if not sandbox_mode else OKX_WEBSOCKET_URLS["private_demo"],
        channels=private_channels_available
    )

    if redis_store:
        async_redis = await init_async_redis()
    else:
        async_redis = None

    async def ws_callback(message):
        message_json = json.loads(message)
        event = message_json.get("event", None)
        print(f"Incoming Raw WS Message: {message_json}")
        if event:
            if event == "error":
                print(f"Error: {message_json}")
                return  # TODO: Handle events, mostly subscribe and error stop and reconnect task
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
            print(f"Received Structured-Data: {structured_message}")

            if redis_store and async_redis:
                redis_ready_message = serialize_for_redis(structured_message)
                await async_redis.xadd(f'okx:websockets@{message_channel}', {'data': redis_ready_message},
                                       maxlen=REDIS_STREAM_MAX_LEN)
                await async_redis.xadd(f'okx:websockets@all', {'data': redis_ready_message},
                                       maxlen=REDIS_STREAM_MAX_LEN)

                ''' (ALPHA)
                ----------------------------------------------------
                Handle supported channels data 
                (can be moved to listen to the redistributed redis channel -from-above-)
                e.g. 
                    message = _deserialize_from_redis(r.xrevrange('okx:websockets@account', count=1)[0][1])
                    account: Account = on_account(incoming_account_message)
                    redis_ready_message = serialize_for_redis(account.to_dict())
                    r.xadd(f'okx:reports@{message.get("arg").get("channel")}', redis_ready_message, maxlen=1000)
                ----------------------------------------------------
                '''

                if message_channel == "index-tickers":
                    await async_redis.xadd(f'okx:websockets@{message_channel}@{message_args.get("instId")}',
                                           {'data': serialize_for_redis(structured_message)},
                                           maxlen=REDIS_STREAM_MAX_LEN)

                # await handle_reports(message_json, async_redis) # TODO: Handle reports


        except Exception as e:
            print(f"Exception: {e} \n {message_json}")
            return  # TODO: Handle exceptions

    public_channels_inputs = []
    business_channels_inputs = []
    private_channels_inputs = []
    for input_channel in input_channel_models:
        if input_channel.channel in public_channels_config.channels:
            public_channels_inputs.append(input_channel)
        elif input_channel.channel in business_channels_config.channels:
            business_channels_inputs.append(input_channel)
        elif input_channel.channel in private_channels_config.channels:
            private_channels_inputs.append(input_channel)
        else:
            raise Exception(f"Channel {input_channel.channel} not found in available channels")

    public_params = [channel.model_dump() for channel in public_channels_inputs]
    business_params = [channel.model_dump() for channel in business_channels_inputs]
    private_params = [channel.model_dump() for channel in private_channels_inputs]

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
        while True:  # This could be the main loop of the trading strategy or at least for the health checks
            await asyncio.sleep(60)
            print("Heartbeat \n ___________")
            # Print stats for redis
            if redis_store and async_redis:
                print(f"Redis Stats: ")
                # print only the relevant stats that have human in them
                redis_stats = await async_redis.info()
                stats_to_print = {k: v for k, v in redis_stats.items() if "human" in k}
                pprint(stats_to_print)
            print("___________ \n Heartbeat")


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


async def handle_reports(message_json, async_redis):
    message_args = message_json.get("arg")
    message_channel = message_args.get("channel")
    # Position Management Service
    if message_channel == "balance_and_position":
        from pyokx.okx_market_maker.position_management_service.WssPositionManagementService import \
            on_balance_and_position
        from pyokx.okx_market_maker.position_management_service.model.BalanceAndPosition import \
            BalanceAndPosition
        balance_and_position: BalanceAndPosition = on_balance_and_position(message_json)
        redis_ready_message = serialize_for_redis(balance_and_position.to_dict())
        await async_redis.xadd(f'okx:reports@balance_and_position', redis_ready_message,
                               maxlen=REDIS_STREAM_MAX_LEN)
    if message_channel == "account":
        from pyokx.okx_market_maker.position_management_service.WssPositionManagementService import \
            on_account
        from pyokx.okx_market_maker.position_management_service.model.Account import Account
        account: Account = on_account(message_json)
        redis_ready_message = serialize_for_redis(account.to_dict())
        await async_redis.xadd(f'okx:reports@account', redis_ready_message,
                               maxlen=REDIS_STREAM_MAX_LEN)

    if message_channel == "positions":
        from pyokx.okx_market_maker.position_management_service.WssPositionManagementService import \
            on_position
        from pyokx.okx_market_maker.position_management_service.model.Positions import Positions
        positions: Positions = on_position(message_json)
        redis_ready_message = serialize_for_redis(positions.to_dict())
        await async_redis.xadd(f'okx:reports@positions', redis_ready_message, maxlen=REDIS_STREAM_MAX_LEN)

    # Order Management Service
    if message_channel == "orders":
        from pyokx.okx_market_maker.order_management_service.WssOrderManagementService import \
            on_orders_update
        from pyokx.okx_market_maker.order_management_service.model.Order import Orders
        orders: Orders = on_orders_update(message_json)
        redis_ready_message = serialize_for_redis(orders.to_dict())
        await async_redis.xadd(f'okx:reports@orders',
                               redis_ready_message,
                               maxlen=REDIS_STREAM_MAX_LEN)

    # Market Data Service
    if message_channel in ["books5", "books", "bbo-tbt", "books50-l2-tbt", "books-l2-tbt"]:
        books: OrderBook = on_orderbook_snapshot_or_update(message_json)
        redis_ready_message = serialize_for_redis(books.to_dict())
        await async_redis.xadd(f'okx:reports@{message_channel}@{message_args.get("instId")}',
                               redis_ready_message,
                               maxlen=REDIS_STREAM_MAX_LEN)

    if message_channel == "mark-price":
        from pyokx.okx_market_maker.market_data_service.WssMarketDataService import on_mark_price_update
        from pyokx.okx_market_maker.market_data_service.model.MarkPx import MarkPxCache
        mark_px: MarkPxCache = on_mark_price_update(message_json)
        redis_ready_message = serialize_for_redis(mark_px.to_dict())
        await async_redis.xadd(f'okx:reports@mark-price@{message_args.get("instId")}',
                               redis_ready_message,
                               maxlen=REDIS_STREAM_MAX_LEN)

    if message_channel == "tickers":
        from pyokx.okx_market_maker.market_data_service.WssMarketDataService import on_ticker_update
        from pyokx.okx_market_maker.market_data_service.model.Tickers import Tickers
        tickers: Tickers = on_ticker_update(message_json)
        redis_ready_message = serialize_for_redis(tickers.to_dict())
        await async_redis.xadd(f'okx:reports@{tickers}',
                               redis_ready_message,
                               maxlen=REDIS_STREAM_MAX_LEN)


def get_instrument_specific_channel_inputs_to_listen_to():
    btc_ = get_ticker_with_higher_volume("BTC-USDT",
                                         instrument_type="FUTURES",
                                         top_n=1)
    eth_ = get_ticker_with_higher_volume("ETH-USDT",
                                         instrument_type="FUTURES",
                                         top_n=1)
    ltc = get_ticker_with_higher_volume("LTC-USDT",
                                        instrument_type="FUTURES",
                                        top_n=1)

    instruments_to_listen_to = btc_ + eth_ + ltc
    instrument_specific_channels = []

    for instrument in instruments_to_listen_to:
        instrument_specific_channels.append(OrderBookInputArgs(channel="books5", instId=instrument.instId))
        instrument_specific_channels.append(OrderBookInputArgs(channel="books", instId=instrument.instId))
        instrument_specific_channels.append(OrderBookInputArgs(channel="bbo-tbt", instId=instrument.instId))
        instrument_specific_channels.append(MarkPriceChannelInputArgs(channel="mark-price", instId=instrument.instId))
        instrument_specific_channels.append(TickersChannelInputArgs(channel="tickers", instId=instrument.instId))

    return instrument_specific_channels


def get_btc_usdt_usd_index_channel_inputs_to_listen_to():
    return [
        IndexTickersChannelInputArgs(channel="index-tickers", instId="BTC-USDT"),
        IndexTickersChannelInputArgs(channel="index-tickers", instId="BTC-USD")
    ]



async def test_restart(public_client, business_client, private_client):
    clients = [client for client in [public_client, business_client, private_client] if
               hasattr(client, "restart")]
    await asyncio.gather(*[client.restart() for client in clients if client])


if __name__ == '__main__':
    dotenv.load_dotenv(dotenv.find_dotenv())
    instrument_specific_channels = []
    btc_usdt_usd_index_channels = []
    # instrument_specific_channels = get_channel_inputs_to_listen_to()
    # btc_usdt_usd_index_channels = get_btc_usdt_usd_index_channel_inputs_to_listen_to()
    input_channel_models = (
            [
                ### Business Channels
                # MarkPriceCandleSticksChannelInputArgs(channel="mark-price-candle1m", instId=instId),
                # IndexCandleSticksChannelInputArgs(channel="index-candle1m", instId=instFamily),

                ### Public Channels
                # # InstrumentsChannelInputArgs(channel="instruments", instType="FUTURES"), # todo handle data
                # PriceLimitChannelInputArgs(channel="price-limit", instId=instId),# todo handle data
                # IndexTickersChannelInputArgs(
                #     # Index with USD, USDT, BTC, USDC as the quote currency, e.g. BTC-USDT, e.g. not BTC-USDT-240628
                #     channel="index-tickers", instId="BTC-USDT"),
                # IndexTickersChannelInputArgs(
                #     # Index with USD, USDT, BTC, USDC as the quote currency, e.g. BTC-USDT, e.g. not BTC-USDT-240628
                #     channel="index-tickers", instId="BTC-USD"),

                ### Private Channels
                # AccountChannelInputArgs(channel="account", ccy=None),
                # PositionsChannelInputArgs(channel="positions", instType="ANY", instFamily=None,
                #                          instId=None),
                # BalanceAndPositionsChannelInputArgs(channel="balance_and_position"),
                OrdersChannelInputArgs(channel="orders", instType="FUTURES", instFamily=None,
                                       instId=None)
            ] + instrument_specific_channels + btc_usdt_usd_index_channels)

    asyncio.run(okx_websockets_main_run(input_channel_models=input_channel_models,
                                        apikey=os.getenv('OKX_API_KEY'), passphrase=os.getenv('OKX_PASSPHRASE'),
                                        secretkey=os.getenv('OKX_SECRET_KEY'),
                                        # todo/fixme this can differ from the actual trading strategy that is
                                        #  listening to the streams thus watch out
                                        sandbox_mode=os.getenv('OKX_SANDBOX_MODE', True), redis_store=True
                                        )
                )
