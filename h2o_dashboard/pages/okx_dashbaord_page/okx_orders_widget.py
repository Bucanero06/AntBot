from typing import List

from h2o_wave import Q, ui, on, data, run_on, AsyncSite, pack  # noqa F401

from h2o_dashboard.util import add_card, convert_to_col_type
from pyokx.redis_structured_streams import get_stream_okx_order_messages
from pyokx.ws_data_structures import OrdersChannel, WSOrder


class OKX_Orders_StreamWidget:

    def __init__(self, q: Q, card_name: str, box: str, history_count: int = 10):
        self.q = q
        self.history_count = history_count
        self.orders_stream: List[OrdersChannel] = []
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

    async def _update_stream(self):
        self.orders_stream: List[OrdersChannel] = await get_stream_okx_order_messages(
            async_redis=self.q.client.async_redis, count=self.history_count)
        return self.orders_stream

    async def _is_initialized(self):
        return len(self.orders_stream) > 0

    async def get_ui_orders_table(self, box: str):
        if await self._is_initialized():
            last_n_orders_data: List[WSOrder] = [order.data[0] for order in self.orders_stream]
            last_n_orders_data = last_n_orders_data[::-1]
        else:
            last_n_orders_data = []
        items = []
        labels = []
        for order in last_n_orders_data:
            label_value = ''
            values = []
            newest_update = True
            for i, (col_key, col_value) in enumerate(self.okx_order_column_mappings.items()):
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
        return ui.stat_table_card(
            box=box,
            title=f'Last N orders messages - okx:websockets@orders (DEPRECATED FOR ORDERHISTORY STREAMS)',
            columns=[col_value['label'] for col_value in self.okx_order_column_mappings.values()],
            items=items
        )

    async def add_cards(self):
        await self._update_stream()
        await add_card(self.q, self.card_name + '_orders_table',
                       await self.get_ui_orders_table(box=self.box))
        await self.q.page.save()

    async def update_cards(self):
        await self._update_stream()
        if await self._is_initialized():
            last_n_orders_data: List[WSOrder] = [order.data[0] for order in self.orders_stream]
            last_n_orders_data = last_n_orders_data[::-1]
        else:
            last_n_orders_data = []

        orders_table_card: ui.stat_table_card = self.q.page[self.card_name + '_orders_table']
        items = []
        labels = []
        for order in last_n_orders_data:
            label_value = ''
            values = []
            newest_update = True
            for i, (col_key, col_value) in enumerate(self.okx_order_column_mappings.items()):
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
