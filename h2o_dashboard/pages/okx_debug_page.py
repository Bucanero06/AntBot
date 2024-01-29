import asyncio
from typing import List

from h2o_wave import Q, ui, on, data, run_on, AsyncSite  # noqa F401

from h2o_dashboard.util import add_card, remove_card, init_page_card_set
from pyokx.redis_structured_streams import get_stream_account_messages, get_stream_position_messages, \
    get_stream_all_messages, get_stream_order_messages
from pyokx.ws_data_structures import AccountChannel, PositionsChannel, WSPosition

app = AsyncSite()


class Account_StreamWidget:

    def __init__(self, q: Q, card_name: str, count: int = 10):
        self.q = q
        self.count = count
        self.account_stream: List[AccountChannel] = []
        self.card_name = card_name

    async def _update_stream(self):
        self.account_stream: List[AccountChannel] = await get_stream_account_messages(
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

    async def add_cards(self):
        await self._update_stream()

        COLORS = ['$blue', '$red', '$green', '$yellow', '$orange', '$pink', '$purple', '$cyan', '$gray']
        await add_card(self.q, self.card_name + '_total_equity',
                       self.get_ui_total_equity_box_as_small_stat(box='grid_1'))
        last_account_stream_entry: AccountChannel = self.account_stream[-1]
        last_account_stream_data = last_account_stream_entry.data[0]
        pies = []
        colors_copy = None

        for account_balance_detail in last_account_stream_data.details:
            if not colors_copy:
                colors_copy = COLORS.copy()
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
        await add_card(self.q, self.card_name + '_account_breakdown', ui.wide_pie_stat_card(
            # box: str,
            # title: str,
            # pies: list[Pie],
            # commands: list[Command] | None = Non
            box='grid_1',
            title='Account Breakdown',
            pies=pies
        ))
        await self.q.page.save()

    async def update_cards(self):
        await self._update_stream()
        last_account_stream_entry: AccountChannel = self.account_stream[-1]
        last_account_stream_data = last_account_stream_entry.data[0]
        '''Total Equity Card'''
        total_equity_card: ui.small_series_stat_card = self.q.page[self.card_name + '_total_equity']
        total_equity_card.plot_data[-1] = [last_account_stream_data.uTime, last_account_stream_data.totalEq]
        total_equity_card.plot_zero_value = min([float(account.data[0].totalEq) for account in self.account_stream]) * 0.9999

        '''Account Breakdown Card'''
        account_breakdown_card: ui.wide_pie_stat_card = self.q.page[self.card_name + '_account_breakdown']
        details = {account_balance_detail.ccy: account_balance_detail.eqUsd for account_balance_detail in last_account_stream_data.details}
        for pie, (k, v) in zip(account_breakdown_card.pies, details.items()):
            fraction = float(v) / float(last_account_stream_data.totalEq)
            percentage_string = str(round(fraction * 100, 2)) + '%'
            pie.label = k
            pie.value = percentage_string
            pie.fraction = fraction
            pie.aux_value = f'${round(float(v), 2)} ({percentage_string})'

        await self.q.page.save()


class Positions_StreamWidget:

    def __init__(self, q: Q, card_name: str, count: int = 10):
        self.q = q
        self.count = count
        self.positions_stream: List[PositionsChannel] = []
        self.card_name = card_name

    async def _update_stream(self):
        self.positions_stream: List[PositionsChannel] = await get_stream_position_messages(
            async_redis=self.q.client.async_redis, count=self.count)
        return self.positions_stream

    async def _is_initialized(self):
        return len(self.positions_stream) > 0

    async def get_ui_positions_table(self, box: str):
        if await self._is_initialized():
            latest_positions_report: PositionsChannel = self.positions_stream[-1]
            latest_positions_data = latest_positions_report.data
        else:
            latest_positions_data = []

        items = []
        for position in latest_positions_data:
            position: WSPosition = position
            label = str(position.posId)
            values = []
            for pos_col in [position.instId, position.pos, position.upl, position.avgPx,
                            position.lever, position.last, position.margin, position.pTime]:
                # see if string is float
                try:
                    pos_col = str(round(float(pos_col), 2))
                except ValueError:
                    pass
                value = str(pos_col)
                values.append(value)
            items.append(ui.stat_table_item(label=label, values=values))
        return ui.stat_table_card(
            box=box,
            title='Positions',
            columns=['Position ID', 'Instrument ID', 'Position', 'UPL', 'Average Price', 'Leverage',
                     'Last', 'Margin', 'Time'],
            items=items
        )

    async def add_cards(self):
        await self._update_stream()
        await add_card(self.q, self.card_name + '_positions_table',
                       await self.get_ui_positions_table(box='grid_2'))
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
            label = str(position.posId)
            values = []
            for pos_col in [position.instId, position.pos, position.upl, position.avgPx,
                            position.lever, position.last, position.margin, position.pTime]:
                # see if string is float
                try:
                    pos_col = str(round(float(pos_col), 2))
                except ValueError:
                    pass
                value = str(pos_col)
                values.append(value)
            items.append(ui.stat_table_item(label=label, values=values))
        positions_table_card.items = items
        await self.q.page.save()



async def okx_debug_page(q: Q):
    '''Define the page space'''
    await init_page_card_set(q, 'okx_debug_page')
    list_of_cards_on_this_page = ["OKXDEBUG_Header",
                                  #
                                  "OKXDEBUG_Account_Stream",
                                  "OKXDEBUG_Account_Stream_account_breakdown",
                                  "OKXDEBUG_Account_Stream_total_equity",
                                  #
                                  "OKXDEBUG_Positions_Stream",
                                  "OKXDEBUG_Positions_Stream_positions_table",
                                  #

                                  ]  # TODO: Make this a list of card names

    '''Header'''
    await add_card(q, 'OKXDEBUG_Header', ui.header_card(box='header', title='OKX Debug Page', subtitle='DevPage',
                                                        # Color
                                                        color='transparent',
                                                        icon='DeveloperTools',
                                                        icon_color=None,
                                                        ))
    '''Init Widgets'''
    account_stream_widget = Account_StreamWidget(q=q, card_name='OKXDEBUG_Account_Stream', count=100)
    positions_stream_widget = Positions_StreamWidget(q=q, card_name='OKXDEBUG_Positions_Stream', count=1)


    '''Init Page Cards'''
    await add_page_cards(q, account_stream_widget, positions_stream_widget)
    await q.page.save()

    q.client.okx_debug_page_running_event.set()
    try:
        while True:
            if not q.client.okx_debug_page_running_event.is_set():
                print("Breaking")
                # list_of_cards_on_this_page = list(q.client.cards)
                # # ignore the Application_Sidebar
                # list_of_cards_on_this_page.remove("Application_Sidebar")

                for card_name in list_of_cards_on_this_page:
                    await remove_card(q, card_name)
                await q.page.save()
                break
            await asyncio.sleep(1)
            await add_page_cards(q, account_stream_widget, positions_stream_widget)
            await q.page.save()
    except asyncio.CancelledError:
        print("Cancelled")
        pass
    finally:
        print("Finally")
        q.client.okx_debug_page_running_event.clear()
        await q.page.save()


async def add_page_cards(q: Q, account_stream_widget: Account_StreamWidget,
                         positions_stream_widget: Positions_StreamWidget):
    all_messages = await get_stream_all_messages(async_redis=q.client.async_redis, count=2)
    print(f'{len(all_messages) = }')
    orders_stream = await get_stream_order_messages(async_redis=q.client.async_redis, count=2)
    print(f'{len(orders_stream) = }')

    '''Account Stream Metrics'''
    # TODO Will likely replace this with BalanceAndPositionsChannelChannel for more up to date data
    if await account_stream_widget._is_initialized():
        print("Updating Account Stream Metrics card")
        await account_stream_widget.update_cards()
    else:
        print("Adding Account Stream Metrics card")
        await account_stream_widget.add_cards()

    '''Positions Stream Metrics'''
    # TODO Will likely replace this with BalanceAndPositionsChannelChannel for more up to date data
    if await positions_stream_widget._is_initialized():
        print("Updating Positions Stream Metrics card")
        await positions_stream_widget.update_cards()
    else:
        print("Adding Positions Stream Metrics card")
        await positions_stream_widget.add_cards()

# signal_response = okx_signal_handler(
#                 red_button=True,
#             )
# signal_response = okx_signal_handler(
#     instID="BTC-USDT-240628",
#     order_size=1,
#     leverage=5,
#     order_side="BUY",
#     order_type="POST_ONLY",
#     max_orderbook_limit_price_offset=0.1,
#     flip_position_if_opposite_side=True,
#     clear_prior_to_new_order=False,
#     red_button=False,
#     # order_usd_amount=100,
#     stop_loss_price_offset=None,
#     tp_price_offset=None,
#     trailing_stop_activation_percentage=None,
#     trailing_stop_callback_ratio=None,
#     stop_loss_trigger_percentage=None,
#     take_profit_trigger_percentage=None,
#     tp_trigger_price_type=None,
#     sl_trigger_price_type=None,
# )
# print(f"{signal_response = }")
