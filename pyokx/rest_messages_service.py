
import asyncio
import os
import traceback
from typing import List

from pyokx import ENFORCED_INSTRUMENT_TYPE
from pyokx.data_structures import FillEntry, FillHistoricalMetricsEntry, FillHistoricalMetrics
from pyokx.low_rest_api.exceptions import OkxAPIException, OkxParamsException, OkxRequestException
from pyokx.okx_market_maker.utils.OkxEnum import InstType
from pyokx.rest_handling import fetch_fill_history, InstrumentSearcher
from redis_tools.utils import init_async_redis, serialize_for_redis
from shared import logging
from shared.tmp_shared import get_timestamp_from_days_ago

logger = logging.setup_logger("okx_rest_messages_service")
REDIS_STREAM_MAX_LEN = int(os.getenv('REDIS_STREAM_MAX_LEN', 1000))


async def analyze_transaction_history(instType: InstType = ENFORCED_INSTRUMENT_TYPE):
    """
    Analyzes the transaction history for a given instrument type over the last 90 days.

    This function fetches the fill history, calculates various metrics for different timeframes,
    and stores the results in a Redis stream.

    :param instType: The type of instrument to analyze (e.g., 'FUTURES'). Default is 'FUTURES'.
    :type instType: InstType
    """
    # When using this endpoint, the maximum time range is 90 days
    start_timestamp = get_timestamp_from_days_ago(days_ago=90)
    end_timestamp = get_timestamp_from_days_ago()
    fill_history: List[FillEntry] = await fetch_fill_history(start_timestamp, end_timestamp, instType)
    redis_ready_message = serialize_for_redis(fill_history)
    await async_redis.xadd('okx:rest@fill@3months', {'data': redis_ready_message}, maxlen=1)

    timeframes = {
        "ONE_DAY": 1,
        "ONE_WEEK": 7,
        "ONE_MONTH": 30,
        "THREE_MONTHS": 90
    }

    _fill_metrics = {}
    for timeframe in timeframes:
        print("timeframe:", timeframe)
        start_query_timestamp = get_timestamp_from_days_ago(days_ago=timeframes[timeframe])
        end_query_timestamp = get_timestamp_from_days_ago()

        # Initialize variables
        total_fill_sz = 0
        total_fill_pnl = 0
        total_fill_fee = 0
        count = 0  # Count the number of entries in the desired time range

        for fill in fill_history:
            fill_time = int(fill.fillTime)
            if start_query_timestamp <= fill_time <= end_query_timestamp:
                total_fill_sz += float(fill.fillSz)
                total_fill_pnl += float(fill.fillPnl)
                total_fill_fee += float(fill.fee)
                count += 1

        # Calculate averages and total
        avg_fill_pnl = total_fill_pnl / count if count else 0
        total_fill_pnl = round(total_fill_pnl, 2)
        total_fill_fee = round(total_fill_fee, 2)

        # Print the results
        print("avg_fill_pnl:", avg_fill_pnl)
        print("total_fill_pnl:", total_fill_pnl)
        print("total_fill_fee:", total_fill_fee)
        print("count:", count)

        _fill_metrics[timeframe] = FillHistoricalMetricsEntry(
            avg_fill_pnl=avg_fill_pnl,
            total_fill_pnl=total_fill_pnl,
            total_fill_fee=total_fill_fee
        )

    fill_metrics = FillHistoricalMetrics(**_fill_metrics)
    redis_ready_message = serialize_for_redis(fill_metrics)
    await async_redis.xadd('okx:reports@fill_metrics', {'data': redis_ready_message}, maxlen=1)


async def update_instruments(okx_futures_instrument_searcher: InstrumentSearcher,
                             instrument_type: str = ENFORCED_INSTRUMENT_TYPE):
    instrument_map = await okx_futures_instrument_searcher.update_instruments()
    redis_ready_message = serialize_for_redis(instrument_map)
    await async_redis.xadd(f'okx:rest@{instrument_type.lower()}-instruments', {'data': redis_ready_message},
                           maxlen=REDIS_STREAM_MAX_LEN)


async def okx_rest_messages_services(reload_interval: int = 30):
    """
    Main service loop for processing OKX REST messages.

    This function initializes the Redis connection and enters a loop that, at each interval,
    calls `analyze_transaction_history` to analyze and store the last 90 days of transaction history.
    Handles exceptions and logs them accordingly.

    :param reload_interval: The interval in seconds between each iteration of the loop. Default is 30 seconds.
    :type reload_interval: int
    """
    print("Starting okx_rest_messages_services")
    global async_redis
    async_redis = await init_async_redis()
    assert async_redis, "async_redis is None, check the connection to the Redis server"

    okx_futures_instrument_searcher = InstrumentSearcher(ENFORCED_INSTRUMENT_TYPE)
    while True:
        try:
            await asyncio.gather(

                analyze_transaction_history(ENFORCED_INSTRUMENT_TYPE),  # by default, analyze and store the last 90 days for futures
                update_instruments(okx_futures_instrument_searcher, ENFORCED_INSTRUMENT_TYPE)
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


if __name__ == "__main__":
    asyncio.run(okx_rest_messages_services())
