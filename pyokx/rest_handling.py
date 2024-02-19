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
import random
import re
import string
import time
from pprint import pprint
from typing import List, Any, Union
from urllib.error import HTTPError

from pyokx.InstrumentSearcher import InstrumentSearcher
from pyokx.data_structures import (Order, Cancelled_Order, Order_Placement_Return,
                                   Position, Closed_Position, Ticker,
                                   Algo_Order, Algo_Order_Placement_Return,
                                   AccountBalanceDetails, AccountBalanceData,
                                   AccountConfigData, MaxOrderSizeData, MaxAvailSizeData, Cancelled_Algo_Order,
                                   Orderbook_Snapshot, Bid, Ask,
                                   Simplified_Balance_Details, InstrumentStatusReport,
                                   OKXPremiumIndicatorSignalRequestForm, FillEntry, OKXSignalInput, DCAInputParameters,
                                   DCAOrderParameters)
from pyokx.okx_market_maker.utils.OkxEnum import InstType
from pyokx.redis_structured_streams import get_instruments_searcher_from_redis
from redis_tools.utils import init_async_redis
from shared import logging
from shared.tmp_shared import calculate_tp_stop_prices_usd, calculate_sl_stop_prices_usd, ccy_usd_to_contracts

logger = logging.setup_logger(__name__)

from pyokx import okx_client, tradeAPI, marketAPI, accountAPI, publicAPI, ENFORCED_INSTRUMENT_TYPE  # noqa

REDIS_STREAM_MAX_LEN = int(os.getenv('REDIS_STREAM_MAX_LEN', 1000))

"""NOTE: THE MODULE NEEDS TO BE UPDATED WITH ENUMS AND STRUCTURED DATA TYPES WHERE APPLICABLE"""


async def get_request_data(returned_data, target_data_structure):
    """
    Processes the returned data from an API call, mapping it to the specified data structure.

    Args:
        returned_data (dict): The raw data returned from the API call.
        target_data_structure (class): The class to which the returned data items will be mapped.

    Returns:
        List[Any]: A list of instances of the target data structure class, populated with the returned data.
    """
    # print(f'{returned_data = }')
    if returned_data["code"] != "0":
        print(f"Unsuccessful {target_data_structure} request，\n  error_code = ", returned_data["code"],
              ", \n  Error_message = ",
              returned_data["msg"])
        return []

    structured_data = []
    for data in returned_data['data']:
        structured_data.append(target_data_structure(**data))
    return structured_data


async def get_ticker_with_higher_volume(seed_symbol_name, instrument_type="FUTURES", top_n=1):
    """
    Retrieves the ticker(s) with the highest trading volume for a given seed symbol and instrument type.
    Optionally, returns the top N tickers sorted by volume.

    Args:
        seed_symbol_name (str): The base symbol to search for.
        instrument_type (str, optional): The type of instrument (e.g., "FUTURES"). Defaults to "FUTURES".
        top_n (int, optional): The number of top-volume tickers to return. Defaults to 1.

    Returns:
        List[Ticker]: A list of tickers, sorted by volume, up to the specified top_n number.
    """
    print(f'{seed_symbol_name = }')  # tickers_data = okx_client.marketAPI.get_tickers(instType=instrument_type)

    # raise DeprecationWarning("This function is deprecated. Waiting to update to Structured Data Types.")
    all_positions = okx_client.accountAPI.get_positions(instType=instrument_type)
    all_position_symbols = [position['instId'] for position in all_positions['data']]
    tickers_data = okx_client.marketAPI.get_tickers(instType=instrument_type)

    # If any tickers data are returned, find the ticker data for the symbol we are trading
    # fixme this is a hack since okx is returning multiple instId's
    _highest_volume = 0
    _highest_volume_ticker = None
    _ticker_data = None
    _top_n_tickers_highest_day_volume = {}
    for ticker_data in tickers_data['data']:
        if ticker_data['instId'].startswith(seed_symbol_name):
            _ticker_data = ticker_data
            _volume = float(ticker_data['volCcy24h'])
            _top_n_tickers_highest_day_volume[_volume] = ticker_data

    # sort the volumes in descending order
    _sorted_volumes = sorted(_top_n_tickers_highest_day_volume.keys(), reverse=True)
    _top_n_tickers = []
    for _volume in _sorted_volumes:
        _top_n_tickers.append(_top_n_tickers_highest_day_volume[_volume])

    tickers = []
    for _ticker_data in _top_n_tickers[:top_n]:
        tickers.append(Ticker(**_ticker_data))
    return tickers

    # get the tickers for the top 5 volumes


async def assert_okx_account_level(account_level: [1, 2, 3, 4]):
    """
    Validates and sets the OKX account level, ensuring it is one of the acceptable levels.

    Args:
        account_level (list[int]): The account level to be validated and set. Acceptable levels are 1, 2, 3, and 4.

    Raises:
        AssertionError: If the account level is not one of the acceptable levels or if the account level could not be set.
    """
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
    if result_set_account_level['code'] != "0":
        print("Unsuccessful request，\n  error_code = ", result_set_account_level['code'], ", \n  Error_message = ",
              result_set_account_level["msg"])

    # Get account configuration
    result_get_account_config = accountAPI.get_account_config()

    if result_get_account_config['code'] == "0":
        acctLv = result_get_account_config["data"][0]["acctLv"]
        assert acctLv == account_level, f"Account level was not set to {ACCLV_MAPPING[account_level]}"
    else:
        print("Unsuccessful `assert_okx_account_level` request，\n  error_code = ", result_get_account_config['code'],
              ", \n  Error_message = ",
              result_get_account_config["msg"])


async def is_valid_alphanumeric(string, max_length):
    """
    Validates if the input string is alphanumeric and conforms to the specified maximum length.

    Args:
        string (str): The string to validate.
        max_length (int): The maximum allowable length for the string.

    Returns:
        bool: True if the string is alphanumeric and does not exceed the max_length, False otherwise.
    """

    return bool(re.match('^[a-zA-Z0-9]{1,' + str(max_length) + '}$', string))


async def get_all_orders(instType: str = None, instId: str = None):
    """
    Fetches all orders matching the given criteria from the trading API.

    Args:
        instType (str, optional): The type of instrument to fetch orders for (e.g., "FUTURES").
        instId (str, optional): The specific instrument ID to fetch orders for.

    Returns:
        List[Order]: A list of orders that match the given criteria.
    """
    params = {}
    if instType is not None:
        params['instType'] = instType
    if instId is not None:
        params['instId'] = instId
    return await get_request_data(tradeAPI.get_order_list(**params), Order)


async def cancel_all_orders(orders_list: List[Order] = None, instType: InstType = None, instId: str = None):
    """
    Cancels all or specific orders based on the provided parameters.

    Args:
        orders_list (List[Order], optional): A list of specific orders to cancel. If not provided, all orders are cancelled.
        instType (InstType, optional): The type of instrument to cancel orders for.
        instId (str, optional): The specific instrument ID to cancel orders for.

    Returns:
        List[Cancelled_Order]: A list of the orders that were successfully cancelled.
    """
    if orders_list is None:
        params = {}
        if instType is not None:
            params['instType'] = instType
        if instId is not None:
            params['instId'] = instId
        orders_list = await get_all_orders(**params)
    # cancelled_orders = []
    orders_to_cancel = []
    for order in orders_list:
        orders_to_cancel.append(order)

    # Batch Cancel Orders
    cancelled_orders = await get_request_data(tradeAPI.cancel_multiple_orders(
        orders_data=[
            {'instId': order.instId,
             'ordId': order.ordId,
             } for order in orders_to_cancel
        ]
    ), Cancelled_Order)

    #
    return cancelled_orders


async def close_position(instId, mgnMode, posSide='', ccy='', autoCxl='', clOrdId='', tag=''):
    """
    Closes a position based on the given parameters.

    :param instId: The instrument ID for the position to be closed.
    :type instId: str
    :param mgnMode: The margin mode for the position (e.g., 'isolated', 'cross').
    :type mgnMode: str
    :param posSide: The position side (e.g., 'long', 'short'). Defaults to an empty string.
    :type posSide: str, optional
    :param ccy: The currency used for the position. Defaults to an empty string.
    :type ccy: str, optional
    :param autoCxl: Automatically cancel the position. Defaults to an empty string.
    :type autoCxl: str, optional
    :param clOrdId: The client order ID. Defaults to an empty string.
    :type clOrdId: str, optional
    :param tag: A tag for the position. Defaults to an empty string.
    :type tag: str, optional
    :returns: The response from the position close request.
    """
    params = {'instId': instId, 'mgnMode': mgnMode, 'posSide': posSide, 'ccy': ccy, 'autoCxl': autoCxl,
              'clOrdId': clOrdId, 'tag': tag}
    from pyokx.low_rest_api.consts import CLOSE_POSITION
    from pyokx.low_rest_api.consts import POST
    closed_position_return = tradeAPI._request_with_params(POST, CLOSE_POSITION, params)
    return closed_position_return


async def close_all_positions(positions_list: List[Position] = None, instType: InstType = None, instId: str = None):
    """
    Closes all or specific positions based on the provided parameters.

    :param positions_list: A list of specific positions to close. If not provided, all positions are closed.
    :type positions_list: List[Position], optional
    :param instType: The type of instrument to close positions for.
    :type instType: InstType, optional
    :param instId: The specific instrument ID to close positions for.
    :type instId: str, optional
    :returns: A list of the positions that were successfully closed.
    """
    if positions_list is None:
        params = {}
        if instType is not None:
            params['instType'] = instType
        if instId is not None:
            params['instId'] = instId
        positions_list = await get_all_positions(**params)

    closed_positions_return = await asyncio.gather(
        *[close_position(instId=position.instId, mgnMode=position.mgnMode,
                         posSide=position.posSide, ccy=position.ccy,
                         autoCxl='true', clOrdId=f'{position.posId}CLOSED',
                         tag='') for position in positions_list]
    )

    closed_positions = []
    for closed_position in closed_positions_return:
        try:
            assert closed_position['code'] == '0', f' {closed_position = }'
            closed_position = await get_request_data(closed_position, Closed_Position)
            closed_positions.append(closed_position[0])
        except AssertionError as e:
            print(e)

    return closed_positions


async def get_all_positions(instType: InstType = None, instId: str = None):
    """
    Fetches all positions matching the given criteria from the account API.

    :param instType: The type of instrument to fetch positions for (e.g., 'FUTURES').
    :type instType: InstType, optional
    :param instId: The specific instrument ID to fetch positions for.
    :type instId: str, optional
    :returns: A list of positions that match the given criteria.
    """
    params = {}
    if instType is not None:
        params['instType'] = instType
    if instId is not None:
        params['instId'] = instId
    return await get_request_data(accountAPI.get_positions(**params), Position)


async def place_order(instId: Any,
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
    """
    Places an order with the specified parameters.

    :param instId: The instrument ID for the order.
    :type instId: Any
    :param tdMode: The trade mode for the order (e.g., 'cash', 'margin').
    :type tdMode: Any
    :param side: The side of the order ('buy' or 'sell').
    :type side: Any
    :param ordType: The type of the order (e.g., 'limit', 'market').
    :type ordType: Any
    :param sz: The size of the order.
    :type sz: Any
    ... (and so on for other parameters)
    :returns: The response from the order placement request.
    """
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

    if result["code"] != "0":
        print(f'{result = }')
        print("Unsuccessful order request，\n  error_code = ", result["msg"], ", \n  Error_message = ",
              result["msg"])
        return None

    result = await get_request_data(result, Order_Placement_Return)
    return result[0]


async def get_ticker(instId):
    """
    Retrieves the latest ticker information for a specified instrument.

    :param instId: The instrument ID for which to get the ticker information.
    :type instId: str
    :returns: The latest ticker information for the specified instrument.
    """
    result = await get_request_data(marketAPI.get_ticker(instId=instId), Ticker)

    if result:
        return result[0]
    else:
        return None


async def get_all_algo_orders(instId=None, ordType=None):
    """
    Fetches all algorithmic orders matching the given criteria from the trading API.

    :param instId: The specific instrument ID to fetch algo orders for, defaults to None.
    :type instId: str, optional
    :param ordType: The type of algo order (e.g., 'trigger', 'oco'), defaults to None.
    :type ordType: str, optional
    :returns: A list of algo orders that match the given criteria.
    """
    if ordType is None:
        ORDER_TYPES_TO_TRY = ['trigger', 'oco', 'conditional', 'move_order_stop', 'twap']
    else:
        ORDER_TYPES_TO_TRY = [ordType]

    # orders_fetched = []

    algo_type_to_fetch_params = []
    for ordType in ORDER_TYPES_TO_TRY:
        params = {'ordType': ordType}
        if instId is not None:
            params['instId'] = instId

        algo_type_to_fetch_params.append(params)

    orders_fetched_list = await asyncio.gather(
        *[get_request_data(
            tradeAPI.order_algos_list(**params), Algo_Order) for params in algo_type_to_fetch_params]
    )

    orders_fetched = []
    for order_types in orders_fetched_list:
        orders_fetched.extend(order_types)

    return orders_fetched


async def cancel_all_algo_orders_with_params(algo_orders_list: List[Algo_Order] = None, instId=None, ordType=None):
    """
    Cancels all or specific algorithmic orders based on the provided parameters.

    :param algo_orders_list: A list of specific algo orders to cancel. If not provided, all algo orders are cancelled.
    :type algo_orders_list: List[Algo_Order], optional
    :param instId: The specific instrument ID to cancel algo orders for, defaults to None.
    :type instId: str, optional
    :param ordType: The type of algo order (e.g., 'trigger', 'oco'), defaults to None.
    :type ordType: str, optional
    :returns: A list of the algo orders that were successfully cancelled.
    """
    assert algo_orders_list is None or (
            instId is not None or ordType is not None), f'algo_orders_list or instId must be provided'

    if algo_orders_list is None and (instId is not None or ordType is not None):
        params = {}
        if instId is not None:
            params['instId'] = instId
        if ordType is not None:
            params['ordType'] = ordType
        algo_orders_list = await get_all_algo_orders(**params)

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
    return await get_request_data(result, Cancelled_Algo_Order)


async def place_algo_order(
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
    """
    Places an algorithmic order with detailed parameters.
    (as defined by the OKX API documentation, see Orders vs Algo Orders for more details)

    :param instId: The instrument ID for the order.
    :type instId: str
    :param tdMode: The trade mode for the order (e.g., 'cash', 'margin').
    :type tdMode: str
    ... (and so on for other parameters)
    :returns: The response from the algorithmic order placement request.
    """
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

    if result["code"] != "0":
        print(f'{result = }')
        print("Unsuccessful algo order request，\n  error_code = ", result["msg"], ", \n  Error_message = ",
              result["msg"])

    return await get_request_data(result, Algo_Order_Placement_Return)


async def get_account_balance():
    """
    Retrieves the account balance details.

    :returns: The account balance data, structured according to the AccountBalanceData class.
    """
    account_balance = accountAPI.get_account_balance()['data'][0]
    details = account_balance['details']
    structured_details = []
    for detail in details:
        structured_details.append(AccountBalanceDetails(**detail))
    account_balance['details'] = structured_details
    return AccountBalanceData(**account_balance)


async def get_account_config():
    """
    Retrieves the account configuration details.

    :returns: The account configuration data, structured according to the AccountConfigData class.
    """
    return AccountConfigData(**accountAPI.get_account_config()['data'][0])


async def get_max_order_size(instId, tdMode):
    """
    Retrieves the maximum order size for a specific instrument and trade mode.

    :param instId: The instrument ID for which to get the maximum order size.
    :type instId: str
    :param tdMode: The trade mode (e.g., 'cash', 'margin').
    :type tdMode: str
    :returns: The maximum order size data, structured according to the MaxOrderSizeData class.
    """
    # return MaxOrderSizeData(**accountAPI.get_max_order_size(instId=instId, tdMode=tdMode)['data'][0])
    result = accountAPI.get_max_order_size(instId=instId, tdMode=tdMode)
    if result["code"] != "0":
        print("Unsuccessful get_max_order_size request，\n  error_code = ", result["code"], ", \n  Error_message = ",
              result["msg"])
        return []
    return MaxOrderSizeData(**result['data'][0])


async def get_max_avail_size(instId, tdMode):
    """
    Retrieves the maximum available size for trading a specific instrument in a specific trade mode.

    :param instId: The instrument ID for which to get the maximum available size.
    :type instId: str
    :param tdMode: The trade mode (e.g., 'cash', 'margin').
    :type tdMode: str
    :returns: The maximum available size data, structured according to the MaxAvailSizeData class.
    """
    # return MaxAvailSizeData(**accountAPI.get_max_avail_size(instId=instId, tdMode=tdMode)['data'][0])
    result = accountAPI.get_max_avail_size(instId=instId, tdMode=tdMode)
    if result["code"] != "0":
        print("Unsuccessful get_max_avail_size request，\n  error_code = ", result["code"], ", \n  Error_message = ",
              result["msg"])
        return []
    return MaxAvailSizeData(**result['data'][0])


def generate_random_string(length, char_type='alphanumeric'):
    """
    Generates a random string of the specified length and character type.

    :param length: The length of the random string to generate.
    :type length: int
    :param char_type: The type of characters to include in the string ('alphanumeric', 'numeric', or 'alphabetic').
                      Defaults to 'alphanumeric'.
    :type char_type: str, optional
    :returns: A random string of the specified length and character type.
    :raises ValueError: If the length exceeds 32 or if an invalid char_type is specified.
    """
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


async def fetch_status_report_for_instrument(instId, TD_MODE):
    """
    Fetches a comprehensive status report for a specific instrument.

    :param instId: The instrument ID for which to fetch the status report.
    :type instId: str
    :param TD_MODE: The trade mode (e.g., 'cash', 'margin').
    :type TD_MODE: str
    :returns: A status report for the instrument, structured according to the InstrumentStatusReport class.
    """
    # Handle the case where instId is None
    if instId is None:
        return None

    (max_order_size, max_avail_size,
     all_positions, all_orders, all_algo_orders) = await asyncio.gather(
        get_max_order_size(instId=instId, tdMode=TD_MODE),
        get_max_avail_size(instId=instId, tdMode=TD_MODE),
        get_all_positions(instId=instId),
        get_all_orders(instId=instId),
        get_all_algo_orders(instId=instId)
    )
    return InstrumentStatusReport(
        instId=instId,
        max_order_size=max_order_size,
        max_avail_size=max_avail_size,
        positions=all_positions,
        orders=all_orders,
        algo_orders=all_algo_orders
    )


async def fetch_initial_data(TD_MODE, instId=None):
    """
    Fetches initial data including account balance, account configuration, and instrument status.

    :param TD_MODE: The trade mode (e.g., 'cash', 'margin').
    :type TD_MODE: str
    :param instId: The instrument ID for which to fetch the data, defaults to None.
    :type instId: str, optional
    :returns: A tuple containing simplified balance details, account configuration data, and instrument status report.
    """
    account_balance, account_config = await asyncio.gather(get_account_balance(), get_account_config())

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

    instrument_status_report = await fetch_status_report_for_instrument(instId, TD_MODE)

    return simplified_balance_details, account_config, instrument_status_report


async def clear_orders_and_positions_for_instrument(instId):
    """
    Clears all orders and positions for a specific instrument.

    :param instId: The instrument ID for which to clear orders and positions.
    :type instId: str
    """
    closed_positions = await close_all_positions(instId=instId)
    cancelled_orders = await cancel_all_orders(instId=instId)
    cancelled_algo_orders = await cancel_all_algo_orders_with_params(instId=instId)
    print(f'{closed_positions = }')
    print(f'{cancelled_orders = }')
    print(f'{cancelled_algo_orders = }')


async def get_order_book(instId, depth):
    """
    Fetches the order book for a specific instrument.

    :param instId: The instrument ID for which to get the order book.
    :type instId: str
    :param depth: The depth of the order book to fetch.
    :type depth: int
    :returns: The order book snapshot, structured according to the Orderbook_Snapshot class.
    :raises ValueError: If the order book could not be fetched for the specified instrument ID.
    """
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


async def place_algo_trailing_stop_loss(
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
    """
    Places a trailing stop-loss order with detailed parameters.

    :param instId: The instrument ID for the order.
    :type instId: str
    :param tdMode: The trade mode for the order (e.g., 'cash', 'margin').
    :type tdMode: str
    ... (and so on for other parameters)
    :returns: The response from the trailing stop-loss order placement request.
    """
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


async def get_leverage(instId, mgnMode):
    result = accountAPI.get_leverage(instId=instId, mgnMode=mgnMode)
    if result["code"] != "0":
        print("Unsuccessful get_leverage request，\n  error_code = ", result["code"], ", \n  Error_message = ",
              result["msg"])
        return []
    if len(result['data']) != 0:
        leverage = result['data'][0]['lever']
        return int(leverage)


async def prepare_limit_price(order_book: Orderbook_Snapshot, quantity: Union[int, float], side, reference_price: float,
                              max_orderbook_price_offset=None,
                              ):
    """
    Prepares a limit price based on the order book, quantity, side, reference price, and maximum order book price offset.

    :param order_book: The snapshot of the order book.
    :type order_book: Orderbook_Snapshot
    :param quantity: The quantity for which to prepare the limit price.
    :type quantity: Union[int, float]
    :param side: The side of the order ('buy' or 'sell').
    :type side: str
    :param reference_price: The reference price to base the limit price on.
    :type reference_price: float
    :param max_orderbook_price_offset: The maximum allowed offset from the reference price, defaults to None.
    :type max_orderbook_price_offset: float, optional
    :returns: The prepared limit price.
    :raises Exception: If a price in the order book that has enough volume to cover the quantity cannot be found.
    """
    assert side.lower() in ['buy', 'sell']
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


async def _validate_instID_and_return_ticker_info(instID):
    """
    Cleans and verifies an instrument ID to ensure it's in the correct format and exists within the list of instruments.

    :param instID: The instrument ID to clean and verify.
    :type instID: str
    :returns: The cleaned and verified instrument ID.
    :raises AssertionError: If the instrument ID is not in the correct format or the instrument is not found.
    """
    # Clean Input Data
    instID = instID.upper()
    splitted = instID.split('-')
    assert len(splitted) == 3, f'The Futures instrument ID must be in the format of "BTC-USDT-210326". {instID = }'
    okx_futures_instrument_searcher: InstrumentSearcher = await get_instruments_searcher_from_redis(
        await init_async_redis(),
        instType=ENFORCED_INSTRUMENT_TYPE)

    instrument = okx_futures_instrument_searcher.find_by_instId(instID)
    assert instrument, f'Instrument not found. {instID = }'
    return instrument


async def _validate_okx_signal_input_tp_sl_trail_params(sl_trigger_price_offset=None,
                                                        tp_trigger_price_offset=None,
                                                        sl_execution_price_offset=None, tp_execution_price_offset=None,
                                                        trailing_stop_activation_price_offset=None,
                                                        trailing_stop_callback_offset=None,
                                                        max_orderbook_limit_price_offset=None,
                                                        flip_position_if_opposite_side=None,
                                                        tp_trigger_price_type=None, sl_trigger_price_type=None):
    if not tp_trigger_price_type:
        tp_trigger_price_type = 'last'
    if not sl_trigger_price_type:
        sl_trigger_price_type = 'last'
    if not sl_trigger_price_offset:
        sl_trigger_price_offset = False
    if not tp_trigger_price_offset:
        tp_trigger_price_offset = False
    if not sl_execution_price_offset:
        sl_execution_price_offset = False
    if not tp_execution_price_offset:
        tp_execution_price_offset = False
    if not trailing_stop_activation_price_offset:
        trailing_stop_activation_price_offset = False
    if not trailing_stop_callback_offset:
        trailing_stop_callback_offset = False

    tp_trigger_price_type, sl_trigger_price_type = tp_trigger_price_type.lower(), sl_trigger_price_type.lower()

    sl_trigger_price_offset = False if (
            sl_trigger_price_offset == '' or not sl_trigger_price_offset) else float(
        sl_trigger_price_offset)
    tp_trigger_price_offset = False if tp_trigger_price_offset == '' or not tp_trigger_price_offset else float(
        tp_trigger_price_offset)
    sl_execution_price_offset = False if sl_execution_price_offset == '' or not sl_execution_price_offset else float(
        sl_execution_price_offset)
    tp_execution_price_offset = False if tp_execution_price_offset == '' or not tp_execution_price_offset else float(
        tp_execution_price_offset)

    trailing_stop_activation_price_offset = False if trailing_stop_activation_price_offset == '' or not trailing_stop_activation_price_offset else float(
        trailing_stop_activation_price_offset)
    trailing_stop_callback_offset = False if trailing_stop_callback_offset == '' or not trailing_stop_callback_offset else float(
        trailing_stop_callback_offset)

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
    if tp_trigger_price_offset or tp_execution_price_offset:
        assert tp_trigger_price_offset and tp_execution_price_offset
        take_profit_activated = True
        tp_trigger_price_type = tp_trigger_price_type or 'last'

    if sl_trigger_price_offset or sl_execution_price_offset:
        assert sl_trigger_price_offset and sl_execution_price_offset
        stop_loss_activated = True
        sl_trigger_price_type = sl_trigger_price_type or 'last'

    if trailing_stop_activation_price_offset or trailing_stop_callback_offset:
        assert trailing_stop_callback_offset, f'trailing_stop_callback_offset must be provided if trailing_stop_activation_price_offset is provided. {trailing_stop_callback_offset = }'
        trailing_stop_loss_activated = True

    assert not sl_trigger_price_offset or isinstance(sl_trigger_price_offset,
                                                     float), f'{sl_trigger_price_offset = }'
    assert not tp_trigger_price_offset or isinstance(tp_trigger_price_offset,
                                                     float), f'{tp_trigger_price_offset = }'
    assert not sl_execution_price_offset or isinstance(sl_execution_price_offset,
                                                       float), f'{sl_execution_price_offset = }'
    assert not tp_execution_price_offset or isinstance(tp_execution_price_offset,
                                                       float), f'{tp_execution_price_offset = }'
    assert not sl_trigger_price_offset or sl_trigger_price_offset >= 0, f'{sl_trigger_price_offset = }'
    assert not tp_trigger_price_offset or tp_trigger_price_offset >= 0, f'{tp_trigger_price_offset = }'
    assert not sl_execution_price_offset or sl_execution_price_offset >= 0, f'{sl_execution_price_offset = }'
    assert not tp_execution_price_offset or tp_execution_price_offset >= 0, f'{tp_execution_price_offset = }'
    assert not tp_trigger_price_type or tp_trigger_price_type in ['index', 'mark',
                                                                  'last'], f'{tp_trigger_price_type = }'
    assert not sl_trigger_price_type or sl_trigger_price_type in ['index', 'mark',
                                                                  'last'], f'{sl_trigger_price_type = }'

    return {
        'sl_trigger_price_offset': sl_trigger_price_offset,
        'tp_trigger_price_offset': tp_trigger_price_offset,
        'sl_execution_price_offset': sl_execution_price_offset,
        'tp_execution_price_offset': tp_execution_price_offset,
        'trailing_stop_activation_price_offset': trailing_stop_activation_price_offset,
        'trailing_stop_callback_offset': trailing_stop_callback_offset,
        'max_orderbook_limit_price_offset': max_orderbook_limit_price_offset,
        'flip_position_if_opposite_side': flip_position_if_opposite_side,
        'tp_trigger_price_type': tp_trigger_price_type,
        'sl_trigger_price_type': sl_trigger_price_type,
        'take_profit_activated': take_profit_activated,
        'stop_loss_activated': stop_loss_activated,
        'trailing_stop_loss_activated': trailing_stop_loss_activated,
    }


async def _validate_okx_signal_order_params(order_type, order_side, order_size):
    if not order_type:
        order_type = 'limit'
    if not order_side:
        order_side = ''
    if not order_size:
        order_size = 0

    order_type, order_side = order_type.lower(), order_side.lower(),
    order_size = int(order_size)
    assert order_side in ['buy', 'sell'] or not order_side, (
        f'order_side must be either "buy" or "sell" or empty. \n '
        f'for maintenance mode \n      {order_side = }')
    assert order_type in ['market', 'limit', 'post_only', 'fok', 'ioc'], f'{order_type = }'
    assert isinstance(order_size, int), f'Order size must be an integer/multiple of a lot size. {order_size = }'
    assert order_size > 0, f'Order size must be greater than 0. {order_size = }'

    return {
        'order_type': order_type,
        'order_side': order_side,
        'order_size': order_size,
    }


async def _validate_okx_signal_additional_params(
        leverage=None, max_orderbook_limit_price_offset=None, flip_position_if_opposite_side=None,
        clear_prior_to_new_order=None
):
    leverage = 0 if not leverage else int(leverage)
    max_orderbook_limit_price_offset = 0 \
        if not max_orderbook_limit_price_offset else float(max_orderbook_limit_price_offset)
    flip_position_if_opposite_side = False \
        if not flip_position_if_opposite_side else bool(flip_position_if_opposite_side)
    clear_prior_to_new_order = False if not clear_prior_to_new_order else bool(clear_prior_to_new_order)

    return {
        'leverage': leverage,
        'max_orderbook_limit_price_offset': max_orderbook_limit_price_offset,
        'flip_position_if_opposite_side': flip_position_if_opposite_side,
        'clear_prior_to_new_order': clear_prior_to_new_order,
    }


async def prepare_dca(dca_parameters: List[DCAInputParameters], side: str, reference_price: float,
                      ccy_contract_size: float, ccy_last_price: float, usd_to_base_rate: float, leverage: int,
                      min_order_quantity: int, max_market_order_quantity: int):
    # Assert the correct input parameters for dca
    assert all([isinstance(param, DCAInputParameters) for param in
                dca_parameters]), f'The dca_parameters must be a list of DCAInputParameters. {dca_parameters = }'

    orders = []

    for params in dca_parameters:
        order_trigger_price = reference_price + params.trigger_price_offset if side == 'BUY' else reference_price - params.trigger_price_offset
        order_exec_price = reference_price + params.execution_price_offset if side == 'BUY' else reference_price - params.execution_price_offset
        usd_amount = params.usd_amount

        order_contracts = ccy_usd_to_contracts(usd_equivalent=usd_amount, ccy_contract_size=ccy_contract_size,
                                               ccy_last_price=ccy_last_price, minimum_contract_size=min_order_quantity,
                                               max_market_contract_size=max_market_order_quantity,
                                               usd_base_ratio=usd_to_base_rate, leverage=leverage)
        orders.append(DCAOrderParameters(
            size=order_contracts,
            trigger_price=order_trigger_price,
            execution_price=order_exec_price,
            type=params.order_type,
            side=params.order_side,
            tp_trigger_price_type=params.tp_trigger_price_type,
            tp_trigger_price_offset=params.tp_trigger_price_offset,
            tp_execution_price_offset=params.tp_execution_price_offset,
            sl_trigger_price_type=params.sl_trigger_price_type,
            sl_trigger_price_offset=params.sl_trigger_price_offset,
            sl_execution_price_offset=params.sl_execution_price_offset
        ))

    return orders


async def validate_okx_signal_params(
        okx_signal: OKXSignalInput
):
    generated_client_order_id = generate_random_string(16, 'alphanumeric')
    dca_parameters = None
    validated_order_params = {}
    validated_tp_sl_trail_params = {}

    if okx_signal.red_button:
        return {'red_button': okx_signal.red_button}
    else:
        red_button = False

    instId_info = await _validate_instID_and_return_ticker_info(okx_signal.instID)
    assert instId_info, f'Instrument not found. {okx_signal.instID = }'

    validated_additional_params = await _validate_okx_signal_additional_params(
        leverage=okx_signal.leverage, max_orderbook_limit_price_offset=okx_signal.max_orderbook_limit_price_offset,
        flip_position_if_opposite_side=okx_signal.flip_position_if_opposite_side,
        clear_prior_to_new_order=okx_signal.clear_prior_to_new_order)
    passed_expiration_test = False if int(instId_info.expTime) < int(time.time() * 1000) else True
    passed_leverage_test = False if int(instId_info.lever) <= validated_additional_params.get('leverage') else True
    assert passed_expiration_test, f'Instrument has expired. {instId_info.expTime = }'
    assert passed_leverage_test, f'Instrument has a higher leverage than the one provided. {instId_info.lever = }'

    _main_order_flag = okx_signal.usd_order_size and okx_signal.order_side

    if _main_order_flag or okx_signal.dca_parameters:
        ctValCcy = instId_info.ctValCcy
        min_order_quantity = int(instId_info.minSz)  # contracts
        max_market_order_quantity = int(instId_info.maxMktSz)  # contracts
        ctval_contract_size = float(instId_info.ctVal)
        instId_ticker: Ticker = await get_ticker(instId=instId_info.instId)
        assert instId_ticker, f'Could not fetch ticker for {instId_info.instId = }'
        ccy_last_price = float(instId_ticker.last)
        leverage = validated_additional_params.get('leverage') or await get_leverage(instId=instId_info.instId,
                                                                                     mgnMode='isolated')

        usd_to_base_rate = 1  # TODO use the USD to USDT and USDC ratio but 1 is close enough

        if okx_signal.dca_parameters:
            dca_parameters: [DCAOrderParameters] = await prepare_dca(
                dca_parameters=okx_signal.dca_parameters,
                side=validated_order_params.get('order_side'),
                reference_price=ccy_last_price,
                ccy_contract_size=ctval_contract_size, ccy_last_price=ccy_last_price,
                usd_to_base_rate=usd_to_base_rate, leverage=leverage,
                min_order_quantity=min_order_quantity,
                max_market_order_quantity=max_market_order_quantity)

    if _main_order_flag:

        usd_amount = float(okx_signal.usd_order_size)
        order_contracts = ccy_usd_to_contracts(usd_equivalent=usd_amount, ccy_contract_size=ctval_contract_size,
                                               ccy_last_price=ccy_last_price, minimum_contract_size=min_order_quantity,
                                               max_market_contract_size=max_market_order_quantity,
                                               usd_base_ratio=usd_to_base_rate, leverage=leverage,
                                               ctValCcy=ctValCcy)
        print(f"Number of contracts you can buy: {order_contracts} {instId_info.instId}")

        # Convert these into trailing_stop_callback_offset to trailing_stop_callback_ratio
        if okx_signal.trailing_stop_callback_offset:
            trailing_stop_callback_offset = float(okx_signal.trailing_stop_callback_offset)
            trailing_stop_callback_ratio = trailing_stop_callback_offset / ccy_last_price
            print(f'{trailing_stop_callback_ratio = }')
            # Min is 0,001 and max is 1
            if trailing_stop_callback_ratio < 0.001:
                trailing_stop_callback_ratio = 0.001
            if trailing_stop_callback_ratio > 1:
                trailing_stop_callback_ratio = 1

            trailing_stop_callback_offset = round(trailing_stop_callback_ratio, 3)
        else:
            trailing_stop_callback_offset = 0.0

        validated_order_params = await _validate_okx_signal_order_params(
            order_type=okx_signal.order_type, order_side=okx_signal.order_side,
            order_size=order_contracts)

        validated_tp_sl_trail_params = await _validate_okx_signal_input_tp_sl_trail_params(
            sl_trigger_price_offset=okx_signal.sl_trigger_price_offset,
            tp_trigger_price_offset=okx_signal.tp_trigger_price_offset,
            sl_execution_price_offset=okx_signal.sl_execution_price_offset,
            tp_execution_price_offset=okx_signal.tp_execution_price_offset,
            trailing_stop_activation_price_offset=okx_signal.trailing_stop_activation_price_offset,
            trailing_stop_callback_offset=trailing_stop_callback_offset,
            max_orderbook_limit_price_offset=okx_signal.max_orderbook_limit_price_offset,
            flip_position_if_opposite_side=okx_signal.flip_position_if_opposite_side,
            tp_trigger_price_type=okx_signal.tp_trigger_price_type,
            sl_trigger_price_type=okx_signal.sl_trigger_price_type)

    result = {
        'instID': instId_info.instId,
        'order_size': validated_order_params.get('order_size'),
        'leverage': validated_additional_params.get('leverage'),
        'order_side': validated_order_params.get('order_side'),
        'order_type': validated_order_params.get('order_type'),
        'max_orderbook_limit_price_offset': validated_additional_params.get('max_orderbook_limit_price_offset'),
        'flip_position_if_opposite_side': validated_additional_params.get('flip_position_if_opposite_side'),
        'clear_prior_to_new_order': validated_additional_params.get('clear_prior_to_new_order'),
        'red_button': red_button,
        'sl_trigger_price_offset': validated_tp_sl_trail_params.get('sl_trigger_price_offset'),
        'tp_trigger_price_offset': validated_tp_sl_trail_params.get('tp_trigger_price_offset'),
        'tp_trigger_price_type': validated_tp_sl_trail_params.get('tp_trigger_price_type'),
        'sl_execution_price_offset': validated_tp_sl_trail_params.get('sl_execution_price_offset'),
        'tp_execution_price_offset': validated_tp_sl_trail_params.get('tp_execution_price_offset'),
        'sl_trigger_price_type': validated_tp_sl_trail_params.get('sl_trigger_price_type'),
        'trailing_stop_activation_price_offset': validated_tp_sl_trail_params.get(
            'trailing_stop_activation_price_offset'),
        'trailing_stop_callback_offset': validated_tp_sl_trail_params.get('trailing_stop_callback_offset'),
        #
        'generated_client_order_id': generated_client_order_id,
        'take_profit_activated': validated_tp_sl_trail_params.get('take_profit_activated'),
        'stop_loss_activated': validated_tp_sl_trail_params.get('stop_loss_activated'),
        'trailing_stop_loss_activated': validated_tp_sl_trail_params.get('trailing_stop_loss_activated'),
        'dca_parameters': dca_parameters
    }
    return result


async def okx_signal_handler(
        instID: str = '',
        usd_order_size: int = None,
        leverage: int = None,
        order_side: str = None,
        order_type: str = None,
        max_orderbook_limit_price_offset: float = None,
        flip_position_if_opposite_side: bool = False,
        clear_prior_to_new_order: bool = False,
        red_button: bool = False,
        sl_trigger_price_offset: float = None,
        tp_trigger_price_offset: float = None,
        tp_trigger_price_type: str = None,
        sl_execution_price_offset: float = None,
        tp_execution_price_offset: float = None,
        sl_trigger_price_type: str = None,
        trailing_stop_activation_price_offset: float = None,
        trailing_stop_callback_offset: float = None,
        dca_parameters: List[DCAInputParameters] = None
):
    """
    Handles trading signals for the OKX platform, executing trades based on the specified parameters and current
    market conditions.

    Overview: 1. Validates and processes input parameters, preparing the trading signal. 2. Checks and manages
    current positions based on new signal, potentially flipping positions or clearing orders as configured. 3.
    Calculates and sets order parameters such as price and size, leveraging current market data and user preferences.
    4. Executes the trading actions (placing/canceling orders, opening/closing positions) on the OKX platform. 5.
    Fetches and returns an updated status report of the instrument, reflecting the changes made by the executed signal.

    Process Flow: The `okx_signal_handler` function is a complex asynchronous function designed to handle trading
    signals for the OKX platform, covering a wide range of trading strategies and actions. Here is a step-by-step
    structural and behavioral walkthrough of the main activities within the function, highlighting how it interacts
    with other helper functions:

        1. **Initialize OKX Signal Input**: It creates an instance of `OKXSignalInput` with all the provided
        parameters. This step is crucial for collecting all user inputs regarding the trading signal they wish to
        execute.

        2. **Pre-validation and Setup**: - Validates trading mode (`TD_MODE`) and position type (`POSSIDETYPE`) to
        ensure they are within acceptable parameters. - If the `red_button` parameter is true, the function triggers
        emergency actions to close all positions, cancel all orders, and return the status of these actions.

        3. **Validate Parameters**: Calls `validate_okx_signal_params` to validate and process input parameters
        comprehensively. This includes instrument ID validation, leverage checks, and configuration of additional
        parameters like order size, type, and various trading strategies (e.g., stop loss, take profit).

        4. **Initial Data Fetching**: Retrieves necessary initial data related to the trading account and the
        specific instrument being traded. This might include balance details, account configurations, and the current
        status report of the instrument.

        5. **Set Leverage**: If leverage is specified, it sets the leverage for the trading account according to the
        provided value.

        6. **Order and Position Management**: - Checks for existing positions and manages them based on the new
        signal. This includes closing positions, canceling orders, or flipping positions if configured to do so by
        the user. - If there are no conflicting positions or if the user has opted to clear previous orders and
        positions, it proceeds to calculate and set new order parameters.

        7. **Order Execution**: - Retrieves current market data (e.g., ticker information) to determine reference
        prices for order placement. - Calls `prepare_limit_price` to calculate the appropriate limit price for the
        order based on current market conditions and user specifications. - Constructs and sends order requests,
        including handling of special order types like take profit, stop loss, and trailing stop losses.

        8. **Dollar-Cost Averaging (DCA) Orders**: - If DCA parameters are provided, it prepares and sends multiple
        DCA orders based on the specified strategies and market conditions. - Each DCA order is configured with
        trigger prices, execution prices, and optional stop loss/take profit parameters.

        9. **Final Actions**: - After all trading actions have been attempted, it fetches and returns an updated
        status report for the instrument, reflecting the changes made by the executed signal. - Handles exceptions
        and errors throughout the process, ensuring that any issues are caught and logged, with appropriate cleanup
        actions taken if necessary.

        This function encapsulates a comprehensive set of trading strategies and operations, leveraging asynchronous
        programming to handle market data fetching, order preparation, and execution in a non-blocking manner. It
        demonstrates a complex integration of trading logic, error handling, and user input validation to manage
        trading signals on the OKX platform effectively.

        :raises Exception: Catches and logs any exceptions that occur during signal handling, providing detailed
        error information.
    """
    okx_signal_input: OKXSignalInput = OKXSignalInput(
        instID=instID,
        usd_order_size=usd_order_size,
        leverage=leverage,
        order_side=order_side,
        order_type=order_type,
        max_orderbook_limit_price_offset=max_orderbook_limit_price_offset,
        flip_position_if_opposite_side=flip_position_if_opposite_side,
        clear_prior_to_new_order=clear_prior_to_new_order,
        red_button=red_button,
        sl_trigger_price_offset=sl_trigger_price_offset,
        tp_trigger_price_offset=tp_trigger_price_offset,
        tp_trigger_price_type=tp_trigger_price_type,
        sl_execution_price_offset=sl_execution_price_offset,
        tp_execution_price_offset=tp_execution_price_offset,
        sl_trigger_price_type=sl_trigger_price_type,
        trailing_stop_activation_price_offset=trailing_stop_activation_price_offset,
        trailing_stop_callback_offset=trailing_stop_callback_offset,
        dca_parameters=dca_parameters
    )
    TD_MODE: str = 'isolated'.lower()  # here for completeness, but assumed to be isolated
    POSSIDETYPE: str = 'net'  # net or long/short, need to cancel all orders/positions to change
    assert TD_MODE in ['isolated', 'crossed'], f'{TD_MODE = }'
    assert POSSIDETYPE in ['net', 'long', 'short'], f'{POSSIDETYPE = }'

    if red_button:
        all_closed_positions = await close_all_positions()
        all_cancelled_orders = await cancel_all_orders()
        all_cancelled_algo_orders = await cancel_all_algo_orders_with_params()
        all_positions = await get_all_positions()
        all_orders = await get_all_orders()
        all_algo_orders = await get_all_algo_orders()
        print(f'{all_closed_positions = }')
        print(f'{all_cancelled_orders = }')
        print(f'{all_cancelled_algo_orders = }')
        print(f'{all_positions = }')
        print(f'{all_orders = }')
        print(f'{all_algo_orders = }')
        return {'red_button': 'ok',
                'all_closed_positions': all_closed_positions,
                'all_cancelled_orders': all_cancelled_orders,
                'all_cancelled_algo_orders': all_cancelled_algo_orders,
                'all_positions': all_positions,
                'all_orders': all_orders,
                'all_algo_orders': all_algo_orders
                }

    # Clean Input Data
    try:
        validated_params = await validate_okx_signal_params(okx_signal_input)
    except Exception as e:
        return {'error': str(e)}

    # Get back all the values validated
    instID = validated_params.get('instID')
    order_size = validated_params.get('order_size')
    leverage = validated_params.get('leverage')
    order_side = validated_params.get('order_side')
    order_type = validated_params.get('order_type')
    max_orderbook_limit_price_offset = validated_params.get('max_orderbook_limit_price_offset')
    flip_position_if_opposite_side = validated_params.get('flip_position_if_opposite_side')
    clear_prior_to_new_order = validated_params.get('clear_prior_to_new_order')
    red_button = validated_params.get('red_button')
    sl_trigger_price_offset = validated_params.get('sl_trigger_price_offset')
    tp_trigger_price_offset = validated_params.get('tp_trigger_price_offset')
    tp_trigger_price_type = validated_params.get('tp_trigger_price_type')
    sl_execution_price_offset = validated_params.get('sl_execution_price_offset')
    tp_execution_price_offset = validated_params.get('tp_execution_price_offset')
    sl_trigger_price_type = validated_params.get('sl_trigger_price_type')
    trailing_stop_activation_price_offset = validated_params.get('trailing_stop_activation_price_offset')
    trailing_stop_callback_offset = validated_params.get('trailing_stop_callback_offset')
    generated_client_order_id = validated_params.get('generated_client_order_id')
    take_profit_activated = validated_params.get('take_profit_activated')
    stop_loss_activated = validated_params.get('stop_loss_activated')
    trailing_stop_loss_activated = validated_params.get('trailing_stop_loss_activated')
    dca_parameters: List[DCAOrderParameters] or None = validated_params.get('dca_parameters')

    assert isinstance(instID, str), f'{instID = }'
    if clear_prior_to_new_order:
        await clear_orders_and_positions_for_instrument(instID)

    (simplified_balance_details, account_config, instrument_status_report) = await fetch_initial_data(TD_MODE,
                                                                                                      instId=instID)

    if leverage and leverage > 0:
        accountAPI.set_leverage(
            lever=leverage,
            mgnMode=TD_MODE,
            instId=instID,
            posSide=POSSIDETYPE
        )

    position = instrument_status_report.positions[0] if len(
        instrument_status_report.positions) > 0 else None  # we are only using net so only one position

    if order_side and order_size:
        ticker = await get_ticker(instId=instID)
        print(f'{ticker = }')
        ask_price = float(ticker.askPx) if ticker.askPx else ticker.bidPx  # fixme sometimes okx returns '' for askPx
        bid_price = float(ticker.bidPx)
        reference_price = ask_price if order_side == 'buy' else bid_price
        if position:
            position_side = 'buy' if float(position.pos) > 0 else 'sell' if float(
                position.pos) < 0 else None  # we are only using net so only one position
            if position_side is None:
                print(f'Closing all positions for {instID = } due to 0 net position')
                await close_all_positions(instId=instID)
                await cancel_all_algo_orders_with_params(instId=instID)
                await cancel_all_orders(instId=instID)
            elif order_side and position_side != order_side:
                if flip_position_if_opposite_side:
                    print(f'Flipping position from {position_side = } to {order_side = }')
                    await close_all_positions(instId=instID)
                    print(f'Closed all positions for {instID = }')

                    cancelled_orders = await cancel_all_orders(instId=instID)
                    print(f"Cancelling orders to flip position: \n"
                          f"    {cancelled_orders = }")
                    cancelled_algo_orders = await cancel_all_algo_orders_with_params(instId=instID)
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
                                await cancel_all_orders(orders_list=orders_to_cancel)
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
                        await cancel_all_orders(instId=instID)
                        await cancel_all_algo_orders_with_params(instId=instID)

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
            order_book = await get_order_book(instID, 400)
            limit_price = await prepare_limit_price(order_book, order_size, order_side, reference_price,
                                                    max_orderbook_price_offset=max_orderbook_limit_price_offset)
            print(f'Setting New Target Limit Price to {limit_price = }')

            order_request_dict['px'] = limit_price

        # Todo TP/SL add options for ordertypes other than limit, similar to how TP/SL's for DCA are configured
        if take_profit_activated:
            stop_surplus_trigger_price, stop_surplus_execute_price = calculate_tp_stop_prices_usd(
                order_side=order_side,
                reference_price=reference_price,
                tp_trigger_usd=tp_trigger_price_offset,
                tp_execute_usd=tp_execution_price_offset,
            )
            order_request_dict.update(
                tpTriggerPx=stop_surplus_trigger_price,
                tpOrdPx=stop_surplus_execute_price,
                tpTriggerPxType=tp_trigger_price_type,
                algoClOrdId=f'{generated_client_order_id}TPORSL'
            )
        if stop_loss_activated:
            stop_loss_trigger_price, stop_loss_execute_price = calculate_sl_stop_prices_usd(
                order_side=order_side,
                reference_price=reference_price,
                sl_trigger_usd=sl_trigger_price_offset,
                sl_execute_usd=sl_execution_price_offset,
            )
            order_request_dict.update(
                slTriggerPx=stop_loss_trigger_price,
                slOrdPx=stop_loss_execute_price,
                slTriggerPxType=sl_trigger_price_type,
                algoClOrdId=f'{generated_client_order_id}TPORSL'
            )

        order_placement_return = await place_order(**order_request_dict)

        print(f'{order_placement_return = }')

        # If error, cancel all orders and exit
        if order_placement_return and order_placement_return.sCode != '0':
            print(f'{order_placement_return.sMsg = }')
            await cancel_all_orders(instId=instID)
            await cancel_all_algo_orders_with_params(instId=instID)
            exit()

        if trailing_stop_loss_activated:
            activePx = None
            if trailing_stop_activation_price_offset:
                activePx = reference_price + trailing_stop_activation_price_offset if order_side == 'buy' else \
                    reference_price - trailing_stop_activation_price_offset

            # Create Trailing Stop Loss
            trailing_stop_order_placement_return = await place_algo_trailing_stop_loss(
                instId=instID,
                tdMode=TD_MODE,
                ordType="move_order_stop",
                side='buy' if order_side == 'sell' else 'sell',
                sz=order_size,
                activePx=activePx or reference_price,
                posSide=POSSIDETYPE,
                callbackRatio=trailing_stop_callback_offset,
                reduceOnly='true',
                algoClOrdId=f'{generated_client_order_id}TrailS',
                cxlOnClosePos="true",
            )
            print(f'{trailing_stop_order_placement_return = }')

    if dca_parameters and isinstance(dca_parameters, list):
        dca_orders_to_call = []
        _order_book = None
        for dca_order in dca_parameters:
            if dca_order.size <= 0:
                print(f'Ignoring DCA order with size {dca_order.size = }')
                continue

            dca_order_request_dict = dict(
                instId=instID,
                side=str(dca_order.side).lower(),
                tdMode=TD_MODE,
                posSide=POSSIDETYPE,
                sz=dca_order.size,
                ordType='trigger',
                triggerPx=dca_order.trigger_price,
                triggerPxType='last',
                orderPx=-1,  # Default to market order, update downstream if not
                algoClOrdId=f'{generate_random_string(16, "alphanumeric") + "DCA"}'
            )

            if not _order_book and dca_order.type != 'market':
                _order_book = await get_order_book(instID, 400)
            if dca_order.type != 'market':
                dca_order_request_dict['orderPx'] = await prepare_limit_price(
                    _order_book, dca_order.size,
                    str(dca_order.side).lower(),
                    dca_order.execution_price,
                    max_orderbook_price_offset=max_orderbook_limit_price_offset)

            if dca_order.tp_trigger_price_offset and dca_order.tp_execution_price_offset:
                stop_surplus_trigger_price, stop_surplus_execute_price = calculate_tp_stop_prices_usd(
                    order_side=str(dca_order.side).lower(),
                    reference_price=dca_order.execution_price,
                    tp_trigger_usd=dca_order.tp_trigger_price_offset,
                    tp_execute_usd=dca_order.tp_execution_price_offset,
                )
                dca_order_request_dict.update(
                    tpTriggerPx=stop_surplus_trigger_price,
                    tpOrdPx=stop_surplus_execute_price,
                    tpTriggerPxType=dca_order.tp_trigger_price_type,
                )
            if dca_order.sl_trigger_price_offset and dca_order.sl_execution_price_offset:
                stop_loss_trigger_price, stop_loss_execute_price = calculate_sl_stop_prices_usd(
                    order_side=str(dca_order.side).lower(),
                    reference_price=dca_order.execution_price,
                    sl_trigger_usd=dca_order.sl_trigger_price_offset,
                    sl_execute_usd=dca_order.sl_execution_price_offset,
                )
                dca_order_request_dict.update(
                    slTriggerPx=stop_loss_trigger_price,
                    slOrdPx=stop_loss_execute_price,
                    slTriggerPxType=dca_order.sl_trigger_price_type,
                )

            dca_orders_to_call.append(dca_order_request_dict)

        dca_orders_placement_return = await asyncio.gather(
            *[place_algo_order(**dca_order) for dca_order in dca_orders_to_call]
        )
        print(f'{dca_orders_placement_return = }')
    print('\n\nFINAL REPORT')
    return await fetch_status_report_for_instrument(instID, TD_MODE)


async def fetch_fill_history(start_timestamp, end_timestamp, instType=None):
    """
    Fetches the fill history for a specific period and instrument type.

    :param start_timestamp: The starting timestamp for the fill history.
    :type start_timestamp: int
    :param end_timestamp: The ending timestamp for the fill history.
    :type end_timestamp: int
    :param instType: The type of instrument for the fill history, defaults to None.
    :type instType: str, optional
    :returns: A list of fill entries.
    :raises AssertionError: If the requested period is outside the allowed range based on the instrument type.
    """
    """

    Note:
        If instType passed in then up to 30 days ago the data can be pulled, but if None then only up to 3 days, verify
            Im refering to AGO!!! meaning from now

    :param start_timestamp:
    :param end_timestamp:
    :param instType:
    :return:
    """
    if instType is None:
        assert (time.time() - start_timestamp) < 259200, f'{time.time() - start_timestamp = }'
    else:
        assert (time.time() - start_timestamp) < 2592000, f'{time.time() - start_timestamp = }'

    limit = 100
    after = ''
    all_data = []
    request_count = 0
    start_time = time.time()

    while True:

        try:
            fills_response = tradeAPI.get_fills_history(
                instType=instType,
                uly='',
                instId='',
                ordId='',
                after=after,
                before='',
                limit=limit,
                instFamily='',
                begin=start_timestamp,
                end=end_timestamp
            )
            if fills_response.get('code') != '0':
                break

            fills_message_data = fills_response['data']
            if not fills_message_data:
                break  # Break if no data is returned

            all_data.extend(fills_message_data)

            # Check if we have reached the start_timestamp
            if int(fills_message_data[-1]['ts']) <= start_timestamp:
                print(f'Found the start_timestamp: {start_timestamp = }')
                break  # Exit the loop if we have reached the start_timestamp

            after = fills_message_data[-1]['billId']  # Prepare the 'after' for the next request
            print(f'{after = }')
            request_count += 1
            if request_count % 10 == 0:
                elapsed = time.time() - start_time
                if elapsed < 2:
                    # time.sleep(2 - elapsed)
                    await asyncio.sleep(2 - elapsed)
                start_time = time.time()


        except HTTPError as http_err:
            logger.error(f'HTTP error occurred: {http_err}')
            break  # Optional: Decide whether to break or retry
        except Exception as err:
            logger.error(f'Other error occurred: {err}')
            break  # Optional: Decide whether to break or retry

    return [FillEntry(**fill) for fill in all_data]


async def okx_premium_indicator_handler(indicator_input: Union[OKXPremiumIndicatorSignalRequestForm, dict]):
    """
    Handles incoming premium indicator signals for trading on the OKX platform. It processes the signals,
    interprets the trading instructions, manages positions based on the received signals, and executes trading actions.

    :param indicator_input: The input containing the signals and parameters from the premium indicator.
                            This can be an instance of PremiumIndicatorSignalRequestForm or a dictionary
                            that corresponds to the structure of PremiumIndicatorSignalRequestForm.
    :type indicator_input: OKXPremiumIndicatorSignalRequestForm or dict

    :returns: A dictionary detailing the outcome of the signal processing. If the processing is successful, it includes
              the 'instrument_status_report' which is a comprehensive status report of the instrument after handling the signal.
              In case of an error, it returns a message detailing the issue.

    Process Flow:
    1. Validates the input type and converts it into PremiumIndicatorSignalRequestForm if necessary.
    2. Extracts and processes trading signals (like Bearish, Bullish, and their respective exit signals) from the input.
    3. Determines the trading action (buy/sell) based on the processed signals.
    4. Fetches the current positions for the given instrument ID and aligns them with the received signals.
    5. Prepares the trading action by setting order sides, clearing prior orders if needed, and handling the 'red_button' emergency stop.
    6. Passes the processed signal to `okx_signal_handler` for executing the trading operations on the OKX platform.
    7. Returns a success message with the 'instrument_status_report' or an error message in case of an exception.

    :raises Exception: Catches and logs any exceptions that occur during the processing of the signal, returning a detailed error message.

    Note:
    The major difference between the `okx_signal_handler` and `okx_premium_indicator` is that the latter is
    specifically designed to handle premium indicator signals (TV), and it includes additional processing
    steps for interpreting the signals and aligning them with the current positions.
    """

    if isinstance(indicator_input, OKXPremiumIndicatorSignalRequestForm):
        input_to_pass = indicator_input.model_dump()
    elif isinstance(indicator_input, dict):
        input_to_pass = indicator_input
    else:
        return {"detail": f"Invalid input type {type(indicator_input)}"}

    indicator_input = OKXPremiumIndicatorSignalRequestForm(**input_to_pass)
    try:
        pprint(f'{indicator_input.OKXSignalInput = }')
        pprint(f'{indicator_input.PremiumIndicatorSignals = }')

        # Interpret Signals
        premium_indicator = indicator_input.PremiumIndicatorSignals

        premium_indicator.Bearish = int(premium_indicator.Bearish)
        premium_indicator.Bearish_plus = int(premium_indicator.Bearish_plus)
        premium_indicator.Bullish = int(premium_indicator.Bullish)
        premium_indicator.Bullish_plus = int(premium_indicator.Bullish_plus)
        premium_indicator.Bearish_Exit = 0 if (premium_indicator.Bearish_Exit in ['null', 0, None]) else float(
            premium_indicator.Bearish_Exit)
        premium_indicator.Bullish_Exit = 0 if (premium_indicator.Bullish_Exit in ['null', 0, None]) else float(
            premium_indicator.Bullish_Exit)

        _order_side = None
        _close_signal = None
        _red_button = indicator_input.OKXSignalInput.red_button
        if premium_indicator.Bearish or premium_indicator.Bearish_plus:
            _order_side = 'sell'
        elif premium_indicator.Bullish or premium_indicator.Bullish_plus:
            _order_side = 'buy'
        if premium_indicator.Bearish_Exit:
            _close_signal = 'exit_sell'
        elif premium_indicator.Bullish_Exit:
            _close_signal = 'exit_buy'

        instId_positions = await get_all_positions(instId=indicator_input.OKXSignalInput.instID)
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
        print(f'{_red_button = }')
        if _order_side or _close_signal or _red_button:
            okx_signal = indicator_input.OKXSignalInput

            okx_signal.order_side = _order_side if _order_side else ''
            okx_signal.clear_prior_to_new_order = True if okx_signal.clear_prior_to_new_order or _close_signal else False

            if _close_signal:  # FIXME this works for Premium indicator but might have issues if not handled in order
                okx_signal.order_side = ''

            pprint(f'updated-{premium_indicator = }')
            pprint(f'updated-{okx_signal= }')

            assert indicator_input.OKXSignalInput, "OKXSignalInput is None"
            okx_signal_input = indicator_input.OKXSignalInput
            instrument_status_report: InstrumentStatusReport = await okx_signal_handler(**okx_signal_input.model_dump())
            pprint(instrument_status_report)
            assert instrument_status_report, "Instrument Status Report is None, check the Instrument ID"
            return {"detail": "okx signal received", "instrument_status_report": instrument_status_report}
        return {"detail": "okx signal received but no action taken"}
    except Exception as e:
        print(f"Exception in okx_premium_indicator {e}")
        return {"detail": "okx signal received but there was an exception, check the logs", "exception": str(e)}


if __name__ == '__main__':
    import dotenv

    dotenv.load_dotenv(dotenv.find_dotenv())

    # Define the test function to be used
    TEST_FUNCTION = 'okx_premium_indicator'

    # Immediately execute the 'red button' functionality to clear all positions and orders
    # TODO: Ensure only relevant orders/positions are handled.
    # asyncio.run(okx_signal_handler(red_button=True))

    # Branching logic based on the test function chosen
    if TEST_FUNCTION == 'okx_signal_handler':
        # Execute the 'okx_signal_handler' with predefined parameters for testing
        response = asyncio.run(okx_signal_handler(
            # Global
            instID="BTC-USDT-240628",
            leverage=5,
            max_orderbook_limit_price_offset=None,
            clear_prior_to_new_order=False,
            red_button=False,
            # Principal Order
            usd_order_size=100,
            order_side="BUY",
            order_type="MARKET",
            flip_position_if_opposite_side=True,
            # Principal Order's TP/SL/Trail
            # tp_trigger_price_offset=100,
            # tp_execution_price_offset=90,
            # sl_trigger_price_offset=100,
            # sl_execution_price_offset=90,
            # trailing_stop_activation_price_offset=100,
            # trailing_stop_callback_offset=10,
            # DCA Orders (are not linked to the principal order)
            # dca_parameters=[
            #     DCAInputParameters(
            #         usd_amount=100,
            #         order_type="LIMIT",
            #         order_side="BUY",
            #         trigger_price_offset=100,
            #         execution_price_offset=90,
            #         tp_trigger_price_offset=100,
            #         tp_execution_price_offset=90,
            #         sl_trigger_price_offset=100,
            #         sl_execution_price_offset=90
            #     ),
            #     DCAInputParameters(
            #         usd_amount=100,
            #         order_type="LIMIT",
            #         order_side="BUY",
            #         trigger_price_offset=150,
            #         execution_price_offset=149,
            #         tp_trigger_price_offset=100,
            #         tp_execution_price_offset=90,
            #         sl_trigger_price_offset=100,
            #         sl_execution_price_offset=90
            #     )
            # ]
        ))
    elif TEST_FUNCTION == 'okx_premium_indicator':
        # Load a payload from a file for testing the 'okx_premium_indicator'
        with open('../tradingview_tools/tradingview_debug_message.json', 'r') as f:
            webhook_payload = json.load(f)

        # Construct the signal request form
        indicator_input = OKXPremiumIndicatorSignalRequestForm(**webhook_payload)


        # Process the indicator input and store the result
        response = asyncio.run(okx_premium_indicator_handler(indicator_input))

        # # Optionally Use a request instead of calling the function directly
        # response = requests.post(
        #     'http://localhost:8080/tradingview/premium_indicator/', # Local
        #     # 'http://localhost/api/tradingview/premium_indicator', # Docker
        #     # 'http://34.170.145.146/api/tradingview/premium_indicator', # GCP
        #     # 'http://34.170.145.146:8080/tradingview/premium_indicator/', # GCP
        #                          json=indicator_input.model_dump()
        # )
        # print(f'{response.content = }')
        # response = response.json()



    else:
        # Handle invalid test function selection
        raise ValueError(f'Invalid test function {TEST_FUNCTION = }')

    # Print the final response for debugging
    print(f'{response = }')

    # Validation and print statements for the instrument status report
    if response is None:
        print("No response")
        exit()

    if isinstance(response, InstrumentStatusReport):
        instrument_report = response
    elif isinstance(response, dict):
        instrument_report = response.get('instrument_status_report')
        if instrument_report is None:
            print("No instrument status report")
            exit()
    else:
        print("No instrument status report")
        exit()

    # Debugging print statements for the instrument report
    print(f'{instrument_report = }')
    pprint(f'{instrument_report.positions = }')
    pprint(f'{len(instrument_report.positions) = }')
    pprint(f'{instrument_report.positions[0].pos = }')
    pprint(f'{instrument_report.orders = }')
    pprint(f'{instrument_report.algo_orders = }')
