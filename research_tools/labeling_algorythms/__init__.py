"""
Labeling techniques used in financial machine learning.
"""

from research_tools.labeling_algorythms.excess_over_mean import excess_over_mean
from research_tools.labeling_algorythms.excess_over_median import excess_over_median
from research_tools.labeling_algorythms.fixed_time_horizon import fixed_time_horizon
from research_tools.labeling_algorythms.fractionally_differenciated import (get_weights, frac_diff,
                                                                                       get_weights_ffd, frac_diff_ffd,
                                                                                       plot_min_ffd)
from research_tools.labeling_algorythms.labeling import (add_vertical_barrier, apply_pt_sl_on_t1,
                                                                    barrier_touched, drop_labels,
                                                                    get_bins, get_events)
from research_tools.labeling_algorythms.matrix_flags import MatrixFlagLabels
from research_tools.labeling_algorythms.raw_return import raw_return
from research_tools.labeling_algorythms.return_vs_benchmark import return_over_benchmark
from research_tools.labeling_algorythms.tail_sets import TailSetLabels
from research_tools.labeling_algorythms.trend_scanning import trend_scanning_labels
