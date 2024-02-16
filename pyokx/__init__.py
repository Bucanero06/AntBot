import os

import dotenv

from pyokx.okx_market_maker.utils.OkxEnum import InstType

dotenv.load_dotenv(dotenv.find_dotenv())
from pyokx.Futures_Exchange_Client import OKX_Futures_Exchange_Client as OKXClient

okx_client = OKXClient(api_key=os.getenv('OKX_API_KEY'), api_secret=os.getenv('OKX_SECRET_KEY'),
                       passphrase=os.getenv('OKX_PASSPHRASE'), sandbox_mode=os.getenv('OKX_SANDBOX_MODE'))
tradeAPI = okx_client.tradeAPI
marketAPI = okx_client.marketAPI
accountAPI = okx_client.accountAPI
publicAPI = okx_client.publicAPI

ENFORCED_INSTRUMENT_TYPE = InstType.FUTURES.name
