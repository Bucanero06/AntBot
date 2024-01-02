from fastapi import APIRouter
from jose import JWTError

from firebase_tools.authenticate import check_token_validity
# from model.okx import InstrumentStatusReportModel, OrderModel, AlgoOrderModel, PositionModel
from pyokx.data_structures import InstrumentStatusReport, InstIdSignalRequestForm
from routers.api_keys import check_token_against_instrument
from fastapi import APIRouter, Depends, HTTPException, status

okx_router = APIRouter(tags=["okx"])

from fastapi import Depends, status
from sqlalchemy.orm import Session
from data.config import get_db


@okx_router.post(path="/okx", status_code=status.HTTP_202_ACCEPTED)
async def okx_antbot_webhook(signal_input: InstIdSignalRequestForm,
                       # db: Session = Depends(get_db),
                       # current_user: CurrentUser = Depends(get_current_user)
                       ):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="credentials invalid",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        valid = check_token_against_instrument(token=signal_input.InstIdAPIKey,
                                               reference_instID=signal_input.SignalInput.instID,
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
        return {"detail": "okx signal received but there was an exception, check the logs", "exception": str(e)}

    from pyokx.entry_way import okx_signal_handler
    try:
        assert signal_input.SignalInput, "SignalInput is None"
        okx_signal_input = signal_input.SignalInput
        instrument_status_report: InstrumentStatusReport = okx_signal_handler(**okx_signal_input.model_dump())
        from pprint import pprint
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

# endpoint to find the highest instID from symbol
@okx_router.get(path="/okx/highest_instID/{symbol}", status_code=status.HTTP_200_OK)
async def okx_highest_instID(symbol: str,
                             current_user = Depends(check_token_validity),
                             ):
    from pyokx.entry_way import get_ticker_with_higher_volume
    return get_ticker_with_higher_volume(symbol)