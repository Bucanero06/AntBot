from shared.tmp_shared import calculate_stop_prices


def prepare_order_request(planType, symbol, productType, marginMode, marginCoin, size, price=None, callbackRatio=None,
                          triggerPrice=None, triggerType=None, side=None, tradeSide=None, orderType=None,
                          clientOid=None,
                          reduceOnly="NO",
                          stopSurplusTriggerPrice=None, stopSurplusExecutePrice=None, stopSurplusTriggerType=None,
                          stopLossTriggerPrice=None, stopLossExecutePrice=None, stopLossTriggerType=None):
    # Validate required fields
    if not all([planType, symbol, productType, marginMode, marginCoin, size, side, orderType]):
        raise ValueError("Missing required fields")

    # Validate fields
    assert planType in ["normal_plan", "track_plan"], "planType must be either 'normal_plan' or 'track_plan'"
    assert productType in ["USDT-FUTURES", "COIN-FUTURES", "USDC-FUTURES", "SUSDT-FUTURES", "SCOIN-FUTURES",
                           "SUSDC-FUTURES"], "Invalid productType"
    assert marginMode in ["isolated", "cross"], "marginMode must be either 'isolated' or 'cross'"
    assert side in ["buy", "sell"], "side must be either 'buy' or 'sell'"
    assert orderType in ["limit", "market"], "orderType must be either 'limit' or 'market'"
    assert (tradeSide is None or tradeSide in ["Open", "Close"]), "tradeSide must be either 'Open', 'Close', or None"
    assert reduceOnly in ["YES", "NO"], "reduceOnly must be either 'YES' or 'NO'"
    assert (triggerType is None or triggerType in ["mark_price", "index_price", "last_price"]), "Invalid triggerType"
    assert (stopSurplusTriggerType is None or stopSurplusTriggerType in ["mark_price", "index_price",
                                                                         "last_price"]), "Invalid stopSurplusTriggerType"
    assert (stopLossTriggerType is None or stopLossTriggerType in ["mark_price", "index_price",
                                                                   "last_price"]), "Invalid stopLossTriggerType"
    assert callbackRatio is None or (
            0 < float(callbackRatio) <= 10), "callbackRatio must be greater than 0 and less than or equal to 10"

    # Conditional logic for trailing stop orders (track_plan)
    if planType == "track_plan":
        if price is not None:
            raise ValueError("For trailing stop orders, price must be empty")
        if callbackRatio is None:
            raise ValueError("Callback ratio is required for trailing stop orders")
        if orderType != "market":
            raise ValueError("For trailing stop orders, orderType must be 'market'")
        if any([stopSurplusExecutePrice, stopLossExecutePrice]):
            raise ValueError("For trailing stop orders, stopSurplusExecutePrice and stopLossExecutePrice must be empty")

    # Conditional logic for normal_plan
    elif planType == "normal_plan":
        if orderType == "limit" and price is None:
            raise ValueError("For limit trigger orders, price is required")
        if orderType == "market" and price is not None:
            raise ValueError("For market trigger orders, price must be empty")
        if stopSurplusTriggerPrice and stopSurplusExecutePrice is None:
            raise ValueError(
                "For a trigger order with stopSurplusTriggerPrice set, stopSurplusExecutePrice is required")
        if stopLossTriggerPrice and stopLossExecutePrice is None:
            raise ValueError("For a trigger order with stopLossTriggerPrice set, stopLossExecutePrice is required")

    # Check for reduceOnly in hedge mode position
    if tradeSide in ["Open", "Close"] and reduceOnly != "NO":
        raise ValueError("reduceOnly must be 'NO' in open and close position (hedge mode position) mode")

    # Construct the order request
    order = {
        "planType": planType,
        "symbol": symbol,
        "productType": productType,
        "marginMode": marginMode,
        "marginCoin": marginCoin,
        "size": size,
        "price": price,
        "callbackRatio": callbackRatio,
        "triggerPrice": triggerPrice,
        "triggerType": triggerType,
        "side": side,
        "tradeSide": tradeSide,
        "orderType": orderType,
        "clientOid": clientOid,
        "reduceOnly": reduceOnly,
        "stopSurplusTriggerPrice": stopSurplusTriggerPrice,
        "stopSurplusExecutePrice": stopSurplusExecutePrice,
        "stopSurplusTriggerType": stopSurplusTriggerType,
        "stopLossTriggerPrice": stopLossTriggerPrice,
        "stopLossExecutePrice": stopLossExecutePrice,
        "stopLossTriggerType": stopLossTriggerType
    }

    # Remove None values
    order = {k: v for k, v in order.items() if v is not None}

    return order


def bitget_signal_handler(order_side, current_market_price, stop_loss_trigger_percentage,
                          stop_surplus_trigger_percentage,
                          stop_loss_price_offset, stop_surplus_price_offset, plan_type, order_size):
    from pybitget.client import Client as BITGETClient
    import os
    bitget_client = BITGETClient(
        os.environ.get("BITGET_API_KEY"),
        os.environ.get("BITGET_SECRET_KEY"),
        os.environ.get("BITGET_PASSPHRASE"),
        use_server_time=False, verbose=True)

    # Calculated Parameters
    tp_sl_params = calculate_stop_prices(order_side, current_market_price, stop_loss_trigger_percentage,
                                         stop_surplus_trigger_percentage, stop_loss_price_offset,
                                         stop_surplus_price_offset)
    stop_loss_trigger_price, stop_surplus_trigger_price, stop_loss_execute_price, stop_surplus_execute_price = tp_sl_params

    # Order Request
    order_request = prepare_order_request(planType=plan_type, symbol="BTCUSDT", productType="SUSDT-FUTURES",
                                          marginMode="isolated", marginCoin="USDT", size=order_size, price="24000",
                                          callbackRatio="0.01", triggerType="mark_price", side=order_side,
                                          tradeSide="Open", orderType="limit", clientOid=None, reduceOnly="NO",
                                          stopSurplusTriggerPrice=stop_surplus_trigger_price,
                                          stopSurplusExecutePrice=stop_surplus_execute_price,
                                          stopSurplusTriggerType="mark_price",
                                          stopLossTriggerPrice=stop_loss_trigger_price,
                                          stopLossExecutePrice=stop_loss_execute_price,
                                          stopLossTriggerType="mark_price")

    from pprint import pprint
    pprint(order_request)
