from datetime import datetime
from enum import Enum
from typing import List, Optional, Union

from pydantic import BaseModel

from redis_tools.syncio.model import Model


class InstType(Enum):
    # Enumerate all possible values for instType
    SPOT = "SPOT"
    MARGIN = "MARGIN"
    SWAP = "SWAP"
    FUTURES = "FUTURES"
    OPTION = "OPTION"


class Order(BaseModel):
    accFillSz: str
    algoClOrdId: str
    algoId: str
    attachAlgoClOrdId: str
    attachAlgoOrds: List[str]
    avgPx: str
    cTime: str
    cancelSource: str
    cancelSourceReason: str
    category: str
    ccy: str
    clOrdId: str
    fee: str
    feeCcy: str
    fillPx: str
    fillSz: str
    fillTime: str
    instId: str
    instType: str
    lever: str
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


class Cancelled_Order(BaseModel):
    clOrdId: str
    ordId: str
    sCode: str
    sMsg: str


class Cancelled_Algo_Order(BaseModel):
    """
    e.g. {'algoClOrdId': '', 'algoId': '661126556584251392', 'clOrdId': '', 'sCode': '0', 'sMsg': '', 'tag': ''}
    """
    algoClOrdId: str
    algoId: str
    clOrdId: str
    sCode: str
    sMsg: str
    tag: str


class Position(Model):
    """
    e.g. {'adl': '1', 'availPos': '', 'avgPx': '45075.3000000000000001', 'baseBal': '', 'baseBorrowed': '', 'baseInterest': '', 'bePx': '45120.39784892446', 'bizRefId': '', 'bizRefType': '', 'cTime': '1703728631744', 'ccy': 'USDT', 'closeOrderAlgo': [], 'deltaBS': '', 'deltaPA': '', 'fee': '-0.901506', 'fundingFee': '0', 'gammaBS': '', 'gammaPA': '', 'idxPx': '43474.0', 'imr': '', 'instId': 'BTC-USDT-240329', 'instType': 'FUTURES', 'interest': '', 'last': '45070.1', 'lever': '3', 'liab': '', 'liabCcy': '', 'liqPenalty': '0', 'liqPx': '30186.137167252637', 'margin': '601.004', 'markPx': '45068', 'mgnMode': 'isolated', 'mgnRatio': '74.05007741388319', 'mmr': '7.21088', 'notionalUsd': '1804.4145568', 'optVal': '', 'pendingCloseOrdLiabVal': '', 'pnl': '0', 'pos': '4', 'posCcy': '', 'posId': '660420980350771429', 'posSide': 'net', 'quoteBal': '', 'quoteBorrowed': '', 'quoteInterest': '', 'realizedPnl': '-0.901506', 'spotInUseAmt': '', 'spotInUseCcy': '', 'thetaBS': '', 'thetaPA': '', 'tradeId': '3014208', 'uTime': '1703728655219', 'upl': '-0.2920000000001164', 'uplLastPx': '-0.2080000000001746', 'uplRatio': '-0.0004858536715233', 'uplRatioLastPx': '-0.0003460875468385', 'usdPx': '', 'vegaBS': '', 'vegaPA': ''}
    """
    adl: str
    availPos: str
    avgPx: str
    baseBal: str
    baseBorrowed: str
    baseInterest: str
    bePx: str
    bizRefId: str
    bizRefType: str
    cTime: str
    ccy: str
    closeOrderAlgo: List[dict]
    deltaBS: str
    deltaPA: str
    fee: str
    fundingFee: str
    gammaBS: str
    gammaPA: str
    idxPx: str
    imr: str
    instId: str
    instType: str
    interest: str
    last: str
    lever: str
    liab: str
    liabCcy: str
    liqPenalty: str
    liqPx: str
    margin: str
    markPx: str
    mgnMode: str
    mgnRatio: str
    mmr: str
    notionalUsd: str
    optVal: str
    pendingCloseOrdLiabVal: str
    pnl: str
    pos: str
    posCcy: str
    posId: str
    posSide: str
    quoteBal: str
    quoteBorrowed: str
    quoteInterest: str
    realizedPnl: str
    spotInUseAmt: str
    spotInUseCcy: str
    thetaBS: str
    thetaPA: str
    tradeId: str
    uTime: str
    upl: str
    uplLastPx: str
    uplRatio: str
    uplRatioLastPx: str
    usdPx: str
    vegaBS: str
    vegaPA: str


class Closed_Position(BaseModel):
    """
    e.g. {'clOrdId': '', 'instId': 'BTC-USDT-240329', 'posSide': 'net', 'tag': ''}
    """
    clOrdId: str
    instId: str
    posSide: str
    tag: str


class Ticker(BaseModel):
    """
    e.g {'instType': 'FUTURES', 'instId': 'BTC-USDT-240329', 'last': '44725.3', 'lastSz': '11', 'askPx': '44727', 'askSz': '147', 'bidPx': '44724.5', 'bidSz': '170', 'open24h': '43854.9', 'high24h': '45406.2', 'low24h': '38196.8', 'volCcy24h': '14025.4', 'vol24h': '1402540', 'ts': '1703741214308', 'sodUtc0': '44977.8', 'sodUtc8': '44452.3'}]}
    """
    instType: str
    instId: str
    last: str
    lastSz: str
    askPx: str
    askSz: str
    bidPx: str
    bidSz: str
    open24h: str
    high24h: str
    low24h: str
    volCcy24h: str
    vol24h: str
    ts: str
    sodUtc0: str
    sodUtc8: str


class Order_Placement_Return(BaseModel):
    """
    e.g. {'clOrdId': '', 'ordId': '660478634888654848', 'sCode': '0', 'sMsg': 'Order placed', 'tag': ''}
    """
    clOrdId: str
    ordId: str
    sCode: str
    sMsg: str
    tag: str


class Algo_Order(BaseModel):
    """
    e.g. {'activePx': '', 'actualPx': '', 'actualSide': '', 'actualSz': '0', 'algoClOrdId': '', 'algoId': '660707839958183936', 'amendPxOnTriggerType': '0', 'attachAlgoOrds': [], 'cTime': '1703797024404', 'callbackRatio': '', 'callbackSpread': '', 'ccy': '', 'clOrdId': '', 'closeFraction': '', 'failCode': '', 'instId': 'BTC-USDT-240329', 'instType': 'FUTURES', 'last': '44080', 'lever': '3', 'moveTriggerPx': '', 'ordId': '', 'ordIdList': [], 'ordPx': '', 'ordType': 'conditional', 'posSide': 'net', 'pxLimit': '', 'pxSpread': '', 'pxVar': '', 'quickMgnType': '', 'reduceOnly': 'false', 'side': 'buy', 'slOrdPx': '', 'slTriggerPx': '', 'slTriggerPxType': '', 'state': 'live', 'sz': '1', 'szLimit': '', 'tag': '', 'tdMode': 'isolated', 'tgtCcy': '', 'timeInterval': '', 'tpOrdPx': '-1', 'tpTriggerPx': '44075', 'tpTriggerPxType': 'last', 'triggerPx': '', 'triggerPxType': '', 'triggerTime': ''}, {'activePx': '', 'actualPx': '', 'actualSide': '', 'actualSz': '0', 'algoClOrdId': '', 'algoId': '660707810421895170', 'amendPxOnTriggerType': '0', 'attachAlgoOrds': [], 'cTime': '1703797017362', 'callbackRatio': '', 'callbackSpread': '', 'ccy': '', 'clOrdId': '', 'closeFraction': '', 'failCode': '', 'instId': 'BTC-USDT-240329', 'instType': 'FUTURES', 'last': '44079.5', 'lever': '3', 'moveTriggerPx': '', 'ordId': '', 'ordIdList': [], 'ordPx': '', 'ordType': 'conditional', 'posSide': 'net', 'pxLimit': '', 'pxSpread': '', 'pxVar': '', 'quickMgnType': '', 'reduceOnly': 'false', 'side': 'buy', 'slOrdPx': '', 'slTriggerPx': '', 'slTriggerPxType': '', 'state': 'live', 'sz': '1', 'szLimit': '', 'tag': '', 'tdMode': 'isolated', 'tgtCcy': '', 'timeInterval': '', 'tpOrdPx': '-1', 'tpTriggerPx': '44074.5', 'tpTriggerPxType': 'last', 'triggerPx': '', 'triggerPxType': '', 'triggerTime': ''}
    """
    activePx: str
    actualPx: str
    actualSide: str
    actualSz: str
    algoClOrdId: str
    algoId: str
    amendPxOnTriggerType: str
    attachAlgoOrds: List[str]
    cTime: str
    callbackRatio: str
    callbackSpread: str
    ccy: str
    clOrdId: str
    closeFraction: str
    failCode: str
    instId: str
    instType: str
    last: str
    lever: str
    moveTriggerPx: str
    ordId: str
    ordIdList: List[str]
    ordPx: str
    ordType: str
    posSide: str
    pxLimit: str
    pxSpread: str
    pxVar: str
    quickMgnType: str
    reduceOnly: str
    side: str
    slOrdPx: str
    slTriggerPx: str
    slTriggerPxType: str
    state: str
    sz: str
    szLimit: str
    tag: str
    tdMode: str
    tgtCcy: str
    timeInterval: str
    tpOrdPx: str
    tpTriggerPx: str
    tpTriggerPxType: str
    triggerPx: str
    triggerPxType: str
    triggerTime: str


class Algo_Order_Placement_Return(BaseModel):
    """
    e.g. {'algoClOrdId': '', 'algoId': '660710963351515145', 'clOrdId': '', 'sCode': '0', 'sMsg': '', 'tag': ''}
    """
    algoClOrdId: str
    algoId: str
    clOrdId: str
    sCode: str
    sMsg: str
    tag: str


class Instrument(BaseModel):
    """
    e.g. {'alias': 'next_month', 'baseCcy': '', 'category': '1', 'ctMult': '1', 'ctType': 'inverse', 'ctVal': '100',
         'ctValCcy': 'USD', 'expTime': '1708675200000', 'instFamily': 'BTC-USD', 'instId': 'BTC-USD-240223',
         'instType': 'FUTURES', 'lever': '100', 'listTime': '1702627800062', 'lotSz': '1',
         'maxIcebergSz': '1000000.0000000000000000', 'maxLmtAmt': '1000000', 'maxLmtSz': '1000000', 'maxMktAmt': '',
         'maxMktSz': '10000', 'maxStopSz': '10000', 'maxTriggerSz': '1000000.0000000000000000',
         'maxTwapSz': '1000000.0000000000000000', 'minSz': '1', 'optType': '', 'quoteCcy': '', 'settleCcy': 'BTC',
         'state': 'live', 'stk': '', 'tickSz': '0.01', 'uly': 'BTC-USD'}
    """
    alias: str
    baseCcy: str
    category: str
    ctMult: str
    ctType: str
    ctVal: str
    ctValCcy: str
    expTime: str
    instFamily: str
    instId: str
    instType: str
    lever: str
    listTime: str
    lotSz: str
    maxIcebergSz: str
    maxLmtAmt: str
    maxLmtSz: str
    maxMktAmt: str
    maxMktSz: str
    maxStopSz: str
    maxTriggerSz: str
    maxTwapSz: str
    minSz: str
    optType: str
    quoteCcy: str
    settleCcy: str
    state: str
    stk: str
    tickSz: str
    uly: str


class Bid(BaseModel):
    """
    e.g. '43752.4', '156', '0', '1'
    """
    price: str
    quantity: str
    deprecated_value: str
    number_of_orders: str


class Ask(BaseModel):
    """
    e.g. '43752.4', '156', '0', '1'
    """
    price: str
    quantity: str
    deprecated_value: str
    number_of_orders: str


class Orderbook_Snapshot(BaseModel):
    """
    e.g. {'asks': [['43746.5', '106', '0', '1'], ['43751.1', '171', '0', '1'], ['43751.2', '118', '0', '1'],
          ['43752.4', '156', '0', '1'], ['43753.5', '151', '0', '1'], ['43753.7', '126', '0', '1'],
          ['43754.7', '121', '0', '1'], ['43754.8', '158', '0', '1'], ['43755.4', '307', '0', '2'],
          ['43755.7', '179', '0', '1'], ['43756.4', '134', '0', '1'], ['43757', '179', '0', '1'],
          ['43757.2', '154', '0', '1'], ['43757.3', '171', '0', '1'], ['43758.1', '165', '0', '1'],
          ['43759.1', '159', '0', '1'], ['43759.2', '128', '0', '1'], ['43759.4', '125', '0', '1'],
          ['43760.3', '169', '0', '1'], ['43922.5', '1', '0', '1']],
 'bids': [['43746.4', '136', '0', '1'], ['43746.3', '151', '0', '1'], ['43740.7', '153', '0', '1'],
          ['43739.6', '163', '0', '1'], ['43739.3', '143', '0', '1'], ['43737.9', '133', '0', '1'],
          ['43736.8', '163', '0', '1'], ['43735.1', '168', '0', '1'], ['43735', '165', '0', '1'],
          ['43734.9', '168', '0', '1'], ['43733.8', '171', '0', '1'], ['43733.1', '296', '0', '2'],
          ['43732.7', '131', '0', '1'], ['43732.6', '127', '0', '1'], ['43731.6', '314', '0', '2'],
          ['43729', '298', '0', '2'], ['43728.8', '180', '0', '1'], ['43514', '1', '0', '1'],
          ['43311.2', '1', '0', '1'], ['43109.3', '1', '0', '1']], 'ts': '1703914467407'}
    """
    instId: str
    depth: str
    asks: List[Ask]
    bids: List[Bid]
    ts: str


class Simplified_Balance_Details(BaseModel):
    Currency: str
    Available_Balance: str
    Equity: str
    Equity_in_USD: str
    Frozen_Balance: str


class AccountBalanceDetails(BaseModel):
    """
    e.g. {'availBal': '1', 'availEq': '1', 'borrowFroz': '', 'cashBal': '1', 'ccy': 'BTC', 'crossLiab': '', 'disEq': '42219',
          'eq': '1', 'eqUsd': '42219', 'fixedBal': '0', 'frozenBal': '0', 'interest': '', 'isoEq': '0', 'isoLiab': '',
          'isoUpl': '0', 'liab': '', 'maxLoan': '', 'mgnRatio': '', 'notionalLever': '0', 'ordFrozen': '0', 'spotInUseAmt': '',
          'spotIsoBal': '0', 'stgyEq': '0', 'twap': '0', 'uTime': '1703639691142', 'upl': '0', 'uplLiab': ''}
    """
    availBal: str
    availEq: str
    borrowFroz: str
    cashBal: str
    ccy: str
    crossLiab: str
    disEq: str
    eq: str
    eqUsd: str
    fixedBal: str
    frozenBal: str
    interest: str
    isoEq: str
    isoLiab: str
    isoUpl: str
    liab: str
    maxLoan: str
    mgnRatio: str
    notionalLever: str
    ordFrozen: str
    spotInUseAmt: str
    spotIsoBal: str
    stgyEq: str
    twap: str
    uTime: str
    upl: str
    uplLiab: str


class AccountBalanceData(BaseModel):
    """
    e.g. {'adjEq': '', 'borrowFroz': '', 'details': [{'availBal': '1', 'availEq': '1', 'borrowFroz': '', 'cashBal': '1', 'ccy': 'BTC', 'crossLiab': '', 'disEq': '42219', 'eq': '1', 'eqUsd': '42219', 'fixedBal': '0', 'frozenBal': '0', 'interest': '', 'isoEq': '0', 'isoLiab': '', 'isoUpl': '0', 'liab': '', 'maxLoan': '', 'mgnRatio': '', 'notionalLever': '0', 'ordFrozen': '0', 'spotInUseAmt': '', 'spotIsoBal': '0', 'stgyEq': '0', 'twap': '0', 'uTime': '1703639691142', 'upl': '0', 'uplLiab': ''}, {'availBal': '100', 'availEq': '100', 'borrowFroz': '', 'cashBal': '100', 'ccy': 'OKB', 'crossLiab': '', 'disEq': '5207.329999999999', 'eq': '100', 'eqUsd': '5481.4', 'fixedBal': '0', 'frozenBal': '0', 'interest': '', 'isoEq': '0', 'isoLiab': '', 'isoUpl': '0', 'liab': '', 'maxLoan': '', 'mgnRatio': '', 'notionalLever': '0', 'ordFrozen': '0', 'spotInUseAmt': '', 'spotIsoBal': '0', 'stgyEq': '0', 'twap': '0', 'uTime': '1703639691152', 'upl': '0', 'uplLiab': ''}, {'availBal': '5069.205129833334', 'availEq': '5069.205129833334', 'borrowFroz': '', 'cashBal': '5069.205129833334', 'ccy': 'USDT', 'crossLiab': '', 'disEq': '5218.680085966916', 'eq': '5217.0627965', 'eqUsd': '5218.680085966916', 'fixedBal': '0', 'frozenBal': '147.85766666666666', 'interest': '', 'isoEq': '147.85766666666666', 'isoLiab': '', 'isoUpl': '2.5', 'liab': '', 'maxLoan': '', 'mgnRatio': '', 'notionalLever': '0', 'ordFrozen': '0', 'spotInUseAmt': '', 'spotIsoBal': '0', 'stgyEq': '0', 'twap': '0', 'uTime': '1703877105585', 'upl': '2.5', 'uplLiab': ''}, {'availBal': '1', 'availEq': '1', 'borrowFroz': '', 'cashBal': '1', 'ccy': 'ETH', 'crossLiab': '', 'disEq': '2310.18', 'eq': '1', 'eqUsd': '2310.18', 'fixedBal': '0', 'frozenBal': '0', 'interest': '', 'isoEq': '0', 'isoLiab': '', 'isoUpl': '0', 'liab': '', 'maxLoan': '', 'mgnRatio': '', 'notionalLever': '0', 'ordFrozen': '0', 'spotInUseAmt': '', 'spotIsoBal': '0', 'stgyEq': '0', 'twap': '0', 'uTime': '1703639691162', 'upl': '0', 'uplLiab': ''}], 'imr': '', 'isoEq': '147.90350254333333', 'mgnRatio': '', 'mmr': '', 'notionalUsd': '', 'ordFroz': '', 'totalEq': '55229.26008596692', 'uTime': '1703884466962'}
    """
    adjEq: str
    borrowFroz: str
    details: List[AccountBalanceDetails]
    imr: str
    isoEq: str
    mgnRatio: str
    mmr: str
    notionalUsd: str
    ordFroz: str
    totalEq: str
    uTime: str


class AccountConfigData(BaseModel):
    acctLv: str
    autoLoan: bool
    ctIsoMode: str
    greeksType: str
    ip: str
    kycLv: str
    label: str
    level: str
    levelTmp: str
    liquidationGear: str
    mainUid: str
    mgnIsoMode: str
    opAuth: str
    perm: str
    posMode: str
    roleType: str
    spotOffsetType: str
    spotRoleType: str
    spotTraderInsts: List[str]
    traderInsts: List[str]
    uid: str


class MaxOrderSizeData(BaseModel):
    ccy: str
    instId: str
    maxBuy: str
    maxSell: str


class MaxAvailSizeData(BaseModel):
    availBuy: str
    availSell: str
    instId: str


#
class InstrumentStatusReport(BaseModel):
    timestamp: str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    instId: str
    max_order_size: MaxOrderSizeData
    max_avail_size: MaxAvailSizeData
    positions: List[Position]
    orders: List[Order]
    algo_orders: List[Algo_Order]


class AccountStatusReport(BaseModel):
    timestamp: str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    account_balance: AccountBalanceData
    account_config: AccountConfigData
    all_positions: List[Position]
    all_orders: List[Order]
    all_algo_orders: List[Algo_Order]
    simplified_balance: Simplified_Balance_Details


class OKXSignalInput(BaseModel):
    instID: str = ''
    order_size: int = None
    leverage: int = None
    order_side: str = ''
    order_type: str = ''
    max_orderbook_limit_price_offset: float = None
    flip_position_if_opposite_side: bool = False
    clear_prior_to_new_order: bool = False
    red_button: bool = False
    order_usd_amount: float = None
    stop_loss_trigger_percentage: float = None
    take_profit_trigger_percentage: float = None
    tp_trigger_price_type: str = ''
    stop_loss_price_offset: float = None
    tp_price_offset: float = None
    sl_trigger_price_type: str = ''
    trailing_stop_activation_percentage: float = None
    trailing_stop_callback_ratio: float = None


class PremiumIndicatorSignals(BaseModel):
    Bullish: Optional[Union[int, str]]
    Bearish: Optional[Union[int, str]]
    Bullish_plus: Optional[Union[int, str]]
    Bearish_plus: Optional[Union[int, str]]
    Bullish_Exit: Optional[Union[int, str]]
    Bearish_Exit: Optional[Union[int, str]]


class PremiumIndicatorSignalRequestForm(BaseModel):
    InstIdAPIKey: str
    OKXSignalInput: OKXSignalInput
    PremiumIndicatorSignals: PremiumIndicatorSignals


class InstIdSignalRequestForm(BaseModel):
    InstIdAPIKey: str
    OKXSignalInput: OKXSignalInput


# {
#   "InstIdAPIKey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJydWJlbkBjYXJib255bC5vcmciLCJpZCI6InFtc2d4c0Eza0taNHMwaml1bTQwOHFvbGJWOTIiLCJyb2xlIjoidHJhZGluZ19pbnN0cnVtZW50IiwiaW5zdElEIjoiQlRDLVVTRFQtMjQwNjI4In0.WyO3oNTT5loBnQzsTcjM8Lt13F8-nNS7DI6PxSEGeSc",
#   "OKXSignalInput": {
#     "instID": "BTC-USDT-240628",
#     "order_size": 1,
#     "leverage": 0,
#     "order_side": "",
#     "order_type": "limit",
#     "max_orderbook_limit_price_offset": 0,
#     "flip_position_if_opposite_side": true,
#     "clear_prior_to_new_order": false,
#     "red_button": false,
#     "order_usd_amount": 0,
#     "stop_loss_trigger_percentage": 0,
#     "take_profit_trigger_percentage": 0,
#     "tp_trigger_price_type": "",
#     "stop_loss_price_offset": 0,
#     "tp_price_offset": 0,
#     "sl_trigger_price_type": "",
#     "trailing_stop_activation_percentage": 0,
#     "trailing_stop_callback_ratio": 0
#   },
#   "PremiumIndicatorSignals": {
#     "Bullish": "{{plot('Bullish')}}",
#     "Bearish": "{{plot('Bearish')}}",
#     "Bullish_plus": "{{plot('Bullish+')}}",
#     "Bearish_plus": "{{plot('Bearish+')}}",
#     "Bullish_Exit": "{{plot('Bullish Exit')}}",
#     "Bearish_Exit": "{{plot('Bearish Exit')}}"
#   }
# }

# {
#   "InstIdAPIKey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJydWJlbkBjYXJib255bC5vcmciLCJpZCI6InFtc2d4c0Eza0taNHMwaml1bTQwOHFvbGJWOTIiLCJyb2xlIjoidHJhZGluZ19pbnN0cnVtZW50IiwiaW5zdElEIjoiQlRDLVVTRFQtMjQwNjI4In0.WyO3oNTT5loBnQzsTcjM8Lt13F8-nNS7DI6PxSEGeSc",
#   "OKXSignalInput": {
#     "instID": "BTC-USDT-240628",
#     "order_size": 1,
#     "leverage": 0,
#     "order_side": "",
#     "order_type": "limit",
#     "max_orderbook_limit_price_offset": 0,
#     "flip_position_if_opposite_side": true,
#     "clear_prior_to_new_order": false,
#     "red_button": false,
#     "order_usd_amount": 0,
#     "stop_loss_trigger_percentage": 0,
#     "take_profit_trigger_percentage": 0,
#     "tp_trigger_price_type": "",
#     "stop_loss_price_offset": 0,
#     "tp_price_offset": 0,
#     "sl_trigger_price_type": "",
#     "trailing_stop_activation_percentage": 0,
#     "trailing_stop_callback_ratio": 0
#   },
#   "PremiumIndicatorSignals": {
#     "Bullish": "{{plot("Bullish")}}",
#     "Bearish": "{{plot("Bearish")}}",
#     "Bullish_plus": "{{plot("Bullish+")}}",
#     "Bearish_plus": "{{plot("Bearish+")}}",
#     "Bullish_Exit": "{{plot("Bullish Exit")}}",
#     "Bearish_Exit": "{{plot("Bearish Exit")}}"
#   }
# }
