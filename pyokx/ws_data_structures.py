from typing import List, Optional

from pydantic import BaseModel

from pyokx.data_structures import InstType, Instrument, AccountBalanceData, Position
from redis_tools.syncio.model import Model


class RedisStoreChannelBase(BaseModel):

    @staticmethod
    def register_models(redis_store) -> None:
        raise NotImplementedError("implement register_models first")

    def refresh_models(self) -> None:
        raise NotImplementedError("implement insert_models first")

    @staticmethod
    def get_models(self) -> dict:
        raise NotImplementedError("implement get_models first")

    @staticmethod
    def update_models(model_inputs: tuple, life_spans_in_seconds: tuple = None, remove_non_present_ids: tuple = (True)):
        if life_spans_in_seconds:
            if len(life_spans_in_seconds) != len(model_inputs):
                print(f'WARNING: the {len(life_spans_in_seconds) = } does not equal the {len(model_inputs) = }'
                      f' thus ignoring life_spans during this request for all model_inputs and using default')
        else:
            life_spans_in_seconds = [None] * len(model_inputs)

        if remove_non_present_ids:
            if len(remove_non_present_ids) != len(model_inputs):
                print(f'WARNING: the {len(remove_non_present_ids) = } does not equal the {len(model_inputs) = }'
                      f' thus ignoring life_spans during this request for all model_inputs and using default')
        else:
            remove_non_present_ids = [None] * len(model_inputs)
        for i_enumerate, models_to_store in enumerate(model_inputs):
            if not models_to_store:
                continue

            model_store = type(models_to_store[0])
            if not issubclass(model_store, Model):
                print(f'WARNING: Passed in model {models_to_store} is not a redis tools Model')
                continue

            models_to_store: List[Model] = models_to_store
            if remove_non_present_ids[i_enumerate]:

                model_primary_key = model_store.get_primary_key_field()

                current_ids = [getattr(model_to_store, model_primary_key) for model_to_store in models_to_store]
                stored_models = model_store.select() or []

                id_to_delete = []
                for stored_model in stored_models:
                    stored_model_id = getattr(stored_model, model_primary_key)
                    if stored_model_id not in current_ids:
                        id_to_delete.append(stored_model_id)
                if id_to_delete:
                    print(f'ids to delete: {id_to_delete}')
                    model_store.delete(ids=id_to_delete)

            model_store.insert(models_to_store, life_span_seconds=life_spans_in_seconds[i_enumerate])
            model_store.update(models_to_store, life_span_seconds=life_spans_in_seconds[i_enumerate])


class CandleStick(Model):
    _primary_key_field = 'timestamp'
    timestamp: str
    open: str
    high: str
    low: str
    close: str
    is_closed: str


class PriceLimit(Model):
    _primary_key_field = 'instId'
    instId: str
    buyLmt: str
    sellLmt: str
    ts: str
    enabled: bool


class InstrumentsChannelInputArgs(Model):
    _primary_key_field = 'instType'
    channel: str
    instType: str


class InstrumentsChannel(BaseModel):
    args: InstrumentsChannelInputArgs
    data: List[Instrument]


class PriceLimitChannelInputArgs(Model):
    _primary_key_field = 'instId'
    channel: str
    instId: str


class PriceLimitChannel(BaseModel):
    args: PriceLimitChannelInputArgs
    data: List[PriceLimit]


class MarkPriceChannelInputArgs(Model):
    _primary_key_field = 'instId'
    channel: str
    instId: str


class MarkPrice(Model):
    _primary_key_field = 'instId'
    instType: str
    instId: str
    markPx: str
    ts: str


class MarkPriceChannel(BaseModel):
    args: MarkPriceChannelInputArgs
    data: List[MarkPrice]


class MarkPriceCandleSticksChannelInputArgs(Model):
    _primary_key_field = 'instId'
    channel: str
    instId: str


class MarkPriceCandleSticksChannel(BaseModel):
    args: MarkPriceChannelInputArgs
    data: List[CandleStick]

    @staticmethod
    def from_array(args: MarkPriceCandleSticksChannelInputArgs, data):
        data: List[CandleStick] = [
            CandleStick(
                timestamp=item[0],
                open=item[1],
                high=item[2],
                low=item[3],
                close=item[4],
                is_closed=item[5]
            ) for item in data
        ]
        return MarkPriceCandleSticksChannel(args=args, data=data)

    # B


class IndexTickersChannelInputArgs(Model):
    _primary_key_field = 'instId'
    channel: str
    instId: str


class IndexTickers(BaseModel):
    instId: str
    idxPx: str
    high24h: str
    low24h: str
    open24h: str
    sodUtc0: str
    sodUtc8: str
    ts: str


class IndexTickersChannel(BaseModel):
    args: IndexTickersChannelInputArgs
    data: List[IndexTickers]


class IndexCandleSticksChannelInputArgs(Model):
    _primary_key_field = 'instId'
    channel: str
    instId: str


class IndexCandleSticksChannel(BaseModel):
    args: IndexCandleSticksChannelInputArgs
    data: List[CandleStick]

    @staticmethod
    def from_array(args: IndexCandleSticksChannelInputArgs, data):
        data: List[CandleStick] = [
            CandleStick(
                timestamp=item[0],
                open=item[1],
                high=item[2],
                low=item[3],
                close=item[4],
                is_closed=item[5]
            ) for item in data
        ]
        return IndexCandleSticksChannel(args=args, data=data)



class AccountChannelInputArgs(BaseModel):
    channel: str
    ccy: Optional[str]


class AccountChannelReturnArgs(BaseModel):
    channel: str
    uid: str



class AccountChannel(BaseModel):
    args: AccountChannelReturnArgs
    data: List[AccountBalanceData]


class PositionChannelInputArgs(BaseModel):
    channel: str
    instType: str
    instFamily: Optional[str]
    instId: Optional[str]


class PositionChannelReturnArgs(BaseModel):
    channel: str
    uid: str
    instType: str


class PositionChannel(BaseModel):
    args: PositionChannelReturnArgs
    data: List[Position]


class BalanceAndPositionsChannelInputArgs(BaseModel):
    channel: str


class BalanceAndPositionsChannelReturnArgs(BaseModel):
    channel: str
    uid: str


class ws_balData_element(Model):
    _primary_key_field: str = "ccy"

    ccy: str
    cashBal: str
    uTime: str


class ws_posData_element(Model):
    _primary_key_field: str = "posId"

    posId: str
    tradeId: str
    instId: str
    instType: str
    mgnMode: str
    posSide: str
    pos: str
    ccy: str
    posCcy: str
    avgPx: str
    uTime: str


class ws_trades_element(Model):
    _primary_key_field: str = "tradeId"

    instId: str
    tradeId: str


class BalanceAndPositionData(BaseModel):
    pTime: str
    eventType: str
    balData: List[ws_balData_element]
    posData: List[ws_posData_element]
    trades: List[ws_trades_element]


class BalanceAndPositionsChannel(RedisStoreChannelBase):
    args: BalanceAndPositionsChannelReturnArgs
    data: List[BalanceAndPositionData]

    @staticmethod
    def register_models(redis_store):
        if ws_posData_element.__name__.lower() not in redis_store.models:
            redis_store.register_model(ws_posData_element)
        if ws_balData_element.__name__.lower() not in redis_store.models:
            redis_store.register_model(ws_balData_element)
        if ws_trades_element.__name__.lower() not in redis_store.models:
            redis_store.register_model(ws_trades_element)

    def refresh_models(self):
        positions: List[ws_posData_element] = self.data[0].posData
        balances: List[ws_balData_element] = self.data[0].balData
        trades: List[ws_trades_element] = self.data[0].trades

        self.update_models((positions, balances), life_spans_in_seconds=None,
                           remove_non_present_ids=(True, False))

    @staticmethod
    def get_models() -> dict:
        posData: List[ws_posData_element] = ws_posData_element.select()
        balData: List[ws_balData_element] = ws_balData_element.select()
        tradeId: List[ws_trades_element] = ws_trades_element.select()
        return {
            'positions': posData or [],
            'balances': balData or [],
            'trades': tradeId or []
        }


class WebSocketConnectionConfig(Model):
    _primary_key_field: str = 'name'
    name: str
    channels: dict = {}
    wss_url: str


class OrdersChannelInputArgs(BaseModel):
    channel: str
    instType: str
    instFamily: Optional[str]
    instId: Optional[str]


class OrdersChannelReturnArgs(BaseModel):
    channel: str
    instType: str
    instId: str
    uid: str


class WSOrder(Model):
    _primary_key_field: str = 'ordId'
    accFillSz: str
    algoClOrdId: str
    algoId: str
    amendResult: str
    amendSource: str
    avgPx: str
    cancelSource: str
    category: str
    ccy: str
    clOrdId: str
    code: str
    cTime: str
    execType: str
    fee: str
    feeCcy: str
    fillFee: str
    fillFeeCcy: str
    fillNotionalUsd: str
    fillPx: str
    fillSz: str
    fillPnl: str
    fillTime: str
    fillPxVol: str
    fillPxUsd: str
    fillMarkVol: str
    fillFwdPx: str
    fillMarkPx: str
    instId: str
    instType: str
    lever: str
    msg: str
    notionalUsd: str
    ordId: str
    ordType: str
    pnl: str
    posSide: str
    px: str
    pxUsd: str
    pxVol: str
    pxType: str
    quickMgnType: str
    rebate: str
    rebateCcy: str
    reduceOnly: str
    reqId: str
    side: str
    attachAlgoClOrdId: str
    slOrdPx: str
    slTriggerPx: str
    slTriggerPxType: str
    source: str
    state: str
    stpId: str
    stpMode: str
    sz: str
    tag: str
    tdMode: str
    tgtCcy: str
    tpOrdPx: str
    tpTriggerPx: str
    tpTriggerPxType: str
    attachAlgoOrds: str
    tradeId: str
    lastPx: str
    uTime: str


class OrdersChannel(BaseModel):
    args: OrdersChannelReturnArgs
    data: List[WSOrder]

    @staticmethod
    def register_models(redis_store):
        if WSOrder.__name__.lower() not in redis_store.models:
            redis_store.register_model(WSOrder)

    def refresh_models(self):
        orders: List[WSOrder] = self.data
        self.update_models((orders), life_spans_in_seconds=None)

    @staticmethod
    def get_models() -> dict:
        orders: List[WSOrder] = WSOrder.select()
        return {
            'orders': orders or [],
        }
