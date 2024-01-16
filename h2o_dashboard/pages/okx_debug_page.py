from typing import List

from h2o_wave import Q, ui, on, data, run_on, AsyncSite  # noqa F401

from h2o_dashboard.util import clear_cards, add_card
from pyokx.data_structures import AccountBalanceData, AccountBalanceDetails

app = AsyncSite()


async def okx_debug_page(q: Q):
    # Clear all cards except the ones needed for this page
    await q.run(clear_cards, q, ignore=['Application_Sidebar',
                                        'OKXDEBUG_Header',
                                        'OKXDEBUG_Positions_Table',
                                        'OKXDEBUG_Balances_Table',])

    '''Static Cards'''
    # Add header
    add_card(q, 'OKXDEBUG_Header', ui.header_card(box='header', title='OKX Debug Page', subtitle='DevPage',
                                                  # Color
                                                  color='transparent',
                                                  icon='DeveloperTools',
                                                  icon_color=None,
                                                  ))

    from pyokx.ws_data_structures import ws_posData_element
    positions: List[ws_posData_element] = q.user.okx_positions

    positions_cell_names = ws_posData_element.__annotations__.keys()

    sort_list = ['posId','instId', 'pos', 'avgPx',  'uTime','posSide','instType']
    positions_cell_names = sort_list + list(
        positions_cell_names - sort_list)
    if '_primary_key_field' in positions_cell_names:
        positions_cell_names.remove('_primary_key_field')

    positions_rows = []
    for position in positions:
        name = positions_cell_names[0]
        cells = [position[cell] for cell in positions_cell_names]
        positions_rows.append(ui.table_row(name=name, cells=cells))

    positions_columns = []
    for position_cell_name in positions_cell_names:
        # (name: str,
        # label: str,
        # min_width: str | None = None,
        # max_width: str | None = None,
        # sortable: bool | None = None,
        # searchable: bool | None = None,
        # filterable: bool | None = None,
        # link: bool | None = None,
        # data_type: str | None = None,
        # cell_type: TableCellType | None = None,
        # cell_overflow: str | None = None,
        # filters: list[str] | None = None,
        # align: str | None = None)
        column = ui.table_column(name=position_cell_name, label=position_cell_name, filterable=True)
        positions_columns.append(column)
    add_card(q, 'OKXDEBUG_Positions_Table',
             ui.form_card(box='grid_1', items=[
                 ui.text_xl('Positions'),
                 ui.table(
                     name='OKXDEBUG_Positions_Table_card',
                     columns=positions_columns,
                     rows=positions_rows,
                     # groupable=True,
                     downloadable=True,
                     resettable=False,
                 )
             ])
             )

    balances: List[AccountBalanceData] = q.user.okx_balances
    balances_details: List[AccountBalanceDetails] = balances[0].details

    # todo left here
    balances_cell_names = AccountBalanceDetails.__annotations__.keys()

    sort_list = ['ccy', 'eqUsd', 'availBal', 'availEq', 'disEq', 'uTime']
    balances_cell_names = sort_list + list(balances_cell_names - sort_list)
    if '_primary_key_field' in balances_cell_names:
        balances_cell_names = balances_cell_names.remove('_primary_key_field')

    balances_rows = []
    for balance_detail in balances_details:
        name = balances_cell_names[0]
        balance_details: AccountBalanceDetails = balance_detail
        cells = [getattr(balance_details, cell) for cell in balances_cell_names]
        print(f'{cells = }')
        balances_rows.append(ui.table_row(name=name, cells=cells))

    balances_columns = []
    for balance_cell_name in balances_cell_names:
        # (name: str,
        # label: str,
        # min_width: str | None = None,
        # max_width: str | None = None,
        # sortable: bool | None = None,
        # searchable: bool | None = None,
        # filterable: bool | None = None,
        # link: bool | None = None,
        # data_type: str | None = None,
        # cell_type: TableCellType | None = None,
        # cell_overflow: str | None = None,
        # filters: list[str] | None = None,
        # align: str | None = None)

        column = ui.table_column(name=balance_cell_name, label=balance_cell_name,
                                 filterable=True, searchable=True)
        balances_columns.append(column)
    add_card(q, 'OKXDEBUG_Balances_Table',
             ui.form_card(box='grid_2', items=[
                 ui.text_xl('Balances'),
                 ui.table(
                     name='OKXDEBUG_Balances_card',
                     columns=balances_columns,
                     rows=balances_rows,
                     # groupable=True,
                     downloadable=True,
                     resettable=False,

                 )
             ])
             )
