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
from h2o_dashboard.widgets.okx_streams import Overview_StreamWidget


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

    '''Init Widgets'''
    overview_widget = Overview_StreamWidget(q=q, card_name='Overview_Page_Account_Stream', count=2)

    '''Init RealTime Page Cards'''
    await overview_widget.add_cards()
    await q.page.save()
    # q.client.overview_page_running_event.set()

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
