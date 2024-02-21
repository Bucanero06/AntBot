from datetime import datetime, timedelta


def ccy_contracts_to_usd(contracts_amount, ccy_contract_size, ccy_last_price, usd_base_ratio, leverage=None):
    base_cost_of_one_contract = ccy_contract_size * ccy_last_price
    base_total_cost = base_cost_of_one_contract * contracts_amount
    total_cost_usd = base_total_cost / usd_base_ratio
    if not leverage:
        return total_cost_usd
    else:
        leverage = 10  # example leverage
        return total_cost_usd / leverage


# TODO TEST THE CONVERSIONS
# Getting error:
#     url: /api/v5/market/ticker?instId=BTC-USDT-240329
#     antbot-okx_rest-1  | {'error': 'USD equivalent of 100.0 is too much to buy the \n'
#     antbot-okx_rest-1  |           'maximum quantity of 3000 contracts for 0.01 at \n'
#     antbot-okx_rest-1  |           '53163.7 with 5 leverage. The maximum cost is 6.0 USDT'}
# The starting boundries will be around the validate_okx_signal_params function in the rest_handling.py file
def ccy_usd_to_contracts(usd_equivalent, ccy_contract_size, ccy_last_price,
                         minimum_contract_size,
                         max_market_contract_size,
                         usd_base_ratio, leverage, ctValCcy):
    if ctValCcy == 'USD':
        cost_of_one_contract_in_usd = ccy_contract_size
        base_equivalent = usd_equivalent
    else:
        cost_of_one_contract_in_usd = ccy_contract_size * ccy_last_price
        base_equivalent = usd_equivalent * usd_base_ratio

    if not leverage:
        leverage = 1

    leveraged_cost_of_one_contract_usd = cost_of_one_contract_in_usd / leverage

    print(f"ctValCcy: {ctValCcy}")
    print(f"ccy_contract_size: {ccy_contract_size}")
    print(f"Cost of one contract in USD: {cost_of_one_contract_in_usd}")
    print(f"Cost of one contract in USD with leverage: {leveraged_cost_of_one_contract_usd}")

    max_contracts = base_equivalent / leveraged_cost_of_one_contract_usd
    max_contracts = int(max_contracts)  # round down to the nearest whole number
    # Raise error if max_contracts is less than min_order_quantity or greater than max_market_order_quantity
    if max_contracts < minimum_contract_size:
        minimum_cost = minimum_contract_size * leveraged_cost_of_one_contract_usd
        raise ValueError(f"USD equivalent of {usd_equivalent} is not enough to buy the \n"
                         f"minimum quantity of {minimum_contract_size} contracts for {ccy_contract_size} at \n"
                         f"{ccy_last_price} with {leverage} leverage. The minimum cost is {minimum_cost} USDT")
    if max_contracts > max_market_contract_size:
        max_cost = max_market_contract_size * leveraged_cost_of_one_contract_usd
        raise ValueError(f"USD equivalent of {usd_equivalent} is too much to buy the \n"
                         f"maximum quantity of {max_market_contract_size} contracts for {ccy_contract_size} at \n"
                         f"{ccy_last_price} with {leverage} leverage. The maximum cost is "
                         f"{max_cost} USDT")
    print(f"Suggested N contracts: {max_contracts} for a total cost of {base_equivalent} USDT")
    return max_contracts


def calculate_stop_prices(order_side, reference_price, sl_trigger_price_offset,
                          stop_surplus_trigger_percentage, sl_execution_price_offset, stop_surplus_price_offset):
    """
    Calculate stop loss and stop surplus trigger and execute prices based on the order side.

    :param order_side: Either 'buy' or 'sell'.
    :param current_market_price: Current market price of the asset.
    :param sl_trigger_price_offset: Percentage for calculating the stop loss trigger price.
    :param stop_surplus_trigger_percentage: Percentage for calculating the stop surplus trigger price.
    :param sl_execution_price_offset: Offset for calculating the stop loss execute price.
    :param stop_surplus_price_offset: Offset for calculating the stop surplus execute price.
    :return: Tuple containing stop_loss_trigger_price, stop_surplus_trigger_price, stop_loss_execute_price, stop_surplus_execute_price.
    :raises ValueError: If order_side is not 'buy' or 'sell'.
    """

    if order_side == 'sell':
        stop_loss_trigger_price = reference_price * (1 + sl_trigger_price_offset / 100)
        stop_loss_execute_price = stop_loss_trigger_price + sl_execution_price_offset
        stop_surplus_trigger_price = reference_price * (1 - stop_surplus_trigger_percentage / 100)
        stop_surplus_execute_price = stop_surplus_trigger_price - stop_surplus_price_offset
        assert stop_loss_execute_price > stop_loss_trigger_price, "stop_loss_execute_price must be less than stop_loss_trigger_price"
        assert stop_surplus_execute_price < stop_surplus_trigger_price, "stop_surplus_execute_price must be greater than stop_surplus_trigger_price"
    elif order_side == 'buy':
        stop_surplus_trigger_price = reference_price * (1 + stop_surplus_trigger_percentage / 100)
        stop_surplus_execute_price = stop_surplus_trigger_price + stop_surplus_price_offset
        stop_loss_trigger_price = reference_price * (1 - sl_trigger_price_offset / 100)
        stop_loss_execute_price = stop_loss_trigger_price - sl_execution_price_offset
        assert stop_loss_execute_price < stop_loss_trigger_price, "stop_loss_execute_price must be greater than stop_loss_trigger_price"
        assert stop_surplus_execute_price > stop_surplus_trigger_price, "stop_surplus_execute_price must be less than stop_surplus_trigger_price"
    else:
        raise ValueError('order_side must be either "buy" or "sell"')

    return round(stop_loss_trigger_price, 2), round(stop_surplus_trigger_price, 2), round(stop_loss_execute_price,
                                                                                          2), round(
        stop_surplus_execute_price, 2)


def calculate_tp_stop_prices(order_side, reference_price, tp_trigger_percentage, tp_execution_price_offset):
    """
    Calculate take profit trigger and execute prices based on the order side.

    :param order_side: Either 'buy' or 'sell'.
    :param current_market_price: Current market price of the asset.
    :param tp_trigger_percentage: Percentage for calculating the take profit trigger price.
    :param tp_execution_price_offset: Offset for calculating the take profit execute price.
    :return: Tuple containing tp_trigger_price, tp_execute_price.
    :raises ValueError: If order_side is not 'buy' or 'sell'.
    """

    if order_side == 'sell':
        tp_trigger_price = reference_price * (1 - tp_trigger_percentage / 100)
        tp_execute_price = tp_trigger_price - tp_execution_price_offset
        assert tp_execute_price < tp_trigger_price, "tp_execute_price must be less than tp_trigger_price"
    elif order_side == 'buy':
        tp_trigger_price = reference_price * (1 + tp_trigger_percentage / 100)
        tp_execute_price = tp_trigger_price + tp_execution_price_offset
        assert tp_execute_price > tp_trigger_price, "tp_execute_price must be greater than tp_trigger_price"
    else:
        raise ValueError('order_side must be either "buy" or "sell"')

    return round(tp_trigger_price, 2), round(tp_execute_price, 2)


def calculate_sl_stop_prices(order_side, reference_price, sl_trigger_percentage, sl_price_offset):
    """
    Calculate stop loss trigger and execute prices based on the order side.

    :param order_side: Either 'buy' or 'sell'.
    :param current_market_price: Current market price of the asset.
    :param sl_trigger_percentage: Percentage for calculating the stop loss trigger price.
    :param sl_price_offset: Offset for calculating the stop loss execute price.
    :return: Tuple containing sl_trigger_price, sl_execute_price.
    :raises ValueError: If order_side is not 'buy' or 'sell'.
    """

    if order_side == 'sell':
        sl_trigger_price = reference_price * (1 + sl_trigger_percentage / 100)
        sl_execute_price = sl_trigger_price + sl_price_offset
        assert sl_execute_price > sl_trigger_price, "sl_execute_price must be greater than sl_trigger_price"
    elif order_side == 'buy':
        sl_trigger_price = reference_price * (1 - sl_trigger_percentage / 100)
        sl_execute_price = sl_trigger_price - sl_price_offset
        assert sl_execute_price < sl_trigger_price, "sl_execute_price must be less than sl_trigger_price"
    else:
        raise ValueError('order_side must be either "buy" or "sell"')

    return round(sl_trigger_price, 2), round(sl_execute_price, 2)


def calculate_tp_stop_prices_usd(order_side, reference_price, tp_trigger_usd, tp_execute_usd):
    """
    Calculate take profit trigger and execute prices based on the order side using USD values.

    :param order_side: Either 'buy' or 'sell'.
    :param reference_price: Current market price of the asset.
    :param tp_trigger_usd: USD value for calculating the take profit trigger price.
    :param tp_execute_usd: USD value for calculating the take profit execute price.
    :return: Tuple containing tp_trigger_price, tp_execute_price.
    :raises ValueError: If order_side is not 'buy' or 'sell'.
    """

    if order_side == 'sell':
        tp_trigger_price = reference_price - tp_trigger_usd
        tp_execute_price = tp_trigger_price - tp_execute_usd
        assert tp_execute_price < tp_trigger_price, "tp_execute_price must be less than tp_trigger_price"
    elif order_side == 'buy':
        tp_trigger_price = reference_price + tp_trigger_usd
        tp_execute_price = tp_trigger_price + tp_execute_usd
        assert tp_execute_price > tp_trigger_price, "tp_execute_price must be greater than tp_trigger_price"
    else:
        raise ValueError('order_side must be either "buy" or "sell"')

    return round(tp_trigger_price, 2), round(tp_execute_price, 2)


def calculate_sl_stop_prices_usd(order_side, reference_price, sl_trigger_usd, sl_execute_usd):
    """
    Calculate stop loss trigger and execute prices based on the order side using USD values.

    :param order_side: Either 'buy' or 'sell'.
    :param reference_price: Current market price of the asset.
    :param sl_trigger_usd: USD value for calculating the stop loss trigger price.
    :param sl_execute_usd: USD value for calculating the stop loss execute price.
    :return: Tuple containing sl_trigger_price, sl_execute_price.
    :raises ValueError: If order_side is not 'buy' or 'sell'.
    """

    if order_side == 'sell':
        sl_trigger_price = reference_price + sl_trigger_usd
        sl_execute_price = sl_trigger_price + sl_execute_usd
        assert sl_execute_price > sl_trigger_price, "sl_execute_price must be greater than sl_trigger_price"
    elif order_side == 'buy':
        sl_trigger_price = reference_price - sl_trigger_usd
        sl_execute_price = sl_trigger_price - sl_execute_usd
        assert sl_execute_price < sl_trigger_price, "sl_execute_price must be less than sl_trigger_price"
    else:
        raise ValueError('order_side must be either "buy" or "sell"')

    return round(sl_trigger_price, 2), round(sl_execute_price, 2)


class FunctionCall:
    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def execute(self):
        return self.func(*self.args, **self.kwargs)


def execute_function_calls(function_calls):
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(func_call.execute) for func_call in function_calls]
        return [future.result() for future in futures]


def get_timestamp_from_days_ago(days_ago=0, hours_ago=0, minutes_ago=0, seconds_ago=0, reference_time: datetime = None):
    if not reference_time:
        reference_time = datetime.now()

    past_time = reference_time - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago, seconds=seconds_ago)
    return int(past_time.timestamp() * 1000)
