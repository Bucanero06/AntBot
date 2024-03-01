import asyncio
import os
import traceback
from typing import List

import pandas as pd

from pyokx import ENFORCED_INSTRUMENT_TYPES
from pyokx.data_structures import FillEntry, FillHistoricalMetrics
from pyokx.low_rest_api.exceptions import OkxAPIException, OkxParamsException, OkxRequestException
from pyokx.OkxEnum import InstType
from pyokx.rest_handling import fetch_fill_history, InstrumentSearcher, fetch_incomplete_algo_orders, \
    fetch_incomplete_orders
from redis_tools.utils import get_async_redis, serialize_for_redis
from shared import logging
from shared.tmp_shared import get_timestamp_from_days_ago

logger = logging.setup_logger("okx_rest_messages_service")
REDIS_STREAM_MAX_LEN = int(os.getenv('REDIS_STREAM_MAX_LEN', 1000))


async def analyze_transaction_history(InstTypes: List[InstType] = ENFORCED_INSTRUMENT_TYPES):
    """
    Analyzes the transaction history for a given instrument type over the last 90 days.

    This function fetches the fill history, calculates various metrics for different timeframes,
    and stores the results in a Redis stream.

    :param InstTypes: The type of instruments to analyze (e.g., 'FUTURES'). Default is ['FUTURES', 'SWAP'].
    :type InstTypes: List[InstType]
    """
    # When using this endpoint, the maximum time range is 90 days
    start_timestamp = get_timestamp_from_days_ago(days_ago=90)
    end_timestamp = get_timestamp_from_days_ago()
    fill_history: List[FillEntry] = []
    for _instType in InstTypes:
        _fill_history: List[FillEntry] = await fetch_fill_history(start_timestamp, end_timestamp, _instType)
        fill_history.extend(_fill_history)

    redis_ready_message = serialize_for_redis(fill_history)
    await async_redis.xadd('okx:rest@fill@3months', {'data': redis_ready_message}, maxlen=1)

    fill_history_ = [fill.model_dump() for fill in fill_history]
    df = pd.DataFrame(fill_history_)

    # Fix types for all columns
    df['side'] = df['side'].astype(str)
    df['fillSz'] = df['fillSz'].astype(float)
    df['fillPx'] = df['fillPx'].astype(float)
    df['fee'] = df['fee'].astype(float)
    df['fillPnl'] = df['fillPnl'].astype(float)
    df['ordId'] = df['ordId'].astype(str)
    df['instType'] = df['instType'].astype(str)
    df['instId'] = df['instId'].astype(str)
    df['clOrdId'] = df['clOrdId'].astype(str)
    df['posSide'] = df['posSide'].astype(str)
    df['billId'] = df['billId'].astype(str)
    df['fillTime'] = df['fillTime'].astype(int)
    df['execType'] = df['execType'].astype(str)
    df['tradeId'] = df['tradeId'].astype(str)
    df['feeCcy'] = df['feeCcy'].astype(str)
    df['ts'] = df['ts'].astype(str)

    # Drop the other columns for now
    df.drop(columns=['fillPxVol', 'fillFwdPx', 'fillPxUsd', 'fillMarkVol', 'tag', 'fillIdxPx', 'fillMarkPx'],
            inplace=True)

    # Lets do it per instrument that we have and break it down into timeframes of 1 day, 1 week, 1 month, 3 months
    timeframes = {
        "ONE_DAY": 1,
        "ONE_WEEK": 7,
        "ONE_MONTH": 30,
        "THREE_MONTHS": 90
    }

    unique_instruments = df['instId'].unique()
    returning_fill_historical_metrics_dict = {}

    for timeframe in timeframes:
        returning_fill_historical_metrics_dict[timeframe] = []
        start_query_timestamp = get_timestamp_from_days_ago(days_ago=timeframes[timeframe])
        end_query_timestamp = get_timestamp_from_days_ago()

        for instrument in unique_instruments:
            print(f"Analyzing instrument: {instrument} for timeframe: {timeframe}")
            instrument_df = df[df['instId'] == instrument]

            # Filter by time
            instrument_df = instrument_df[(instrument_df['fillTime'] >= start_query_timestamp) & (
                        instrument_df['fillTime'] <= end_query_timestamp)]

            volume_traded = instrument_df['fillSz'].sum()
            average_fill_price = (instrument_df['fillPx'] * instrument_df['fillSz']).sum() / volume_traded
            profit_loss = instrument_df['fillPnl'].sum()
            fees_paid = instrument_df['fee'].sum()
            profitable_trades = instrument_df[instrument_df['fillPnl'] > 0].shape[0]
            loss_making_trades = instrument_df[instrument_df['fillPnl'] < 0].shape[0]
            best_trade = instrument_df['fillPnl'].max()
            worst_trade = instrument_df['fillPnl'].min()
            avg_fill_pnl = profit_loss / (profitable_trades + loss_making_trades)

            returning_fill_historical_metrics_dict[timeframe].append({
                "instrument_id": instrument,
                "volume_traded": volume_traded,
                "average_fill_price": average_fill_price,
                "profit_loss": profit_loss,
                "fees_paid": fees_paid,
                "profitable_trades": profitable_trades,
                "loss_making_trades": loss_making_trades,
                "best_trade": best_trade,
                "worst_trade": worst_trade,
                "avg_fill_pnl": avg_fill_pnl,
            })

    # Validate results
    fill_metrics = FillHistoricalMetrics(**returning_fill_historical_metrics_dict)
    redis_ready_message = serialize_for_redis(fill_metrics)
    await async_redis.xadd('okx:reports@fill_metrics', {'data': redis_ready_message}, maxlen=1)


async def update_instruments(okx_instrument_searcher: InstrumentSearcher):
    instrument_map = await okx_instrument_searcher.update_instruments()
    redis_ready_message = serialize_for_redis(instrument_map)
    await async_redis.xadd(f'okx:rest@instruments', {'data': redis_ready_message},
                           maxlen=1)


async def slow_polling_service(reload_interval: int = 30):
    okx_instrument_searcher = InstrumentSearcher(ENFORCED_INSTRUMENT_TYPES)
    while True:
        try:
            await asyncio.gather(
                # by default, analyze and store the last 90 days for futures
                analyze_transaction_history(ENFORCED_INSTRUMENT_TYPES),
                update_instruments(okx_instrument_searcher)
            )
        except KeyboardInterrupt:
            break
        except (OkxAPIException, OkxParamsException, OkxRequestException):
            logger.warning(traceback.format_exc())
            continue
        except Exception:
            logger.error(traceback.format_exc())
            continue
        finally:
            print(f"Sleeping for {reload_interval} seconds")
            await asyncio.sleep(reload_interval)


async def loop_fetch_incomplete_algo_orders(reload_interval: int = 0.2):
    while True:
        try:
            algo_orders = await fetch_incomplete_algo_orders()
            redis_ready_message = serialize_for_redis(algo_orders)
            await async_redis.xadd('okx:rest@algo-orders', {'data': redis_ready_message}, maxlen=1)
        except KeyboardInterrupt:
            break
        except (OkxAPIException, OkxParamsException, OkxRequestException):
            logger.warning(traceback.format_exc())
            continue
        except Exception:
            logger.error(traceback.format_exc())
            continue
        finally:
            print(f"Sleeping loop_fetch_incomplete_algo_orders for {reload_interval} seconds")
            await asyncio.sleep(reload_interval)


async def loop_fetch_incomplete_orders(reload_interval: int = 0.2):
    while True:
        try:
            orders = await fetch_incomplete_orders()
            redis_ready_message = serialize_for_redis(orders)
            await async_redis.xadd('okx:rest@orders', {'data': redis_ready_message}, maxlen=1)
        except KeyboardInterrupt:
            break
        except (OkxAPIException, OkxParamsException, OkxRequestException):
            logger.warning(traceback.format_exc())
            continue
        except Exception:
            logger.error(traceback.format_exc())
            continue
        finally:
            await asyncio.sleep(reload_interval)


async def okx_rest_messages_services(slow_reload_interval: int = 30):
    """
    Main service loop for processing OKX REST messages.

    This function initializes the Redis connection and enters a loop that, at each interval,
    calls `analyze_transaction_history` to analyze and store the last 90 days of transaction history.
    Handles exceptions and logs them accordingly.

    :param slow_reload_interval: The interval in seconds between each iteration of the loop. Default is 30 seconds.
    :type slow_reload_interval: int
    """
    print("Starting okx_rest_messages_services")
    global async_redis
    async_redis = await get_async_redis()

    assert async_redis, "async_redis is None, check the connection to the Redis server"
    slow_polling_task = asyncio.create_task(slow_polling_service(slow_reload_interval))
    loop_fetch_incomplete_algo_orders_task = asyncio.create_task(loop_fetch_incomplete_algo_orders())
    loop_fetch_incomplete_orders_task = asyncio.create_task(loop_fetch_incomplete_orders())
    await asyncio.gather(slow_polling_task, loop_fetch_incomplete_algo_orders_task, loop_fetch_incomplete_orders_task)


if __name__ == "__main__":
    asyncio.run(okx_rest_messages_services())
