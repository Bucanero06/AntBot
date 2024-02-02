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
import asyncio

from h2o_wave import Q, ui, on, data, run_on, AsyncSite  # noqa F401

from h2o_dashboard.util import add_card
from h2o_dashboard.widgets.okx_streams import OKX_Account_StreamWidget, OKX_Positions_StreamWidget, \
    OKX_Fill_Report_StreamWidget, OKX_Manual_ControlsWidget

app = AsyncSite()


async def okx_dashboard_page(q: Q):
    ''''''
    '''Header'''
    await add_card(q, 'OKXDEBUG_Header', ui.header_card(box='header', title='OKX Dashboard', subtitle='DevPage',
                                                        # Color
                                                        color='transparent',
                                                        icon='DeveloperTools',
                                                        icon_color=None,
                                                        ))

    # await add_tradingview_advanced_chart(q, card_name='OKXDEBUG_TradingView_Advanced_Chart', box='grid_1')

    '''Init Widgets'''
    account_stream_widget = OKX_Account_StreamWidget(q=q, card_name='OKXDEBUG_Account_Stream', box='grid_2', count=900)
    positions_stream_widget = OKX_Positions_StreamWidget(q=q, card_name='OKXDEBUG_Positions_Stream', box='grid_3',
                                                         count=1)
    fill_report_stream_widget = OKX_Fill_Report_StreamWidget(q=q, card_name='OKXDEBUG_Fill_Report_Stream', box='grid_4',
                                                             count=1)
    manual_controls_widget = OKX_Manual_ControlsWidget(q=q, card_name='OKXDEBUG_Manual_Controls', box='mvp_bot_manual_controls_1')

    '''Init RealTime Page Cards'''
    await add_page_cards(q, account_stream_widget, positions_stream_widget, fill_report_stream_widget,
                         manual_controls_widget)
    await q.page.save()

    # q.client.okx_dashboard_page_running_event.set()
    try:
        while True:
            if not q.client.okx_dashboard_page_running_event.is_set():
                print("Breaking OKX Dashboard Page Loop")
                break
            await asyncio.sleep(1)
            await add_page_cards(q, account_stream_widget, positions_stream_widget, fill_report_stream_widget,
                                 manual_controls_widget)
            await q.page.save()
    except asyncio.CancelledError:
        print("Cancelled")
        pass
    finally:
        print("Finally")
        q.client.okx_dashboard_page_running_event.clear()
        await q.page.save()


async def add_page_cards(q: Q, account_stream_widget: OKX_Account_StreamWidget,
                         positions_stream_widget: OKX_Positions_StreamWidget,
                         fill_report_stream_widget: OKX_Fill_Report_StreamWidget,
                         manual_controls_widget: OKX_Manual_ControlsWidget):
    # '''Account Stream Metrics'''
    if await account_stream_widget._is_initialized():
        print("Updating Account Stream Metrics card")
        await account_stream_widget.update_cards()
    else:
        print("Adding Account Stream Metrics card")
        await account_stream_widget.add_cards()

    '''Positions Stream Metrics'''
    if await positions_stream_widget._is_initialized():
        print("Updating Positions Stream Metrics card")
        await positions_stream_widget.update_cards()
    else:
        print("Adding Positions Stream Metrics card")
        await positions_stream_widget.add_cards()

    if await fill_report_stream_widget._is_initialized():
        print("Updating Fills Report Stream Metrics card")
        await fill_report_stream_widget.update_cards()
    else:
        print("Adding Fills Report Stream Metrics card")
        await fill_report_stream_widget.add_cards()

    if await manual_controls_widget._is_initialized():
        print("Updating Manual Controls card")

        await manual_controls_widget.update_cards()
    else:
        print("Adding Manual Controls card")
        await manual_controls_widget.add_cards()
    await q.page.save()

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
