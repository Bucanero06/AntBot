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
from typing import List, Any, Optional, Dict, Union
from urllib.error import HTTPError

import dotenv

from pyokx.data_structures import (Order, Cancelled_Order, Order_Placement_Return,
                                   Position, Closed_Position, Ticker,
                                   Algo_Order, Algo_Order_Placement_Return,
                                   AccountBalanceDetails, AccountBalanceData,
                                   AccountConfigData, MaxOrderSizeData, MaxAvailSizeData, Cancelled_Algo_Order,
                                   Instrument, Orderbook_Snapshot, Bid, Ask,
                                   Simplified_Balance_Details, InstrumentStatusReport,
                                   PremiumIndicatorSignalRequestForm, FillEntry)
from pyokx.okx_market_maker.utils.OkxEnum import InstType
from redis_tools.utils import serialize_for_redis
from shared import logging
from shared.tmp_shared import calculate_tp_stop_prices, calculate_sl_stop_prices, FunctionCall, execute_function_calls

logger = logging.setup_logger(__name__)

dotenv.load_dotenv(dotenv.find_dotenv())
from pyokx.Futures_Exchange_Client import OKX_Futures_Exchange_Client as OKXClient

okx_client = OKXClient(api_key=os.getenv('OKX_API_KEY'), api_secret=os.getenv('OKX_SECRET_KEY'),
                       passphrase=os.getenv('OKX_PASSPHRASE'), sandbox_mode=os.getenv('OKX_SANDBOX_MODE'))
tradeAPI = okx_client.tradeAPI
marketAPI = okx_client.marketAPI
accountAPI = okx_client.accountAPI
publicAPI = okx_client.publicAPI

REDIS_STREAM_MAX_LEN = int(os.getenv('REDIS_STREAM_MAX_LEN', 1000))

"""NOTE: THE MODULE NEEDS TO BE UPDATED WITH ENUMS AND STRUCTURED DATA TYPES WHERE APPLICABLE"""


def get_request_data(returned_data, target_data_structure):
    """
    Processes the returned data from an API call, mapping it to the specified data structure.

    Args:
        returned_data (dict): The raw data returned from the API call.
        target_data_structure (class): The class to which the returned data items will be mapped.

    Returns:
        List[Any]: A list of instances of the target data structure class, populated with the returned data.
    """
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
    """
    Provides functionality to search for instruments within a provided list of instruments based on various criteria
    such as instrument ID, type, or underlying asset.

    Args:
        instruments (List[Instrument]): A list of instruments to search within.

    Methods:
        find_by_instId: Returns an instrument matching a specific instrument ID.
        find_by_type: Returns all instruments of a specific type.
        find_by_underlying: Returns all instruments with a specific underlying asset.
    """

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


def get_ticker_with_higher_volume(seed_symbol_name, instrument_type="FUTURES", top_n=1):
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


def assert_okx_account_level(account_level: [1, 2, 3, 4]):
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
    """
    Validates if the input string is alphanumeric and conforms to the specified maximum length.

    Args:
        string (str): The string to validate.
        max_length (int): The maximum allowable length for the string.

    Returns:
        bool: True if the string is alphanumeric and does not exceed the max_length, False otherwise.
    """

    return bool(re.match('^[a-zA-Z0-9]{1,' + str(max_length) + '}$', string))


def get_all_orders(instType: str = None, instId: str = None):
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
    return get_request_data(tradeAPI.get_order_list(**params), Order)


def cancel_all_orders(orders_list: List[Order] = None, instType: InstType = None, instId: str = None):
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


def close_all_positions(positions_list: List[Position] = None, instType: InstType = None, instId: str = None):
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

    if result["code"] == "0":
        print("Successful order request，\n  order_id = ", result["data"][0]["ordId"])

    else:
        print(f'{result = }')
        print("Unsuccessful order request，\n  error_code = ", result["msg"], ", \n  Error_message = ",
              result["msg"])
    return get_request_data(result, Order_Placement_Return)[0]


def get_ticker(instId):
    """
    Retrieves the latest ticker information for a specified instrument.

    :param instId: The instrument ID for which to get the ticker information.
    :type instId: str
    :returns: The latest ticker information for the specified instrument.
    """
    return get_request_data(marketAPI.get_ticker(instId=instId), Ticker)[0]


def get_all_algo_orders(instId=None, ordType=None):
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

    if result["code"] == "0":
        print("Successful order request，\n  order_id = ", result["data"][0]["algoId"])

    else:
        print(f'{result = }')
        print("Unsuccessful order request，\n  error_code = ", result["msg"], ", \n  Error_message = ",
              result["msg"])

    return get_request_data(result, Algo_Order_Placement_Return)


def get_account_balance():
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


def get_account_config():
    """
    Retrieves the account configuration details.

    :returns: The account configuration data, structured according to the AccountConfigData class.
    """
    return AccountConfigData(**accountAPI.get_account_config()['data'][0])


def get_max_order_size(instId, tdMode):
    """
    Retrieves the maximum order size for a specific instrument and trade mode.

    :param instId: The instrument ID for which to get the maximum order size.
    :type instId: str
    :param tdMode: The trade mode (e.g., 'cash', 'margin').
    :type tdMode: str
    :returns: The maximum order size data, structured according to the MaxOrderSizeData class.
    """
    return MaxOrderSizeData(**accountAPI.get_max_order_size(instId=instId, tdMode=tdMode)['data'][0])


def get_max_avail_size(instId, tdMode):
    """
    Retrieves the maximum available size for trading a specific instrument in a specific trade mode.

    :param instId: The instrument ID for which to get the maximum available size.
    :type instId: str
    :param tdMode: The trade mode (e.g., 'cash', 'margin').
    :type tdMode: str
    :returns: The maximum available size data, structured according to the MaxAvailSizeData class.
    """
    return MaxAvailSizeData(**accountAPI.get_max_avail_size(instId=instId, tdMode=tdMode)['data'][0])


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


def fetch_status_report_for_instrument(instId, TD_MODE):
    """
    Fetches a comprehensive status report for a specific instrument.

    :param instId: The instrument ID for which to fetch the status report.
    :type instId: str
    :param TD_MODE: The trade mode (e.g., 'cash', 'margin').
    :type TD_MODE: str
    :returns: A status report for the instrument, structured according to the InstrumentStatusReport class.
    """
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
    """
    Fetches initial data including account balance, account configuration, and instrument status.

    :param TD_MODE: The trade mode (e.g., 'cash', 'margin').
    :type TD_MODE: str
    :param instId: The instrument ID for which to fetch the data, defaults to None.
    :type instId: str, optional
    :returns: A tuple containing simplified balance details, account configuration data, and instrument status report.
    """
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
    """
    Clears all orders and positions for a specific instrument.

    :param instId: The instrument ID for which to clear orders and positions.
    :type instId: str
    """
    print(f'{ close_all_positions(instId=instId) = }')
    print(f'{ cancel_all_orders(instId=instId) = }')
    print(f'{ cancel_all_algo_orders_with_params(instId=instId) = }')


def get_order_book(instId, depth):
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


def prepare_limit_price(order_book: Orderbook_Snapshot, quantity: Union[int, float], side, reference_price: float,
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


def clean_and_verify_instID(instID):
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
    instrument = instrument_searcher.find_by_instId(instID)
    assert instrument is not None, f'Instrument {instID} not found in {all_futures_instruments = }'
    # assert instrument.instType == InstType.FUTURES, f'{instrument.instType = }'
    return instID


async def okx_signal_handler(
        instID: str = '',
        order_size: int = None,
        leverage: int = None,
        order_side: str = None,
        order_type: str = None,
        max_orderbook_limit_price_offset: float = None,
        flip_position_if_opposite_side: bool = False,
        clear_prior_to_new_order: bool = False,
        red_button: bool = False,
        order_usd_amount: float = None,
        stop_loss_trigger_percentage: float = None,
        take_profit_trigger_percentage: float = None,
        tp_trigger_price_type: str = None,
        stop_loss_price_offset: float = None,
        tp_price_offset: float = None,
        sl_trigger_price_type: str = None,
        trailing_stop_activation_percentage: float = None,
        trailing_stop_callback_ratio: float = None,
):
    """
    Handles trading signals for the OKX platform, executing trades based on the specified parameters and current market conditions.

    :param instID: Instrument ID for trading.
    :type instID: str, optional
    :param order_size: Size of the order to execute.
    :type order_size: int, optional
    :param leverage: Leverage to apply for the trade.
    :type leverage: int, optional
    :param order_side: Side of the order ('buy' or 'sell').
    :type order_side: str, optional
    :param order_type: Type of the order (e.g., 'limit', 'market').
    :type order_type: str, optional
    :param max_orderbook_limit_price_offset: Maximum offset for the limit price from the order book.
    :type max_orderbook_limit_price_offset: float, optional
    :param flip_position_if_opposite_side: Flag to indicate if the position should be flipped if the current position is on the opposite side.
    :type flip_position_if_opposite_side: bool, optional
    :param clear_prior_to_new_order: Flag to clear existing orders before placing a new order.
    :type clear_prior_to_new_order: bool, optional
    :param red_button: Emergency stop flag to cancel all orders and close all positions.
    :type red_button: bool, optional
    :param order_usd_amount: Amount in USD for the order, used for calculations if specified.
    :type order_usd_amount: float, optional
    :param stop_loss_trigger_percentage: Percentage for triggering the stop loss.
    :type stop_loss_trigger_percentage: float, optional
    :param take_profit_trigger_percentage: Percentage for triggering take profit.
    :type take_profit_trigger_percentage: float, optional
    :param tp_trigger_price_type: Type of trigger price for take profit ('index', 'mark', 'last').
    :type tp_trigger_price_type: str, optional
    :param stop_loss_price_offset: Offset price for stop loss.
    :type stop_loss_price_offset: float, optional
    :param tp_price_offset: Offset price for take profit.
    :type tp_price_offset: float, optional
    :param sl_trigger_price_type: Type of trigger price for stop loss ('index', 'mark', 'last').
    :type sl_trigger_price_type: str, optional
    :param trailing_stop_activation_percentage: Activation percentage for the trailing stop loss.
    :type trailing_stop_activation_percentage: float, optional
    :param trailing_stop_callback_ratio: Callback ratio for the trailing stop loss.
    :type trailing_stop_callback_ratio: float, optional
    :returns: An object containing the status report of the instrument after processing the signal, detailing the positions, orders, and algo orders.

    Process Flow:
    1. Validates and processes input parameters, preparing the trading signal.
    2. Checks and manages current positions based on new signal, potentially flipping positions or clearing orders as configured.
    3. Calculates and sets order parameters such as price and size, leveraging current market data and user preferences.
    4. Executes the trading actions (placing/canceling orders, opening/closing positions) on the OKX platform.
    5. Fetches and returns an updated status report of the instrument, reflecting the changes made by the executed signal.

    :raises Exception: Catches and logs any exceptions that occur during signal handling, providing detailed error information.
    """
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

    if not tp_trigger_price_type:
        tp_trigger_price_type = 'last'
    if not sl_trigger_price_type:
        sl_trigger_price_type = 'last'
    if not order_type:
        order_type = 'limit'
    if not order_side:
        order_side = ''
    if not order_size:
        order_size = 0
    if not leverage:
        leverage = 0
    if not max_orderbook_limit_price_offset:
        max_orderbook_limit_price_offset = False
    if not stop_loss_trigger_percentage:
        stop_loss_trigger_percentage = False
    if not take_profit_trigger_percentage:
        take_profit_trigger_percentage = False
    if not stop_loss_price_offset:
        stop_loss_price_offset = False
    if not tp_price_offset:
        tp_price_offset = False
    if not trailing_stop_activation_percentage:
        trailing_stop_activation_percentage = False
    if not trailing_stop_callback_ratio:
        trailing_stop_callback_ratio = False
    if not flip_position_if_opposite_side:
        flip_position_if_opposite_side = False
    if not clear_prior_to_new_order:
        clear_prior_to_new_order = False

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

    position = instrument_status_report.positions[0] if len(
        instrument_status_report.positions) > 0 else None  # we are only using net so only one position

    if order_side:
        ticker = get_ticker(instId=instID)
        print(f'{ticker = }')
        ask_price = float(ticker.askPx) if ticker.askPx else ticker.bidPx  # fixme sometimes okx returns '' for askPx
        bid_price = float(ticker.bidPx)
        reference_price = ask_price if order_side == 'buy' else bid_price
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
    instType = 'FUTURES'
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


async def okx_premium_indicator(indicator_input: PremiumIndicatorSignalRequestForm):
    """
    Handles incoming premium indicator signals for trading on the OKX platform. It processes the signals,
    interprets the trading instructions, manages positions based on the received signals, and executes trading actions.

    :param indicator_input: The input containing the signals and parameters from the premium indicator.
                            This can be an instance of PremiumIndicatorSignalRequestForm or a dictionary
                            that corresponds to the structure of PremiumIndicatorSignalRequestForm.
    :type indicator_input: PremiumIndicatorSignalRequestForm or dict

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
    """
    if isinstance(indicator_input, PremiumIndicatorSignalRequestForm):
        input_to_pass = indicator_input
    elif isinstance(indicator_input, dict):
        input_to_pass = indicator_input
    else:
        return {"detail": f"Invalid input type {type(indicator_input)}"}
    indicator_input = PremiumIndicatorSignalRequestForm(**input_to_pass)

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
        _red_button = indicator_input.OKXSignalInput.red_button
        if premium_indicator.Bearish or premium_indicator.Bearish_plus:
            _order_side = 'buy'
        elif premium_indicator.Bullish or premium_indicator.Bullish_plus:
            _order_side = 'sell'
        if premium_indicator.Bearish_Exit:
            _close_signal = 'exit_buy'
        elif premium_indicator.Bullish_Exit:
            _close_signal = 'exit_sell'

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
            instrument_status_report: InstrumentStatusReport = okx_signal_handler(**okx_signal_input.model_dump())
            pprint(instrument_status_report)
            assert instrument_status_report, "Instrument Status Report is None, check the Instrument ID"
            return {"detail": "okx signal received", "instrument_status_report": instrument_status_report}
        return {"detail": "okx signal received but no action taken"}
    except Exception as e:
        print(f"Exception in okx_premium_indicator {e}")
        return {"detail": "okx signal received but there was an exception, check the logs", "exception": str(e)}


if __name__ == '__main__':
    import dotenv

    # Define the test function to be used
    TEST_FUNCTION = 'okx_signal_handler'

    # Immediately execute the 'red button' functionality to clear all positions and orders
    # TODO: Ensure only relevant orders/positions are handled.
    okx_signal_handler(red_button=True)

    # Load environment variables from a .env file
    dotenv.load_dotenv(dotenv.find_dotenv())

    # Branching logic based on the test function chosen
    if TEST_FUNCTION == 'okx_signal_handler':
        # Execute the 'okx_signal_handler' with predefined parameters for testing
        response = okx_signal_handler(
            # Parameters for the 'okx_signal_handler'
            instID="BTC-USDT-240628",
            order_size=1,
            leverage=5,
            order_side="",
            order_type="MARKET",
            max_orderbook_limit_price_offset=None,
            flip_position_if_opposite_side=True,
            clear_prior_to_new_order=False,
            red_button=False,
            # More parameters...
        )
    elif TEST_FUNCTION == 'okx_premium_indicator':
        # Load a payload from a file for testing the 'okx_premium_indicator'
        with open('../debugging_payload.json', 'r') as f:
            webhook_payload = json.load(f)

        # Debugging print statement
        pprint(f'{webhook_payload = }')

        # Construct the signal request form
        indicator_input = PremiumIndicatorSignalRequestForm(**webhook_payload)
        import redis

        # Connect to Redis server
        r = redis.Redis(host='localhost', port=6379, db=0)

        # Prepare and send a message to a Redis stream for debugging
        redis_ready_message = serialize_for_redis(indicator_input.model_dump())
        r.xadd(f'okx:webhook@premium_indicator@input', fields=redis_ready_message)

        # Process the indicator input and store the result
        result = okx_premium_indicator(indicator_input)

        # Get the response from the 'okx_premium_indicator' function
        response = okx_premium_indicator(webhook_payload)
        if isinstance(result, dict):
            # Send the result to a Redis stream for debugging
            r.xadd(f'okx:webhook@premium_indicator@result', fields=serialize_for_redis(result))
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