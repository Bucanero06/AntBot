import os
from typing import List

import pandas as pd
from dotenv import load_dotenv, find_dotenv

from pyokx.data_structures import FillEntry, FillHistoricalMetrics
from pyokx.redis_structured_streams import get_okx_fills_history
from redis_tools.config import RedisConfig
from redis_tools.utils import deserialize_from_redis, get_async_redis
from shared.tmp_shared import get_timestamp_from_days_ago

load_dotenv(find_dotenv())







import asyncio

async def main():
    async_redis = await get_async_redis()
    fills_stream = await get_okx_fills_history(async_redis, count=1)
    fill_history = fills_stream[-1]

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
            instrument_df = instrument_df[(instrument_df['fillTime'] >= start_query_timestamp) & (instrument_df['fillTime'] <= end_query_timestamp)]

            volume_traded = instrument_df['fillSz'].sum()
            average_fill_price = (instrument_df['fillPx'] * instrument_df['fillSz']).sum() / volume_traded
            profit_loss = instrument_df['fillPnl'].sum()
            fees_paid = instrument_df['fee'].sum()
            profitable_trades = instrument_df[instrument_df['fillPnl'] > 0].shape[0]
            loss_making_trades = instrument_df[instrument_df['fillPnl'] < 0].shape[0]
            best_trade = instrument_df['fillPnl'].max()
            worst_trade = instrument_df['fillPnl'].min()
            avg_fill_pnl = profit_loss / (profitable_trades + loss_making_trades)
            total_fill_pnl = profit_loss

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
                "total_fill_pnl": total_fill_pnl
            })

    # Validate results
    returning_fill_historical_metrics = FillHistoricalMetrics(**returning_fill_historical_metrics_dict)
    print(returning_fill_historical_metrics)

# To returns
asyncio.run(main())