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

    def _get_fills_ui_columns(self):
        return [
            ui.table_column(name='timeframe', label='Timeframe', sortable=True, filterable=True, searchable=True),
            ui.table_column(name='instrument_id', label='Instrument ID', sortable=True, filterable=True,
                            searchable=True),
            ui.table_column(name='volume_traded', label='Volume Traded', sortable=True, filterable=True),
            ui.table_column(name='average_fill_price', label='Average Fill Price', sortable=True, filterable=True),
            ui.table_column(name='profit_loss', label='Profit Loss', sortable=True, filterable=True),
            ui.table_column(name='fees_paid', label='Fees Paid', sortable=True, filterable=True),
            ui.table_column(name='profitable_trades', label='Profitable Trades', sortable=True, filterable=True),
            ui.table_column(name='loss_making_trades', label='Loss Making Trades', sortable=True, filterable=True),
            ui.table_column(name='best_trade', label='Best Trade', sortable=True, filterable=True),
            ui.table_column(name='worst_trade', label='Worst Trade', sortable=True, filterable=True),
            ui.table_column(name='avg_fill_pnl', label='Avg Fill PnL', sortable=True, filterable=True),
        ]

    async def get_ui_fill_metrics_report(self, box: str):
        if await self._is_initialized():
            latest_fill_metrics_report: FillHistoricalMetrics = self.fill_metrics_report_stream[-1]
        else:
            latest_fill_metrics_report = []

        rows = []
        for timeframe, fill_metrics in latest_fill_metrics_report:
            fill_metrics: List[FillHistoricalMetricsEntry]
            for instrument_metrics in fill_metrics:
                if float(instrument_metrics.volume_traded) == 0:
                    continue
                if round(abs(float(instrument_metrics.profit_loss)), 2) <= 0:
                    continue
                values = [
                    timeframe.replace('_', ' '),
                    instrument_metrics.instrument_id,
                    instrument_metrics.volume_traded,
                    instrument_metrics.average_fill_price,
                    instrument_metrics.profit_loss,
                    instrument_metrics.fees_paid,
                    instrument_metrics.profitable_trades,
                    instrument_metrics.loss_making_trades,
                    instrument_metrics.best_trade,
                    instrument_metrics.worst_trade,
                    instrument_metrics.avg_fill_pnl,
                ]

                for i, value in enumerate(values):
                    if value is None:
                        values[i] = 'N/A'
                    elif isinstance(value, float):
                        values[i] = str(f'{value:.2f}')
                    else:
                        values[i] = str(value)

                rows.append(
                    ui.table_row(
                        name=timeframe + instrument_metrics.instrument_id,
                        cells=values
                    )
                )

        return ui.form_card(box=box, items=[
            ui.text_xl('Fill Metrics Report'),
            ui.table(
                name='fill_metrics_report',
                columns=self._get_fills_ui_columns(),
                rows=rows,
                groupable=True,
                downloadable=True,
                resettable=True,
                height='600px'
            )
        ])

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
                ONE_DAY=[FillHistoricalMetricsEntry(
                    instrument_id='N/A',
                    volume_traded=0,
                    average_fill_price=0,
                    profit_loss=0,
                    fees_paid=0,
                    profitable_trades=0,
                    loss_making_trades=0,
                    best_trade=0,
                    worst_trade=0,
                    avg_fill_pnl=0
                )]
            )

        fill_metrics_report_card: ui.stat_table_card = self.q.page[self.card_name + '_fill_metrics_report']
        rows = []
        for timeframe, fill_metrics in latest_fill_metrics_report:
            fill_metrics: List[FillHistoricalMetricsEntry]
            for instrument_metrics in fill_metrics:
                if float(instrument_metrics.volume_traded) == 0:
                    continue
                if round(abs(float(instrument_metrics.profit_loss)), 2) <= 0:
                    continue
                values = [
                    timeframe.replace('_', ' '),
                    instrument_metrics.instrument_id,
                    instrument_metrics.volume_traded,
                    instrument_metrics.average_fill_price,
                    instrument_metrics.profit_loss,
                    instrument_metrics.fees_paid,
                    instrument_metrics.profitable_trades,
                    instrument_metrics.loss_making_trades,
                    instrument_metrics.best_trade,
                    instrument_metrics.worst_trade,
                    instrument_metrics.avg_fill_pnl,
                ]

                for i, value in enumerate(values):
                    if value is None:
                        values[i] = 'N/A'
                    elif isinstance(value, float):
                        values[i] = str(f'{value:.2f}')
                    else:
                        values[i] = str(value)

                rows.append(
                    ui.table_row(
                        name=timeframe + instrument_metrics.instrument_id,
                        cells=values
                    )
                )

        fill_metrics_report_card.items[0].table.rows = rows
        await self.q.page.save()
