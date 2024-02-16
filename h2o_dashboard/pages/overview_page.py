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

from h2o_wave import main, Q, app, ui, on, run_on, data  # noqa F401

from h2o_dashboard.util import add_card
from h2o_dashboard.pages.okx_streams import Overview_StreamWidget


async def add_tradingview_advanced_chart(q: Q, card_name: str, box: str):
    await add_card(q, card_name, ui.form_card(box=box, items=[
        ui.frame(content="""<!-- TradingView Widget BEGIN -->
            <div class="tradingview-widget-container" style="height:100%;width:100%">
              <div class="tradingview-widget-container__widget" style="height:calc(100% - 32px);width:100%"></div>
              <div class="tradingview-widget-copyright"><a href="https://www.tradingview.com/" rel="noopener nofollow" target="_blank"><span class="blue-text">Track all markets on TradingView</span></a></div>
              <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js" async>
              {
              "autosize": true,
              "symbol": "OKX:BTCUSDT.P",
              "interval": "D",
              "timezone": "Etc/UTC",
              "theme": "light",
              "style": "1",
              "locale": "en",
              "enable_publishing": false,
              "withdateranges": true,
              "hide_side_toolbar": false,
              "allow_symbol_change": true,
              "details": true,
              "hotlist": true,
              "theme": "dark",
              "calendar": true,
              "show_popup_button": true,
              "popup_width": "1000",
              "popup_height": "650",
              "support_host": "https://www.tradingview.com"
            }
              </script>
            </div>
            <!-- TradingView Widget END -->""", height="500px", width="100%")
    ]))


# Usage


async def overview_page(q: Q):
    print("Loading Overview Page")
    '''Header'''
    await add_card(q, 'Overview_Page_Header',
                   ui.header_card(box='header', title='Overview Home', subtitle='Welcome to the AntBot Dashboard',
                                  # Color
                                  color='transparent',
                                  icon='Home',
                                  icon_color=None,
                                  ))



    await add_tradingview_advanced_chart(q, card_name='Overview_Page_TradingView_Advanced_Chart', box='grid_1')

    # await add_card(q, 'Overview_Page_TradingView_Info', ui.form_card(box='grid_1', items=[
    #     ui.frame(height="100px", width="300px",
    #              content=str(get_info_widget("AAPL"))
    #      )
    # ]))

    '''Init Widgets'''
    overview_widget = Overview_StreamWidget(q=q, card_name='grid_2', box='grid_2', count=2)

    '''Init RealTime Page Cards'''
    await overview_widget.add_cards()
    if not isinstance(q.client.overview_tv_card_symbol_name, str):
        q.client.overview_tv_card_symbol_name = "OKX:BTCUSDT.P"

    await q.page.save()

    try:
        while True:
            if not q.client.overview_page_running_event.is_set():
                print("Breaking Overview Page Loop")
                break
            await asyncio.sleep(1)

            '''CARD UPDATES'''
            if await overview_widget._is_initialized():
                print("Updating Overview card")
                await overview_widget.update_cards()
            else:
                print("Adding Overview card")
                await overview_widget.add_cards()
            await q.page.save()
    except asyncio.CancelledError:
        print("Cancelled")
        pass
    finally:
        print("Finally")
        q.client.overview_page_running_event.clear()
        await q.page.save()
