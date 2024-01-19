from dataclasses import dataclass, field
from typing import Dict

from pyokx.okx_market_maker.utils.OkxEnum import InstType


@dataclass
class MarkPx:
    inst_type: InstType = None
    inst_id: str = 0
    mark_px: float = 0
    ts: int = 0

    @classmethod
    def init_from_ws_json_message(cls, json_response):
        mark_px_instance = MarkPx()
        mark_px_instance.inst_type = InstType(json_response["instType"])
        mark_px_instance.inst_id = json_response.get("instId", "")
        mark_px_instance.mark_px = float(json_response.get("markPx", 0))
        mark_px_instance.ts = int(json_response.get("ts", 0))
        return mark_px_instance

    def to_dict(self):
        return {
            "instType": self.inst_type.value,
            "instId": self.inst_id,
            "markPx": self.mark_px,
            "ts": self.ts
        }


@dataclass
class MarkPxCache:
    _mark_px_map: Dict[str, MarkPx] = field(default_factory=lambda: dict())

    def update_from_ws_json_message(self, json_response):
        data_list = json_response["data"]
        for data in data_list:
            mark_px = MarkPx.init_from_ws_json_message(data)
            self._mark_px_map[mark_px.inst_id] = mark_px

    def get_mark_px(self, inst_id) -> MarkPx:
        return self._mark_px_map.get(inst_id)

    def to_dict(self):
        return {
            "mark_px_map": {k: v.to_dict() for k, v in self._mark_px_map.items()}
        }
