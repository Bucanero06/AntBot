from pyokx.data_structures import CandleStick
from pyokx.entry_way import marketAPI


candles = marketAPI.get_history_candlesticks(instId='BTC-USDT-240628',
                                             before='',
                                             bar='',
                                             limit=''
                                             )

if candles['code'] !='0':
    print(f'Error!! ==> {candles = }')

while

# structured_candles = []
# for candlestick in candles['data']:
#     structured_candle = CandleStick(
#         timestamp=candlestick[0],
#         open=candlestick[1],
#         high=candlestick[2],
#         low=candlestick[3],
#         close=candlestick[4],
#         is_closed=candlestick[5]
#     )
#     structured_candles.append(structured_candle)
#
# print(f'{structured_candles = }')


