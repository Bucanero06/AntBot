from typing import List, Dict, Optional


from pyokx import publicAPI, ENFORCED_INSTRUMENT_TYPES
from pyokx.data_structures import Instrument
from pyokx.okx_market_maker.utils.OkxEnum import InstType


class InstrumentSearcher:
    """
    Provides functionality to search for instruments within a provided list of instruments based on various criteria
    such as instrument ID, type, or underlying asset.

    Args:
        instruments (List[Instrument]): A list of instruments to search within.

    Methods:
        find_by_instId: Returns an instrument matching a specific instrument ID.
        find_by_type: Returns all instruments of a specific type.
        find_by_underlying: Returns all instruments with a specific underlying asset.
    """

    def __init__(self, instTypes=ENFORCED_INSTRUMENT_TYPES, _instrument_map=None):
        """
        InstrumentSearcher is a class that allows you to search for instruments by instId, instType, or underlying

        :param instruments:

        Usage:
        ```
        okx_instrument_searcher = InstrumentSearcher(all_futures_instruments)
        print(f'{okx_instrument_searcher.find_by_instId("BTC-USDT-240329") = }')
        print(f'{okx_instrument_searcher.find_by_type(InstType.FUTURES) = }')
        print(f'{okx_instrument_searcher.find_by_underlying("BTC-USDT") = }')
        print(f'{"BTC-USDT-240329" in okx_instrument_searcher._instrument_map = }')
        ```
        """
        self.instTypes = instTypes
        if _instrument_map is None:
            self.instruments = self.request_instruments()
            self._instrument_map = self._create_map(self.instruments)
        else:
            self._instrument_map = _instrument_map
            self.instruments = list(_instrument_map.values())

    def request_instruments(self):
        instruments = []
        for instTypes in self.instTypes:
            returned_data = publicAPI.get_instruments(instType=instTypes)
            if len(returned_data['data']) == 0:
                if returned_data["code"] != '0':
                    print(f'{returned_data["code"] = }')
                    print(f'{returned_data["msg"] = }')
                _instruments = []
            else:
                _instruments = []
                for data in returned_data['data']:
                    _instruments.append(Instrument(**data))
            instruments.extend(_instruments)

        return instruments

    def _create_map(self, instruments: List[Instrument]) -> Dict[str, Instrument]:
        """ Create a map for quicker search by instId """
        return {instrument.instId: instrument for instrument in instruments}

    def find_by_instId(self, instId: str) -> Optional[Instrument]:
        """ Find an instrument by its instId """
        instrument=self._instrument_map.get(instId)
        if instrument:
            return instrument if isinstance(instrument, Instrument) else Instrument(**instrument)
        else:
            return None
    def find_by_type(self, instType: InstType) -> List[Instrument]:
        """ Find all instruments of a specific type """
        return [instrument for instrument in self.instruments if instrument.instType == instType]

    def find_by_underlying(self, underlying: str) -> List[Instrument]:
        """ Find all instruments of a specific underlying """
        return [instrument for instrument in self.instruments if instrument.uly == underlying]

    def get_instrument_ids(self) -> List[str]:
        """ Get all instrument IDs """
        return list(self._instrument_map.keys())

    async def update_instruments(self):
        """ Update the instruments list """
        self.instruments = self.request_instruments()
        self._instrument_map = self._create_map(self.instruments)

        return self._instrument_map
