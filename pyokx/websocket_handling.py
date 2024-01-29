import asyncio
import json
import os
from pprint import pprint

import dotenv

from pyokx.okx_market_maker.market_data_service.WssMarketDataService import on_orderbook_snapshot_or_update
from pyokx.okx_market_maker.market_data_service.model.OrderBook import OrderBook
from pyokx.signal_handling import get_ticker_with_higher_volume
from pyokx.ws_clients.WsPprivateAsync import WsPrivateAsync
from pyokx.ws_clients.WsPublicAsync import WsPublicAsync
from pyokx.ws_data_structures import PriceLimitChannel, InstrumentsChannel, \
    MarkPriceChannel, IndexTickersChannel, MarkPriceCandleSticksChannel, IndexCandleSticksChannel, AccountChannel, \
    PositionChannel, BalanceAndPositionsChannel, WebSocketConnectionConfig, OrdersChannel, OrderBookChannel, \
    TickersChannel, IndexTickersChannelInputArgs, OrderBookInputArgs, MarkPriceChannelInputArgs, \
    TickersChannelInputArgs, OrdersChannelInputArgs, OKX_WEBSOCKET_URLS, public_channels_available, \
    business_channels_available, private_channels_available, available_channel_models
from redis_tools.utils import serialize_for_redis, connect_to_aioredis, connect_to_redis, _deserialize_from_redis

REDIS_STREAM_MAX_LEN = int(os.getenv('REDIS_STREAM_MAX_LEN', 1000))

async def okx_websockets_main_run(input_channel_models: list,
                                  apikey: str = None, passphrase: str = None, secretkey: str = None,
                                  sandbox_mode: bool = True, redis_store: bool = True):
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
        async_redis = await connect_to_aioredis()
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
                redis_ready_message = serialize_for_redis(structured_message.model_dump())
                await async_redis.xadd(f'okx:messages@{message_channel}', redis_ready_message,
                                       maxlen=REDIS_STREAM_MAX_LEN)
                await async_redis.xadd(f'okx:messages@all', redis_ready_message,
                                       maxlen=REDIS_STREAM_MAX_LEN)

                ''' (ALPHA)
                ----------------------------------------------------
                Handle supported channels data 
                (can be moved to listen to the redistributed redis channel -from-above-)
                e.g. 
                    message = _deserialize_from_redis(r.xrevrange('okx:messages@account', count=1)[0][1])
                    account: Account = on_account(incoming_account_message)
                    redis_ready_message = serialize_for_redis(account.to_dict())
                    r.xadd(f'okx:reports@{message.get("arg").get("channel")}', redis_ready_message, maxlen=1000)
                ----------------------------------------------------
                '''
                # await handle_reports(message_json, async_redis) # todo re-enable reports


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
            await asyncio.sleep(1)
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


async def handle_reports(message_json, async_redis, structured_message=None):
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
        await async_redis.xadd(f'okx:reports@{message_channel}', redis_ready_message,
                               maxlen=REDIS_STREAM_MAX_LEN)
    if message_channel == "account":
        from pyokx.okx_market_maker.position_management_service.WssPositionManagementService import \
            on_account
        from pyokx.okx_market_maker.position_management_service.model.Account import Account
        account: Account = on_account(message_json)
        redis_ready_message = serialize_for_redis(account.to_dict())
        await async_redis.xadd(f'okx:reports@{message_channel}', redis_ready_message,
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
        await async_redis.xadd(f'okx:reports@{message_channel}',
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
        await async_redis.xadd(f'okx:reports@{message_channel}@{message_args.get("instId")}',
                               redis_ready_message,
                               maxlen=REDIS_STREAM_MAX_LEN)

    if message_channel == "tickers":
        from pyokx.okx_market_maker.market_data_service.WssMarketDataService import on_ticker_update
        from pyokx.okx_market_maker.market_data_service.model.Tickers import Tickers
        tickers: Tickers = on_ticker_update(message_json)
        redis_ready_message = serialize_for_redis(tickers.to_dict())
        await async_redis.xadd(f'okx:reports@{message_channel}',
                               redis_ready_message,
                               maxlen=REDIS_STREAM_MAX_LEN)

    if message_channel == "index-tickers":
        await async_redis.xadd(f'okx:reports@{message_channel}@{message_args.get("instId")}',
                               serialize_for_redis(structured_message.model_dump()),
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


def testout():
    r = connect_to_redis()

    incoming_message = {'arg': {'channel': 'account', 'uid': '452871299048588011'}, 'data': [
        {'adjEq': '', 'borrowFroz': '', 'details': [
            {'availBal': '1', 'availEq': '1', 'borrowFroz': '', 'cashBal': '1', 'ccy': 'BTC', 'coinUsdPrice': '42630.1',
             'crossLiab': '', 'disEq': '42630.1', 'eq': '1', 'eqUsd': '42630.1', 'fixedBal': '0', 'frozenBal': '0',
             'imr': '0', 'interest': '', 'isoEq': '0', 'isoLiab': '', 'isoUpl': '0', 'liab': '', 'maxLoan': '',
             'mgnRatio': '', 'mmr': '0', 'notionalLever': '0', 'ordFrozen': '0', 'spotInUseAmt': '', 'spotIsoBal': '0',
             'stgyEq': '0', 'twap': '0', 'uTime': '1703639691142', 'upl': '0', 'uplLiab': ''},
            {'availBal': '100', 'availEq': '100', 'borrowFroz': '', 'cashBal': '100', 'ccy': 'OKB',
             'coinUsdPrice': '54.92', 'crossLiab': '', 'disEq': '5217.4', 'eq': '100', 'eqUsd': '5492', 'fixedBal': '0',
             'frozenBal': '0', 'imr': '0', 'interest': '', 'isoEq': '0', 'isoLiab': '', 'isoUpl': '0', 'liab': '',
             'maxLoan': '', 'mgnRatio': '', 'mmr': '0', 'notionalLever': '0', 'ordFrozen': '0', 'spotInUseAmt': '',
             'spotIsoBal': '0', 'stgyEq': '0', 'twap': '0', 'uTime': '1703639691152', 'upl': '0', 'uplLiab': ''},
            {'availBal': '4879.1068088', 'availEq': '4879.1068088', 'borrowFroz': '', 'cashBal': '4879.1068088',
             'ccy': 'USDT', 'coinUsdPrice': '0.99957', 'crossLiab': '', 'disEq': '4877.008792872216',
             'eq': '4879.1068088', 'eqUsd': '4877.008792872216', 'fixedBal': '0', 'frozenBal': '0', 'imr': '0',
             'interest': '', 'isoEq': '0', 'isoLiab': '', 'isoUpl': '0', 'liab': '', 'maxLoan': '', 'mgnRatio': '',
             'mmr': '0', 'notionalLever': '0', 'ordFrozen': '0', 'spotInUseAmt': '', 'spotIsoBal': '0', 'stgyEq': '0',
             'twap': '0', 'uTime': '1705451890859', 'upl': '0', 'uplLiab': ''},
            {'availBal': '1', 'availEq': '1', 'borrowFroz': '', 'cashBal': '1', 'ccy': 'ETH', 'coinUsdPrice': '2531.68',
             'crossLiab': '', 'disEq': '2531.68', 'eq': '1', 'eqUsd': '2531.68', 'fixedBal': '0', 'frozenBal': '0',
             'imr': '0', 'interest': '', 'isoEq': '0', 'isoLiab': '', 'isoUpl': '0', 'liab': '', 'maxLoan': '',
             'mgnRatio': '', 'mmr': '0', 'notionalLever': '0', 'ordFrozen': '0', 'spotInUseAmt': '', 'spotIsoBal': '0',
             'stgyEq': '0', 'twap': '0', 'uTime': '1703639691162', 'upl': '0', 'uplLiab': ''}], 'imr': '', 'isoEq': '0',
         'mgnRatio': '', 'mmr': '', 'notionalUsd': '', 'ordFroz': '', 'totalEq': '55530.78879287221',
         'uTime': '1705522902915', 'upl': ''}]}

    '''Incoming Message:'''
    message_args = incoming_message.get("arg")
    message_channel = message_args.get("channel")
    structured_message = AccountChannel(**incoming_message)
    print(f"Received Data: {structured_message}")
    redis_ready_message = serialize_for_redis(structured_message.model_dump())
    r.xadd(f'okx:messages@{message_channel}', redis_ready_message, maxlen=1000)

    '''Handle Data Type Specific Channels:'''
    incoming_account_message = _deserialize_from_redis(r.xrevrange('okx:messages@account', count=1)[0][1])

    message_args = incoming_account_message.get("arg")
    message_channel = message_args.get("channel")

    # Use the incoming_account_message for the account report channel
    from pyokx.okx_market_maker.position_management_service.WssPositionManagementService import \
        on_account
    from pyokx.okx_market_maker.position_management_service.model.Account import Account

    account: Account = on_account(incoming_account_message)
    redis_ready_message = serialize_for_redis(account.to_dict())
    r.xadd(f'okx:reports@{message_channel}', redis_ready_message, maxlen=1000)

    '''Intake Data from Redis:'''
    account_report_serialized = r.xrevrange('okx:reports@account', count=1)[0][1]
    print(f'{account_report_serialized = }')

    account_report_deserialized = _deserialize_from_redis(account_report_serialized)
    print(f'{account_report_deserialized = }')

    account: Account = Account().from_dict(account_dict=account_report_deserialized)
    print(f'{account = }')

    exit()


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
                # PositionChannelInputArgs(channel="positions", instType="ANY", instFamily=None,
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
