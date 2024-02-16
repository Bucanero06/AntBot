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
from h2o_dashboard.pages.okx_dashbaord_page.okx_antbot_okx_premium_indicator_handler import OKX_Premium_Indicator_Handler_Widget
from h2o_dashboard.pages.okx_dashbaord_page.okx_antbot_okx_signal_handler import OKX_Signal_Handler_Widget
from h2o_dashboard.pages.okx_streams import OKX_Account_StreamWidget, OKX_Positions_StreamWidget, \
    OKX_Fill_Report_StreamWidget

app = AsyncSite()


async def okx_dashboard_page(q: Q):
    '''Header'''
    await add_card(q, 'OKXDEBUG_Header', ui.header_card(box='header', title='OKX Dashboard', subtitle='DevPage',
                                                        # Color
                                                        color='transparent',
                                                        icon='DeveloperTools',
                                                        icon_color=None,
                                                        ))

    # Add the the
    '''Init Widgets'''
    account_stream_widget = OKX_Account_StreamWidget(q=q, card_name='OKXDEBUG_Account_Stream', box='grid_1', count=900)
    positions_stream_widget = OKX_Positions_StreamWidget(q=q, card_name='OKXDEBUG_Positions_Stream', box='grid_2',
                                                         count=1)
    fill_report_stream_widget = OKX_Fill_Report_StreamWidget(q=q, card_name='OKXDEBUG_Fill_Report_Stream', box='grid_2',
                                                             count=1)

    okx_signal_handler_widget = OKX_Signal_Handler_Widget(q=q, card_name='OKXDEBUG_Manual_Controls', box='grid_3')
    okx_premium_indicator_handler_widget = OKX_Premium_Indicator_Handler_Widget(q=q,
                                                                                card_name='OKXDEBUG_Premium_Manual_Controls',
                                                                                box='grid_4')

    '''Init RealTime Page Cards'''
    await add_page_cards(q, account_stream_widget, positions_stream_widget, fill_report_stream_widget,
                         okx_signal_handler_widget,
                         okx_premium_indicator_handler_widget)
    await q.page.save()

    try:
        while True:
            if not q.client.okx_dashboard_page_running_event.is_set():
                print("Breaking OKX Dashboard Page Loop")
                break
            await asyncio.sleep(1)
            await add_page_cards(q, account_stream_widget, positions_stream_widget, fill_report_stream_widget,
                                 okx_signal_handler_widget,
                                 okx_premium_indicator_handler_widget)
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
                         oks_signal_handler_widget: OKX_Signal_Handler_Widget,
okx_premium_indicator_handler_widget: OKX_Premium_Indicator_Handler_Widget
                         ):
    # '''Account Stream Metrics'''
    # if await account_stream_widget._is_initialized():
    #     print("Updating Account Stream Metrics card")
    #     await account_stream_widget.update_cards()
    # else:
    #     print("Adding Account Stream Metrics card")
    #     await account_stream_widget.add_cards()
    # #
    # '''Positions Stream Metrics'''
    # if await positions_stream_widget._is_initialized():
    #     print("Updating Positions Stream Metrics card")
    #     await positions_stream_widget.update_cards()
    # else:
    #     print("Adding Positions Stream Metrics card")
    #     await positions_stream_widget.add_cards()
    #
    # '''Fills Report Stream Metrics'''
    # if await fill_report_stream_widget._is_initialized():
    #     print("Updating Fills Report Stream Metrics card")
    #     await fill_report_stream_widget.update_cards()
    # else:
    #     print("Adding Fills Report Stream Metrics card")
    #     await fill_report_stream_widget.add_cards()

    # if await oks_signal_handler_widget._is_initialized():
    #     print("Updating Manual Controls card")
    #
    #     await oks_signal_handler_widget.update_cards()
    # else:
    #     print("Adding Manual Controls card")
    #     await oks_signal_handler_widget.add_cards()

    if await okx_premium_indicator_handler_widget._is_initialized():
        print("Updating Premium Manual Controls card")

        await okx_premium_indicator_handler_widget.update_cards()
    else:
        print("Adding Premium Manual Controls card")
        await okx_premium_indicator_handler_widget.add_cards()
    await q.page.save()
