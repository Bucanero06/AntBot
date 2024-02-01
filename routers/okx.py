# Copyright (c) 2024 Carbonyl LLC & Carbonyl R&D
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import os
from pprint import pprint

from fastapi import APIRouter, HTTPException
from jose import JWTError
from pydantic import BaseModel

from firebase_tools.authenticate import check_token_validity
from pyokx.data_structures import InstrumentStatusReport, InstIdSignalRequestForm, PremiumIndicatorSignalRequestForm
from pyokx.rest_handling import okx_premium_indicator
from redis_tools.utils import serialize_for_redis, init_async_redis
from routers.okx_authentication import check_token_against_instrument

okx_router = APIRouter(tags=["OKX"])

from fastapi import Depends, status


REDIS_STREAM_MAX_LEN = int(os.getenv('REDIS_STREAM_MAX_LEN', 1000))


@okx_router.post(path="/okx_antbot_signal", status_code=status.HTTP_202_ACCEPTED)
async def okx_antbot_webhook(signal_input: InstIdSignalRequestForm):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="credentials invalid",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        valid = check_token_against_instrument(token=signal_input.InstIdAPIKey,
                                               reference_instID=signal_input.OKXSignalInput.instID,
                                               )
        assert valid == True, "InstIdAPIKey verification failed"
    except JWTError as e:
        print(f"JWTError in okx_antbot_webhook: {e}")
        raise credentials_exception
    except AssertionError as e:
        print(f"AssertionError in okx_antbot_webhook: {e}")
        raise credentials_exception
    except HTTPException as e:
        print(f"HTTPException in okx_antbot_webhook: {e}")
        raise credentials_exception
    except Exception as e:
        print(f"Exception in okx_antbot_webhook: {e}")
        raise credentials_exception
    from pyokx.rest_handling import okx_signal_handler
    try:
        assert signal_input.OKXSignalInput, "OKXSignalInput is None"
        okx_signal_input = signal_input.OKXSignalInput
        instrument_status_report: InstrumentStatusReport = okx_signal_handler(**okx_signal_input.model_dump())
        pprint(instrument_status_report)
        assert instrument_status_report, "Instrument Status Report is None, check the Instrument ID"

    except Exception as e:
        print(f"Exception in okx_antbot_webhook: {e}")
        return {"detail": "okx signal received but there was an exception, check the logs", "exception": str(e)}

    if instrument_status_report:
        # instrument_status_model = InstrumentStatusReportModel(
        #     timestamp=instrument_status_report.timestamp,
        #     instID=instrument_status_report.instID,
        #     # orders=instrument_status_report.orders,
        #     # positions=instrument_status_report.positions,
        #     # algo_orders=instrument_status_report.algo_orders
        #     orders=[OrderModel(**order) for order in instrument_status_report.orders],
        #     positions=[PositionModel(**position) for position in instrument_status_report.positions],
        #     algo_orders=[AlgoOrderModel(**algo_order) for algo_order in instrument_status_report.algo_orders]
        # )
        # db.add(instrument_status_model)
        # db.commit()
        # db.refresh(instrument_status_model)
        return {"detail": "okx signal and report received"}
    else:
        return {"detail": "okx signal received but no report returned"}

    # Update the enxchange info on the database
    return {"detail": "okx signal received"}

@okx_router.post(path="/tradingview/premium_indicator", status_code=status.HTTP_200_OK)
async def okx_premium_indicator_handler(indicator_input: PremiumIndicatorSignalRequestForm):
    async_redis = await init_async_redis()
    redis_ready_message = serialize_for_redis(indicator_input.model_dump())
    await async_redis.xadd(f'okx:webhook@premium_indicator@input', {'data': redis_ready_message},
                           maxlen=REDIS_STREAM_MAX_LEN)
    result = okx_premium_indicator(indicator_input)
    if isinstance(result, (dict, list, tuple, BaseModel)):
        await async_redis.xadd(f'okx:webhook@premium_indicator@result', {'data': serialize_for_redis(result)},
                               maxlen=REDIS_STREAM_MAX_LEN)
    return result
@okx_router.get(path="/okx/highest_volume_ticker/{symbol}", status_code=status.HTTP_200_OK)
async def okx_highest_volume_ticker(symbol: str,
                                    current_user=Depends(check_token_validity),
                                    ):
    from pyokx.rest_handling import get_ticker_with_higher_volume
    return get_ticker_with_higher_volume(symbol)


@okx_router.get(path="/okx/instID/{instID}", status_code=status.HTTP_200_OK)
async def okx_instID_status(instID: str,
                            TD_MODE='isolated',
                            current_user=Depends(check_token_validity),
                            ):
    assert TD_MODE == 'isolated', f"TD_MODE {TD_MODE} is currently not supported by this endpoint, try \'isolated\'"

    from pyokx.rest_handling import fetch_status_report_for_instrument
    return fetch_status_report_for_instrument(instID, TD_MODE)



