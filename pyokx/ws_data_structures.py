from typing import List

from pydantic import BaseModel

from pyokx.data_structures import InstType, Instrument, AccountBalanceData, Position


class CandleStick(BaseModel):
    timestamp: str
    open: str
    high: str
    low: str
    close: str
    is_closed: str


class PriceLimit(BaseModel):
    instId: str
    buyLmt: str
    sellLmt: str
    ts: str
    enabled: bool


class ws_PublicChannelInputArgsTypeInstID(BaseModel):
    channel: str
    instId: str


class ws_PublicChannelInputArgsTypeInstType(BaseModel):
    channel: str
    instType: str


class InstrumentsChannelInputArgs(ws_PublicChannelInputArgsTypeInstType):
    ...


class InstrumentsChannel(BaseModel):
    args: InstrumentsChannelInputArgs
    data: List[Instrument]


class PriceLimitChannelInputArgs(ws_PublicChannelInputArgsTypeInstID):
    ...


class PriceLimitChannel(BaseModel):
    args: PriceLimitChannelInputArgs
    data: List[PriceLimit]


class MarkPriceChannelInputArgs(ws_PublicChannelInputArgsTypeInstID):
    ...


class MarkPrice(BaseModel):
    instType: str
    instId: str
    markPx: str
    ts: str


class MarkPriceChannel(BaseModel):
    args: MarkPriceChannelInputArgs
    data: List[MarkPrice]


class MarkPriceCandleSticksChannelInputArgs(ws_PublicChannelInputArgsTypeInstID):
    ...

class MarkPriceCandleSticksChannel(BaseModel):
    args: MarkPriceChannelInputArgs
    data: List[CandleStick]

    @staticmethod
    def from_array(args:MarkPriceCandleSticksChannelInputArgs, data):
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


class IndexTickersChannelInputArgs(ws_PublicChannelInputArgsTypeInstID):
    ...


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



class IndexCandleSticksChannelInputArgs(ws_PublicChannelInputArgsTypeInstID):
    ...

class IndexCandleSticksChannel(BaseModel):
    args: IndexCandleSticksChannelInputArgs
    data: List[CandleStick]

    @staticmethod
    def from_array(args:IndexCandleSticksChannelInputArgs, data):
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

class ws_TradingAccountChannelInputArgsTypeCCY(BaseModel):
    channel: str
    ccy: str

class AccountChannelInputArgs(ws_TradingAccountChannelInputArgsTypeCCY):
    ...

class AccountChannelReturnArgs(ws_TradingAccountChannelInputArgsTypeCCY):
    uid: str

class AccountChannel(BaseModel):
    args: AccountChannelReturnArgs
    data: List[AccountBalanceData]


class PositionChannelInputArgs(BaseModel):
    channel: str
    instType: str
    instFamily: str
    instId: str

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


class ws_balData_element(BaseModel):
    ccy: str
    cashBal: str
    uTime: str

class ws_posData_element(BaseModel):
    posId: str
    tradeId: str
    instId: str
    instType: InstType
    mgnMode: str
    posSide: str
    pos: str
    ccy: str
    posCcy: str
    avgPx: str
    uTIme: str

class ws_trades_element(BaseModel):
    instId: str
    tradeId: str

class BalanceAndPositionData(BaseModel):
    pTime: str
    eventType: str
    balData: List[ws_balData_element]
    posData: List[ws_posData_element]
    trades: List[ws_trades_element]

class BalanceAndPositionsChannel(BaseModel):
    args: BalanceAndPositionsChannelReturnArgs
    data: List[BalanceAndPositionData]

class WebSocketConnectionConfig(BaseModel):
    channels: dict = {}
    wss_url: str


