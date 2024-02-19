
from os import getenv
from pprint import pformat  # noqa F401

from pyokx.low_rest_api.Account import AccountAPI
from pyokx.low_rest_api.Funding import FundingAPI
from pyokx.low_rest_api.MarketData import MarketAPI
from pyokx.low_rest_api.PublicData import PublicAPI
from pyokx.low_rest_api.Trade import TradeAPI
from shared.logging import setup_logger

logger = setup_logger(__name__.split(".")[0])

import dotenv
dotenv.load_dotenv(dotenv.find_dotenv())

class OKX_Futures_Exchange_Client:

    def __init__(self, api_key=None, api_secret=None, passphrase=None, sandbox_mode=None):
        self.logger = logger
        self.exchange_name = "OKX"
        #
        self.api_key: str = api_key or getenv("OKX_API_KEY"),
        self.api_secret: str = api_secret or getenv("OKX_SECRET_KEY")
        self.passphrase: str = passphrase or getenv("OKX_PASSPHRASE")
        self.exchange_type: str = getenv("OKX_EXCHANGE_TYPE", default="FUTURES").upper()
        self.sandbox_mode: str = sandbox_mode or getenv("OKX_SANDBOX_MODE", default=True),
        #
        self.verbose = getenv("OKX_VERBOSE", default="DEBUG").upper()
        self.enable_rate_limit = getenv("ENABLE_RATE_LIMIT", default=True)

        # TODO: Implement SPOT
        if self.exchange_type != "FUTURES":
            raise NotImplementedError(f"Exchange type {self.exchange_type} is not implemented yet")

        _config = dict(
            api_key=api_key,
            api_secret_key=api_secret,
            passphrase=self.passphrase,
            use_server_time=False,
            flag="1" if self.sandbox_mode else "0"
        )


        # Check All Needed Inputs are available at this time
        assert self.logger, f"Logger {self.logger}"
        assert self.exchange_name == "OKX", f"Exchange name {self.exchange_name}"
        assert self.api_key is not None, f"API key was not provided"
        assert self.api_secret is not None, f"API secret key was not provided"
        assert  self.passphrase is not None, f"Passphrase was not provided"
        ... # Need to add more here but boilerplate not required at this moment



        # Python-OKX Specific
        self.marketAPI: MarketAPI = MarketAPI(flag=_config["flag"])
        self.publicAPI: PublicAPI = PublicAPI(flag=_config["flag"])
        self.fundingAPI: FundingAPI = FundingAPI(**_config)
        self.accountAPI: AccountAPI = AccountAPI(**_config)
        self.tradeAPI: TradeAPI = TradeAPI(**_config)
        self.use_server_time: bool = False
        self.flag: str = _config["flag"]
        self.derivative_type: str = self.exchange_type


    def pprint(self, data, log_level='info'):
        assert log_level.upper() in ['INFO', 'DEBUG', 'WARNING', 'ERROR', 'CRITICAL']
        eval(f'self.logger.{log_level.lower()}(pformat({data}))')
