import os

import dotenv

dotenv.load_dotenv(dotenv.find_dotenv())
# api key credential
API_KEY = os.environ.get("OKX_API_KEY")
API_KEY_SECRET = os.environ.get("OKX_SECRET_KEY")
API_PASSPHRASE = os.environ.get("OKX_PASSPHRASE")
IS_PAPER_TRADING = bool(os.environ.get("OKX_SANDBOX_MODE"))

assert API_KEY, "Please set OKX_API_KEY in environment variable"
assert API_KEY_SECRET, "Please set OKX_SECRET_KEY in environment variable"
assert API_PASSPHRASE, "Please set OKX_PASSPHRASE in environment variable"
assert IS_PAPER_TRADING in [True, False], "Please set OKX_SANDBOX_MODE in environment variable"

# market-making instrument
# TRADING_INSTRUMENT_ID = "BTC-USDT-SWAP"
TRADING_INSTRUMENT_ID = "BTC-USDT-240329"
TRADING_MODE = "isolated"  # "cash" / "isolated" / "cross"

# default latency tolerance level
ORDER_BOOK_DELAYED_SEC = 60  # Warning if OrderBook not updated for these seconds, potential issues from wss connection
ACCOUNT_DELAYED_SEC = 60  # Warning if Account not updated for these seconds, potential issues from wss connection

# risk-free ccy
RISK_FREE_CCY_LIST = ["USDT", "USDC", "DAI"]

# params yaml path
PARAMS_PATH = os.path.abspath(os.path.dirname(__file__) + "/params.yaml")
