from typing import List

from h2o_wave import Q, ui, on, data, run_on, AsyncSite, pack  # noqa F401

from h2o_dashboard.util import add_card
from pyokx.redis_structured_streams import get_stream_okx_account_messages
from pyokx.ws_data_structures import AccountChannel


class OKX_Account_StreamWidget:

    def __init__(self, q: Q, card_name: str, box: str, history_count: int = 999):
        self.q = q
        self.history_count = history_count
        self.account_stream: List[AccountChannel] = []
        self.card_name = card_name
        self.box = box
        self.colors = ['$blue', '$red', '$green', '$yellow', '$orange', '$pink', '$purple', '$cyan', '$gray']

    async def _update_stream(self):
        self.account_stream: List[AccountChannel] = await get_stream_okx_account_messages(
            async_redis=self.q.client.async_redis, count=self.history_count)
        return self.account_stream

    async def _is_initialized(self):
        return bool(self.account_stream)

    def get_ui_total_equity_box_as_small_stat(self, box: str):
        last_account_stream_entry: AccountChannel = self.account_stream[-1]
        last_account_stream_data = last_account_stream_entry.data[0]


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
            plot_data=data('u_time total_eq', -self.history_count,
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
                # value=percentage_string,
                value='',
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
            # pie.value = percentage_string
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
