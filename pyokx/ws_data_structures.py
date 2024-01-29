from typing import List, Optional

from pydantic import BaseModel

from pyokx.data_structures import Instrument, AccountBalanceData, Position, Ask, Bid, Ticker


class TickersChannelInputArgs(BaseModel):
    channel: str
    instId: str


class TickersChannelReturnArgs(BaseModel):
    channel: str
    instId: str


class TickersChannel(BaseModel):
    arg: TickersChannelReturnArgs
    data: List[Ticker]


class CandleStick(BaseModel):
    _primary_key_field = 'timestamp'
    timestamp: str
    open: str
    high: str
    low: str
    close: str
    is_closed: str


class PriceLimit(BaseModel):
    _primary_key_field = 'instId'
    instId: str
    buyLmt: str
    sellLmt: str
    ts: str
    enabled: bool


class InstrumentsChannelInputArgs(BaseModel):
    _primary_key_field = 'instType'
    channel: str
    instType: str


class InstrumentsChannel(BaseModel):
    arg: InstrumentsChannelInputArgs
    data: List[Instrument]


class PriceLimitChannelInputArgs(BaseModel):
    _primary_key_field = 'instId'
    channel: str
    instId: str


class PriceLimitChannel(BaseModel):
    arg: PriceLimitChannelInputArgs
    data: List[PriceLimit]


class MarkPriceChannelInputArgs(BaseModel):
    _primary_key_field = 'instId'
    channel: str
    instId: str


class MarkPrice(BaseModel):
    _primary_key_field = 'instId'
    instType: str
    instId: str
    markPx: str
    ts: str


class MarkPriceChannel(BaseModel):
    arg: MarkPriceChannelInputArgs
    data: List[MarkPrice]


class MarkPriceCandleSticksChannelInputArgs(BaseModel):
    _primary_key_field = 'instId'
    channel: str
    instId: str


class MarkPriceCandleSticksChannel(BaseModel):
    arg: MarkPriceChannelInputArgs
    data: List[CandleStick]

    @staticmethod
    def from_array(arg: MarkPriceCandleSticksChannelInputArgs, data):
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
        return MarkPriceCandleSticksChannel(args=arg, data=data)

    # B


class IndexTickersChannelInputArgs(BaseModel):
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
    arg: IndexTickersChannelInputArgs
    data: List[IndexTickers]


class IndexCandleSticksChannelInputArgs(BaseModel):
    _primary_key_field = 'instId'
    channel: str
    instId: str


class IndexCandleSticksChannel(BaseModel):
    arg: IndexCandleSticksChannelInputArgs
    data: List[CandleStick]

    @staticmethod
    def from_array(arg: IndexCandleSticksChannelInputArgs, data):
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
        return IndexCandleSticksChannel(arg=arg, data=data)


class AccountChannelInputArgs(BaseModel):
    channel: str
    ccy: Optional[str] = None


class AccountChannelReturnArgs(BaseModel):
    channel: str
    uid: str


class AccountChannel(BaseModel):
    arg: AccountChannelReturnArgs
    data: List[AccountBalanceData]


class PositionChannelInputArgs(BaseModel):
    channel: str
    instType: str
    instFamily: Optional[str] = None
    instId: Optional[str] = None


class PositionChannelReturnArgs(BaseModel):
    channel: str
    uid: str
    instType: str
    instFamily: Optional[str] = None
    instId: Optional[str] = None


class PositionChannel(BaseModel):
    arg: PositionChannelReturnArgs
    data: List[Position]


class BalanceAndPositionsChannelInputArgs(BaseModel):
    channel: str


class BalanceAndPositionsChannelReturnArgs(BaseModel):
    channel: str
    uid: str


class ws_balData_element(BaseModel):
    _primary_key_field: str = "ccy"

    ccy: str
    cashBal: str
    uTime: str


class ws_posData_element(BaseModel):
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


class ws_trades_element(BaseModel):
    _primary_key_field: str = "tradeId"

    instId: str
    tradeId: str


class BalanceAndPositionData(BaseModel):
    pTime: str
    eventType: str
    balData: List[ws_balData_element]
    posData: List[ws_posData_element]
    trades: List[ws_trades_element]


class BalanceAndPositionsChannel(BaseModel):
    arg: BalanceAndPositionsChannelReturnArgs
    data: List[BalanceAndPositionData]


class WebSocketConnectionConfig(BaseModel):
    _primary_key_field: str = 'name'
    name: str
    channels: dict = {}
    wss_url: str


class OrdersChannelInputArgs(BaseModel):
    channel: str
    instType: str
    instFamily: Optional[str] = None
    instId: Optional[str] = None


class OrdersChannelReturnArgs(BaseModel):
    channel: str
    instType: str
    uid: str
    instFamily: Optional[str] = None
    instId: Optional[str] = None


class WSOrder(BaseModel):
    accFillSz: str
    algoClOrdId: str
    algoId: str
    amendResult: str
    amendSource: str
    attachAlgoClOrdId: str
    attachAlgoOrds: List[str]
    avgPx: str
    cTime: str
    cancelSource: str
    category: str
    ccy: str
    clOrdId: str
    code: str
    execType: str
    fee: str
    feeCcy: str
    fillFee: str
    fillFeeCcy: str
    fillFwdPx: str
    fillMarkPx: str
    fillMarkVol: str
    fillNotionalUsd: str
    fillPnl: str
    fillPx: str
    fillPxUsd: str
    fillPxVol: str
    fillSz: str
    fillTime: str
    instId: str
    instType: str
    lastPx: str
    lever: str
    msg: str
    notionalUsd: str
    ordId: str
    ordType: str
    pnl: str
    posSide: str
    px: str
    pxType: str
    pxUsd: str
    pxVol: str
    quickMgnType: str
    rebate: str
    rebateCcy: str
    reduceOnly: str
    reqId: str
    side: str
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
    tradeId: str
    uTime: str


class OrdersChannel(BaseModel):
    arg: OrdersChannelReturnArgs
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


class OrderBookInputArgs(BaseModel):
    channel: str
    instId: str


class OrderBookReturnArgs(BaseModel):
    channel: str
    instId: str


class OrderBookData(BaseModel):
    asks: List[Ask]
    bids: List[Bid]
    ts: str
    seqId: int
    instId: Optional[str] = None
    checksum: Optional[int] = None
    prevSeqId: Optional[int] = None


class OrderBookChannel(BaseModel):
    arg: OrderBookReturnArgs
    data: List[OrderBookData]
    action: Optional[str] = None

    @staticmethod
    def from_array(arg: OrderBookReturnArgs, data, action: str = None):
        arg = OrderBookReturnArgs(channel=arg.get('channel'), instId=arg.get('instId'))

        data: List[OrderBookData] = [
            OrderBookData(
                asks=[Ask(price=ask[0], quantity=ask[1], deprecated_value=ask[2], number_of_orders=ask[3]) for ask in
                      item['asks']],
                bids=[Bid(price=bid[0], quantity=bid[1], deprecated_value=bid[2], number_of_orders=bid[3]) for bid in
                      item['bids']],
                ts=item['ts'],
                seqId=item['seqId'],
                instId=item.get('instId'),
                checksum=item.get('checksum'),
                prevSeqId=item.get('prevSeqId')
            ) for item in data
        ]

        return OrderBookChannel(arg=arg, data=data, action=action)




OKX_WEBSOCKET_URLS = dict(
    public="wss://ws.okx.com:8443/ws/v5/public",
    private="wss://ws.okx.com:8443/ws/v5/private",
    business="wss://ws.okx.com:8443/ws/v5/business",
    public_aws="wss://wsaws.okx.com:8443/ws/v5/public",
    private_aws="wss://wsaws.okx.com:8443/ws/v5/private",
    business_aws="wss://wsaws.okx.com:8443/ws/v5/business",
    public_demo="wss://wspap.okx.com:8443/ws/v5/public?brokerId=9999",
    private_demo="wss://wspap.okx.com:8443/ws/v5/private?brokerId=9999",
    business_demo="wss://wspap.okx.com:8443/ws/v5/business?brokerId=9999",
)

public_channels_available = {
    "price-limit": PriceLimitChannel,
    "instruments": InstrumentsChannel,
    "mark-price": MarkPriceChannel,
    "index-tickers": IndexTickersChannel,
    "tickers": TickersChannel,
    "books5": OrderBookChannel,
    "books": OrderBookChannel,
    "bbo-tbt": OrderBookChannel,
    "books50-l2-tbt": OrderBookChannel,
    "books-l2-tbt": OrderBookChannel,
}
business_channels_available = {
    "mark-price-candle1m": MarkPriceCandleSticksChannel,
    "mark-price-candle3m": MarkPriceCandleSticksChannel,
    "mark-price-candle5m": MarkPriceCandleSticksChannel,
    "mark-price-candle15m": MarkPriceCandleSticksChannel,
    "mark-price-candle30m": MarkPriceCandleSticksChannel,
    "mark-price-candle1H": MarkPriceCandleSticksChannel,
    "mark-price-candle2H": MarkPriceCandleSticksChannel,
    "mark-price-candle4H": MarkPriceCandleSticksChannel,
    "mark-price-candle6H": MarkPriceCandleSticksChannel,
    "mark-price-candle12H": MarkPriceCandleSticksChannel,
    "mark-price-candle5D": MarkPriceCandleSticksChannel,
    "mark-price-candle3D": MarkPriceCandleSticksChannel,
    "mark-price-candle2D": MarkPriceCandleSticksChannel,
    "mark-price-candle1D": MarkPriceCandleSticksChannel,
    "mark-price-candle1W": MarkPriceCandleSticksChannel,
    "mark-price-candle1M": MarkPriceCandleSticksChannel,
    "mark-price-candle3M": MarkPriceCandleSticksChannel,
    "mark-price-candle1Yutc": MarkPriceCandleSticksChannel,
    "mark-price-candle3Mutc": MarkPriceCandleSticksChannel,
    "mark-price-candle1Mutc": MarkPriceCandleSticksChannel,
    "mark-price-candle1Wutc": MarkPriceCandleSticksChannel,
    "mark-price-candle1Dutc": MarkPriceCandleSticksChannel,
    "mark-price-candle2Dutc": MarkPriceCandleSticksChannel,
    "mark-price-candle3Dutc": MarkPriceCandleSticksChannel,
    "mark-price-candle5Dutc": MarkPriceCandleSticksChannel,
    "mark-price-candle12Hutc": MarkPriceCandleSticksChannel,
    "mark-price-candle6Hutc": MarkPriceCandleSticksChannel,
    #
    "index-candle1m": IndexCandleSticksChannel,
    "index-candle3m": IndexCandleSticksChannel,
    "index-candle5m": IndexCandleSticksChannel,
    "index-candle15m": IndexCandleSticksChannel,
    "index-candle30m": IndexCandleSticksChannel,
    "index-candle1H": IndexCandleSticksChannel,
    "index-candle2H": IndexCandleSticksChannel,
    "index-candle4H": IndexCandleSticksChannel,
    "index-candle6H": IndexCandleSticksChannel,
    "index-candle12H": IndexCandleSticksChannel,
    "index-candle5D": IndexCandleSticksChannel,
    "index-candle3D": IndexCandleSticksChannel,
    "index-candle2D": IndexCandleSticksChannel,
    "index-candle1D": IndexCandleSticksChannel,
    "index-candle1W": IndexCandleSticksChannel,
    "index-candle1M": IndexCandleSticksChannel,
    "index-candle3M": IndexCandleSticksChannel,
    "index-candle1Yutc": IndexCandleSticksChannel,
    "index-candle3Mutc": IndexCandleSticksChannel,
    "index-candle1Mutc": IndexCandleSticksChannel,
    "index-candle1Wutc": IndexCandleSticksChannel,
    "index-candle1Dutc": IndexCandleSticksChannel,
    "index-candle2Dutc": IndexCandleSticksChannel,
    "index-candle3Dutc": IndexCandleSticksChannel,
    "index-candle5Dutc": IndexCandleSticksChannel,
    "index-candle12Hutc": IndexCandleSticksChannel,
    "index-candle6Hutc": IndexCandleSticksChannel,
}
private_channels_available = {
    "account": AccountChannel,  # Missing coinUsdPrice
    "positions": PositionChannel,  # Missing pTime
    "balance_and_position": BalanceAndPositionsChannel,
    "orders": OrdersChannel
}

available_channel_models = (
        public_channels_available | business_channels_available | private_channels_available
)

