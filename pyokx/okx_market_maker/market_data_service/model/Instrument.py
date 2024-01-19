from dataclasses import dataclass
from decimal import Decimal

from pyokx.okx_market_maker.utils.OkxEnum import InstType, OptType, CtType, InstState


@dataclass
class Instrument:
    inst_type: InstType = None
    inst_id: str = ""
    uly: str = ""
    inst_family: str = ""
    base_ccy: str = ""
    quote_ccy: str = ""
    settle_ccy: str = ""

    ct_val: float = 0
    ct_mul: float = 0
    ct_val_ccy: str = ""
    opt_type: OptType = None
    stk: float = 0
    list_time: int = 0
    exp_time: int = 0

    tick_sz: Decimal = 0
    lot_sz: Decimal = 0
    min_sz: Decimal = 0
    ct_type: CtType = None

    state: InstState = None


    @classmethod
    def init_from_ws_json_message(cls, json_response):
        instrument = Instrument()
        instrument.inst_type = InstType(json_response["instType"])
        instrument.inst_id = json_response.get("instId")
        instrument.uly = json_response.get("uly")
        instrument.inst_family = json_response.get("instFamily")
        instrument.base_ccy = json_response.get("baseCcy")
        instrument.quote_ccy = json_response.get("quoteCcy")
        instrument.settle_ccy = json_response.get("settleCcy")

        instrument.ct_val = float(json_response["ctVal"]) if json_response.get("ctVal") else 0
        instrument.ct_mul = float(json_response["ctMult"]) if json_response.get("ctMult") else 0
        instrument.ct_val_ccy = json_response.get("ctValCcy")
        instrument.opt_type = OptType(json_response["optType"]) if json_response.get("optType") else None
        instrument.stk = float(json_response["stk"]) if json_response.get("stk") else 0
        instrument.list_time = int(json_response["listTime"]) if json_response.get("listTime") else 0
        instrument.exp_time = int(json_response["expTime"]) if json_response.get("expTime") else 0

        instrument.tick_sz = Decimal(json_response["tickSz"]) if json_response.get("tickSz") else Decimal('0')
        instrument.lot_sz = Decimal(json_response["lotSz"]) if json_response.get("lotSz") else Decimal('0')
        instrument.min_sz = Decimal(json_response["minSz"]) if json_response.get("minSz") else Decimal('0')
        instrument.ct_type = CtType(json_response["ctType"]) if json_response.get("ctType") else None

        instrument.state = InstState(json_response["state"]) if json_response.get("state") else None
        return instrument

    def to_dict(self):
        return {
            "instType": self.inst_type.value,
            "instId": self.inst_id,
            "uly": self.uly,
            "instFamily": self.inst_family,
            "baseCcy": self.base_ccy,
            "quoteCcy": self.quote_ccy,
            "settleCcy": self.settle_ccy,
            "ctVal": self.ct_val,
            "ctMult": self.ct_mul,
            "ctValCcy": self.ct_val_ccy,
            "optType": self.opt_type.value if self.opt_type else None,
            "stk": self.stk,
            "listTime": self.list_time,
            "expTime": self.exp_time,
            "tickSz": str(self.tick_sz),
            "lotSz": str(self.lot_sz),
            "minSz": str(self.min_sz),
            "ctType": self.ct_type.value if self.ct_type else None,
            "state": self.state.value if self.state else None,
        }
