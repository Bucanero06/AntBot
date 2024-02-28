from typing import List

from h2o_wave import Q, ui, on, data, run_on, AsyncSite, pack  # noqa F401

from h2o_dashboard.util import add_card, convert_to_col_type
from pyokx.data_structures import Algo_Order
from pyokx.redis_structured_streams import get_stream_okx_incomplete_algo_orders


class OKX_Orders_StreamWidget:

    def __init__(self, q: Q, card_name: str, box: str):
        self.q = q
        self.algo_orders_rest_stream: List[List[Algo_Order]] = []
        self.card_name = card_name
        self.box = box

        self.okx_order_column_mappings = dict(
            ordId={'label': 'Order ID', 'type': 'str'},
            instId={'label': 'Instrument ID', 'type': 'str'},
            state={'label': 'State', 'type': 'str'},
            pnl={'label': 'Profit/Loss', 'type': 'float'},
            sz={'label': 'Size', 'type': 'float'},
            fillSz={'label': 'Fill Size', 'type': 'float'},
            side={'label': 'Side', 'type': 'str'},
            ordType={'label': 'Type', 'type': 'str'},
            avgPx={'label': 'Avg Price', 'type': 'float'},
            fee={'label': 'Fee', 'type': 'float'},
            fillFee={'label': 'Fill Fee', 'type': 'float'},
            lever={'label': 'Leverage', 'type': 'float'},
            # slOrdPx={'label': 'SL Order Price', 'type': 'float'},
            # slTriggerPx={'label': 'SL Trigger Price', 'type': 'float'},
            # tpOrdPx={'label': 'TP Order Price', 'type': 'float'},
            # tpTriggerPx={'label': 'TP Trigger Price', 'type': 'float'},
            execType={'label': 'ExecType', 'type': 'str'},
            feeCcy={'label': 'Fee Currency', 'type': 'str'},
            fillPnl={'label': 'Fill Profit/Loss', 'type': 'float'},
            fillFeeCcy={'label': 'Fill Fee Currency', 'type': 'str'},
            msg={'label': 'Message', 'type': 'str'},
            cancelSource={'label': 'Cancel Source', 'type': 'str'},

            cTime={'label': 'cTime', 'type': 'timestamp'},
            uTime={'label': 'uTime', 'type': 'timestamp'},
        )

        self.okx_order_column_mappings = dict(
            ordId={'label': 'Order ID', 'type': 'str'},
            instId={'label': 'Instrument ID', 'type': 'str'},
            state={'label': 'State', 'type': 'str'},
            pnl={'label': 'Profit/Loss', 'type': 'float'},
            sz={'label': 'Size', 'type': 'float'},
            fillSz={'label': 'Fill Size', 'type': 'float'},
            side={'label': 'Side', 'type': 'str'},
            ordType={'label': 'Type', 'type': 'str'},
            avgPx={'label': 'Avg Price', 'type': 'float'},
            fee={'label': 'Fee', 'type': 'float'},
            fillFee={'label': 'Fill Fee', 'type': 'float'},
            lever={'label': 'Leverage', 'type': 'float'},
            # slOrdPx={'label': 'SL Order Price', 'type': 'float'},
            # slTriggerPx={'label': 'SL Trigger Price', 'type': 'float'},
            # tpOrdPx={'label': 'TP Order Price', 'type': 'float'},
            # tpTriggerPx={'label': 'TP Trigger Price', 'type': 'float'},
            execType={'label': 'ExecType', 'type': 'str'},
            feeCcy={'label': 'Fee Currency', 'type': 'str'},
            fillPnl={'label': 'Fill Profit/Loss', 'type': 'float'},
            fillFeeCcy={'label': 'Fill Fee Currency', 'type': 'str'},
            msg={'label': 'Message', 'type': 'str'},
            cancelSource={'label': 'Cancel Source', 'type': 'str'},

            cTime={'label': 'cTime', 'type': 'timestamp'},
            uTime={'label': 'uTime', 'type': 'timestamp'},
        )

        self.okx_algo_order_column_mappings = dict(
            algoClOrdId={'label': 'Order ID', 'type': 'str'},
            instId={'label': 'Instrument ID', 'type': 'str'},
            state={'label': 'State', 'type': 'str'},
            # pnl={'label': 'Profit/Loss', 'type': 'float'},
            sz={'label': 'Size', 'type': 'float'},
            # fillSz={'label': 'Fill Size', 'type': 'float'},
            side={'label': 'Side', 'type': 'str'},
            ordType={'label': 'Type', 'type': 'str'},
            # avgPx={'label': 'Avg Price', 'type': 'float'},
            # fee={'label': 'Fee', 'type': 'float'},
            # fillFee={'label': 'Fill Fee', 'type': 'float'},
            lever={'label': 'Leverage', 'type': 'float'},
            ordPx={'label': 'Exec Price', 'type': 'float'},
            triggerPx={'label': 'Trigger Price', 'type': 'float'},
            # slOrdPx={'label': 'SL Order Price', 'type': 'float'},
            # slTriggerPx={'label': 'SL Trigger Price', 'type': 'float'},
            # tpOrdPx={'label': 'TP Order Price', 'type': 'float'},
            # tpTriggerPx={'label': 'TP Trigger Price', 'type': 'float'},
            # execType={'label': 'ExecType', 'type': 'str'},
            # feeCcy={'label': 'Fee Currency', 'type': 'str'},
            # fillPnl={'label': 'Fill Profit/Loss', 'type': 'float'},
            # fillFeeCcy={'label': 'Fill Fee Currency', 'type': 'str'},
            # msg={'label': 'Message', 'type': 'str'},
            # cancelSource={'label': 'Cancel Source', 'type': 'str'},

            cTime={'label': 'cTime', 'type': 'timestamp'},
            # uTime={'label': 'uTime', 'type': 'timestamp'},
        )

    async def _update_stream(self):
        self.algo_orders_rest_stream: List[List[Algo_Order]] = await get_stream_okx_incomplete_algo_orders(
            async_redis=self.q.client.async_redis)
        return self.algo_orders_rest_stream

    async def _is_initialized(self):
        return len(self.algo_orders_rest_stream) > 0

    async def get_ui_algo_orders_table(self, box: str):
        if await self._is_initialized():
            last_n_orders_data: List[Algo_Order] = self.algo_orders_rest_stream[-1]
        else:
            print('Not initialized')
            last_n_orders_data = []

        print(f'last_n_orders_data: {last_n_orders_data}')
        items = []
        labels = []
        for order in last_n_orders_data:
            label_value = ''
            values = []
            newest_update = True
            for i, (col_key, col_value) in enumerate(self.okx_algo_order_column_mappings.items()):
                if i == 0:
                    label_value = f'{getattr(order, col_key)}'
                    if label_value in labels:
                        newest_update = False
                        break
                    newest_update = True
                    labels.append(label_value)
                    continue
                order_col = getattr(order, col_key)
                expected_type = None
                try:
                    expected_type = col_value['type']
                    order_col = convert_to_col_type(order_col, expected_type)

                except ValueError:
                    print(f"Error converting {col_key} to {expected_type}")

                value = str(order_col)
                values.append(value)
            if newest_update:
                items.append(ui.stat_table_item(label=label_value, values=values))
        return ui.stat_table_card(
            box=box,
            title=f'Live Algo Orders - okx:rest@algo-orders (does not include completed or unfulfilled orders)',
            columns=[col_value['label'] for col_value in self.okx_algo_order_column_mappings.values()],
            items=items
        )

    async def add_cards(self):
        await self._update_stream()
        await add_card(self.q, self.card_name + '_orders_table',
                       await self.get_ui_algo_orders_table(box=self.box))
        await self.q.page.save()

    async def update_cards(self):
        if await self._is_initialized():
            last_n_orders_data: List[Algo_Order] = self.algo_orders_rest_stream[-1]
        else:
            print('Not initialized')
            last_n_orders_data = []

        orders_table_card: ui.stat_table_card = self.q.page[self.card_name + '_orders_table']
        items = []
        labels = []
        for order in last_n_orders_data:
            label_value = ''
            values = []
            newest_update = True
            for i, (col_key, col_value) in enumerate(self.okx_algo_order_column_mappings.items()):
                if i == 0:
                    label_value = f'{getattr(order, col_key)}'
                    if label_value in labels:
                        newest_update = False
                        break
                    newest_update = True
                    labels.append(label_value)
                    continue
                order_col = getattr(order, col_key)
                try:
                    expected_type = col_value['type']
                    order_col = convert_to_col_type(order_col, expected_type)

                except ValueError:
                    print(f"Error converting {col_key} to {expected_type}")

                value = str(order_col)
                values.append(value)

            if newest_update:
                items.append(ui.stat_table_item(label=label_value, values=values))
        orders_table_card.items = items
        await self.q.page.save()
