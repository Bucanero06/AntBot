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
from h2o_wave import main, Q, app, ui, on, run_on, data  # noqa F401

from h2o_dashboard.util import add_card


async def documentation_page(q: Q):
    print("Loading Documentation Page")

    #
    await add_card(q, 'Documentation_Page_Header',
                   ui.header_card(box='header', title='Home', subtitle='Welcome to the H2O Dashboard',
                                  # Color
                                  color='transparent',
                                  icon='Home',
                                  icon_color=None,
                                  ))

    # embed https://bucanero06.github.io/AntBot
    await add_card(q, 'Documentation_Page_Documentation', ui.markdown_card(box='first_context_1', title='Documentation',
                                                                           content='<div style="width: 640px; height: 480px; margin: 10px; position: relative;"><iframe allowfullscreen frameborder="0" style="width:640px; height:480px" src="https://bucanero06.github.io/AntBot" id="ygM8fjvwnLkk"></iframe></div>'
                                                                           ))
    await add_card(q, 'Documentation_Page_Diagram', ui.markdown_card(box='first_context_1', title='Diagram',
                                                                     content='<div style="width: 640px; height: 480px; margin: 10px; position: relative;"><iframe allowfullscreen frameborder="0" style="width:640px; height:480px" src="https://lucid.app/documents/embedded/e5260455-d74f-4d36-af21-5e018177e9f0" id="ygM8fjvwnLkk"></iframe></div>'
                                                                     ))
    # q.client.documentation_page_running_event.set()


    try:
        while True:
            if not q.client.documentation_page_running_event.is_set():
                print("Breaking Documentation Page Loop")
                break
            await asyncio.sleep(1)
            await q.page.save()
    except asyncio.CancelledError:
        print("Cancelled")
        pass
    finally:
        print("Finally")
        q.client.documentation_page_running_event.clear()
        await q.page.save()


    await q.page.save()
