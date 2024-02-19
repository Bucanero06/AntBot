

"""
PLEASE REFER TO OKX_MARKET_MAKER, THIS MODULE IS UNDER CONSTRUCTION BASED ON THAT EXAMPLE AND THE CURRENT
IMPLEMENTATION OF ANTBOT WHICH HAS BEEN GENERATED FROM THE OKX_MARKET_MAKER EXAMPLE
"""
from redis_tools.consumers import on_stream_data


@on_stream_data("okx:websockets@positions")
async def listen_position_stream(data):
    print(f"Listening to position stream: {data}")

@on_stream_data("okx:websockets@account")
async def listen_account_stream(data):
    print(f"Listening to account stream: {data}")

@on_stream_data("okx:websockets@orders")
async def listen_orders_stream(data):
    print(f"Listening to orders stream: {data}")

@on_stream_data("okx:websockets@fills")
async def listen_fills_stream(data):
    print(f"Listening to fills stream: {data}")

