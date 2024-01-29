import asyncio
import pprint
import time
from typing import List

from h2o_wave import Q, ui, on, data, run_on, AsyncSite  # noqa F401
from h2o_dashboard.util import add_card, remove_card, init_page_card_set
from pyokx.redis_structured_streams import get_stream_account_messages, get_stream_position_messages, \
    get_stream_all_messages

app = AsyncSite()


class Account_StreamWidget:

    def __init__(self, q: Q, card_name: str, count: int = 10):
        self.q = q
        self.count = count
        self.account_stream: List[Account] = []
        self.card_name = card_name

    async def _update_stream(self):
        self.account_stream = await get_stream_account_report(async_redis=self.q.client.async_redis, count=self.count)
        return self.account_stream

    async def _is_initialized(self):
        return bool(self.account_stream)

    def get_ui_total_equity_box_as_small_stat(self, box: str):
        last_account_stream_entry: Account = self.account_stream[-1]
        return ui.small_series_stat_card(
            box=box,
            title='Total Equity',
            value='=${{intl total_eq minimum_fraction_digits=2 maximum_fraction_digits=2}}',
            data=dict(u_time=last_account_stream_entry.u_time, total_eq=last_account_stream_entry.total_eq),
            plot_type='area',
            plot_value='total_eq',
            plot_color='$green',
            plot_data=data('u_time total_eq', -self.count,
                           rows=[[account.u_time, account.total_eq] for account in self.account_stream]),
            plot_zero_value=min([account.total_eq for account in self.account_stream]) * 0.9999,
            plot_curve='linear',
        )

    async def add_cards(self):
        await self._update_stream()

        COLORS = ['$blue', '$red', '$green', '$yellow', '$orange', '$pink', '$purple', '$cyan', '$gray']
        await add_card(self.q, self.card_name + '_total_equity',
                       self.get_ui_total_equity_box_as_small_stat(box='first_context_1'))
        last_account_stream_entry: Account = self.account_stream[-1]
        pies = []
        colors_copy = None
        for k, v in last_account_stream_entry.details.items():
            if not colors_copy:
                colors_copy = COLORS.copy()
            color = colors_copy.pop()
            fraction = v.eq_usd / last_account_stream_entry.total_eq
            percentage_string = str(round(fraction * 100, 2)) + '%'
            pies.append(ui.pie(
                # label: str,
                # value: str,
                # fraction: float,
                # color: str,
                # aux_value: str | None = None
                label=k,
                value=percentage_string,

                fraction=fraction,
                color=color,
                aux_value=f'${v.eq_usd} ({percentage_string})'
            ))
        await add_card(self.q, self.card_name + '_account_breakdown', ui.wide_pie_stat_card(
            # box: str,
            # title: str,
            # pies: list[Pie],
            # commands: list[Command] | None = Non
            box='first_context_1',
            title='Account Breakdown',
            pies=pies
        ))
        await self.q.page.save()

    async def update_cards(self):
        await self._update_stream()
        last_account_stream_entry: Account = self.account_stream[-1]

        '''Total Equity Card'''
        total_equity_card: ui.small_series_stat_card = self.q.page[self.card_name + '_total_equity']
        total_equity_card.plot_data[-1] = [last_account_stream_entry.u_time, last_account_stream_entry.total_eq]
        total_equity_card.plot_zero_value = min([account.total_eq for account in self.account_stream]) * 0.9999

        '''Account Breakdown Card'''
        account_breakdown_card: ui.wide_pie_stat_card = self.q.page[self.card_name + '_account_breakdown']
        details = {k: v.eq_usd for k, v in last_account_stream_entry.details.items()}
        for pie, (k, v) in zip(account_breakdown_card.pies, details.items()):
            fraction = v / last_account_stream_entry.total_eq
            percentage_string = str(round(fraction * 100, 2)) + '%'
            pie.label = k
            pie.value = percentage_string
            pie.fraction = fraction
            pie.aux_value = f'${round(v, 2)} ({percentage_string})'

        await self.q.page.save()


class Positions_StreamWidget:

    def __init__(self, q: Q, card_name: str, count: int = 10):
        self.q = q
        self.count = count
        self.positions_stream: List[Positions] = []
        self.card_name = card_name

    async def _update_stream(self):
        self.positions_stream: [Positions] = await get_stream_positions_report(async_redis=self.q.client.async_redis,
                                                                        count=self.count)
        print(f"{self.positions_stream[-1] = }")
        return self.positions_stream

    async def _is_initialized(self):
        return bool(self.positions_stream)

    def get_ui_positions_table(self, box: str):
        latest_positions_report: Positions = self.positions_stream[-1]
        positions = latest_positions_report.get_position_map().values()

        items = []
        for position in positions:
            position: Position = position
            label = str(position.position_id)
            values = []
            for pos_col in [position.inst_id, position.pos, position.upl,  position.avg_px,
                            position.lever, position.last, position.margin, position.p_time]:
                value = str(round(float(pos_col), 2) if isinstance(pos_col, float) else pos_col)
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
        await add_card(self.q, self.card_name + '_positions_table', self.get_ui_positions_table(box='first_context_1'))
        await self.q.page.save()

    async def update_cards(self):
        await self._update_stream()
        latest_positions_report: Positions = self.positions_stream[-1]
        positions = latest_positions_report.get_position_map().values()

        positions_table_card: ui.stat_table_card = self.q.page[self.card_name + '_positions_table']
        items = []
        for position in positions:
            position: Position = position
            label = str(position.position_id)
            values = []
            for pos_col in [position.inst_id, position.pos, position.upl, position.avg_px,
                            position.lever, position.last, position.margin, position.p_time]:
                value = str(round(float(pos_col), 2) if isinstance(pos_col, float) else pos_col)
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
    positions_stream_widget = Positions_StreamWidget(q=q, card_name='OKXDEBUG_Positions_Stream', count=2)

    '''Init Page Cards'''
    await add_page_cards(q, account_stream_widget, positions_stream_widget)
    await q.page.save()
    # return  # todo remove this return after plottings

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
    account_stream = await get_stream_account_messages(async_redis=q.client.async_redis, count=2)
    print(f'{len(account_stream) = }')
    positions_stream = await get_stream_position_messages(async_redis=q.client.async_redis, count=2)
    print(f'{len(positions_stream) = }')

    # await add_card(q, 'OKXDEBUG_Account_Stream', ui.form_card(box='first_context_1', items=[
    #     ui.text_xl('Account Stream'),
    #     ui.text_xl(pprint.pformat(q.user.okx_account_stream))
    # ]))

    # await add_card(q, 'OKXDEBUG_Positions_Table', ui.form_card(box='first_context_1', items=[
    #     ui.text_xl('Positions'),
    #     ui.text_xl(pprint.pformat(q.user.okx_positions))
    # ]))
    #
    # await add_card(q, 'OKXDEBUG_Balances_Table', ui.form_card(box='first_context_1', items=[
    #     ui.text_xl('Balances and Positions'),
    #     ui.text_xl(pprint.pformat(q.user.okx_balances_and_positions))
    # ]))
    #
    # await add_card(q, 'OKXDEBUG_Orders_Table', ui.form_card(box='first_context_1', items=[
    #     ui.text_xl('Orders'),
    #     ui.text_xl(pprint.pformat(q.user.okx_orders))
    # ]))
    #
    # await add_card(q, 'OKXDEBUG_Account_Table', ui.form_card(box='grid_1', items=[
    #     ui.text_xl('Account'),
    #     ui.text_xl(pprint.pformat(q.user.okx_account))
    # ]))
    #
    # await add_card(q, 'OKXDEBUG_Tickers_Table', ui.form_card(box='grid_2', items=[
    #     ui.text_xl('Tickers'),
    #     ui.text_xl(pprint.pformat(q.user.okx_tickers))
    # ]))
    #
    # await add_card(q, 'OKXDEBUG_BTCUSDT_Index_Ticker_Table', ui.form_card(box='grid_3', items=[
    #     ui.text_xl('BTC-USDT Index Ticker'),
    #     ui.text_xl(pprint.pformat(q.user.okx_index_ticker))
    # ]))



    # '''Account Stream Metrics'''
    # if await account_stream_widget._is_initialized():
    #     print("Updating Account Stream Metrics card")
    #     await account_stream_widget.update_cards()
    # else:
    #     print("Adding Account Stream Metrics card")
    #     await account_stream_widget.add_cards()

    '''Positions Stream Metrics'''
    # if await positions_stream_widget._is_initialized():
    #     print("Updating Positions Stream Metrics card")
    #     await positions_stream_widget.update_cards()
    # else:
    #     print("Adding Positions Stream Metrics card")
    #     await positions_stream_widget.add_cards()



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
