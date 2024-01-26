import asyncio
import pprint
from typing import List

from h2o_wave import Q, ui, on, data, run_on, AsyncSite  # noqa F401

from h2o_dashboard.redis_refresh import refresh_redis
from h2o_dashboard.util import clear_cards, add_card, remove_card
from pyokx.okx_market_maker.position_management_service.model.Account import Account
from pyokx.redis_handling import get_stream_account

app = AsyncSite()


async def okx_debug_page(q: Q):


    account_stream_widget = AccountWidget(q=q, card_name='OKXDEBUG_Account_Stream', count=1000)
    await asyncio.gather(add_page_cards(q, account_stream_widget), refresh_redis(q))

    list_of_cards_on_this_page = ["OKXDEBUG_Header",
                                    "OKXDEBUG_Account_Stream",
                                    "OKXDEBUG_Account_Stream_total_equity",
                                    "OKXDEBUG_Positions_Table",
                                    "OKXDEBUG_Balances_Table",
                                    "OKXDEBUG_Orders_Table",
                                    "OKXDEBUG_Account_Table",
                                    "OKXDEBUG_Tickers_Table",
                                    "OKXDEBUG_BTCUSDT_Index_Ticker_Table",
                                    ]

    q.client.okx_debug_page_running_event.set()
    while True:
        if not q.client.okx_debug_page_running_event.is_set():
            print("Breaking")
            # list_of_cards_on_this_page = list(q.client.cards.keys())
            # ignore the Application_Sidebar
            # list_of_cards_on_this_page.remove("Application_Sidebar")

            for card_name in list_of_cards_on_this_page:
                await remove_card(q, card_name)
            await q.page.save()
            break

        await asyncio.sleep(1)
        await refresh_redis(q)
        await asyncio.gather(add_page_cards(q, account_stream_widget), refresh_redis(q))
        await q.page.save()


    await q.page.save()

class AccountWidget:

    def __init__(self, q: Q, card_name: str, count: int = 10):
        super().__init__()
        self.q = q
        self.count = count
        self.account_stream: List[Account] = []
        self.card_name = card_name

    async def _update_account_stream(self):
        self.account_stream = await get_stream_account(async_redis=self.q.client.async_redis, count=self.count)
        return self.account_stream

    async def _as_table(self):
        return ui.form_card(box='grid_4',
                            items=[
                                ui.text_xl('Account Stream'),
                                ui.table(
                                    name='OKXDEBUG_Account_Stream_Table_card',
                                    # groupable=True,
                                    downloadable=True,
                                    resettable=False,
                                    columns=[
                                        ui.table_column(name='u_time', label='u_time', filterable=True,
                                                        searchable=True),
                                        ui.table_column(name='total_eq', label='total_eq', filterable=True,
                                                        searchable=True),
                                        ui.table_column(name='details', label='details', filterable=True,
                                                        searchable=True,
                                                        cell_overflow='wrap'),
                                    ],
                                    rows=[
                                        ui.table_row(name=str(account.u_time),
                                                     cells=[str(account.u_time), str(account.total_eq),
                                                            str(account.details)])
                                        for account in self.account_stream
                                    ]
                                )
                            ]
                            )

    async def _is_present(self) -> bool:
        return self.card_name in self.q.client.cards

    async def _is_populated(self) -> bool:
        return await self._is_present() and self.q.page[
            self.card_name].OKXDEBUG_Account_Stream_Table_card.rows

    def get_ui_total_equity_box_as_small_stat(self, box: str):
        return ui.small_series_stat_card(
            box=box,
            title='Total Equity',
            value='=${{intl total_eq minimum_fraction_digits=2 maximum_fraction_digits=2}}',
            data=dict(u_time=self.account_stream[0].u_time, total_eq=self.account_stream[0].total_eq),
            plot_type='area',
            plot_value='total_eq',
            plot_color='$green',
            plot_data=data('u_time total_eq', self.count,
                           rows=[[account.u_time, account.total_eq] for account in self.account_stream]),
            plot_zero_value=min([account.total_eq for account in self.account_stream]) * 0.9999,
            plot_curve='linear',
        )

    async def add_cards(self):
        await self._update_account_stream()
        await add_card(self.q, self.card_name + '_total_equity',
                       self.get_ui_total_equity_box_as_small_stat(box='first_context_1'))
        await add_card(self.q, self.card_name, ui.form_card(box='first_context_1', items=[
            ui.text_xl('Account Stream'),
            ui.stats(items=[
                ui.stat(
                    # label: str,
                #          value: str | None = None,
                #          caption: str | None = None,
                #          icon: str | None = None,
                #          icon_color: str | None = None) -> Sta
                label='Total Equity',
                value=str(self.account_stream[0].total_eq),
                caption='USD',
                icon='Money',
                icon_color='$green',
                ),
                ui.stat(
                    label='u_time',
                    value=str(self.account_stream[0].u_time),
                    caption='UNIX Timestamp',
                    icon='Clock',
                    icon_color='$red',
                ),
                ui.stat(
                    label='details',
                    # Get only the eq_usd of each detail in details dict
                    value=str({k: v.eq_usd for k, v in self.account_stream[0].details.items()}),
                    caption='Details',
                    icon='Info',
                    icon_color='$blue',
                ),
            ])
        ]))

    async def update_cards(self):
        await self.add_cards()

        # await self._update_account_stream()

        # card_info = self.card_name_and_type_set.get(card_name, None)
        # if not card_info:
        #     raise Exception(f"Card {card_name} not found in card_name_and_type_set")
        # elif card_info['as_type'] == 'table':
        #     await add_card(self.q, card_name, await self._as_table())
        # elif card_info['as_type'] == 'small_stat':
        #     await add_card(self.q, card_name, await self._as_small_stat())


async def add_page_cards(q: Q, account_stream_widget: AccountWidget):

    '''Header'''
    await add_card(q, 'OKXDEBUG_Header', ui.header_card(box='header', title='OKX Debug Page', subtitle='DevPage',
                                                        # Color
                                                        color='transparent',
                                                        icon='DeveloperTools',
                                                        icon_color=None,
                                                        ))

    '''Account Stream Metrics'''
    if await account_stream_widget._is_populated():
        print("Updating card")
        await account_stream_widget.update_cards()
    else:
        print("Adding card")
        await account_stream_widget.add_cards()

    await add_card(q, 'OKXDEBUG_Positions_Table', ui.form_card(box='first_context_2', items=[
        ui.text_xl('Positions'),
        ui.text_xl(pprint.pformat(q.user.okx_positions))
    ]))

    await add_card(q, 'OKXDEBUG_Balances_Table', ui.form_card(box='first_context_1', items=[
        ui.text_xl('Balances and Positions'),
        ui.text_xl(pprint.pformat(q.user.okx_balances_and_positions))
    ]))

    await add_card(q, 'OKXDEBUG_Orders_Table', ui.form_card(box='first_context_1', items=[
        ui.text_xl('Orders'),
        ui.text_xl(pprint.pformat(q.user.okx_orders))
    ]))

    await add_card(q, 'OKXDEBUG_Account_Table', ui.form_card(box='grid_1', items=[
        ui.text_xl('Account'),
        ui.text_xl(pprint.pformat(q.user.okx_account))
    ]))

    await add_card(q, 'OKXDEBUG_Tickers_Table', ui.form_card(box='grid_2', items=[
        ui.text_xl('Tickers'),
        ui.text_xl(pprint.pformat(q.user.okx_tickers))
    ]))

    await add_card(q, 'OKXDEBUG_BTCUSDT_Index_Ticker_Table', ui.form_card(box='grid_3', items=[
        ui.text_xl('BTC-USDT Index Ticker'),
        ui.text_xl(pprint.pformat(q.user.okx_index_ticker))
    ]))
