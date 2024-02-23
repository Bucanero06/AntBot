import asyncio

from h2o_wave import Q, ui, on, data, run_on, AsyncSite  # noqa F401

# from h2o_dashboard.pages.okx_dashbaord_page.okx_algo_orders_widget import OKX_AlgoOrders_StreamWidget
from h2o_dashboard.pages.okx_dashbaord_page.okx_antbot_okx_premium_indicator_handler import \
    OKX_Premium_Indicator_Handler_Widget
from h2o_dashboard.pages.okx_dashbaord_page.okx_fill_report_widget import OKX_Fill_Report_StreamWidget
from h2o_dashboard.pages.okx_dashbaord_page.okx_orders_widget import OKX_Orders_StreamWidget
from h2o_dashboard.pages.okx_dashbaord_page.okx_positions_widget import OKX_Live_Positions_StreamWidget
from h2o_dashboard.util import add_card

app = AsyncSite()


async def okx_dashboard_page(q: Q, update_seconds: int = 2):
    '''Header'''
    await add_card(q, 'OKXDEBUG_Header', ui.header_card(box='header', title='OKX Dashboard',
                                                        subtitle='DevPage',
                                                        # Color
                                                        color='transparent',
                                                        icon='DeveloperTools',
                                                        icon_color=None,
                                                        items=[
                                                            ui.link(label="OKX Market's Data Page",
                                                                    name='okx_website_stats',
                                                                    path='https://www.okx.com/markets/data/contracts',
                                                                    target=''),
                                                            ui.link(label="OKX API Docs", name='okx_website_stats',
                                                                    path='https://www.okx.com/docs-v5/en/', target=''),
                                                        ]
                                                        ))

    # Add the the
    '''Init Widgets'''
    # await add_card(q, 'linktest',
    #                ui.form_card(box='grid_1', items=[
    #                       ui.link(label="OKX Market's Data Page", name='okx_website_stats', path='https://www.okx.com/markets/data/contracts', target=''),
    #                       ui.link(label="OKX API Docs", name='okx_website_stats', path='https://www.okx.com/docs-v5/en/', target=''),
    #                  ]))

    # account_stream_widget = OKX_Account_StreamWidget(q=q, card_name='OKXDEBUG_Account_Stream', box='grid_1',
    #                                                  history_count=900)
    positions_stream_widget = OKX_Live_Positions_StreamWidget(q=q, card_name='OKXDEBUG_Positions_Stream', box='grid_2')
    fill_report_stream_widget = OKX_Fill_Report_StreamWidget(q=q, card_name='OKXDEBUG_Fill_Report_Stream', box='grid_2')

    orders_stream_widget = OKX_Orders_StreamWidget(q=q, card_name='OKXDEBUG_Orders_Stream', box='footer',
                                                   history_count=20)
    # algo_orders_stream_widget = OKX_AlgoOrders_StreamWidget(q=q, card_name='OKXDEBUG_Algo_Orders_Stream', box='grid_4',
    #                                                         history_count=20)
    okx_premium_indicator_handler_widget = OKX_Premium_Indicator_Handler_Widget(q=q,
                                                                                card_name='OKXDEBUG_Premium_Manual_Controls',
                                                                                box='grid_5')



    '''Init RealTime Page Cards'''
    # await account_stream_widget.add_cards()
    # await positions_stream_widget.add_cards()
    # await fill_report_stream_widget.add_cards()
    await okx_premium_indicator_handler_widget.add_cards()
    # await orders_stream_widget.add_cards()
    # await algo_orders_stream_widget.add_cards()

    await q.page.save()

    try:
        while True:
            if not q.client.okx_dashboard_page_running_event.is_set():
                print("Breaking OKX Dashboard Page Loop")
                break
            await asyncio.sleep(update_seconds)
            #
            # await account_stream_widget.update_cards()
            # await positions_stream_widget.update_cards()
            # await fill_report_stream_widget.update_cards()
            await okx_premium_indicator_handler_widget.update_cards()
            # await orders_stream_widget.update_cards()
            # await algo_orders_stream_widget.update_cards()

            await q.page.save()
    except asyncio.CancelledError:
        print("Cancelled")
        pass
    finally:
        print("Finally")
        q.client.okx_dashboard_page_running_event.clear()
        await q.page.save()
