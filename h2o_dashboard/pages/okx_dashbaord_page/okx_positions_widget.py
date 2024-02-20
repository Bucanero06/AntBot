from typing import List

from h2o_wave import Q, ui, on, data, run_on, AsyncSite, pack  # noqa F401

from h2o_dashboard.util import add_card
from pyokx.redis_structured_streams import get_stream_okx_position_messages
from pyokx.ws_data_structures import PositionsChannel, WSPosition


class OKX_Live_Positions_StreamWidget:

    def __init__(self, q: Q, card_name: str, box: str):
        self.q = q
        self.count = 1  # Enforce only the latest data entry since it contains all latest data
        self.positions_stream: List[PositionsChannel] = []
        self.card_name = card_name
        self.box = box

        self._column_mappings = dict(
            posId='Position ID',
            instId='Instrument ID',
            pos='Position',
            upl='UPL',
            avgPx='Average Price',
            lever='Leverage',
            last='Last',
            margin='Margin',
            pTime='Time'
        )

    async def _update_stream(self):
        self.positions_stream: List[PositionsChannel] = await get_stream_okx_position_messages(
            async_redis=self.q.client.async_redis, count=self.count)
        return self.positions_stream

    async def _is_initialized(self):
        return len(self.positions_stream) > 0

    async def get_ui_live_positions_table(self, box: str):
        if await self._is_initialized():
            latest_positions_report: PositionsChannel = self.positions_stream[-1]
            latest_positions_data = latest_positions_report.data
        else:
            latest_positions_data = []

        items = []
        for position in latest_positions_data:
            position: WSPosition = position
            columns_values = [getattr(position, col) for col in self._column_mappings.keys()]
            label = str(columns_values.pop(0))
            values = []
            for pos_col in columns_values:
                try:
                    pos_col = str(round(float(pos_col), 2))
                except ValueError:
                    pass
                value = str(pos_col)
                values.append(value)
            items.append(ui.stat_table_item(label=label, values=values))
        return ui.stat_table_card(
            box=box,
            title='Live Positions - okx:websockets@positions',
            columns=list(self._column_mappings.values()),
            items=items
        )

    async def add_cards(self):
        await self._update_stream()
        await add_card(self.q, self.card_name + '_positions_table',
                       await self.get_ui_live_positions_table(box=self.box))
        await self.q.page.save()

    async def update_cards(self):
        await self._update_stream()
        if await self._is_initialized():
            latest_positions_report: PositionsChannel = self.positions_stream[-1]
            latest_positions_data = latest_positions_report.data
        else:
            latest_positions_data = []

        positions_table_card: ui.stat_table_card = self.q.page[self.card_name + '_positions_table']
        items = []
        for position in latest_positions_data:
            position: WSPosition = position
            columns_values = [getattr(position, col) for col in self._column_mappings.keys()]
            label = str(columns_values.pop(0))
            values = []
            for pos_col in columns_values:
                try:
                    pos_col = str(round(float(pos_col), 2))
                except ValueError:
                    pass
                value = str(pos_col)
                values.append(value)
            items.append(ui.stat_table_item(label=label, values=values))
        positions_table_card.items = items
        await self.q.page.save()
