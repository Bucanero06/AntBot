import asyncio

from h2o_wave import Q, ui, on, data, run_on, AsyncSite  # noqa F401

from h2o_dashboard.util import add_card, init_page_card_set
from h2o_dashboard.widgets.okx_streams import OKX_Account_StreamWidget, OKX_Positions_StreamWidget, \
    OKX_Fill_Report_StreamWidget

app = AsyncSite()


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
    account_stream_widget = OKX_Account_StreamWidget(q=q, card_name='OKXDEBUG_Account_Stream', box='grid_2', count=100)
    positions_stream_widget = OKX_Positions_StreamWidget(q=q, card_name='OKXDEBUG_Positions_Stream', box='grid_3',
                                                         count=1)
    fill_report_stream_widget = OKX_Fill_Report_StreamWidget(q=q, card_name='OKXDEBUG_Fill_Report_Stream', box='grid_4',
                                                             count=1)
    '''Init RealTime Page Cards'''
    await add_page_cards(q, account_stream_widget, positions_stream_widget, fill_report_stream_widget)
    await q.page.save()

    # q.client.okx_dashboard_page_running_event.set()
    try:
        while True:
            if not q.client.okx_dashboard_page_running_event.is_set():
                print("Breaking OKX Dashboard Page Loop")
                break
            await asyncio.sleep(1)
            await add_page_cards(q, account_stream_widget, positions_stream_widget, fill_report_stream_widget)
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
                         fill_report_stream_widget: OKX_Fill_Report_StreamWidget):



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

    if await fill_report_stream_widget._is_initialized():
        print("Updating Fills Report Stream Metrics card")
        await fill_report_stream_widget.update_cards()
    else:
        print("Adding Fills Report Stream Metrics card")
        await fill_report_stream_widget.add_cards()



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
