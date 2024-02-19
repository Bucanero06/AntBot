
import os
from pprint import pprint

from fastapi import APIRouter, HTTPException
from jose import JWTError

from firebase_tools.authenticate import check_token_validity
from pyokx.data_structures import InstrumentStatusReport, InstIdSignalRequestForm, OKXPremiumIndicatorSignalRequestForm
from pyokx.rest_handling import okx_premium_indicator_handler
from redis_tools.utils import serialize_for_redis, init_async_redis
from routers.okx_authentication import check_token_against_instrument

okx_router = APIRouter(tags=["OKX"])

from fastapi import Depends, status

REDIS_STREAM_MAX_LEN = int(os.getenv('REDIS_STREAM_MAX_LEN', 1000))

@okx_router.post(path="/okx_antbot_signal", status_code=status.HTTP_202_ACCEPTED)
async def okx_antbot_webhook(signal_input: InstIdSignalRequestForm):
    print(f"Received signal from {signal_input.OKXSignalInput.instID}")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="credentials invalid",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        valid = await check_token_against_instrument(token=signal_input.InstIdAPIKey,
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
        async_redis = await init_async_redis()
        instrument_id = signal_input.OKXSignalInput.instID
        await async_redis.xadd(f'okx:webhook@okx_antbot_webhook@input@{instrument_id}',
                               {'data': serialize_for_redis(signal_input)},
                               maxlen=REDIS_STREAM_MAX_LEN)

        okx_signal_input = signal_input.OKXSignalInput
        instrument_status_report: InstrumentStatusReport = await okx_signal_handler(**okx_signal_input.model_dump())
        await async_redis.xadd(f'okx:webhook@okx_antbot_webhook@response@{instrument_id}',
                               {'data': serialize_for_redis(instrument_status_report)},
                               maxlen=REDIS_STREAM_MAX_LEN)
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


@okx_router.post(path="/tradingview/premium_indicator", status_code=status.HTTP_200_OK)
async def okx_premium_indicator_webhook(indicator_input: OKXPremiumIndicatorSignalRequestForm):
    from fastapi import HTTPException
    from starlette import status
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="credentials invalid",
        headers={"WWW-Authenticate": "Bearer"},
    )
    from jose import JWTError
    try:
        from routers.okx_authentication import check_token_against_instrument
        valid = await check_token_against_instrument(token=indicator_input.InstIdAPIKey,
                                                     reference_instID=indicator_input.OKXSignalInput.instID
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
        return {"detail": "okx signal received but there was an exception, check the logs", "exception": str(e)}

    async_redis = await init_async_redis()
    instrument_id = indicator_input.OKXSignalInput.instID
    await async_redis.xadd(f'okx:webhook@okx_premium_indicator@input@{instrument_id}',
                           {'data': serialize_for_redis(indicator_input)},
                           maxlen=REDIS_STREAM_MAX_LEN)
    returning_message = await okx_premium_indicator_handler(indicator_input)
    await async_redis.xadd(f'okx:webhook@okx_premium_indicator@response@{instrument_id}',
                           {'data': serialize_for_redis(returning_message)},
                           maxlen=REDIS_STREAM_MAX_LEN)
    return returning_message


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
