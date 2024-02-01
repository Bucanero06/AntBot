# Copyright (c) 2024 Carbonyl LLC & Carbonyl R&D
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
from datetime import datetime
from typing import List

from h2o_wave import Q, ui, on, data, run_on, AsyncSite  # noqa F401

from h2o_dashboard.util import add_card
from pyokx.data_structures import AccountBalanceData, FillHistoricalMetrics, FillHistoricalMetricsEntry
from pyokx.redis_structured_streams import get_stream_okx_account_messages, get_stream_okx_position_messages, \
    get_stream_okx_fill_metrics_report
from pyokx.ws_data_structures import AccountChannel, PositionsChannel, WSPosition


class OKX_Account_StreamWidget:

    def __init__(self, q: Q, card_name: str, box: str, count: int = 10):
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

    def __init__(self, q: Q, card_name: str, box: str, count: int = 10):
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


class OKX_Manual_ControlsWidget:

    def __init__(self, q: Q, card_name: str, box: str):
        self.q = q
        self.card_name = card_name
        self.box = box
        self._initialized = False

    async def _is_initialized(self):
        return self._initialized

    async def get_manual_controls(self, box: str):
        # # signal_response = okx_signal_handler(
        # #                 red_button=True,
        # #             )
        # # signal_response = okx_signal_handler(
        # #     instID="BTC-USDT-240628",
        # #     order_size=1,
        # #     leverage=5,
        # #     order_side="BUY",
        # #     order_type="POST_ONLY",
        # #     max_orderbook_limit_price_offset=0.1,
        # #     flip_position_if_opposite_side=True,
        # #     clear_prior_to_new_order=False,
        # #     red_button=False,
        # #     # order_usd_amount=100,
        # #     stop_loss_price_offset=None,
        # #     tp_price_offset=None,
        # #     trailing_stop_activation_percentage=None,
        # #     trailing_stop_callback_ratio=None,
        # #     stop_loss_trigger_percentage=None,
        # #     take_profit_trigger_percentage=None,
        # #     tp_trigger_price_type=None,
        # #     sl_trigger_price_type=None,
        # # )
        # # print(f"{signal_response = }")

        return ui.form_card(
            box=box,
            # Lets set up a form to send a signal to the okx_signal_handler
            items=[
                ui.text_xl('Ping the bot'),
                ui.buttons([ui.button(name='ping_bot', label='Ping', primary=True),
                            ui.button(name='send_signal', label='Send', primary=True)]),
            ]
        )

    async def add_cards(self):
        await add_card(self.q, self.card_name + '_manual_controls', await self.get_manual_controls(box=self.box))
        await self.q.page.save()
        self._initialized = True

    async def update_cards(self):
        await self.q.page.save()


class Overview_StreamWidget:  # TODO: Will connect to the account streams for all exchanges, rn it's just okx

    def __init__(self, q: Q, card_name: str, box: str, count: int = 10):
        self.q = q
        self.count = count
        self.card_name = card_name
        self.colors = ['$blue', '$red', '$green', '$yellow', '$orange', '$pink', '$purple', '$cyan', '$gray']
        self.okx_account_stream: List[AccountChannel] = []
        self.okx_positions_stream: List[PositionsChannel] = []
        self.okx_position_column_mappings = dict(
            instId={'label': 'Instrument ID', 'type': 'str'},
            posId={'label': 'Position ID', 'type': 'int'},
            pos={'label': 'Position', 'type': 'float'},
            upl={'label': 'UPnL', 'type': 'float'},
            avgPx={'label': 'Avg Price', 'type': 'float'},
            lever={'label': 'Lev', 'type': 'float'},
            last={'label': 'Last', 'type': 'float'},
            margin={'label': 'Margin', 'type': 'float'},
            pTime={'label': 'Time', 'type': 'timestamp'},
        )
        self.box = box

    async def _update_stream(self):
        self.okx_account_stream: List[AccountChannel] = await get_stream_okx_account_messages(
            async_redis=self.q.client.async_redis, count=self.count)
        self.okx_positions_stream: List[PositionsChannel] = await get_stream_okx_position_messages(
            async_redis=self.q.client.async_redis, count=self.count)

    async def _is_initialized(self):
        return len(self.okx_account_stream) > 0 and len(self.okx_positions_stream) > 0

    async def get_all_exchanges_account_breakdown_table_card(self, box: str):
        # Table Exchange:Asset|Total-Asset-Value|FreeAssetCash
        latest_account_report: AccountChannel = self.okx_account_stream[-1]
        latest_account_data: AccountBalanceData = latest_account_report.data[0]

        # TODO Use values from all exchanges, then generate the ui item for each exchange prior to ui.stat ...
        okx_total_equity = latest_account_data.totalEq
        bitget_total_equity = 0  # TODO
        total_equity = float(okx_total_equity) + float(bitget_total_equity)

        '''OKX Exchange'''
        items = []
        for account_balance_detail in latest_account_data.details:
            label = f'OKX:{account_balance_detail.ccy}'
            total_asset_value = round(float(account_balance_detail.eqUsd), 2)
            unused_value = round(float(account_balance_detail.availBal) * (
                    float(account_balance_detail.disEq) / float(account_balance_detail.eq)), 2)
            fraction_of_total_equity = float(account_balance_detail.eqUsd) / float(total_equity)
            percentage_string = str(round(fraction_of_total_equity * 100, 0)) + '%'
            update_time = datetime.fromtimestamp(int(account_balance_detail.uTime) / 1000, tz=None).strftime(
                '%Y-%m-%d %H:%M:%S')
            #
            values = [total_asset_value, unused_value, percentage_string, update_time]
            items.append(ui.stat_table_item(label=label, values=[str(value) for value in values]))

        return ui.stat_table_card(
            box=box,
            title=f'Live Account - {{exchange}}:websockets@account - ${round(total_equity, 2)}',
            columns=['Exchange:Asset', 'Total-Asset-Value', 'FreeAssetCash', '% of Total Equity', 'Update Time'],
            items=items
        )

    async def get_all_exchanges_live_positions_table_card(self, box: str):
        latest_positions_report: PositionsChannel = self.okx_positions_stream[-1]
        latest_positions_data: List[WSPosition] = latest_positions_report.data

        items = []
        label_value = ''
        for position in latest_positions_data:
            values = []
            for i, (col_key, col_value) in enumerate(self.okx_position_column_mappings.items()):
                if i == 0:
                    label_value = f'OKX:{getattr(position, col_key)}'
                    continue
                pos_col = getattr(position, col_key)
                try:
                    expected_type = col_value['type']
                    if expected_type == 'float':
                        pos_col = round(float(pos_col), 2)
                    elif expected_type == 'int':
                        pos_col = int(pos_col)
                    elif expected_type == 'timestamp':
                        pos_col = datetime.fromtimestamp(int(pos_col) / 1000, tz=None).strftime(
                            '%Y-%m-%d %H:%M:%S')
                    else:
                        pos_col = str(pos_col)
                except ValueError:
                    pass
                value = str(pos_col)
                values.append(value)
            items.append(ui.stat_table_item(label=label_value, values=values))
        return ui.stat_table_card(
            box=box,
            title=f'Live Positions - {{exchange}}:websockets@positions - {len(latest_positions_data)} positions',
            columns=[col_value['label'] for col_value in self.okx_position_column_mappings.values()],
            items=items
        )

    async def get_all_exchanges_account_breakdown_pie_chart_card(self, box: str):
        latest_account_report: AccountChannel = self.okx_account_stream[-1]
        latest_account_data: AccountBalanceData = latest_account_report.data[0]
        # Pie Chart
        pies = []
        colors_copy = None
        COLORS = ['$blue', '$red', '$green', '$yellow', '$orange', '$pink', '$purple', '$cyan', '$gray']
        for account_balance_detail in latest_account_data.details:
            if not colors_copy:
                colors_copy = COLORS.copy()
            color = colors_copy.pop()
            fraction = float(account_balance_detail.eqUsd) / float(latest_account_data.totalEq)
            percentage_string = str(round(fraction * 100, 0)) + '%'
            pies.append(ui.pie(
                # label: str,
                # value: str,
                # fraction: float,
                # color: str,
                # aux_value: str | None = None
                label=account_balance_detail.ccy,
                value='',
                fraction=fraction,
                color=color,
                aux_value=f'({percentage_string})'
            ))

        return ui.wide_pie_stat_card(
            # box: str,
            # title: str,
            # pies: list[Pie],
            # commands: list[Command] | None = Non
            box=box,
            title='All Exchanges Account Breakdown',
            pies=pies
        )

    async def update_all_exchanges_account_breakdown_table_card(self):
        latest_account_report: AccountChannel = self.okx_account_stream[-1]
        latest_account_data: AccountBalanceData = latest_account_report.data[0]

        # TODO Use values from all exchanges, then generate the ui item for each exchange prior to ui.stat ...
        okx_total_equity = latest_account_data.totalEq
        bitget_total_equity = 0
        total_equity = float(okx_total_equity) + float(bitget_total_equity)
        account_breakdown_card: ui.stat_table_card = self.q.page[self.card_name + '_overview_accounts_table']
        items = []
        for account_balance_detail in latest_account_data.details:
            label = f'OKX:{account_balance_detail.ccy}'
            total_asset_value = round(float(account_balance_detail.eqUsd), 2)
            unused_value = round(float(account_balance_detail.availBal) * (
                    float(account_balance_detail.disEq) / float(account_balance_detail.eq)), 2)
            fraction_of_total_equity = float(account_balance_detail.eqUsd) / float(total_equity)
            percentage_string = str(round(fraction_of_total_equity * 100, 0)) + '%'
            update_time = datetime.fromtimestamp(int(account_balance_detail.uTime) / 1000, tz=None).strftime(
                '%Y-%m-%d %H:%M:%S')
            #
            values = [total_asset_value, unused_value, percentage_string, update_time]
            items.append(ui.stat_table_item(label=label, values=[str(value) for value in values]))
        account_breakdown_card.items = items
        account_breakdown_card.title = f'Live Account - {{exchange}}:websockets@account - ${round(total_equity, 2)}'
        await self.q.page.save()

    async def update_all_exchanges_live_positions_table_card(self):
        latest_positions_report: PositionsChannel = self.okx_positions_stream[-1]
        latest_positions_data: List[WSPosition] = latest_positions_report.data

        positions_table_card: ui.stat_table_card = self.q.page[self.card_name + '_overview_positions_table']
        items = []
        for position in latest_positions_data:
            values = []
            for i, (col_key, col_value) in enumerate(self.okx_position_column_mappings.items()):
                if i == 0:
                    label_value = f'OKX:{getattr(position, col_key)}'
                    continue
                pos_col = getattr(position, col_key)
                try:
                    expected_type = col_value['type']
                    if expected_type == 'float':
                        pos_col = round(float(pos_col), 2)
                    elif expected_type == 'int':
                        pos_col = int(pos_col)
                    elif expected_type == 'timestamp':
                        pos_col = datetime.fromtimestamp(int(pos_col) / 1000, tz=None).strftime(
                            '%Y-%m-%d %H:%M:%S')
                    else:
                        pos_col = str(pos_col)
                except ValueError:
                    pass
                value = str(pos_col)
                values.append(value)
            items.append(ui.stat_table_item(label=label_value, values=values))
        positions_table_card.items = items
        await self.q.page.save()

    async def add_cards(self):
        await self._update_stream()
        # await add_card(self.q, self.card_name + 'Accounts_PieChart',
        #                await self.get_all_exchanges_account_breakdown_pie_chart_card(box='first_context_1'))
        await add_card(self.q, self.card_name + '_overview_accounts_table',
                       await self.get_all_exchanges_account_breakdown_table_card(box=self.box))
        await add_card(self.q, self.card_name + '_overview_positions_table',
                       await self.get_all_exchanges_live_positions_table_card(box=self.box))
        await self.q.page.save()

    async def update_cards(self):
        await self._update_stream()
        await self.update_all_exchanges_account_breakdown_table_card()
        # await self.update_all_exchanges_live_positions_table_card()
        await self.q.page.save()
