"""
Utility functions. In particular Chapter20 code on Multiprocessing and Vectorization
"""

from research_tools.util.fast_ewma import ewma
from research_tools.util.multiprocess import expand_call, lin_parts, mp_pandas_obj, nested_parts, process_jobs, process_jobs_, \
    report_progress
from research_tools.util.volatility import get_daily_vol, get_garman_class_vol, get_yang_zhang_vol, get_parksinson_vol
from research_tools.util.volume_classifier import get_bvc_buy_volume
from research_tools.util.generate_dataset import get_classification_data

