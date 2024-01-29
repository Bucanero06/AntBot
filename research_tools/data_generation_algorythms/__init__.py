"""
Tools for synthetic data generation.
"""

from research_tools.data_generation_algorythms.corrgan import sample_from_corrgan
from research_tools.data_generation_algorythms.data_verification import (
    plot_pairwise_dist,
    plot_eigenvalues,
    plot_eigenvectors,
    plot_hierarchical_structure,
    plot_mst_degree_count,
    plot_stylized_facts,
    plot_time_series_dependencies,
    plot_optimal_hierarchical_cluster)
from research_tools.data_generation_algorythms.vines import (
    sample_from_cvine,
    sample_from_dvine,
    sample_from_ext_onion)
from research_tools.data_generation_algorythms.correlated_random_walks import generate_cluster_time_series
from research_tools.data_generation_algorythms.hcbm import (
    time_series_from_dist,
    generate_hcmb_mat)
from research_tools.data_generation_algorythms.bootstrap import (
    row_bootstrap,
    pair_bootstrap,
    block_bootstrap)
