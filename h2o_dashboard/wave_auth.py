import json
import os

import dotenv
import requests
from h2o_wave import Q, app, ui, on, data, run_on, AsyncSite  # noqa F401

from h2o_dashboard.pages.home_page import homepage
from h2o_dashboard.pages.okx_debug_page import okx_debug_page
from h2o_dashboard.redis_refresh import load_page_recipe_with_refresh
from h2o_dashboard.util import load_env_file, add_card, clear_cards


dotenv.load_dotenv(dotenv.find_dotenv())

FIREBASE_CONFIG = {
    "apiKey": os.environ.get("FIREBASE_API_KEY"),
}

# ruben@carbonyl.org
# u8hwr9y4y74w8huehewh893
async def init(q: Q) -> None:
    """
    Q Page Meta (meta_card) Arguments:
        box
            A string indicating how to place this component on the page.
        title
            The title of the page.
        refresh
            Refresh rate in seconds. A value of 0 turns off live-updates. Values != 0 are currently ignored (reserved for future use).
        notification
            Display a desktop notification.
        notification_bar
            Display an in-app notification bar.
        redirect
            Redirect the page to a new URL.
        icon
            Shortcut icon path. Preferably a .png file (.ico files may not work in mobile browsers). Not supported in Safari.
        layouts
            The layouts supported by this page.
        dialog
            Display a dialog on the page.
        side_panel
            Display a side panel on the page.
        theme
            Specify the name of the theme (color scheme) to use on this page. One of 'light', 'neon' or 'h2o-dark'.
        themes
            Themes (color schemes) that define color used in the app.
        tracker
            Configure a tracker for the page (for web analytics).
        scripts
            External Javascript files to load into the page.
        script
            Javascript code to execute on this page.
        stylesheet
            CSS stylesheet to be applied to this page.
        stylesheets
            External CSS files to load into the page.
        commands
            Contextual menu commands for this component.
    """
    # Static Business Website
    # index_file = open('static/html/index.html', 'r').read()

    q.page['meta'] = ui.meta_card(box='',
                                  title='AntBot',
                                  layouts=[ui.layout(breakpoint='xs', min_height='100vh', zones=[
                                      ui.zone('main', size='1', direction=ui.ZoneDirection.ROW, zones=[
                                          ui.zone('sidebar', size='208px'),
                                          ui.zone('body', zones=[
                                              ui.zone('header'),
                                              ui.zone('content', zones=[
                                                  # Specify various zones and use the one that is currently needed. Empty zones are ignored.
                                                  ui.zone('first_context', size='0 0 1 4',
                                                          direction=ui.ZoneDirection.ROW,
                                                          zones=[
                                                              ui.zone('first_context_1', size='1 4 0 0'),
                                                              ui.zone('first_context_2', size='1 4 0 0'),
                                                              ui.zone('first_context_3', size='1 4 0 0'),
                                                              ui.zone('first_context_4', size='1 4 0 0'),
                                                          ]),
                                                  ui.zone('second_context', size='0 0 1 4',
                                                          direction=ui.ZoneDirection.ROW,
                                                          zones=[
                                                              ui.zone('second_context_1', size='1 4 0 0'),
                                                              ui.zone('second_context_2', size='1 4 0 0'),
                                                              ui.zone('second_context_3', size='1 4 0 0',
                                                                      direction=ui.ZoneDirection.ROW,
                                                                      zones=[
                                                                          ui.zone('second_context_3_1', size='1 4 0 0'),
                                                                          ui.zone('second_context_3_2', size='1 4 0 0')
                                                                      ]),
                                                          ]),
                                                  ui.zone('details', size='4 4 4 4'),
                                                  ui.zone('horizontal', size='1', direction=ui.ZoneDirection.ROW),
                                                  ui.zone('centered', size='1 1 1 1', align='center'),
                                                  ui.zone('vertical', size='1'),
                                                  ui.zone('grid_1', direction=ui.ZoneDirection.ROW, wrap='stretch',
                                                          justify='center'),
                                                  ui.zone('grid_2', direction=ui.ZoneDirection.ROW, wrap='stretch',justify='center'),
                                                  ui.zone('grid_3', direction=ui.ZoneDirection.ROW, wrap='stretch',justify='center'),
                                                  ui.zone('grid_4', direction=ui.ZoneDirection.ROW, wrap='stretch',justify='center'),
                                                  ui.zone('grid_5', direction=ui.ZoneDirection.ROW, wrap='stretch',justify='center'),
                                                  ui.zone('grid_6', direction=ui.ZoneDirection.ROW, wrap='stretch',justify='center'),

                                              ]),
                                          ]),
                                      ]),
                                      ui.zone('footer', size='0 1 0 0', direction=ui.ZoneDirection.ROW),
                                  ]),
                                           ],
                                  themes=[
                                      ui.theme(
                                          name='my-awesome-theme',
                                          primary='#8C1B11',  # Header and Sidebaer - Color Light Red
                                          text='#000000',  #
                                          card='#ffffff',
                                          page='#F2F2F2',
                                          # page='#D91A1A',

                                      )
                                  ],
                                  theme='my-awesome-theme'

                                  )

    q.client.initialized = False


async def initialize_client(q: Q):
    q.client.cards = set()
    await init(q)
    q.client.initialized = True
    q.client.token = None  # Initially, no token is set.


def authenticate_with_firebase(email, password):
    """Authenticate with Firebase and return token if successful, or an error message."""
    endpoint = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_CONFIG['apiKey']}"
    data = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }

    try:
        response = requests.post(endpoint, data=json.dumps(data))
        response_data = response.json()

        if "idToken" in response_data:
            return {
                'status': 'success',
                'error_message': None,
                'token': response_data.get('idToken'),
                'refresh_token': response_data.get('refreshToken'),
                'user_id': response_data.get('localId'),
                'email': response_data.get('email'),
                'expires_in': response_data.get('expiresIn'),
            }

        elif "error" in response_data:
            return {
                'status': 'error',
                'error_message': f"Authentication failed: {response_data['error'].get('message', 'Unknown error.')}",
                'token': None,
                'refresh_token': None,
                'user_id': None,
                'email': None,
                'expires_in': None,
            }
    except requests.RequestException as e:
        return {
            'status': 'error',
            'error_message': f"Authentication failed: {e}",
            'token': None,
            'refresh_token': None,
            'user_id': None,
            'email': None,
            'expires_in': None,
        }
    return {
        'status': 'error',
        'error_message': f"Authentication failed: Unknown error.",
        'token': None,
        'refresh_token': None,
        'user_id': None,
        'email': None,
        'expires_in': None,
    }


def check_token_validity(idToken):
    """Check if a Firebase token is valid."""
    endpoint = f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={FIREBASE_CONFIG['apiKey']}"
    data = {"idToken": idToken}
    response = requests.post(endpoint, data=json.dumps(data))
    return (response.status_code == 200)


async def render_login_page(q: Q, error_message=None):
    """Render the login page."""

    await q.run(clear_cards, q, ignore=['Application_Sidebar'])

    await init(q)

    items = [
        ui.text_xl('Login'),
        ui.textbox(name='email', label='Email', required=True),
        ui.textbox(name='password', label='Password', required=True, password=True),
        ui.buttons([ui.button(name='login', label='Login', primary=True, )]),
    ]
    if error_message:
        items.insert(0, ui.message_bar(type='error', text=error_message, ))

    add_card(q, 'login', ui.form_card(box='centered', items=items, ), )


async def render_hidden_content(q: Q):
    """
    Render pages content e.g. homepage or other pages get added here
    """

    # First clear all cards
    await q.run(clear_cards, q, ignore=['Application_Sidebar'])

    await init(q)

    image_address ='data:image/png;base64,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'
    # Then add the sidebar
    add_card(q, 'Application_Sidebar', ui.nav_card(
        box='sidebar', color='primary', title='AntBot',
        subtitle="just a tiny bot here to help you out",
        value=f'#{q.args["#"]}' if q.args['#'] else '#homepage',
        # image='https://wave.h2o.ai/img/h2o-logo.svg', items=[]
        # Loading from local file rather than url
        image=image_address,
        items=[
            ui.nav_group('', items=[
                # ui.nav_item(name='#homepage', label='Home', icon='Home'),
                ui.nav_item(name='#debug_page', label='OKX Debug Page', icon='DeveloperTools'),
            ]),
            # ui.nav_group('Docs', items=[
            #     ui.nav_item(name='#admin_userdocs_link', label='Usage Documentation', icon='TextDocumentShared'),
            #     ui.nav_item(name='#admin_devdocs_link', label='Codebase Documentation', icon='TextDocumentEdit'),
            # ]),
            # ui.nav_group('Account', items=[
            #     ui.nav_item(name='#admin_account_page', label='Account', icon='AccountManagement'),
            #     ui.nav_item(name='#admin_plans_page', label='Plans', icon='PaymentCard'),
            #     ui.nav_item(name='logout', label='Logout', icon='Logout'),
            # ]),

        ],
    ))

    if q.args['#'] == 'homepage':
        await load_page_recipe_with_refresh(q, homepage)
    elif q.args["#"] == 'debug_page':
        await load_page_recipe_with_refresh(q, okx_debug_page)

    await q.page.save()
    await run_on(q)


@on('#homepage')
async def prepare_homepage(q: Q):
    await load_page_recipe_with_refresh(q, homepage)
    await q.page.save()



@on('#debug_page')
async def prepare_okx_debug_page(q: Q):
    await load_page_recipe_with_refresh(q, okx_debug_page)
    await q.page.save()








async def serve_security(q: Q,bypass_security=False):
    response = None
    # If logout is triggered, clear token and show login page
    if q.args.logout:
        q.client.token = None
        await render_login_page(q)
        return  # End the function after logging out

    # If login is triggered, try to authenticate and decide what to render next
    if q.args.login:
        response = authenticate_with_firebase(q.args.email, q.args.password)

        if response['status'] == 'success':
            print("Token already exists and is valid")
            q.client.token = response['token']
            await render_login_page(q, error_message=response['error_message'])
        else:
            await render_login_page(q, error_message=response['error_message'])
            return  # End the function if login fails

    if bypass_security:
        q.client.token = 'bypass'
        await render_hidden_content(q)
        return

    # If the client already has a token, check its validity and act accordingly
    if q.client.token:
        if check_token_validity(q.client.token):
            context = response  # todo: implement better context handling
            await render_hidden_content(q)
        else:
            q.client.token = None
            await render_login_page(q)
    else:
        await render_login_page(q)


