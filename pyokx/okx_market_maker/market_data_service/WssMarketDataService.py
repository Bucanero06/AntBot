from typing import Dict, List

from pyokx.okx_market_maker import order_books, tickers_container, mark_px_container
from pyokx.okx_market_maker.market_data_service.model.MarkPx import MarkPxCache
from pyokx.okx_market_maker.market_data_service.model.OrderBook import OrderBook, OrderBookLevel
from pyokx.okx_market_maker.market_data_service.model.Tickers import Tickers


def _prepare_args(self) -> List[Dict]:
    args = []
    books5_sub = {
        "channel": self.channel,
        "instId": self.inst_id
    }
    args.append(books5_sub)
    return args


def _callback(message):
    arg = message.get("arg")
    # print(message)
    if not arg or not arg.get("channel"):
        return
    if message.get("event") == "subscribe":
        return
    if arg.get("channel") in ["books5", "books", "bbo-tbt", "books50-l2-tbt", "books-l2-tbt"]:
        on_orderbook_snapshot_or_update(message)
        # print(order_books)


def on_orderbook_snapshot_or_update(message):
    """
    """
    arg = message.get("arg")
    inst_id = arg.get("instId")
    action = message.get("action")
    if inst_id not in order_books:
        order_books[inst_id] = OrderBook(inst_id=inst_id)
    data = message.get("data")[0]

    if data.get("asks"):
        if action == "snapshot" or not action:
            ask_list = [OrderBookLevel(price=float(level_info[0]),
                                       quantity=float(level_info[1]),
                                       order_count=int(level_info[3]),
                                       price_string=level_info[0],
                                       quantity_string=level_info[1],
                                       order_count_string=level_info[3],
                                       ) for level_info in data["asks"]]
            order_books[inst_id].set_asks_on_snapshot(ask_list)
        if action == "update":
            for level_info in data["asks"]:
                order_books[inst_id].set_asks_on_update(
                    OrderBookLevel(price=float(level_info[0]),
                                   quantity=float(level_info[1]),
                                   order_count=int(level_info[3]),
                                   price_string=level_info[0],
                                   quantity_string=level_info[1],
                                   order_count_string=level_info[3],
                                   )
                )
    if data.get("bids"):
        if action == "snapshot" or not action:
            bid_list = [OrderBookLevel(price=float(level_info[0]),
                                       quantity=float(level_info[1]),
                                       order_count=int(level_info[3]),
                                       price_string=level_info[0],
                                       quantity_string=level_info[1],
                                       order_count_string=level_info[3],
                                       ) for level_info in data["bids"]]
            order_books[inst_id].set_bids_on_snapshot(bid_list)
        if action == "update":
            for level_info in data["bids"]:
                order_books[inst_id].set_bids_on_update(
                    OrderBookLevel(price=float(level_info[0]),
                                   quantity=float(level_info[1]),
                                   order_count=int(level_info[3]),
                                   price_string=level_info[0],
                                   quantity_string=level_info[1],
                                   order_count_string=level_info[3],
                                   )
                )
    if data.get("ts"):
        order_books[inst_id].set_timestamp(int(data["ts"]))
    if data.get("checksum"):
        order_books[inst_id].set_exch_check_sum(data["checksum"])
    return order_books[inst_id]


def on_ticker_update(message):
    if not tickers_container:
        tickers_container.append(Tickers())

    tickers_container[0].update_from_json(message)

    return tickers_container[0]


def on_mark_price_update(message):
    if not mark_px_container:
        mark_px_container.append(MarkPxCache())

    mark_px_container[0].update_from_json(message)

    return mark_px_container[0]
