from datetime import datetime
from typing import List

from h2o_wave import Q, ui, on, data, run_on, AsyncSite, pack  # noqa F401

from h2o_dashboard.util import add_card, convert_to_col_type
from pyokx.data_structures import AccountBalanceData
from pyokx.redis_structured_streams import get_stream_okx_account_messages, get_stream_okx_position_messages
from pyokx.ws_data_structures import AccountChannel, PositionsChannel, WSPosition


class Overview_StreamWidget:  # TODO: Will connect to the account streams for all exchanges, rn it's just okx

    def __init__(self, q: Q, card_name: str, box: str):
        self.q = q
        self.count = 1  # Enforce only the latest data entry since it contains all latest data
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
                    pos_col = convert_to_col_type(pos_col, expected_type)
                except ValueError:
                    print(f"Error converting {col_key} to {expected_type}")
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
        await self.update_all_exchanges_live_positions_table_card()
        await self.q.page.save()
