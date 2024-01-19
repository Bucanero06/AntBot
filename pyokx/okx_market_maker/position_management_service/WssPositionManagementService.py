import time
from typing import List, Dict
import copy

from pyokx.okx_market_maker import balance_and_position_container, account_container, positions_container
from pyokx.okx_market_maker.position_management_service.model.Account import Account
from pyokx.okx_market_maker.position_management_service.model.BalanceAndPosition import BalanceAndPosition
from pyokx.okx_market_maker.position_management_service.model.Positions import Positions


def _prepare_position_management_args() -> List[Dict]:
    args = []
    account_sub = {
            "channel": "account"
    }
    args.append(account_sub)
    positions_sub = {
        "channel": "positions",
        "instType": "ANY"
    }
    args.append(positions_sub)
    balance_and_position_sub = {
        "channel": "balance_and_position"
    }
    args.append(balance_and_position_sub)
    return args


def _callback(message):
    arg = message.get("arg")
    if not arg or not arg.get("channel"):
        return
    if message.get("event") == "subscribe":
        return
    if arg.get("channel") == "balance_and_position":
        on_balance_and_position(message)
    if arg.get("channel") == "account":
        on_account(message)
    if arg.get("channel") == "positions":
        on_position(message)




def on_balance_and_position(message):
    if not balance_and_position_container:
        balance_and_position_container.append(BalanceAndPosition.init_from_ws_json_message(message))
    else:
        balance_and_position_container[0].update_from_ws_json_message(message)
    return balance_and_position_container[0]


def on_account(message):
    if not account_container:
        account_container.append(Account.init_from_ws_json_message(message))
    else:
        account_container[0].update_from_ws_json_message(message)

    return account_container[0]




def on_position(message):
    if not positions_container:
        positions_container.append(Positions.init_from_ws_json_message(message))
    else:
        positions_container[0].update_from_ws_json_message(message)

    return positions_container[0]

