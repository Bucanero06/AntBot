from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, List

from pyokx.okx_market_maker.utils.OkxEnum import OrderCategory, OrderExecType, InstType, OrderType, PosSide, OrderSide, \
    OrderState


@dataclass
class Order:
    acc_fill_sz: str = "0"
    amend_result: str = 0
    avg_px: float = 0
    c_time: int = 0
    category: OrderCategory = None
    ccy: str = ""
    cl_ord_id: str = ""
    exec_type: OrderExecType = None
    fee: float = 0
    fee_ccy: str = ""
    fill_fee: float = 0
    fill_fee_ccy: str = ""
    fill_notional_usd: float = 0
    fill_px: float = 0
    fill_sz: str = "0"
    fill_time: int = 0
    inst_id: str = ""
    inst_type: InstType = None
    lever: float = 0
    notional_usd: float = 0
    ord_id: str = ""
    ord_type: OrderType = None
    pnl: float = 0
    pos_side: PosSide = None
    px: float = 0
    rebate: float = 0
    rebate_ccy: str = ""
    reduce_only: bool = False,
    req_id: str = ""
    side: OrderSide = None
    state: OrderState = None
    sz: float = 0
    tag: str = ""
    trade_id: str = ""
    u_time: int = 0

    @classmethod
    def init_from_ws_json_message(cls, json_response):
        order = Order()
        order.acc_fill_sz = json_response.get("accFillSz", "0")
        order.amend_result = json_response.get("amendResult")
        order.avg_px = float(json_response.get("avgPx", 0))
        order.c_time = int(json_response.get("cTime", 0))
        order.category = OrderCategory(json_response["category"])
        order.ccy = json_response["ccy"]
        order.cl_ord_id = json_response["clOrdId"]
        order.exec_type = OrderExecType(json_response["execType"]) if json_response["execType"] else None
        order.fee = float(json_response.get("fee", 0))
        order.fee_ccy = json_response.get("feeCcy", "")
        order.fill_fee = float(json_response.get("fillFee", 0))
        order.fill_fee_ccy = json_response.get("fillFeeCcy", "")
        order.fill_notional_usd = float(json_response.get("fillNotionalUsd")) \
            if json_response.get("fillNotionalUsd") else 0
        order.fill_px = float(json_response.get("fillPx")) if json_response.get("fillPx") else 0
        order.fill_sz = json_response.get("fillSz") if json_response.get("fillSz") else '0'
        order.fill_time = int(json_response.get("fillTime")) if json_response.get("fillTime") else 0
        order.inst_id = json_response.get("instId", "")
        order.inst_type = InstType(json_response["instType"])
        order.lever = float(json_response.get("lever", 0))
        order.notional_usd = float(json_response.get("notionalUsd", 0))
        order.ord_id = json_response.get("ordId", "")
        order.ord_type = OrderType(json_response["ordType"])
        order.pnl = float(json_response.get("pnl", 0))
        order.pos_side = PosSide(json_response["posSide"]) if json_response.get("posSide") else None
        order.px = float(json_response.get("px", 0)) if json_response.get("px") else 0
        order.rebate = float(json_response.get("rebate", 0))
        order.rebate_ccy = json_response.get("rebateCcy", "")
        order.reduce_only = True if json_response.get("reduceOnly") == "true" else False
        order.req_id = json_response.get("reqId", "")
        order.side = OrderSide(json_response["side"])
        order.state = OrderState(json_response["state"])
        order.sz = float(json_response.get("sz", 0))
        order.tag = json_response.get("tag", "")
        order.trade_id = json_response.get("tradeId", "")
        order.u_time = int(json_response.get("uTime", 0))
        return order

    def to_dict(self):
        return {
            "acc_fill_sz": self.acc_fill_sz,
            "amend_result": self.amend_result,
            "avg_px": self.avg_px,
            "c_time": self.c_time,
            "category": self.category,
            "ccy": self.ccy,
            "cl_ord_id": self.cl_ord_id,
            "exec_type": self.exec_type,
            "fee": self.fee,
            "fee_ccy": self.fee_ccy,
            "fill_fee": self.fill_fee,
            "fill_fee_ccy": self.fill_fee_ccy,
            "fill_notional_usd": self.fill_notional_usd,
            "fill_px": self.fill_px,
            "fill_sz": self.fill_sz,
            "fill_time": self.fill_time,
            "inst_id": self.inst_id,
            "inst_type": self.inst_type,
            "lever": self.lever,
            "notional_usd": self.notional_usd,
            "ord_id": self.ord_id,
            "ord_type": self.ord_type,
            "pnl": self.pnl,
            "pos_side": self.pos_side,
            "px": self.px,
            "rebate": self.rebate,
            "rebate_ccy": self.rebate_ccy,
            "reduce_only": self.reduce_only,
            "req_id": self.req_id,
            "side": self.side,
            "state": self.state,
            "sz": self.sz,
            "tag": self.tag,
            "trade_id": self.trade_id,
            "u_time": self.u_time
        }


@dataclass
class Orders:
    _order_map: Dict[str, Order] = field(default_factory=lambda: dict())
    _client_order_map: Dict[str, Order] = field(default_factory=lambda: dict())
    _non_client_order_map: Dict[str, Order] = field(default_factory=lambda: dict())

    @classmethod
    def init_from_ws_json_message(cls, json_response):
        orders = Orders()
        data = json_response.get("data", [])
        orders._order_map = {single_order["ordId"]: Order.init_from_ws_json_message(single_order) for single_order in data}
        orders._client_order_map = {order.cl_ord_id: order for ord_id, order in orders._order_map.items()
                                    if order.cl_ord_id}
        orders._non_client_order_map = {order.ord_id: order for ord_id, order in orders._order_map.items()
                                        if not order.cl_ord_id}
        return orders

    def update_from_ws_json_message(self, json_response):
        data = json_response.get("data", [])
        for single_order in data:
            new_order = Order.init_from_ws_json_message(single_order)
            # if new_order.state in [OrderState.CANCELED, OrderState.FILLED] and new_order.ord_id in self._order_map:
            #     del self._order_map[new_order.ord_id]
            #     del self._non_client_order_map[new_order.ord_id]
            # if new_order.state == OrderState.CANCELED and new_order.fill_sz == 0:
            #     if new_order.ord_id in self._order_map:
            #         del self._order_map[new_order.ord_id]
            #     continue
            self._order_map[new_order.ord_id] = new_order
            if new_order.cl_ord_id:
                self._client_order_map[new_order.cl_ord_id] = new_order
            else:
                self._non_client_order_map[new_order.ord_id] = new_order

    def get_order_by_order_id(self, order_id: str) -> Order:
        return self._order_map.get(order_id)

    def get_order_by_client_order_id(self, client_order_id: str) -> Order:
        return self._client_order_map.get(client_order_id)

    def get_non_client_order(self):
        return self._non_client_order_map

    def get_active_orders(self):
        return {order_id: order for order_id, order in self._order_map.items()
                if order.state in [OrderState.LIVE, OrderState.PARTIALLY_FILLED]}

    def get_filled_orders(self):
        return {order_id: order for order_id, order in self._order_map.items()
                if order.state in [OrderState.FILLED, OrderState.PARTIALLY_FILLED, OrderState.CANCELED]}

    def get_inactive_orders(self):
        return {order_id: order for order_id, order in self._order_map.items()
                if order.state in [OrderState.FILLED, OrderState.CANCELED]}

    def remove_orders(self, order_list: List[Order]):
        for order in order_list:
            client_order_id = order.cl_ord_id
            order_id = order.ord_id
            del self._order_map[order_id]
            if order_id in self._non_client_order_map:
                del self._non_client_order_map[order_id]
            if client_order_id in self._client_order_map:
                del self._client_order_map[client_order_id]

    def to_dict(self):
        return {
            "order_map": {order_id: order.to_dict() for order_id, order in self._order_map.items()},
            "client_order_map": {order_id: order.to_dict() for order_id, order in self._client_order_map.items()},
            "non_client_order_map": {order_id: order.to_dict() for order_id, order in self._non_client_order_map.items()}
        }

    def from_dict(self, orders_dict):
        self._order_map = {order_id: Order(**order) for order_id, order in orders_dict["order_map"].items()}
        self._client_order_map = {order_id: Order(**order) for order_id, order in orders_dict["client_order_map"].items()}
        self._non_client_order_map = {order_id: Order(**order) for order_id, order in orders_dict["non_client_order_map"].items()}
        return self
