from typing import List

from h2o_wave import Q, ui, on, data, run_on, AsyncSite  # noqa F401

from h2o_dashboard.util import add_card
from pyokx.redis_structured_streams import get_stream_okx_account_messages, get_stream_okx_position_messages, \
    get_stream_okx_fill_metrics_report
from pyokx.rest_messages_service import FillHistoricalMetrics, FillHistoricalMetricsEntry
from pyokx.ws_data_structures import AccountChannel, PositionsChannel, WSPosition


class OKX_Account_StreamWidget:

    def __init__(self, q: Q, card_name: str, box:str,count: int = 10):
        self.q = q
        self.count = count
        self.account_stream: List[AccountChannel] = []
        self.card_name = card_name
        self.box = box
        self.colors = ['$blue', '$red', '$green', '$yellow', '$orange', '$pink', '$purple', '$cyan', '$gray']

    async def _update_stream(self):
        self.account_stream: List[AccountChannel] = await get_stream_okx_account_messages(
            async_redis=self.q.client.async_redis, count=self.count)
        return self.account_stream

    async def _is_initialized(self):
        return bool(self.account_stream)

    def get_ui_total_equity_box_as_small_stat(self, box: str):
        last_account_stream_entry: AccountChannel = self.account_stream[-1]
        last_account_stream_data = last_account_stream_entry.data[0]

        print(f'{[account.data[0].totalEq for account in self.account_stream] = }')

        return ui.small_series_stat_card(
            box=box,
            title='Total Equity',
            value='=${{intl total_eq minimum_fraction_digits=2 maximum_fraction_digits=2}}',
            data=dict(
                u_time=last_account_stream_data.uTime,
                total_eq=last_account_stream_data.totalEq),
            plot_type='area',
            plot_value='total_eq',
            plot_color='$green',
            plot_data=data('u_time total_eq', -self.count,
                           rows=[[account.data[0].uTime, account.data[0].totalEq] for account in self.account_stream]),
            plot_zero_value=min([float(account.data[0].totalEq) for account in self.account_stream]) * 0.9999,
            plot_curve='linear',
        )

    def get_ui_account_breakdown_box_as_pie_stat(self, box: str):
        last_account_stream_entry: AccountChannel = self.account_stream[-1]
        last_account_stream_data = last_account_stream_entry.data[0]
        pies = []
        colors_copy = None

        for account_balance_detail in last_account_stream_data.details:
            if not colors_copy:
                colors_copy = self.colors.copy()
            color = colors_copy.pop()
            fraction = float(account_balance_detail.eqUsd) / float(last_account_stream_data.totalEq)
            percentage_string = str(round(fraction * 100, 2)) + '%'
            pies.append(ui.pie(
                # label: str,
                # value: str,
                # fraction: float,
                # color: str,
                # aux_value: str | None = None
                label=account_balance_detail.ccy,
                value=percentage_string,
                fraction=fraction,
                color=color,
                aux_value=f'${account_balance_detail.eqUsd} ({percentage_string})'
            ))
        return ui.wide_pie_stat_card(
            # box: str,
            # title: str,
            # pies: list[Pie],
            # commands: list[Command] | None = Non
            box=box,
            title='Account Breakdown',
            pies=pies
        )

    async def update_account_breakdown_card(self):
        last_account_stream_entry: AccountChannel = self.account_stream[-1]
        last_account_stream_data = last_account_stream_entry.data[0]
        account_breakdown_card: ui.wide_pie_stat_card = self.q.page[self.card_name + '_account_breakdown']
        details = {account_balance_detail.ccy: account_balance_detail.eqUsd for account_balance_detail in
                   last_account_stream_data.details}
        for pie, (k, v) in zip(account_breakdown_card.pies, details.items()):
            fraction = float(v) / float(last_account_stream_data.totalEq)
            percentage_string = str(round(fraction * 100, 2)) + '%'
            pie.label = k
            pie.value = percentage_string
            pie.fraction = fraction
            pie.aux_value = f'${round(float(v), 2)} ({percentage_string})'

    async def update_total_equity_card(self):
        last_account_stream_entry: AccountChannel = self.account_stream[-1]
        last_account_stream_data = last_account_stream_entry.data[0]
        total_equity_card: ui.small_series_stat_card = self.q.page[self.card_name + '_total_equity']
        total_equity_card.plot_data[-1] = [last_account_stream_data.uTime, last_account_stream_data.totalEq]
        total_equity_card.plot_zero_value = min(
            [float(account.data[0].totalEq) for account in self.account_stream]) * 0.9999
        total_equity_card.data = dict(
            u_time=last_account_stream_data.uTime,
            total_eq=last_account_stream_data.totalEq)

    async def add_cards(self):
        await self._update_stream()
        await add_card(self.q, self.card_name + '_total_equity',
                       self.get_ui_total_equity_box_as_small_stat(box=self.box))
        await add_card(self.q, self.card_name + '_account_breakdown',
                       self.get_ui_account_breakdown_box_as_pie_stat(box=self.box))
        await self.q.page.save()

    async def update_cards(self):
        await self._update_stream()
        await self.update_total_equity_card()
        await self.update_account_breakdown_card()
        await self.q.page.save()


class OKX_Positions_StreamWidget:

    def __init__(self, q: Q, card_name: str,box:str, count: int = 10):
        self.q = q
        self.count = count
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


class OKX_Fill_Report_StreamWidget:

    def __init__(self, q: Q, card_name: str, box: str, count: int = 10):
        self.q = q
        self.count = count
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
