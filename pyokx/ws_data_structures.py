
from typing import List, Optional

from pyokx.data_structures import OKXBaseModel, Instrument, AccountBalanceData, Ask, Bid, Ticker

"""The data structures used to represent the data received from the OKX Websocket API.""
The channels are split into three categories: public, business, and private. The public channels are available to all
users, the business channels are typically for market makers, and the private channels are for the user's account data.
The websocket paths are
- wss://ws.okx.com:8443/ws/v5/public
- wss://ws.okx.com:8443/ws/v5/business
- wss://ws.okx.com:8443/ws/v5/private
- wss://wsaws.okx.com:8443/ws/v5/public
- wss://wsaws.okx.com:8443/ws/v5/business
- wss://wsaws.okx.com:8443/ws/v5/private
- wss://wspap.okx.com:8443/ws/v5/public?brokerId=9999
- wss://wspap.okx.com:8443/ws/v5/private?brokerId=9999
- wss://wspap.okx.com:8443/ws/v5/business?brokerId=9999
"""


class TickersChannelInputArgs(OKXBaseModel):
    channel: str
    instId: str


class TickersChannelReturnArgs(OKXBaseModel):
    channel: str
    instId: str


class TickersChannel(OKXBaseModel):
    arg: TickersChannelReturnArgs
    data: List[Ticker]


class CandleStick(OKXBaseModel):
    _primary_key_field = 'timestamp'
    timestamp: str
    open: str
    high: str
    low: str
    close: str
    is_closed: str


class PriceLimit(OKXBaseModel):
    _primary_key_field = 'instId'
    instId: str
    buyLmt: str
    sellLmt: str
    ts: str
    enabled: bool


class InstrumentsChannelInputArgs(OKXBaseModel):
    _primary_key_field = 'instType'
    channel: str
    instType: str


class InstrumentsChannel(OKXBaseModel):
    arg: InstrumentsChannelInputArgs
    data: List[Instrument]


class PriceLimitChannelInputArgs(OKXBaseModel):
    _primary_key_field = 'instId'
    channel: str
    instId: str


class PriceLimitChannel(OKXBaseModel):
    arg: PriceLimitChannelInputArgs
    data: List[PriceLimit]


class MarkPriceChannelInputArgs(OKXBaseModel):
    _primary_key_field = 'instId'
    channel: str
    instId: str


class MarkPrice(OKXBaseModel):
    _primary_key_field = 'instId'
    instType: str
    instId: str
    markPx: str
    ts: str


class MarkPriceChannel(OKXBaseModel):
    arg: MarkPriceChannelInputArgs
    data: List[MarkPrice]


class MarkPriceCandleSticksChannelInputArgs(OKXBaseModel):
    _primary_key_field = 'instId'
    channel: str
    instId: str


class MarkPriceCandleSticksChannel(OKXBaseModel):
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


class IndexTickersChannelInputArgs(OKXBaseModel):
    _primary_key_field = 'instId'
    channel: str
    instId: str


class IndexTickers(OKXBaseModel):
    instId: str
    idxPx: str
    high24h: str
    low24h: str
    open24h: str
    sodUtc0: str
    sodUtc8: str
    ts: str


class IndexTickersChannel(OKXBaseModel):
    arg: IndexTickersChannelInputArgs
    data: List[IndexTickers]


class IndexCandleSticksChannelInputArgs(OKXBaseModel):
    _primary_key_field = 'instId'
    channel: str
    instId: str


class IndexCandleSticksChannel(OKXBaseModel):
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


class AccountChannelInputArgs(OKXBaseModel):
    channel: str
    ccy: Optional[str] = None
    extraParams: Optional[str] = None


class AccountChannelReturnArgs(OKXBaseModel):
    channel: str
    uid: str


class AccountChannel(OKXBaseModel):
    arg: AccountChannelReturnArgs
    data: List[AccountBalanceData]


class WSPosition(OKXBaseModel):
    instType: str
    mgnMode: str
    posId: str
    posSide: str
    pos: str
    baseBal: str
    quoteBal: str
    baseBorrowed: str
    baseInterest: str
    quoteBorrowed: str
    quoteInterest: str
    posCcy: str
    availPos: str
    avgPx: str
    upl: str
    uplRatio: str
    uplLastPx: str
    uplRatioLastPx: str
    instId: str
    lever: str
    liqPx: str
    markPx: str
    imr: str
    margin: str
    mgnRatio: str
    mmr: str
    liab: str
    liabCcy: str
    interest: str
    tradeId: str
    notionalUsd: str
    optVal: str
    adl: str
    bizRefId: str
    bizRefType: str
    ccy: str
    last: str
    idxPx: str
    usdPx: str
    bePx: str
    deltaBS: str
    deltaPA: str
    gammaBS: str
    gammaPA: str
    thetaBS: str
    thetaPA: str
    vegaBS: str
    vegaPA: str
    spotInUseAmt: str
    spotInUseCcy: str
    realizedPnl: str
    pnl: str
    fee: str
    fundingFee: str
    liqPenalty: str
    closeOrderAlgo: List[dict]
    cTime: str
    uTime: str
    pTime: str


class PositionsChannelInputArgs(OKXBaseModel):
    # {
    #       "channel": "positions",
    #       "instType": "ANY",
    #       "extraParams": "
    #         {
    #           \"updateInterval\": \"0\"
    #         }
    #       "
    #     }
    channel: str
    instType: str
    instFamily: Optional[str] = None
    instId: Optional[str] = None
    extraParams: Optional[str] = None


class PositionsChannelReturnArgs(OKXBaseModel):
    channel: str
    uid: str
    instType: str
    instFamily: Optional[str] = None
    instId: Optional[str] = None


class PositionsChannel(OKXBaseModel):
    arg: PositionsChannelReturnArgs
    data: List[WSPosition]


class BalanceAndPositionsChannelInputArgs(OKXBaseModel):
    channel: str


class BalanceAndPositionsChannelReturnArgs(OKXBaseModel):
    channel: str
    uid: str


class ws_balData_element(OKXBaseModel):
    _primary_key_field: str = "ccy"

    ccy: str
    cashBal: str
    uTime: str


class ws_posData_element(OKXBaseModel):
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


class ws_trades_element(OKXBaseModel):
    _primary_key_field: str = "tradeId"

    instId: str
    tradeId: str


class BalanceAndPositionData(OKXBaseModel):
    pTime: str
    eventType: str
    balData: List[ws_balData_element]
    posData: List[ws_posData_element]
    trades: List[ws_trades_element]


class BalanceAndPositionsChannel(OKXBaseModel):
    arg: BalanceAndPositionsChannelReturnArgs
    data: List[BalanceAndPositionData]


class WebSocketConnectionConfig(OKXBaseModel):
    _primary_key_field: str = 'name'
    name: str
    channels: dict = {}
    wss_url: str


class OrdersChannelInputArgs(OKXBaseModel):
    channel: str
    instType: str
    instFamily: Optional[str] = None
    instId: Optional[str] = None


class OrdersChannelReturnArgs(OKXBaseModel):
    channel: str
    instType: str
    uid: str
    instFamily: Optional[str] = None
    instId: Optional[str] = None


class WSOrder(OKXBaseModel):
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


class OrdersChannel(OKXBaseModel):
    arg: OrdersChannelReturnArgs
    data: List[WSOrder]


class OrderBookInputArgs(OKXBaseModel):
    channel: str
    instId: str


class OrderBookReturnArgs(OKXBaseModel):
    channel: str
    instId: str


class OrderBookData(OKXBaseModel):
    asks: List[Ask]
    bids: List[Bid]
    ts: str
    seqId: int
    instId: Optional[str] = None
    checksum: Optional[int] = None
    prevSeqId: Optional[int] = None


class OrderBookChannel(OKXBaseModel):
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
    "positions": PositionsChannel,  # Missing pTime
    "balance_and_position": BalanceAndPositionsChannel,
    "orders": OrdersChannel
}

available_channel_models = (
        public_channels_available | business_channels_available | private_channels_available
)
