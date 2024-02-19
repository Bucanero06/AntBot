
import pprint
from datetime import datetime, timedelta

from h2o_wave import Q, ui, on, data, run_on, AsyncSite, pack, copy_expando  # noqa F401
from pydantic import ValidationError

from firebase_tools.authenticate import check_str_token_validity
from h2o_dashboard.util import add_card
from pyokx import ENFORCED_INSTRUMENT_TYPE
from pyokx.InstrumentSearcher import InstrumentSearcher
from pyokx.data_structures import OKXSignalInput, InstrumentStatusReport, PremiumIndicatorSignals, \
    OKXPremiumIndicatorSignalRequestForm
from pyokx.redis_structured_streams import get_instruments_searcher_from_redis
from pyokx.rest_handling import okx_signal_handler, validate_okx_signal_params, okx_premium_indicator_handler
from routers.okx_authentication import InstIdAPIKeyCreationRequestForm, create_instrument_api_key

OKX_SIGNAL_INPUT_KEYS = OKXSignalInput.model_fields.keys()
OKX_PREMIUM_INDICATOR_SIGNAL_INPUT_KEYS = PremiumIndicatorSignals.model_fields.keys()


class OKX_Premium_Indicator_Handler_Widget:

    def __init__(self, q: Q, card_name: str, box: str, minimum_update_delay: int = 2 * 60):
        self.q = q
        self.card_name = card_name
        self.box = box
        self._initialized = False

        self.okx_futures_instruments_searcher: InstrumentSearcher = None

        self._last_update_time = None
        self._minimum_update_delay = minimum_update_delay

    async def _update_stream(self):
        # Only update every n seconds minimum, updating the instruments is not a high priority
        if self._last_update_time:
            if (self._last_update_time - self._last_update_time) < timedelta(seconds=self._minimum_update_delay):
                return
        self._last_update_time = datetime.now()
        self.okx_futures_instruments_searcher = await get_instruments_searcher_from_redis(
            async_redis=self.q.client.async_redis, instType=ENFORCED_INSTRUMENT_TYPE)

    async def _is_initialized(self):
        return self._initialized and self.okx_futures_instruments_searcher

    async def add_cards(self):
        await self._update_stream()
        instrument_id_choices = [ui.choice(name=instID, label=instID) for instID in
                                 self.okx_futures_instruments_searcher.get_instrument_ids()]
        bot_okx_signal_inputs = ui.form_card(
            box=self.box,
            items=[
                ui.mini_buttons(items=[
                    ui.mini_button(name=f'okx_dashboard_page_okx_premium_indicator_validate_inputs',
                                   label='Validate Input',
                                   icon='CheckMark'),
                    ui.mini_button(name='okx_dashboard_page_okx_premium_indicator_submit_okx_signal',
                                   label='Submit Signal',
                                   icon='Send'),
                    ui.mini_button(name='okx_dashboard_page_okx_premium_indicator_generate_tv_payload',
                                   label='Generate TV Payload',
                                   icon='Send'),
                ]),

                ui.expander(name='okx_dashboard_page_okx_premium_indicator_expander',
                            label='OKX Premium Indicator Signal', expanded=True,
                            items=[
                                # Small note
                                ui.message_bar(
                                    type='warning',
                                    text='Bullish or Bearish signals will override order side'
                                ),
                                ui.message_bar(
                                    type='warning',
                                    text='OKX SIGNAL should be validated prior to submitting'
                                ),
                                ui.mini_buttons(
                                    items=[
                                        ui.mini_button(
                                            name=f'okx_dashboard_page_okx_premium_indicator_{PremiumIndicatorSignals.Bullish}',
                                            label='Bullish', icon='ChevronUpSmall'),
                                        ui.mini_button(
                                            name=f'okx_dashboard_page_okx_premium_indicator_{PremiumIndicatorSignals.Bullish_plus}',
                                            label='Bullish Plus', icon='DoubleChevronUp8'),
                                        ui.mini_button(
                                            name=f'okx_dashboard_page_okx_premium_indicator_{PremiumIndicatorSignals.Bullish_Exit}',
                                            label='Bullish Exit', icon='GroupedDescending'),
                                    ]
                                ),
                                ui.mini_buttons(
                                    items=[
                                        ui.mini_button(
                                            name=f'okx_dashboard_page_okx_premium_indicator_{PremiumIndicatorSignals.Bearish}',
                                            label='Bearish', icon='ChevronDownSmall'),
                                        ui.mini_button(
                                            name=f'okx_dashboard_page_okx_premium_indicator_{PremiumIndicatorSignals.Bearish_plus}',
                                            label='Bearish Plus', icon='DoubleChevronDown8'),
                                        ui.mini_button(
                                            name=f'okx_dashboard_page_okx_premium_indicator_{PremiumIndicatorSignals.Bearish_Exit}',
                                            label='Bearish Exit', icon='GroupedAscending')
                                    ]
                                ),
                                ui.dropdown(
                                    name=f'okx_dashboard_page_okx_premium_indicator_{OKXSignalInput.instID}',
                                    label='Instrument ID',
                                    choices=instrument_id_choices,
                                    trigger=True
                                ),
                                ui.message_bar(
                                    type='info',
                                    text='RECOMMENDED!',
                                ),
                                ui.toggle(
                                    name=f'okx_dashboard_page_okx_premium_indicator_{OKXSignalInput.flip_position_if_opposite_side}',
                                    label='Flip Position If Opposite Side',
                                    value=True,
                                    tooltip='This is recommended for automated trading unless you want to keep by default '
                                            'all orders and positions untouched, unlikely unless market making'),

                                ui.expander(name='okx_dashboard_page_okx_premium_indicator_advanced_expander',
                                            label='Advanced',
                                            items=[
                                                ui.toggle(
                                                    name=f'okx_dashboard_page_okx_premium_indicator_{OKXSignalInput.red_button}',
                                                    label='Red Button'),
                                                ui.toggle(
                                                    name=f'okx_dashboard_page_okx_premium_indicator_{OKXSignalInput.clear_prior_to_new_order}',
                                                    label='Clear Prior To New Order'),
                                                ui.textbox(
                                                    name=f'okx_dashboard_page_okx_premium_indicator_{OKXSignalInput.max_orderbook_limit_price_offset}',
                                                    label='Max Orderbook Limit Price Offset (USD)',
                                                    placeholder='float: 0.0',
                                                ),
                                            ]),
                                ui.expander(name=f'okx_dashboard_page_okx_premium_indicator_order_parameters_expander',
                                            label='Order Parameters', items=[
                                        ui.textbox(
                                            name=f'okx_dashboard_page_okx_premium_indicator_{OKXSignalInput.usd_order_size}',
                                            label='Order Size (USD)', placeholder='float: 0 USD',
                                        ),
                                        ui.textbox(
                                            name=f'okx_dashboard_page_okx_premium_indicator_{OKXSignalInput.leverage}',
                                            label='Leverage',
                                            placeholder='int: 0',
                                        ),
                                        ui.textbox(
                                            name=f'okx_dashboard_page_okx_premium_indicator_{OKXSignalInput.order_side}',
                                            label='Order Side',
                                            placeholder='BUY or SELL or ""',
                                        ),
                                        ui.dropdown(
                                            name=f'okx_dashboard_page_okx_premium_indicator_{OKXSignalInput.order_type}',
                                            label='Order Type',
                                            placeholder='MARKET or LIMIT or POST_ONLY',
                                            choices=[ui.choice(name='MARKET', label='MARKET'),
                                                     ui.choice(name='LIMIT', label='LIMIT'),
                                                     ui.choice(name='POST_ONLY', label='POST_ONLY')],
                                            value='MARKET'
                                        ),
                                    ]),
                                ui.expander(name='okx_dashboard_page_okx_premium_indicator_tp_sl_expander',
                                            label='TP/SL', items=[
                                        ui.dropdown(
                                            name=f'okx_dashboard_page_okx_premium_indicator_{OKXSignalInput.tp_trigger_price_type}',
                                            label='TP Trigger Price Type',
                                            placeholder='index or mark or last',
                                            value='last',
                                            choices=[
                                                # 'index', 'mark', 'last'
                                                ui.choice(name='index', label='index'),
                                                ui.choice(name='mark', label='mark'),
                                                ui.choice(name='last', label='last')
                                            ],
                                        ),
                                        ui.textbox(
                                            name=f'okx_dashboard_page_okx_premium_indicator_{OKXSignalInput.tp_execution_price_offset}',
                                            label='TP Execution Price Offset (USD)',
                                            placeholder='float: 0.0 USD',
                                        ),
                                        ui.textbox(
                                            name=f'okx_dashboard_page_okx_premium_indicator_{OKXSignalInput.tp_trigger_price_offset}',
                                            label='Take Profit Trigger Offset (USD)',
                                            placeholder='float: 0.0 USD',
                                        ),
                                        ui.dropdown(
                                            name=f'okx_dashboard_page_okx_premium_indicator_{OKXSignalInput.sl_trigger_price_type}',
                                            label='SL Trigger Price Type',
                                            placeholder='index or mark or last',
                                            value='last',
                                            choices=[
                                                # 'index', 'mark', 'last'
                                                ui.choice(name='index', label='index'),
                                                ui.choice(name='mark', label='mark'),
                                                ui.choice(name='last', label='last')
                                            ],
                                        ),
                                        ui.textbox(
                                            name=f'okx_dashboard_page_okx_premium_indicator_{OKXSignalInput.sl_execution_price_offset}',
                                            label='SL Execution Price Offset (USD)',
                                            placeholder='float: 0.0 USD'),
                                        ui.textbox(
                                            name=f'okx_dashboard_page_okx_premium_indicator_{OKXSignalInput.sl_trigger_price_offset}',
                                            label='Stop Loss Trigger Offset (USD)',
                                            placeholder='float: 0.0 USD',
                                        ),

                                    ]),
                                ui.expander(name='okx_dashboard_page_okx_premium_indicator_trailing_stop_expander',
                                            label='Trailing Stop', items=[
                                        ui.textbox(
                                            name=f'okx_dashboard_page_okx_premium_indicator_{OKXSignalInput.trailing_stop_activation_price_offset}',
                                            label='Trailing Stop Activation Offset (USD)',
                                            placeholder='float: 0.0 (USD)'),
                                        ui.textbox(
                                            name=f'okx_dashboard_page_okx_premium_indicator_{OKXSignalInput.trailing_stop_callback_offset}',
                                            label='Trailing Stop Callback Offset (USD)',
                                            placeholder='float: 0.0 (USD)'),
                                    ]),
                                ui.expander(name='okx_dashboard_page_okx_premium_indicator_dca_expander',
                                            label='SINGLE DCA PARAMS (UI-Form not enabled)', items=[
                                            # DCAInputParameters(
                                            #         usd_amount=100,
                                            #         order_type="LIMIT",
                                            #         order_side="BUY",
                                            #         trigger_price_offset=100,
                                            #         execution_price_offset=90,
                                            #         tp_trigger_price_offset=100,
                                            #         tp_execution_price_offset=90,
                                            #         sl_trigger_price_offset=100,
                                            #         sl_execution_price_offset=90
                                            #     ),
                                        ui.textbox(
                                            name=f'okx_dashboard_page_okx_premium_indicator_{OKXSignalInput.trailing_stop_callback_offset}',
                                            label="""DCAInputParameters(
                                                    usd_amount=100,
                                                    order_type="LIMIT",
                                                    order_side="BUY",
                                                    trigger_price_offset=100,
                                                    execution_price_offset=90,
                                                    tp_trigger_price_offset=100,
                                                    tp_execution_price_offset=90,
                                                    sl_trigger_price_offset=100,
                                                    sl_execution_price_offset=90
                                                ),""",
                                            # placeholder='float: 0.0 (USD)'
                                        ),
                                    ]),
                            ]),
            ])




        output_value = "When ready or in doubt, \n  press the `Validate Input Model` button" if not self.q.client.okx_dashboard_page_okx_signal_input else self.q.client.okx_dashboard_page_okx_signal_input.model_dump()
        output_value = str(output_value) if not isinstance(output_value, dict) else pprint.pformat(output_value,
                                                                                                   compact=True,
                                                                                                   sort_dicts=False,
                                                                                                   width=100, depth=5)
        # Height should be the same as the height of the OKX Premium Indicator Signal input card
        bot_okx_signal_input_model_box = ui.form_card(
            box=self.box,
            items=[
                ui.separator(label='Input Model for Endpoint', width='300px'),
                ui.copyable_text(
                    label='',
                    value=output_value,
                    multiline=True,
                    height='1',
                ),
                #         ui.separator(label='A separator sections forms'),
                #         ui.toggle(name='toggle', label='Toggle'),
                #         ui.choice_group(name='choice_group', label='Choice group', choices=[
                #             ui.choice(name=x, label=x) for x in ['Egg', 'Bacon', 'Spam']
                #         ]),
                #         ui.dropdown(name='dropdown1', label='Dropdown', choices=[
                #             ui.choice(name=x, label=x) for x in ['Egg', 'Bacon', 'Spam']
                #         ]),
                #
                #         ui.slider(name='slider', label='Slider'),
                #         ui.range_slider(name='range_slider', label='Range slider', max=99),
                #         ui.file_upload(name='file_upload', label='File upload'),
                #         ui.tabs(name='tabs', items=[
                #             ui.tab(name='email', label='Mail', icon='Mail'),
                #             ui.tab(name='events', label='Events', icon='Calendar'),
                #             ui.tab(name='spam', label='Spam'),
                #         ]),
                #         ui.stepper(name='stepper', items=[
                #             ui.step(label='Step 1', icon='MailLowImportance', done=True),
                #             ui.step(label='Step 2', icon='TaskManagerMirrored'),
                #             ui.step(label='Step 3', icon='Cafe'),
                #         ]),
                #         ui.expander(name='expander', label='Expander', items=[
                #             ui.combobox(name='combobox', label='Combobox', choices=['Choice 1', 'Choice 2', 'Choice 3']),
                #             ui.slider(name='slider', label='Slider'),
                #             ui.range_slider(name='range_slider', label='Range slider', max=99),
                #             ui.spinbox(name='spinbox', label='Spinbox'),
                #         ]),
                #         ui.picker(name='picker', label='Picker', choices=[
                #             ui.choice('choice1', label='Choice 1'),
                #             ui.choice('choice2', label='Choice 2'),
                #             ui.choice('choice3', label='Choice 3'),
                #         ]),
                #         ui.button(name='show_inputs', label='Submit', primary=True),
            ])
        bot_okx_signal_output_response_card = ui.form_card(
            box=self.box,
            items=[
                ui.separator(label='Output Response', width='300px'),
                ui.copyable_text(
                    label='',
                    value='output response will appear here',
                    multiline=True,
                    height='1'
                ),
            ])

        await add_card(self.q, self.card_name + '_okx_signal_inputs', bot_okx_signal_inputs)
        await add_card(self.q, self.card_name + '_okx_signal_input_model_box', bot_okx_signal_input_model_box)
        await add_card(self.q, self.card_name + '_okx_signal_output_response_card', bot_okx_signal_output_response_card)
        self.q.client.OKX_Manual_ControlsWidget_card_name = self.card_name

        await self.q.page.save()
        self._initialized = True

    async def update_cards(self):
        await self._update_stream()
        await self.q.page.save()


#  input_form = InstIdSignalRequestForm(
#         InstIdAPIKey="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJydWJlbkBjYXJib255bC5vcmciLCJpZCI6Ilk5UUVOdExIZThiMnRwVEVuNVRnNllZRUxsZDIiLCJyb2xlIjoidHJhZGluZ19pbnN0cnVtZW50IiwiaW5zdElEIjoiQlRDLVVTRC0yNDAyMDkifQ.lVxzjoxGGwH_qzrRu1uMFklEGRQjpgHMKgJo44J1_BE",
#         OKXSignalInput=OKXSignalInput(
#             instID="BTC-USD-240209",
#         )
#     )
# result = requests.post("http://localhost:8080/okx_antbot_signal",
#                        json=input_form.model_dump())
# print(f'{result = }')
# print(f'{result.json() = }')
#
# return
@on('okx_dashboard_page_okx_premium_indicator_instID')
async def on_instID_selection(q: Q):
    copy_expando(q.args, q.client)
    try:
        # Lets show the rest of the ticker/instID information in the Output Response card
        instID = q.client.okx_dashboard_page_okx_premium_indicator_instID
        instruments_searcher: InstrumentSearcher = await get_instruments_searcher_from_redis(q.client.async_redis,
                                                                                             instType=ENFORCED_INSTRUMENT_TYPE)
        instrument_ticker = instruments_searcher.find_by_instId(instID)
        if instrument_ticker:
            q.client.okx_dashboard_page_instrument_ticker = instrument_ticker
            output_response_card = q.page[
                q.client.OKX_Manual_ControlsWidget_card_name + '_okx_signal_output_response_card']

            returning_txt_value = f'Instrument Ticker Information:\n\n'
            for k, v in instrument_ticker.model_dump().items():
                returning_txt_value += f'{k}: {pprint.pformat(v, compact=True, sort_dicts=False, width=100, depth=5)}\n'

            output_response_card.items[1].copyable_text.value = returning_txt_value
            await q.page.save()
        else:
            q.client.okx_dashboard_page_instrument_ticker = None
            output_response_card = q.page[
                q.client.OKX_Manual_ControlsWidget_card_name + '_okx_signal_output_response_card']
            output_response_card.items[1].copyable_text.value = f'No instrument ticker found for {instID}'
            await q.page.save()


    except Exception as e:
        print(f'{e = }')
        output_response_card = q.page[q.client.OKX_Manual_ControlsWidget_card_name + '_okx_signal_output_response_card']
        output_response_card.items[1].copyable_text.value = pprint.pformat(e, compact=True, sort_dicts=False,
                                                                           width=100, depth=5)
        await q.page.save()
        return


@on('okx_dashboard_page_okx_premium_indicator_validate_inputs')
async def okx_signal_validate_inputs(q: Q):
    # Copy the inputs from the args if found to the client
    copy_expando(q.args, q.client)
    okx_signal_params = {att: q.client[f'okx_dashboard_page_okx_premium_indicator_{att}'] for att in
                         OKX_SIGNAL_INPUT_KEYS}

    try:
        # Clean the OKX Signal params
        keys_to_remove = []
        for k, v in okx_signal_params.items():
            if v == '' or v is None:
                print(f'Warning: {k} is empty')
                keys_to_remove.append(k)
        for k in keys_to_remove:
            okx_signal_params.pop(k)
        okx_signal = OKXSignalInput(**okx_signal_params)
        q.client.okx_dashboard_page_okx_signal_input = okx_signal

        try:
            validated_inputs = await validate_okx_signal_params(okx_signal)

            return_txt_value = (f'Inputs have been validated by Pydantic, furthermore, all transformation done to '
                                f'validate the input from inside the OKXSignalHandler have passed. Make sure '
                                f'variables have their expected values:\n\n')
            for k, v in validated_inputs.items():
                return_txt_value += f'{k}: {v}\n'

            bot_okx_signal_input_model_box: ui.form_card = q.page[
                q.client.OKX_Manual_ControlsWidget_card_name + '_okx_signal_input_model_box']
            output_value = "When ready or in doubt, \n  press the `Validate Input Model` button" \
                if not okx_signal else okx_signal.model_dump()
            # Pretty output the pydantic model without reordering the keys
            bot_okx_signal_input_model_box.items[1].copyable_text.value = str(output_value) if not isinstance(
                output_value,
                dict) else pprint.pformat(
                output_value, compact=True, sort_dicts=False,
                width=100, depth=5)
            output_response_card = q.page[
                q.client.OKX_Manual_ControlsWidget_card_name + '_okx_signal_output_response_card']
            output_response_card.items[1].copyable_text.value = return_txt_value
            await q.page.save()
            return True
        except Exception as e:
            raise e

    except ValidationError as e:
        print(f"{e = }")
        # Parse and format the errors
        errors = []
        for error in e.errors():
            field = error.get('loc', [])[0]
            msg = error.get('msg', '')
            error_type = error.get('type', '')
            input_value = error.get('input_value', '')
            errors.append(f"Field: {field}, Error: {msg}, Type: {error_type}, Input Value: {input_value}")

        # Create a card to display the error
        return_txt_value = f'Validation Errors:\n\n\n'
        for error in errors:
            return_txt_value += f'• {error}\n'

        output_response_card = q.page[q.client.OKX_Manual_ControlsWidget_card_name + '_okx_signal_output_response_card']
        output_response_card.items[1].copyable_text.value = return_txt_value
    except Exception as e:
        output_response_card = q.page[q.client.OKX_Manual_ControlsWidget_card_name + '_okx_signal_output_response_card']
        output_response_card.items[1].copyable_text.value = str(e)

    await q.page.save()
    return


@on('okx_dashboard_page_okx_premium_indicator_submit_okx_signal')
async def submit_okx_signal(q: Q):
    output_response_card = q.page[q.client.OKX_Manual_ControlsWidget_card_name + '_okx_signal_output_response_card']

    okx_signal_txt_header = 'OKX Signal Response:\n\n'

    # First validate the inputs
    try:
        successful_validation = await okx_signal_validate_inputs(q)
        print(f'{successful_validation= }')
        if not successful_validation:
            return
    except Exception as e:
        output_response_card.items[1].copyable_text.value = f"{e = }"
        await q.page.save()
        return

    okx_signal = q.client.okx_dashboard_page_okx_signal_input
    if not okx_signal:
        output_response_card.items[1].copyable_text.value = 'No OKX Signal found'
        await q.page.save()
        return
    try:
        output_response_card.items[1].copyable_text.value = f"Submitting OKX Signal Handler Request..."
        await q.page.save()
        signal_response = await okx_signal_handler(
            **okx_signal.model_dump()
        )
        print(f'{signal_response= }')
        if isinstance(signal_response, dict) and (signal_response.get('error') or signal_response.get('red_button')):
            print('Is instance of dict')
            output_response_card.items[1].copyable_text.value = okx_signal_txt_header + pprint.pformat(signal_response,
                                                                                                       compact=True,
                                                                                                       sort_dicts=False,
                                                                                                       width=100,
                                                                                                       depth=5)
        elif isinstance(signal_response, InstrumentStatusReport):
            print('Is instance of InstrumentStatusReport')
            output_response_card.items[1].copyable_text.value = okx_signal_txt_header + pprint.pformat(signal_response,
                                                                                                       compact=True,
                                                                                                       sort_dicts=False,
                                                                                                       width=100,
                                                                                                       depth=5)
        else:
            print('Is instance of else')
            output_response_card.items[1].copyable_text.value = okx_signal_txt_header + pprint.pformat(signal_response,
                                                                                                       compact=True,
                                                                                                       sort_dicts=False,
                                                                                                       width=100,
                                                                                                       depth=5)
    except Exception as e:
        print(f'{e = }')
        output_response_card.items[1].copyable_text.value = f"{e = }"
        await q.page.save()
        return

    await q.page.save()


@on('okx_dashboard_page_okx_premium_indicator_generate_tv_payload')
async def generate_tv_payload(q: Q):
    output_response_card = q.page[q.client.OKX_Manual_ControlsWidget_card_name + '_okx_signal_output_response_card']
    okx_signal_txt_header = 'TV Payload Response:\n\n'

    try:
        output_response_card.items[1].copyable_text.value = f"Generating TV Payload..."
        await q.page.save()

        if q.client.token:
            auth_response = await check_str_token_validity(q.client.token)
            print(f'{auth_response = }')
            if not auth_response:
                raise ValueError("Token is invalid, please reload the page and log in again")
        if not q.client.okx_dashboard_page_okx_premium_indicator_instID:
            raise ValueError("Choose an instrument ID first")
        # Curl create_instrument_api_key using the InstIdAPIKeyCreationRequestForm model
        request_payload = InstIdAPIKeyCreationRequestForm(
            username=q.client.email,
            password=q.client.password,
            instID=q.client.okx_dashboard_page_okx_premium_indicator_instID,
            expire_time=None
        )
        instrument_api_key_response = await create_instrument_api_key(request_payload, q.client.token)

        print(f'{instrument_api_key_response = }')
        if not instrument_api_key_response.get('access_token'):
            raise ValueError("Failed to create instrument API key")

        request_model = await on_premium_indicator_signal_selection(q, only_return_request_model=True)
        print(f'{request_model = }')
        if not request_model:
            return

        print(f'{request_model = }')
        request_model.InstIdAPIKey = instrument_api_key_response.get('access_token')

        tradingview_payload = request_model.to_tradingview_json_payload()
        print(f'{tradingview_payload = }')
        # Pretty print but keep json integrity meaning without the string quotes

        output_response_card.items[1].copyable_text.value = tradingview_payload
    except Exception as e:
        print(f'{e = }')
        output_response_card.items[1].copyable_text.value = f"{e = }"
        await q.page.save()
        return

    await q.page.save()


@on('okx_dashboard_page_okx_premium_indicator_Bullish')
@on('okx_dashboard_page_okx_premium_indicator_Bearish')
@on('okx_dashboard_page_okx_premium_indicator_Bullish_plus')
@on('okx_dashboard_page_okx_premium_indicator_Bearish_plus')
@on('okx_dashboard_page_okx_premium_indicator_Bullish_Exit')
@on('okx_dashboard_page_okx_premium_indicator_Bearish_Exit')
async def on_premium_indicator_signal_selection(q: Q, only_return_request_model=False):
    output_response_card = q.page[q.client.OKX_Manual_ControlsWidget_card_name + '_okx_signal_output_response_card']
    okx_signal_txt_header = 'OKX Premium Indicator Signal Response:\n\n'

    premium_indicator_signal_params = {att: q.args[f'okx_dashboard_page_okx_premium_indicator_{att}'] for att in
                                       OKX_PREMIUM_INDICATOR_SIGNAL_INPUT_KEYS}
    cleaned_indicator_params = {k: 1 if v is not None else 0 for k, v in premium_indicator_signal_params.items()}
    print(f'{cleaned_indicator_params = }')
    if not only_return_request_model and sum(cleaned_indicator_params.values()) != 1:
        raise ValueError("Only one of the premium indicator signals should be True")

    # Now lets Validate the inputs for the OKX signal
    try:
        okx_premium_indicator_signals = PremiumIndicatorSignals(**cleaned_indicator_params)

        successful_validation = await okx_signal_validate_inputs(
            q,
            # override_okx_signal_params=q.client.okx_dashboard_page_okx_signal_input
        )

        bot_okx_signal_input_model_box: ui.form_card = q.page[
            q.client.OKX_Manual_ControlsWidget_card_name + '_okx_signal_input_model_box']
        input_values = f'\nPremium Indicator Signal:\n'
        #     input_values += f'{k}: {v}\n'

        input_values += pprint.pformat(cleaned_indicator_params, compact=True, sort_dicts=False, width=100, depth=5)
        input_values += '\n\n'
        input_values += f'OKX Signal:\n'
        input_values += pprint.pformat(q.client.okx_dashboard_page_okx_signal_input.model_dump(), compact=True,
                                       sort_dicts=False, width=100, depth=5)

        bot_okx_signal_input_model_box.items[1].copyable_text.value = input_values

        # TODO the OKX SIGNAL  we need to transform the indicator signals to actionable okx_signal which is not done yet
        #   here thus okx_signal_validate_inputs does not validate inside the okx_signal_handler function, only outside
        #   through pydantic models
        print(f'{successful_validation= }')
        if not successful_validation:
            return
        print()


    except Exception as e:
        output_response_card.items[1].copyable_text.value = f"{e = }"
        await q.page.save()
        return

    okx_signal = q.client.okx_dashboard_page_okx_signal_input

    if not okx_signal:
        output_response_card.items[1].copyable_text.value = 'No OKX Signal found'
        await q.page.save()
        return

    # Now lets Submit the OKX signal but this time to the OKX Premium Indicator Signal Handler
    try:
        output_response_card.items[1].copyable_text.value = f"Submitting OKX Premium Indicator Signal Request..."
        await q.page.save()

        request_model = OKXPremiumIndicatorSignalRequestForm(
            InstIdAPIKey='place_holder_until_generated',  # TODO this should be a valid API key for the endpoint
            OKXSignalInput=okx_signal,
            PremiumIndicatorSignals=okx_premium_indicator_signals
        )

        if only_return_request_model:
            return request_model

        signal_response = await okx_premium_indicator_handler(indicator_input=request_model)

        print(f'{signal_response= }')
        if isinstance(signal_response, dict) and (signal_response.get('error') or signal_response.get('red_button')):
            print('Is instance of dict')
            output_response_card.items[1].copyable_text.value = okx_signal_txt_header + pprint.pformat(signal_response,
                                                                                                       compact=True,
                                                                                                       sort_dicts=False,
                                                                                                       width=100,
                                                                                                       depth=5)
        elif isinstance(signal_response, InstrumentStatusReport):
            print('Is instance of InstrumentStatusReport')
            output_response_card.items[1].copyable_text.value = okx_signal_txt_header + pprint.pformat(signal_response,
                                                                                                       compact=True,
                                                                                                       sort_dicts=False,
                                                                                                       width=100,
                                                                                                       depth=5)
        else:
            print('Is instance of else')
            output_response_card.items[1].copyable_text.value = okx_signal_txt_header + pprint.pformat(signal_response,
                                                                                                       compact=True,
                                                                                                       sort_dicts=False,
                                                                                                       width=100,
                                                                                                       depth=5)
    except Exception as e:
        print(f'{e = }')
        output_response_card.items[1].copyable_text.value = f"{e = }"
        await q.page.save()
        return

    await q.page.save()

# premium_indicator_signal_params = {att: q.client[f'okx_dashboard_page_okx_premium_indicator_{att}'] for att in
#                                    OKX_PREMIUM_INDICATOR_SIGNAL_INPUT_KEYS}
# keys_to_remove = []
# for k, v in premium_indicator_signal_params.items():
#     if v == '' or v is None:
#         print(f'Warning: {k} is empty')
#         keys_to_remove.append(k)
# for k in keys_to_remove:
#     premium_indicator_signal_params.pop(k)
#
# for k in OKX_PREMIUM_INDICATOR_SIGNAL_INPUT_KEYS:
#     if k not in premium_indicator_signal_params:
#         premium_indicator_signal_params[k] = '0'
#
# okx_premium_indicator = PremiumIndicatorSignals(**premium_indicator_signal_params)
# q.client.okx_dashboard_page_okx_signal_input = okx_premium_indicator
#
# print(f'{q.client.okx_dashboard_page_okx_signal_input = }')
