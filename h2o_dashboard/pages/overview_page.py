
import asyncio

import requests
from h2o_wave import main, Q, app, ui, on, run_on, data  # noqa F401

from h2o_dashboard.pages.okx_streams import Overview_StreamWidget
from h2o_dashboard.util import add_card


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
async def _ping_services(q):
    try:
        header_card = q.page['Overview_Page_Header']
        rest_handling_check, websocket_handling_check = await asyncio.gather(
            q.run(requests.request, 'GET', 'http://localhost:8080/health'),
            q.run(requests.request, 'GET', 'http://localhost:8081/health'),
        )

        header_card.subtitle = f'Rest Service Ping: {rest_handling_check.text}\n' \
                               f'Websockets Service Ping: {websocket_handling_check.text}\n '

    except Exception as e:
        header_card.subtitle = f'Error: {e}'
        print(f'{e = }')


async def overview_page(q: Q, update_seconds: int = 2):
    print("Loading Overview Page")
    '''Header'''
    await add_card(q, 'Overview_Page_Header',
                   ui.header_card(box='header', title='Overview Home', subtitle='Welcome to the AntBot Dashboard',
                                  # Color
                                  color='transparent',
                                  icon='Home',
                                  icon_color=None,
                                  items=[
                                      ui.message_bar(
                                          type='info',
                                          text=f''
                                      ),
                                  ]
                                  ))

    await add_tradingview_advanced_chart(q, card_name='Overview_Page_TradingView_Advanced_Chart', box='grid_1')

    # Redis Iframe Card
    await add_card(q, 'Redis_Iframe_Card',
                   ui.form_card(box='grid_3', items=[
                       ui.frame(content="""<iframe src="http://localhost:8001" width="100%" height="100%"></iframe>""",
                                height="800px", width="100%")
                   ]))

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
            await asyncio.sleep(update_seconds)

            '''CARD UPDATES'''
            if await overview_widget._is_initialized():
                print("Updating Overview card")
                await overview_widget.update_cards()
            else:
                print("Adding Overview card")
                await overview_widget.add_cards()

            await _ping_services(q)




            await q.page.save()
    except asyncio.CancelledError:
        print("Cancelled")
        pass
    finally:
        print("Finally")
        q.client.overview_page_running_event.clear()
        await q.page.save()
