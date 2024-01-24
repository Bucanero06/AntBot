from pprint import pprint

from fastapi import APIRouter, HTTPException
from jose import JWTError

from firebase_tools.authenticate import check_token_validity
from pyokx.data_structures import InstrumentStatusReport, InstIdSignalRequestForm, PremiumIndicatorSignalRequestForm
from pyokx.signal_handling import okx_premium_indicator
from redis_tools.utils import serialize_for_redis
from routers.okx_authentication import check_token_against_instrument

okx_router = APIRouter(tags=["OKX"])

from fastapi import Depends, status

from routers import async_redis


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
    except JWTError:
        raise credentials_exception
    # except AssertionError:
    #     raise credentials_exception
    # except HTTPException:
    #     raise credentials_exception
    except Exception as e:
        print(f"Exception in okx_antbot_webhook: {e}")
        # return {"detail": "okx signal received but there was an exception, check the logs", "exception": str(e)}
        raise credentials_exception
    from pyokx.signal_handling import okx_signal_handler
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


@okx_router.get(path="/okx/highest_volume_ticker/{symbol}", status_code=status.HTTP_200_OK)
async def okx_highest_volume_ticker(symbol: str,
                                    current_user=Depends(check_token_validity),
                                    ):
    from pyokx.signal_handling import get_ticker_with_higher_volume
    return get_ticker_with_higher_volume(symbol)


@okx_router.get(path="/okx/instID/{instID}", status_code=status.HTTP_200_OK)
async def okx_instID_status(instID: str,
                            TD_MODE='isolated',
                            current_user=Depends(check_token_validity),
                            ):
    assert TD_MODE == 'isolated', f"TD_MODE {TD_MODE} is currently not supported by this endpoint, try \'isolated\'"

    from pyokx.signal_handling import fetch_status_report_for_instrument
    return fetch_status_report_for_instrument(instID, TD_MODE)


@okx_router.post(path="/tradingview/premium_indicator", status_code=status.HTTP_200_OK)
async def okx_premium_indicator_handler(indicator_input: PremiumIndicatorSignalRequestForm):
    redis_ready_message = serialize_for_redis(indicator_input.model_dump())
    await async_redis.xadd(f'okx:webhook@premium_indicator@input', fields=redis_ready_message)
    result = okx_premium_indicator(indicator_input)
    if isinstance(result, dict):
        await async_redis.xadd(f'okx:webhook@premium_indicator@result', fields=serialize_for_redis(result))
    return result
