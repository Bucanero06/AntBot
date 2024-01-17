import json
import time
from typing import List, Dict

from pyokx.okx_market_maker import orders_container
from pyokx.okx_market_maker.order_management_service.model.Order import Orders


@staticmethod
def _prepare_args() -> List[Dict]:
    args = []
    orders_sub = {
        "channel": "orders",
        "instType": "ANY",
    }
    args.append(orders_sub)
    return args


def _callback(message):
    arg = message.get("arg")
    # print(message)
    if not arg or not arg.get("channel"):
        return
    if message.get("event") == "subscribe":
        return
    if arg.get("channel") == "orders":
        on_orders_update(message)


def on_orders_update(message):
    if not orders_container:
        orders_container.append(Orders.init_from_json(message))
    else:
        orders_container[0].update_from_json(message)

    return orders_container[0]


