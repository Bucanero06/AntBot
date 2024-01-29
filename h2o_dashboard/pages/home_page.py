from h2o_wave import main, Q, app, ui, on, run_on, data  # noqa F401

from h2o_wave import main, Q, app, ui, on, run_on, data  # noqa F401

from h2o_dashboard.util import add_card


async def homepage(q: Q):
    print("Loading homepage")

    list_of_cards_on_this_page = ["Homepage_Header",
                                  "Homepage_Diagram",
                                  "Homepage_Sidebar",
                                  "Homepage_Content",
                                  "Homepage_Documentation",
                                  ]

    await add_card(q, 'Homepage_Content', ui.form_card(box='first_context_1', items=[
        ui.text_xl('Welcome to the AntBot-H2O Dashboard'),
        ui.text_xl('This is a work in progress, please be patient.'),
    ]))

    await add_card(q, 'Homepage_Header',
                   ui.header_card(box='header', title='Home', subtitle='Welcome to the H2O Dashboard',
                                  # Color
                                  color='transparent',
                                  icon='Home',
                                  icon_color=None,
                                  ))

    await add_card(q, 'Homepage_Diagram', ui.markdown_card(box='first_context_1', title='Diagram',
                                                           content='<div style="width: 640px; height: 480px; margin: 10px; position: relative;"><iframe allowfullscreen frameborder="0" style="width:640px; height:480px" src="https://lucid.app/documents/embedded/e5260455-d74f-4d36-af21-5e018177e9f0" id="ygM8fjvwnLkk"></iframe></div>'
                                                           ))

    # embed https://bucanero06.github.io/AntBot
    await add_card(q, 'Homepage_Documentation', ui.markdown_card(box='first_context_1', title='Documentation',
                                                                 content='<div style="width: 640px; height: 480px; margin: 10px; position: relative;"><iframe allowfullscreen frameborder="0" style="width:640px; height:480px" src="https://bucanero06.github.io/AntBot" id="ygM8fjvwnLkk"></iframe></div>'
                                                                 ))

    await q.page.save()
