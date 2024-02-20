from typing import List

from h2o_wave import Q, ui, on, data, run_on, AsyncSite, pack  # noqa F401

from h2o_dashboard.util import add_card
from pyokx.data_structures import FillHistoricalMetrics, FillHistoricalMetricsEntry
from pyokx.redis_structured_streams import get_stream_okx_fill_metrics_report


class OKX_Fill_Report_StreamWidget:

    def __init__(self, q: Q, card_name: str, box: str):
        self.q = q
        self.count = 1  # Enforce only the latest data entry since it contains all latest data
        self.fill_metrics_report_stream: List[FillHistoricalMetrics] = []
        self.card_name = card_name
        self.box = box

    async def _update_stream(self):
        self.fill_metrics_report_stream: List[FillHistoricalMetrics] = await get_stream_okx_fill_metrics_report(
            async_redis=self.q.client.async_redis, count=self.count)
        return self.fill_metrics_report_stream

    async def _is_initialized(self):
        return len(self.fill_metrics_report_stream) > 0

    async def get_ui_fill_metrics_report(self, box: str):
        if await self._is_initialized():
            latest_fill_metrics_report: FillHistoricalMetrics = self.fill_metrics_report_stream[-1]
        else:
            latest_fill_metrics_report = []
        items = []
        for timeframe, fill_metrics in latest_fill_metrics_report:
            print(f'{timeframe = }')
            print(f'{fill_metrics = }')
            items.append(ui.stat_table_item(
                label=timeframe,
                values=[str(fill_metrics.avg_fill_pnl), str(fill_metrics.total_fill_pnl),
                        str(fill_metrics.total_fill_fee)]
            ))
        return ui.stat_table_card(
            box=box,
            title='Fill Metrics Report - okx:reports@fill_metrics',
            columns=['Timeframe', 'Avg Fill PnL', 'Total Fill PnL', 'Total Fill Fee'],
            items=items
        )

    async def add_cards(self):
        await self._update_stream()
        await add_card(self.q, self.card_name + '_fill_metrics_report',
                       await self.get_ui_fill_metrics_report(box=self.box))
        await self.q.page.save()

    async def update_cards(self):
        await self._update_stream()
        if await self._is_initialized():
            latest_fill_metrics_report: FillHistoricalMetrics = self.fill_metrics_report_stream[-1]
        else:
            latest_fill_metrics_report = FillHistoricalMetrics(
                ONE_DAY=FillHistoricalMetricsEntry(avg_fill_pnl=0, total_fill_pnl=0, total_fill_fee=0),
                ONE_WEEK=FillHistoricalMetricsEntry(avg_fill_pnl=0, total_fill_pnl=0, total_fill_fee=0),
                ONE_MONTH=FillHistoricalMetricsEntry(avg_fill_pnl=0, total_fill_pnl=0, total_fill_fee=0),
                THREE_MONTHS=FillHistoricalMetricsEntry(avg_fill_pnl=0, total_fill_pnl=0, total_fill_fee=0)
            )

        fill_metrics_report_card: ui.stat_table_card = self.q.page[self.card_name + '_fill_metrics_report']
        items = []
        for timeframe, fill_metrics in latest_fill_metrics_report:
            items.append(ui.stat_table_item(
                label=timeframe,
                values=[str(fill_metrics.avg_fill_pnl), str(fill_metrics.total_fill_pnl),
                        str(fill_metrics.total_fill_fee)]
            ))
        fill_metrics_report_card.items = items
        await self.q.page.save()
