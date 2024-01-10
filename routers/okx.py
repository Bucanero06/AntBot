from pprint import pprint

from fastapi import APIRouter, HTTPException
from jose import JWTError

from firebase_tools.authenticate import check_token_validity
from pyokx.data_structures import InstrumentStatusReport, InstIdSignalRequestForm, PremiumIndicatorSignalRequestForm
from routers.okx_authentication import check_token_against_instrument

okx_router = APIRouter(tags=["OKX"])

from fastapi import Depends, status


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
        return {"detail": "okx signal received but there was an exception, check the logs", "exception": str(e)}

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
async def okx_premium_indicator(indicator_input: PremiumIndicatorSignalRequestForm):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="credentials invalid",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        valid = check_token_against_instrument(token=indicator_input.InstIdAPIKey,
                                               reference_instID=indicator_input.OKXSignalInput.instID
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

    try:
        pprint(f'{indicator_input.OKXSignalInput = }')
        pprint(f'{indicator_input.PremiumIndicatorSignals = }')

        # Interpret Signals
        premium_indicator = indicator_input.PremiumIndicatorSignals

        premium_indicator.Bearish = int(premium_indicator.Bearish)
        premium_indicator.Bearish_plus = int(premium_indicator.Bearish_plus)
        premium_indicator.Bullish = int(premium_indicator.Bullish)
        premium_indicator.Bullish_plus = int(premium_indicator.Bullish_plus)
        premium_indicator.Bearish_Exit = 0 if premium_indicator.Bearish_Exit == 'null' else float(
            premium_indicator.Bearish_Exit)
        premium_indicator.Bullish_Exit = 0 if premium_indicator.Bullish_Exit == 'null' else float(
            premium_indicator.Bullish_Exit)

        _order_side = None
        _close_signal = None
        if premium_indicator.Bearish or premium_indicator.Bearish_plus:
            _order_side = 'buy'
        elif premium_indicator.Bullish or premium_indicator.Bullish_plus:
            _order_side = 'sell'
        if premium_indicator.Bearish_Exit:
            _close_signal = 'exit_buy'
        elif premium_indicator.Bullish_Exit:
            _close_signal = 'exit_sell'

        # Get current positions
        from pyokx.signal_handling import get_all_positions
        instId_positions = get_all_positions(instId=indicator_input.OKXSignalInput.instID)
        if len(instId_positions) > 0:
            current_position = instId_positions[0]
            current_position_side = 'buy' if float(current_position.pos) > 0 else 'sell' if float(
                current_position.pos) < 0 else None  # we are only using net so only one position

            if _close_signal:
                buy_exit = _close_signal == 'exit_buy' and current_position_side == 'buy'
                sell_exit = _close_signal == 'exit_sell' and current_position_side == 'sell'
                if not (buy_exit or sell_exit):
                    _close_signal = None

        # TODO - IDEA: Logic here betweeen _close_signal and entry, if just a closing then it can be handled using market or limit orders but if it is an entry and exit then we decide depening on wehther the entry is in the same or opposite directoion and if flip on opposite order is true.
        #   lets assume that we are not flipping on opposite order  then cancel if entry in opposite direction and close_order then clear before starting, if just closing then trat them as an actual order which can be market post only or limits
        print(f'{_order_side or _close_signal = }')
        if _order_side or _close_signal:
            okx_signal = indicator_input.OKXSignalInput

            okx_signal.order_side = _order_side if _order_side else ''
            okx_signal.clear_prior_to_new_order = True if okx_signal.clear_prior_to_new_order or _close_signal else False

            pprint(f'updated-{premium_indicator = }')
            pprint(f'updated-{okx_signal= }')

            assert indicator_input.OKXSignalInput, "OKXSignalInput is None"
            okx_signal_input = indicator_input.OKXSignalInput
            from pyokx.signal_handling import okx_signal_handler
            instrument_status_report: InstrumentStatusReport = okx_signal_handler(**okx_signal_input.model_dump())
            pprint(instrument_status_report)
            assert instrument_status_report, "Instrument Status Report is None, check the Instrument ID"
        return {"detail": "okx signal received"}
    except Exception as e:
        print(f"Exception in okx_premium_indicator {e}")
        return {
            "detail": "okx premium indicator signal received but not handled yet",
            "exception": "okx premium indicator signal received but not handled yet"
        }

    # Update the enxchange info on the database
    return {"detail": "unexpected end of point??."}
