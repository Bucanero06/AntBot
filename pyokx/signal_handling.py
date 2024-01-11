import json
import os
import random
import re
import string
from pprint import pprint
from typing import List, Any, Optional, Dict, Union

import dotenv

from pyokx.data_structures import (Order, Cancelled_Order, Order_Placement_Return,
                                   Position, Closed_Position, Ticker,
                                   Algo_Order, Algo_Order_Placement_Return,
                                   AccountBalanceDetails, AccountBalanceData,
                                   AccountConfigData, MaxOrderSizeData, MaxAvailSizeData, Cancelled_Algo_Order,
                                   Instrument, InstType, Orderbook_Snapshot, Bid, Ask,
                                   Simplified_Balance_Details, InstrumentStatusReport,
                                   PremiumIndicatorSignalRequestForm)
from shared.tmp_shared import calculate_tp_stop_prices, calculate_sl_stop_prices, FunctionCall, execute_function_calls

dotenv.load_dotenv(dotenv.find_dotenv())
from pyokx.Futures_Exchange_Client import OKX_Futures_Exchange_Client as OKXClient

okx_client = OKXClient(api_key=os.getenv('OKX_API_KEY'), api_secret=os.getenv('OKX_SECRET_KEY'),
                       passphrase=os.getenv('OKX_PASSPHRASE'), sandbox_mode=os.getenv('OKX_SANDBOX_MODE'))
tradeAPI = okx_client.tradeAPI
marketAPI = okx_client.marketAPI
accountAPI = okx_client.accountAPI
publicAPI = okx_client.publicAPI

DATA_STRUCTURES = [
    Order, Cancelled_Order, Order_Placement_Return,
    Position, Closed_Position, Ticker,
    Algo_Order, Algo_Order_Placement_Return,
    AccountBalanceDetails, AccountBalanceData,
    AccountConfigData, MaxOrderSizeData, MaxAvailSizeData,
    Cancelled_Algo_Order, Instrument, InstType,
    Orderbook_Snapshot, Bid, Ask,
    Simplified_Balance_Details, InstrumentStatusReport
]


def get_request_data(returned_data, target_data_structure):
    # print(f'{returned_data = }')
    if len(returned_data['data']) == 0:
        if returned_data["code"] != '0':
            print(f'{returned_data["code"] = }')
            print(f'{returned_data["msg"] = }')
        return []
    structured_data = []
    for data in returned_data['data']:
        structured_data.append(target_data_structure(**data))
    return structured_data


all_futures_instruments = get_request_data(publicAPI.get_instruments(instType='FUTURES'),
                                           target_data_structure=Instrument)


class InstrumentSearcher:
    def __init__(self, instruments: List[Instrument]):
        """
        InstrumentSearcher is a class that allows you to search for instruments by instId, instType, or underlying

        :param instruments:

        Usage:
        ```
        instrument_searcher = InstrumentSearcher(all_futures_instruments)
        print(f'{instrument_searcher.find_by_instId("BTC-USDT-240329") = }')
        print(f'{instrument_searcher.find_by_type(InstType.FUTURES) = }')
        print(f'{instrument_searcher.find_by_underlying("BTC-USDT") = }')
        print(f'{"BTC-USDT-240329" in instrument_searcher._instrument_map = }')
        ```
        """

        self.instruments = instruments
        self._instrument_map = self._create_map(instruments)

    def _create_map(self, instruments: List[Instrument]) -> Dict[str, Instrument]:
        """ Create a map for quicker search by instId """
        return {instrument.instId: instrument for instrument in instruments}

    def find_by_instId(self, instId: str) -> Optional[Instrument]:
        """ Find an instrument by its instId """
        return self._instrument_map.get(instId)

    def find_by_type(self, instType: InstType) -> List[Instrument]:
        """ Find all instruments of a specific type """
        return [instrument for instrument in self.instruments if instrument.instType == instType]

    def find_by_underlying(self, underlying: str) -> List[Instrument]:
        """ Find all instruments of a specific underlying """
        return [instrument for instrument in self.instruments if instrument.uly == underlying]


instrument_searcher = InstrumentSearcher(all_futures_instruments)


def get_ticker_with_higher_volume(seed_symbol_name):
    print(f'{seed_symbol_name = }')
    print(f'{okx_client.derivative_type = }')

    # raise DeprecationWarning("This function is deprecated. Waiting to update to Structured Data Types.")
    all_positions = okx_client.accountAPI.get_positions(instType=okx_client.derivative_type)
    all_position_symbols = [position['instId'] for position in all_positions['data']]
    tickers_data = okx_client.marketAPI.get_tickers(instType=okx_client.derivative_type)

    # If any tickers data are returned, find the ticker data for the symbol we are trading
    # fixme this is a hack since okx is returning multiple instId's
    _highest_volume = 0
    _highest_volume_ticker = None
    _ticker_data = None
    for ticker_data in tickers_data['data']:
        if ticker_data['instId'] in all_position_symbols:
            _ticker_data = ticker_data
            break
        if seed_symbol_name in ticker_data['instId']:
            print(f'{ticker_data = }')
            vol24 = float(ticker_data['vol24h'])
            if vol24 > _highest_volume:
                _highest_volume = vol24
                _highest_volume_ticker = ticker_data
    ticker_data = _ticker_data or _highest_volume_ticker
    return Ticker(**ticker_data)


def assert_okx_account_level(account_level: [1, 2, 3, 4]):
    raise DeprecationWarning("This function is deprecated. Waiting to update to Structured Data Types.")
    ACCLV_MAPPING = {
        1: "Simple mode",
        2: "Single-currency margin mode",
        3: "Multi-currency margin mode",
        4: "Portfolio margin mode"
    }

    assert account_level in ACCLV_MAPPING.keys(), f"Account level must be one of {ACCLV_MAPPING.keys()}"

    # Set account level
    result_set_account_level = accountAPI.set_account_level(acctLv=2)
    print(result_set_account_level)
    if result_set_account_level['code'] == "0":
        print("Successful request，\n  acctLv = ", result_set_account_level["data"][0]["acctLv"])
    else:
        print("Unsuccessful request，\n  error_code = ", result_set_account_level['code'], ", \n  Error_message = ",
              result_set_account_level["msg"])

    # Get account configuration
    result_get_account_config = accountAPI.get_account_config()

    if result_get_account_config['code'] == "0":
        acctLv = result_get_account_config["data"][0]["acctLv"]
        assert acctLv == account_level, f"Account level was not set to {ACCLV_MAPPING[account_level]}"
    else:
        print("Unsuccessful request，\n  error_code = ", result_get_account_config['code'], ", \n  Error_message = ",
              result_get_account_config["msg"])


def is_valid_alphanumeric(string, max_length):
    """ Validate alphanumeric strings with a maximum length """

    return bool(re.match('^[a-zA-Z0-9]{1,' + str(max_length) + '}$', string))


def try_to_get_request_data(returned_data, data_structures_to_try=DATA_STRUCTURES):
    if len(returned_data['data']) == 0:
        print(f'{returned_data["code"] = }')
        print(f'{returned_data["msg"] = }')
        return []

    for data_struct in data_structures_to_try:
        try:
            print(returned_data['data'][0])

            data_struct(**returned_data['data'][0])
        except Exception as e:
            data_struct = None
        finally:
            if data_struct is not None:
                break
    assert data_struct is not None, f'Could not find a valid data structure for {returned_data["data"][0]}'

    orders_data = []
    for data in returned_data['data']:
        order_data = data_struct(**data)
        orders_data.append(order_data)
    return orders_data


def get_all_orders(instType: str = None, instId: str = None):
    params = {}
    if instType is not None:
        params['instType'] = instType
    if instId is not None:
        params['instId'] = instId
    return get_request_data(tradeAPI.get_order_list(**params), Order)


def cancel_all_orders(orders_list: List[Order] = None, instType: InstType = None, instId: str = None):
    if orders_list is None:
        params = {}
        if instType is not None:
            params['instType'] = instType
        if instId is not None:
            params['instId'] = instId
        orders_list = get_all_orders(**params)
    # cancelled_orders = []
    orders_to_cancel = []
    for order in orders_list:
        orders_to_cancel.append(order)

    # Batch Cancel Orders
    cancelled_orders = get_request_data(tradeAPI.cancel_multiple_orders(
        orders_data=[
            {'instId': order.instId,
             'ordId': order.ordId,
             } for order in orders_to_cancel
        ]
    ), Cancelled_Order)

    #
    return cancelled_orders


def close_position(instId, mgnMode, posSide='', ccy='', autoCxl='', clOrdId='', tag=''):
    params = {'instId': instId, 'mgnMode': mgnMode, 'posSide': posSide, 'ccy': ccy, 'autoCxl': autoCxl,
              'clOrdId': clOrdId, 'tag': tag}
    from pyokx.low_rest_api.consts import CLOSE_POSITION
    from pyokx.low_rest_api.consts import POST
    closed_position_return = tradeAPI._request_with_params(POST, CLOSE_POSITION, params)
    return closed_position_return


def close_all_positions(positions_list: List[Position] = None, instType: InstType = None, instId: str = None):
    if positions_list is None:
        params = {}
        if instType is not None:
            params['instType'] = instType
        if instId is not None:
            params['instId'] = instId
        positions_list = get_all_positions(**params)

    functions_to_execute = []
    for position in positions_list:
        functions_to_execute.append(
            FunctionCall(close_position, instId=position.instId, mgnMode=position.mgnMode,
                         posSide=position.posSide, ccy=position.ccy,
                         autoCxl='true', clOrdId=f'{position.posId}CLOSED',
                         tag='')
        )
    closed_positions_return = execute_function_calls(functions_to_execute)

    closed_positions = []
    for closed_position in closed_positions_return:
        try:
            assert closed_position['code'] == '0', f' {closed_position = }'
            closed_positions.append(get_request_data(closed_position, Closed_Position)[0])
        except AssertionError as e:
            print(e)

    return closed_positions


def get_all_positions(instType: InstType = None, instId: str = None):
    params = {}
    if instType is not None:
        params['instType'] = instType
    if instId is not None:
        params['instId'] = instId
    return get_request_data(accountAPI.get_positions(**params), Position)


def place_order(instId: Any,
                tdMode: Any,
                side: Any,
                ordType: Any,
                sz: Any,
                ccy: str = '',
                clOrdId: str = '',
                tag: str = '',
                posSide: str = '',
                px: str = '',
                reduceOnly: str = '',
                tgtCcy: str = '',
                tpTriggerPx: str = '',
                tpOrdPx: str = '',
                slTriggerPx: str = '',
                slOrdPx: str = '',
                tpTriggerPxType: str = '',
                slTriggerPxType: str = '',
                quickMgnType: str = '',
                stpId: str = '',
                stpMode: str = '',
                algoClOrdId: str = '',
                # This one is commented out because it needs multiple TP's to work and is not
                # developed yet downstream
                # amendPxOnTriggerType: str = ''
                ):
    result = tradeAPI.place_order(
        instId=instId, tdMode=tdMode, side=side, ordType=ordType, sz=sz,
        ccy=ccy, clOrdId=clOrdId, tag=tag, posSide=posSide,
        px=px, reduceOnly=reduceOnly, tgtCcy=tgtCcy,
        tpTriggerPx=tpTriggerPx, tpOrdPx=tpOrdPx,
        slTriggerPx=slTriggerPx, slOrdPx=slOrdPx,
        tpTriggerPxType=tpTriggerPxType, slTriggerPxType=slTriggerPxType,
        quickMgnType=quickMgnType, stpId=stpId, stpMode=stpMode,
        algoClOrdId=algoClOrdId,
        # This one is commented out because it needs multiple TP's to work and is not
        # developed yet downstream
        # amendPxOnTriggerType=amendPxOnTriggerType,

    )

    if result["code"] == "0":
        print("Successful order request，\n  order_id = ", result["data"][0]["ordId"])

    else:
        print(f'{result = }')
        print("Unsuccessful order request，\n  error_code = ", result["msg"], ", \n  Error_message = ",
              result["msg"])
    return get_request_data(result, Order_Placement_Return)[0]


def get_ticker(instId):
    return get_request_data(marketAPI.get_ticker(instId=instId), Ticker)[0]


def get_all_algo_orders(instId=None, ordType=None):
    if ordType is None:
        ORDER_TYPES_TO_TRY = ['trigger', 'oco', 'conditional', 'move_order_stop', 'twap']
    else:
        ORDER_TYPES_TO_TRY = [ordType]

    # orders_fetched = []

    algo_type_to_fetch = []
    for ordType in ORDER_TYPES_TO_TRY:
        params = {'ordType': ordType}
        if instId is not None:
            params['instId'] = instId

        algo_type_to_fetch.append(
            FunctionCall(tradeAPI.order_algos_list, **params)
        )
    orders_fetched_list = execute_function_calls(algo_type_to_fetch)

    print(f'{orders_fetched_list = }')
    orders_fetched = []
    for order_types in orders_fetched_list:
        orders_fetched.extend(get_request_data(order_types, Algo_Order))

    return orders_fetched


def cancel_all_algo_orders_with_params(algo_orders_list: List[Algo_Order] = None, instId=None, ordType=None):
    assert algo_orders_list is None or (
            instId is not None or ordType is not None), f'algo_orders_list or instId must be provided'

    if algo_orders_list is None and (instId is not None or ordType is not None):
        params = {}
        if instId is not None:
            params['instId'] = instId
        if ordType is not None:
            params['ordType'] = ordType
        algo_orders_list = get_all_algo_orders(**params)

    if algo_orders_list is None or len(algo_orders_list) == 0:
        return []

    result = tradeAPI.cancel_algo_order(
        params=[
            {'algoId': algo_order.algoId,
             'instId': algo_order.instId,
             } for algo_order in algo_orders_list
        ]
    )
    print(f'{result = }')
    return get_request_data(result, Cancelled_Algo_Order)


def place_algo_order(
        instId: str = '',
        tdMode: str = '',
        side: str = '',
        ordType: str = '',
        sz: str = '',
        ccy: str = '',
        posSide: str = '',
        reduceOnly: str = '',
        tpTriggerPx: str = '',
        tpOrdPx: str = '',
        slTriggerPx: str = '',
        slOrdPx: str = '',
        triggerPx: str = '',
        orderPx: str = '',
        tgtCcy: str = '',
        pxVar: str = '',
        pxSpread: str = '',
        szLimit: str = '',
        pxLimit: str = '',
        timeInterval: str = '',
        tpTriggerPxType: str = '',
        slTriggerPxType: str = '',
        callbackRatio: str = '',
        callbackSpread: str = '',
        activePx: str = '',
        tag: str = '',
        triggerPxType: str = '',
        closeFraction: str = '',
        quickMgnType: str = '',
        algoClOrdId: str = '',
        cxlOnClosePos: str = ''
):
    result = tradeAPI.place_algo_order(
        # Main Order with TP and SL
        instId=instId,
        tdMode=tdMode,
        side=side,
        ordType=ordType,
        sz=sz,
        ccy=ccy,
        posSide=posSide,
        reduceOnly=reduceOnly,
        tpTriggerPx=tpTriggerPx, tpOrdPx=tpOrdPx, slTriggerPx=slTriggerPx, slOrdPx=slOrdPx, triggerPx=triggerPx,
        orderPx=orderPx, tgtCcy=tgtCcy, pxVar=pxVar, pxSpread=pxSpread, szLimit=szLimit, pxLimit=pxLimit,
        timeInterval=timeInterval, tpTriggerPxType=tpTriggerPxType, slTriggerPxType=slTriggerPxType,
        callbackRatio=callbackRatio, callbackSpread=callbackSpread, activePx=activePx, tag=tag,
        triggerPxType=triggerPxType, closeFraction=closeFraction, quickMgnType=quickMgnType, algoClOrdId=algoClOrdId,
        cxlOnClosePos=cxlOnClosePos
    )
    print(f'{result = }')

    if result["code"] == "0":
        print("Successful order request，\n  order_id = ", result["data"][0]["algoId"])

    else:
        print(f'{result = }')
        print("Unsuccessful order request，\n  error_code = ", result["msg"], ", \n  Error_message = ",
              result["msg"])

    return get_request_data(result, Algo_Order_Placement_Return)


def get_account_balance():
    account_balance = accountAPI.get_account_balance()['data'][0]
    details = account_balance['details']
    structured_details = []
    for detail in details:
        structured_details.append(AccountBalanceDetails(**detail))
    account_balance['details'] = structured_details
    return AccountBalanceData(**account_balance)


def get_account_config():
    return AccountConfigData(**accountAPI.get_account_config()['data'][0])


def get_max_order_size(instId, tdMode):
    return MaxOrderSizeData(**accountAPI.get_max_order_size(instId=instId, tdMode=tdMode)['data'][0])


def get_max_avail_size(instId, tdMode):
    return MaxAvailSizeData(**accountAPI.get_max_avail_size(instId=instId, tdMode=tdMode)['data'][0])


from concurrent.futures import ThreadPoolExecutor


def generate_random_string(length, char_type='alphanumeric'):
    if length > 32:
        raise ValueError("Maximum length allowed is 32")

    if char_type == 'alphanumeric':
        char_set = string.ascii_letters + string.digits
    elif char_type == 'numeric':
        char_set = string.digits
    elif char_type == 'alphabetic':
        char_set = string.ascii_letters
    else:
        raise ValueError("Invalid character type. Choose 'alphanumeric', 'numeric', or 'alphabetic'.")

    return ''.join(random.choices(char_set, k=length))


def fetch_status_report_for_instrument(instId, TD_MODE):
    initial_data_pull = [
        FunctionCall(get_max_order_size, instId=instId, tdMode=TD_MODE),
        FunctionCall(get_max_avail_size, instId=instId, tdMode=TD_MODE),
        FunctionCall(get_all_positions, instId=instId),
        FunctionCall(get_all_orders, instId=instId),
        FunctionCall(get_all_algo_orders, instId=instId),
    ]
    (max_order_size, max_avail_size,
     all_positions, all_orders, all_algo_orders) = execute_function_calls(initial_data_pull)

    return InstrumentStatusReport(
        instId=instId,
        max_order_size=max_order_size,
        max_avail_size=max_avail_size,
        positions=all_positions,
        orders=all_orders,
        algo_orders=all_algo_orders
    )


def fetch_initial_data(TD_MODE, instId=None):
    initial_data_pull = [
        FunctionCall(get_account_balance),
        FunctionCall(get_account_config),
    ]
    (account_balance, account_config) = execute_function_calls(initial_data_pull)

    simplified_balance_details = [
        Simplified_Balance_Details(
            Currency=detail.ccy,
            Available_Balance=detail.availBal,
            Equity=detail.eq,
            Equity_in_USD=detail.eqUsd,
            Frozen_Balance=detail.frozenBal,
        )
        for detail in account_balance.details
    ]

    instrument_status_report = fetch_status_report_for_instrument(instId, TD_MODE)

    return simplified_balance_details, account_config, instrument_status_report


def clear_orders_and_positions_for_instrument(instId):
    print(f'{ close_all_positions(instId=instId) = }')
    print(f'{ cancel_all_orders(instId=instId) = }')
    print(f'{ cancel_all_algo_orders_with_params(instId=instId) = }')


def get_order_book(instId, depth):
    orderbook_return = marketAPI.get_orderbook(instId=instId, sz=depth)
    if orderbook_return['code'] != '0':
        print(f'{orderbook_return = }')
        raise ValueError(f'Could not fetch orderbook for {instId = }')
    data = orderbook_return['data'][0]
    asks = data['asks']
    bids = data['bids']
    ts = data['ts']
    structured_asks = []
    structured_bids = []

    for ask, bid in zip(asks, bids):
        structured_asks.append(Ask(price=ask[0], quantity=ask[1], deprecated_value=ask[2], number_of_orders=ask[3]))
        structured_bids.append(Bid(price=bid[0], quantity=bid[1], deprecated_value=bid[2], number_of_orders=bid[3]))

    return Orderbook_Snapshot(instId=instId, depth=str(depth), ts=ts, asks=structured_asks, bids=structured_bids)


def prepare_limit_price(order_book: Orderbook_Snapshot, quantity: Union[int, float], side, reference_price: float,
                        max_orderbook_price_offset=None,
                        ):
    assert side in ['buy', 'sell']
    limit_price = None

    reference_side = 'asks' if side == 'buy' else 'bids'
    asks_or_bids = order_book.asks if reference_side == 'asks' else order_book.bids

    aggregate_quantity = 0
    for ask_or_bid in asks_or_bids:
        # check that if buy order then skip if reference price is greater than ask price
        # check that if sell order then skip if reference price is less than bid price
        aggregate_quantity += float(ask_or_bid.quantity)

        if (side == 'buy' and reference_price > float(ask_or_bid.price)) or \
                (side == 'sell' and reference_price < float(ask_or_bid.price)):
            continue

        if aggregate_quantity >= quantity:
            print(f"ask_or_bid_price: {ask_or_bid.price}, ask_or_bid_volume: {ask_or_bid.quantity}")

            # Check if the price is within the range we want to place our order
            # get the price offset from the last price
            price_offset = abs(float(ask_or_bid.price) - float(reference_price)) / reference_price
            if (not max_orderbook_price_offset or price_offset <= max_orderbook_price_offset):
                limit_price = float(ask_or_bid.price)
                print(f"{price_offset}% diff between reference price: {reference_price} and and "
                      f"limit price: {limit_price}")
                break
            else:
                raise Exception(
                    f"Computed Limit Price {ask_or_bid.price} is not within the range given by"
                    f" {max_orderbook_price_offset}"
                    f" if you want to remove this check, set max_orderbook_price_offset=False"
                )

    if limit_price is None:
        raise Exception("Could not find a price in the orderbook that has enough volume to cover the quantity")

    return round(limit_price, 2)


def place_algo_trailing_stop_loss(
        instId: str = '',
        tdMode: str = '',
        ordType: str = '',
        side: str = '',
        sz: str = '',
        activePx: str = '',
        posSide: str = '',
        callbackRatio: str = '',
        reduceOnly: str = '',
        algoClOrdId: str = '',
        cxlOnClosePos: str = ''
):
    return place_algo_order(
        instId=instId,
        tdMode=tdMode,
        ordType=ordType,
        side=side,
        sz=sz,
        activePx=activePx,
        posSide=posSide,
        callbackRatio=callbackRatio,
        reduceOnly=reduceOnly,
        algoClOrdId=algoClOrdId,
        cxlOnClosePos=cxlOnClosePos
    )


def clean_and_verify_instID(instID):
    # Clean Input Data
    instID = instID.upper()
    splitted = instID.split('-')
    assert len(splitted) == 3, f'The Futures instrument ID must be in the format of "BTC-USDT-210326". {instID = }'
    instrument = instrument_searcher.find_by_instId(instID)
    assert instrument is not None, f'Instrument {instID} not found in {all_futures_instruments = }'
    assert instrument.instType == InstType.FUTURES, f'{instrument.instType = }'
    return instID


def okx_signal_handler(
        instID: str = '',
        order_size: int = None,
        leverage: int = None,
        order_side: str = '',
        order_type: str = '',
        max_orderbook_limit_price_offset: float = None,
        flip_position_if_opposite_side: bool = False,
        clear_prior_to_new_order: bool = False,
        red_button: bool = False,
        order_usd_amount: float = None,
        stop_loss_trigger_percentage: float = None,
        take_profit_trigger_percentage: float = None,
        tp_trigger_price_type: str = '',
        stop_loss_price_offset: float = None,
        tp_price_offset: float = None,
        sl_trigger_price_type: str = '',
        trailing_stop_activation_percentage: float = None,
        trailing_stop_callback_ratio: float = None,
):
    TD_MODE: str = 'isolated'
    POSSIDETYPE: str = 'net'  # net or long/short, need to cancel all orders/positions to change

    if red_button:
        print(f'{close_all_positions() = }')
        print(f'{cancel_all_orders() = }')
        print(f'{cancel_all_algo_orders_with_params() = }')
        print(f'{get_all_positions() = }')
        print(f'{get_all_orders() = }')
        print(f'{get_all_algo_orders() = }')
        return
    if not instID:
        return None
    # Clean Input Data
    instID = clean_and_verify_instID(instID)

    if order_side:
        (order_type, order_side,
         TD_MODE,
         tp_trigger_price_type, sl_trigger_price_type) = (order_type.lower(), order_side.lower(),
                                                          TD_MODE.lower(), tp_trigger_price_type.lower(),
                                                          sl_trigger_price_type.lower())
        order_size = int(order_size)
        leverage = int(leverage)

        stop_loss_trigger_percentage = False if (
                stop_loss_trigger_percentage == '' or not stop_loss_trigger_percentage) else float(
            stop_loss_trigger_percentage)
        take_profit_trigger_percentage = False if take_profit_trigger_percentage == '' or not take_profit_trigger_percentage else float(
            take_profit_trigger_percentage)
        stop_loss_price_offset = False if stop_loss_price_offset == '' or not stop_loss_price_offset else float(
            stop_loss_price_offset)
        tp_price_offset = False if tp_price_offset == '' or not tp_price_offset else float(
            tp_price_offset)

        trailing_stop_activation_percentage = False if trailing_stop_activation_percentage == '' or not trailing_stop_activation_percentage else float(
            trailing_stop_activation_percentage)
        trailing_stop_callback_ratio = False if trailing_stop_callback_ratio == '' or not trailing_stop_callback_ratio else float(
            trailing_stop_callback_ratio)

        max_orderbook_limit_price_offset = False if max_orderbook_limit_price_offset == '' or max_orderbook_limit_price_offset == 0 or not max_orderbook_limit_price_offset else float(
            max_orderbook_limit_price_offset)

        flip_position_if_opposite_side = False if flip_position_if_opposite_side == '' or not flip_position_if_opposite_side else bool(
            flip_position_if_opposite_side)

        take_profit_activated = None
        stop_loss_activated = None
        trailing_stop_loss_activated = None
        # TODO multiple_tp and amendPxOnTriggerType are commented out because they need multiple TP's to work and is not
        #   developed yet downstream
        #   multiple_tp = None
        #   amendPxOnTriggerType = None
        if take_profit_trigger_percentage or tp_price_offset:
            assert take_profit_trigger_percentage and tp_price_offset
            take_profit_activated = True
            tp_trigger_price_type = tp_trigger_price_type or 'last'

        if stop_loss_trigger_percentage or stop_loss_price_offset:
            assert stop_loss_trigger_percentage and stop_loss_price_offset
            stop_loss_activated = True
            sl_trigger_price_type = sl_trigger_price_type or 'last'

        if trailing_stop_activation_percentage or trailing_stop_callback_ratio:
            assert trailing_stop_callback_ratio, f'trailing_stop_callback_ratio must be provided if trailing_stop_activation_percentage is provided. {trailing_stop_callback_ratio = }'
            trailing_stop_loss_activated = True

        assert TD_MODE in ['isolated', 'crossed'], f'{TD_MODE = }'
        assert order_side in ['buy', 'sell'] or not order_side, (
            f'order_side must be either "buy" or "sell" or empty. \n '
            f'for maintenance mode \n      {order_side = }')

        assert not stop_loss_trigger_percentage or isinstance(stop_loss_trigger_percentage,
                                                              float), f'{stop_loss_trigger_percentage = }'
        assert not take_profit_trigger_percentage or isinstance(take_profit_trigger_percentage,
                                                                float), f'{take_profit_trigger_percentage = }'
        assert not stop_loss_price_offset or isinstance(stop_loss_price_offset, float), f'{stop_loss_price_offset = }'
        assert not tp_price_offset or isinstance(tp_price_offset, float), f'{tp_price_offset = }'
        assert not stop_loss_trigger_percentage or stop_loss_trigger_percentage >= 0, f'{stop_loss_trigger_percentage = }'
        assert not take_profit_trigger_percentage or take_profit_trigger_percentage >= 0, f'{take_profit_trigger_percentage = }'
        assert not stop_loss_price_offset or stop_loss_price_offset >= 0, f'{stop_loss_price_offset = }'
        assert not tp_price_offset or tp_price_offset >= 0, f'{tp_price_offset = }'
        assert not tp_trigger_price_type or tp_trigger_price_type in ['index', 'mark',
                                                                      'last'], f'{tp_trigger_price_type = }'
        assert not sl_trigger_price_type or sl_trigger_price_type in ['index', 'mark',
                                                                      'last'], f'{sl_trigger_price_type = }'

        assert order_type in ['market', 'limit', 'post_only', 'fok', 'ioc'], f'{order_type = }'
        assert isinstance(order_size, int), f'Order size must be an integer/multiple of a lot size. {order_size = }'
        assert order_size > 0, f'Order size must be greater than 0. {order_size = }'

        generated_client_order_id = generate_random_string(20, 'alphanumeric')  # 6 characters for type later

    if clear_prior_to_new_order:
        clear_orders_and_positions_for_instrument(instID)

    (simplified_balance_details, account_config, instrument_status_report) = fetch_initial_data(TD_MODE, instId=instID)

    if leverage and leverage > 0:
        accountAPI.set_leverage(
            lever=leverage,
            mgnMode=TD_MODE,
            instId=instID,
            posSide=POSSIDETYPE
        )

    ticker = get_ticker(instId=instID)
    ask_price = float(ticker.askPx)
    bid_price = float(ticker.bidPx)
    reference_price = ask_price if order_side == 'buy' else bid_price
    # position = all_positions[0] if len(all_positions) > 0 else None  # we are only using net so only one position
    position = instrument_status_report.positions[0] if len(
        instrument_status_report.positions) > 0 else None  # we are only using net so only one position
    # # find the set of algo orders that are the oldest
    # # if there are any algo orders that are not in the set of oldest algo orders, cancel them
    # oldest_algo_order = None
    # for algo_order in all_algo_orders:
    #     if oldest_algo_order is None:
    #         oldest_algo_order: Algo_Order = algo_order
    #     elif algo_order.cTime < oldest_algo_order.cTime:
    #         oldest_algo_order: Algo_Order = algo_order
    #
    # oldest_algoClOrdId = oldest_algo_order.algoClOrdId.strip('TPORSL').strip('TrailS')
    # print(f'{oldest_algoClOrdId = }')
    #
    # algo_orders_to_cancel = []
    # for algo_order in all_algo_orders:
    #     if oldest_algoClOrdId not in algo_order.algoClOrdId:
    #         algo_orders_to_cancel.append(algo_order)
    # if algo_orders_to_cancel:
    #     print(f'Cancelling all but the oldest set of algo orders \n   {algo_orders_to_cancel = }')
    #     # cancelled_algo_orders = cancel_all_algo_orders_with_params(algo_orders_list=algo_orders_to_cancel)
    # print(f'{all_algo_orders = }')
    #
    # exit()
    if order_side:
        if position:
            position_side = 'buy' if float(position.pos) > 0 else 'sell' if float(
                position.pos) < 0 else None  # we are only using net so only one position
            if position_side is None:
                print(f'Closing all positions for {instID = } due to 0 net position')
                close_all_positions(instId=instID)
                cancel_all_algo_orders_with_params(instId=instID)
                cancel_all_orders(instId=instID)
            elif order_side and position_side != order_side:
                if flip_position_if_opposite_side:
                    print(f'Flipping position from {position_side = } to {order_side = }')
                    close_all_positions(instId=instID)
                    print(f'Closed all positions for {instID = }')

                    cancelled_orders = cancel_all_orders(instId=instID)
                    print(f"Cancelling orders to flip position: \n"
                          f"    {cancelled_orders = }")
                    cancelled_algo_orders = cancel_all_algo_orders_with_params(instId=instID)
                    print(f"Cancelling Algo orders to flip position: \n"
                          f"    {cancelled_algo_orders = }")
                else:
                    print(f'Closing all positions for {instID = } due to {position_side = }')
                    agg_pos = float(position.pos) + order_size
                    if agg_pos > 0:
                        dominant_pos_side = 'buy'
                    elif agg_pos < 0:
                        dominant_pos_side = 'sell'
                    else:
                        dominant_pos_side = None

                    if dominant_pos_side is not None:
                        print(f'{dominant_pos_side = }')
                        if dominant_pos_side != order_side:
                            # This means that the future to be position net direction is not the same as the order side
                            # thus we need to cancel all orders that are not on the dominant side
                            # and prevent new algo orders from being placed
                            take_profit_activated = False
                            stop_loss_activated = False
                            trailing_stop_loss_activated = False
                        else:
                            orders_to_cancel = []
                            for order in instrument_status_report.orders:
                                if order.side != dominant_pos_side:
                                    orders_to_cancel.append(order)
                            algo_orders_to_cancel = []
                            for algo_order in instrument_status_report.algo_orders:
                                if algo_order.side != dominant_pos_side:
                                    algo_orders_to_cancel.append(algo_order)

                            if orders_to_cancel:
                                cancel_all_orders(orders_list=orders_to_cancel)
                                print(f"Cancelling orders to prep for incoming orders: \n"
                                      f"    {orders_to_cancel = }")
                            if algo_orders_to_cancel:
                                print(f'{algo_orders_to_cancel = }')
                                cancelled_algo_orders = cancel_all_algo_orders_with_params(
                                    algo_orders_list=algo_orders_to_cancel)
                                print(f"Cancelling Algo orders to prep for incoming orders: \n"
                                      f"    {cancelled_algo_orders = }")

                    else:
                        print(f'The new position will result in a net 0 after the incoming orders'
                              f' {position_side = } and the order side is {order_side = }'
                              f' with {position.pos = } and {order_size = }')
                        cancel_all_orders(instId=instID)
                        cancel_all_algo_orders_with_params(instId=instID)

        order_request_dict = dict(
            instId=instID,
            tdMode=TD_MODE,
            side=order_side,
            posSide=POSSIDETYPE,
            ordType=order_type,  # post_only, limit, market
            sz=order_size,
            clOrdId=generated_client_order_id,
        )

        if order_type != 'market':
            order_book = get_order_book(instID, 400)
            limit_price = prepare_limit_price(order_book, order_size, order_side, reference_price,
                                              max_orderbook_price_offset=max_orderbook_limit_price_offset)
            print(f'Setting New Target Limit Price to {limit_price = }')

            order_request_dict['px'] = limit_price

        if take_profit_activated:
            stop_surplus_trigger_price, stop_surplus_execute_price = calculate_tp_stop_prices(
                reference_price=reference_price, order_side=order_side,
                tp_trigger_percentage=take_profit_trigger_percentage,
                tp_price_offset=tp_price_offset,
            )

            tpTriggerPxType = tp_trigger_price_type
            order_request_dict.update(
                tpTriggerPx=stop_surplus_trigger_price,
                tpOrdPx=stop_surplus_execute_price,
                tpTriggerPxType=tpTriggerPxType,
                algoClOrdId=f'{generated_client_order_id}TPORSL'
            )
        if stop_loss_activated:
            stop_loss_trigger_price, stop_loss_execute_price = calculate_sl_stop_prices(
                reference_price=reference_price, order_side=order_side,
                sl_trigger_percentage=stop_loss_trigger_percentage,
                sl_price_offset=stop_loss_price_offset)
            slTriggerPxType = sl_trigger_price_type
            order_request_dict.update(
                slTriggerPx=stop_loss_trigger_price,
                slOrdPx=stop_loss_execute_price,
                slTriggerPxType=slTriggerPxType,
                algoClOrdId=f'{generated_client_order_id}TPORSL'
            )
        order_placement_return = place_order(**order_request_dict)

        print(f'{order_placement_return = }')

        # If error, cancel all orders and exit
        if order_placement_return.sCode != '0':
            print(f'{order_placement_return.sMsg = }')
            cancel_all_orders()
            cancel_all_algo_orders_with_params(instId=instID)
            exit()

        if trailing_stop_loss_activated:
            activePx = None
            if trailing_stop_activation_percentage:
                activePx = reference_price * (1 + trailing_stop_activation_percentage) if order_side == 'buy' else \
                    reference_price * (1 - trailing_stop_activation_percentage)
            # Create Trailing Stop Loss
            trailing_stop_order_placement_return = place_algo_trailing_stop_loss(
                instId=instID,
                tdMode=TD_MODE,
                ordType="move_order_stop",
                side='buy' if order_side == 'sell' else 'sell',
                sz=order_size,
                activePx=activePx or reference_price,
                posSide=POSSIDETYPE,
                callbackRatio=trailing_stop_callback_ratio,
                reduceOnly='true',
                algoClOrdId=f'{generated_client_order_id}TrailS',
                cxlOnClosePos="true",
            )
            print(f'{trailing_stop_order_placement_return = }')
    else:
        """
        Maintainence
        """
        if position:
            position_side = 'buy' if float(position.pos) > 0 else 'sell' if float(
                position.pos) < 0 else None  # we are only using net so only one position
            if position_side is None:
                print(f'Will Attempt to close all positions for {instID = } due to 0 net position')
                close_all_positions(instId=instID)
                # cancel_all_algo_orders_with_params(instId=instID)
                # cancel_all_orders(instId=instID)

    print('\n\nFINAL REPORT')
    return fetch_status_report_for_instrument(instID, TD_MODE)

if __name__ == '__main__':
    def okx_premium_indicator(indicator_input: PremiumIndicatorSignalRequestForm):
        from fastapi import HTTPException
        from starlette import status
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="credentials invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )
        indicator_input = PremiumIndicatorSignalRequestForm(**indicator_input)
        from jose import JWTError
        try:
            from routers.okx_authentication import check_token_against_instrument
            valid = check_token_against_instrument(token=indicator_input.InstIdAPIKey,
                                                   reference_instID=indicator_input.OKXSignalInput.instID
                                                   )
            assert valid == True, "InstIdAPIKey verification failed"
        except JWTError:
            raise credentials_exception
        # except AssertionError:
        #     raise credentials_exception
        # except HTTPException:
        #     raise credentials_exception
        except Exception as e:
            print(f"Exception in okx_antbot_webhook: {e}")
            return {"detail": "okx signal received but there was an exception, check the logs", "exception": str(e)}

        try:
            pprint(f'{indicator_input.OKXSignalInput = }')
            pprint(f'{indicator_input.PremiumIndicatorSignals = }')

            # Interpret Signals
            premium_indicator = indicator_input.PremiumIndicatorSignals

            premium_indicator.Bearish = int(premium_indicator.Bearish)
            premium_indicator.Bearish_plus = int(premium_indicator.Bearish_plus)
            premium_indicator.Bullish = int(premium_indicator.Bullish)
            premium_indicator.Bullish_plus = int(premium_indicator.Bullish_plus)
            premium_indicator.Bearish_Exit = 0 if premium_indicator.Bearish_Exit == 'null' else float(
                premium_indicator.Bearish_Exit)
            premium_indicator.Bullish_Exit = 0 if premium_indicator.Bullish_Exit == 'null' else float(
                premium_indicator.Bullish_Exit)

            _order_side = None
            _close_signal = None
            if premium_indicator.Bearish or premium_indicator.Bearish_plus:
                _order_side = 'buy'
            elif premium_indicator.Bullish or premium_indicator.Bullish_plus:
                _order_side = 'sell'
            if premium_indicator.Bearish_Exit:
                _close_signal = 'exit_buy'
            elif premium_indicator.Bullish_Exit:
                _close_signal = 'exit_sell'

            # Get current positions
            from pyokx.signal_handling import get_all_positions
            instId_positions = get_all_positions(instId=indicator_input.OKXSignalInput.instID)
            if len(instId_positions) > 0:
                current_position = instId_positions[0]
                current_position_side = 'buy' if float(current_position.pos) > 0 else 'sell' if float(
                    current_position.pos) < 0 else None  # we are only using net so only one position

                if _close_signal:
                    buy_exit = _close_signal == 'exit_buy' and current_position_side == 'buy'
                    sell_exit = _close_signal == 'exit_sell' and current_position_side == 'sell'
                    if not (buy_exit or sell_exit):
                        _close_signal = None

            # TODO - IDEA: Logic here betweeen _close_signal and entry, if just a closing then it can be handled using market or limit orders but if it is an entry and exit then we decide depening on wehther the entry is in the same or opposite directoion and if flip on opposite order is true.
            #   lets assume that we are not flipping on opposite order  then cancel if entry in opposite direction and close_order then clear before starting, if just closing then trat them as an actual order which can be market post only or limits
            print(f'{_order_side or _close_signal = }')
            if _order_side or _close_signal:
                okx_signal = indicator_input.OKXSignalInput

                okx_signal.order_side = _order_side if _order_side else ''
                okx_signal.clear_prior_to_new_order = True if okx_signal.clear_prior_to_new_order or _close_signal else False

                if _close_signal:  # FIXME this works for Premium indicator but might have issues if not handled in order
                    okx_signal.order_side = ''

                pprint(f'updated-{premium_indicator = }')
                pprint(f'updated-{okx_signal= }')

                assert indicator_input.OKXSignalInput, "OKXSignalInput is None"
                okx_signal_input = indicator_input.OKXSignalInput
                from pyokx.signal_handling import okx_signal_handler
                instrument_status_report: InstrumentStatusReport = okx_signal_handler(**okx_signal_input.model_dump())
                pprint(instrument_status_report)
                assert instrument_status_report, "Instrument Status Report is None, check the Instrument ID"
                return {"detail": "okx signal received", "instrument_status_report": instrument_status_report}
            return {"detail": "okx signal received but no action taken"}
        except Exception as e:
            print(f"Exception in okx_premium_indicator {e}")
            return {
                "detail": "okx premium indicator signal received but not handled yet",
                "exception": "okx premium indicator signal received but not handled yet"
            }

        # Update the enxchange info on the database
        return {"detail": "unexpected end of point??."}
    import dotenv
    from data_structures import OKXSignalInput

    dotenv.load_dotenv(dotenv.find_dotenv())

    # webhook_payload = json.loads('')
    # Read debugging_payload.json
    with open('../debugging_payload.json', 'r') as f:
        webhook_payload = json.load(f)
    pprint(f'{webhook_payload = }')
    # okx_input = OKXSignalInput(
    #     # instID=get_ticker_with_higher_volume('BTC-USDT').instId,
    #     instID="BTC-USDT-240628",
    #     clear_prior_to_new_order=False,
    #     red_button=False,
    # )
    #
    # response = okx_signal_handler(**okx_input.model_dump())

    response = okx_premium_indicator(webhook_payload)['instrument_status_report']

    print(f'{response = }')
    pprint(f'{response.positions = }')
    pprint(f'{len(response.positions) = }')
    pprint(f'{response.positions[0].pos = }')
    pprint(f'{response.orders = }')
    pprint(f'{response.algo_orders = }')
