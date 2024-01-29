import asyncio

from h2o_wave import main, Q, app, ui, on,run_on, data # noqa F401

from h2o_dashboard.pages.okx_debug_page import okx_debug_page
from h2o_dashboard.util import clear_cards, add_card, stream_message


async def homepage(q: Q):
    print("Loading homepage")

    list_of_cards_on_this_page = ["Homepage_Header",
                                    "OKXDEBUG_Diagram",
                                    "Homepage_Sidebar",
                                    "Homepage_Content",
                                    ]

    await add_card(q, 'Homepage_Header', ui.header_card(box='header', title='Home', subtitle='Welcome to the H2O Dashboard',
                                                  # Color
                                                  color='transparent',
                                                  icon='Home',
                                                  icon_color=None,
                                                  ))

    await add_card(q, 'OKXDEBUG_Diagram', ui.markdown_card(box='grid_6', title='Diagram',
                                                           content='<div style="width: 640px; height: 480px; margin: 10px; position: relative;"><iframe allowfullscreen frameborder="0" style="width:640px; height:480px" src="https://lucid.app/documents/embedded/e5260455-d74f-4d36-af21-5e018177e9f0" id="ygM8fjvwnLkk"></iframe></div>'
                                                           ))

    # await add_card(q, 'Homepage_Sidebar', ui.nav_card(
    #     box='sidebar',
    #     items=[
    #         ui.nav_group('Main', items=[
    #             ui.nav_item(name='home', label='Home', icon='Home'),
    #             ui.nav_item(name='okx', label='OKX', icon='Money'),
    #             ui.nav_item(name='okx_debug', label='OKX Debug', icon='DeveloperTools'),
    #         ]),
    #         ui.nav_group('Settings', items=[
    #             ui.nav_item(name='settings', label='Settings', icon='Settings'),
    #             ui.nav_item(name='logout', label='Logout', icon='LogOut'),
    #         ]),
    #     ],
    # ))
    #
    # await add_card(q, 'Homepage_Content', ui.form_card(box='content', items=[
    #     ui.text_xl('Welcome to the AntBot-H2O Dashboard'),
    #     ui.text_xl('This is a work in progress, please be patient.'),
    # ]))

    # add <div style="width: 640px; height: 480px; margin: 10px; position: relative;"><iframe allowfullscreen frameborder="0" style="width:640px; height:480px" src="https://lucid.app/documents/embedded/e5260455-d74f-4d36-af21-5e018177e9f0" id="ygM8fjvwnLkk"></iframe></div>

    await q.page.save()






