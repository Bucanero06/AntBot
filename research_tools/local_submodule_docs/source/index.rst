
================================================
Machine Learning Financial Laboratory (genieml_src)
================================================

MlFinlab is a python package which helps portfolio managers and traders who want to leverage the power of machine learning
by providing reproducible, interpretable, and easy to use tools. Adding MlFinLab to your companies pipeline is like adding
a department of PhD researchers to your team.


We source all of our implementations from the most elite and peer-reviewed journals. Including publications from:

1. `The Journal of Financial Data Science <https://jfds.pm-research.com/>`_
2. `The Journal of Portfolio Management <https://jpm.pm-research.com/>`_
3. `The Journal of Algorithmic Finance <http://www.algorithmicfinance.org/>`_
4. `Cambridge University Press <https://www.cambridge.org/>`_

We are making a big drive to include techniques from various authors, however the most dominant author would be Dr. Marcos
Lopez de Prado (`QuantResearch.org <http://www.quantresearch.org/>`_). This package has its foundations in the two graduate
level textbooks:

1. `Advances in Financial Machine Learning <https://www.amazon.co.uk/Advances-Financial-Machine-Learning-Marcos/dp/1119482089>`_
2. `Machine Learning for Asset Managers <https://www.cambridge.org/core/books/machine-learning-for-asset-managers/6D9211305EA2E425D33A9F38D0AE3545>`_

.. figure:: logo/journals.png
   :scale: 100 %
   :align: center
   :figclass: align-center
   :alt: Academic Journals
   :target: https://www.pm-research.com/

Praise for MlFinLab
###################

“Financial markets are complex systems like no other. Extracting signal from financial data requires specialized tools
that are distinct from those used in general machine learning. The MlFinLab package compiles important algorithms
that every quant should know and use.”

\- `Dr. Marcos Lopez de Prado <https://www.linkedin.com/in/lopezdeprado/>`_, Co-founder and CIO at True Positive Technologies; Professor of Practice at Cornell University

----

"Those who doubt open-source libraries just need to look at the impact of Pandas, Scikit-learn, and the like. MIFinLab
is doing to financial machine learning what Tensorflow and PyTorch are doing to deep learning."

\- `Dr. Ernest Chan <https://www.linkedin.com/in/epchan/>`_, Hedge Fund Manager at QTS & Author

----

"For many decades, finance has relied on overly simplistic statistical techniques to identify patterns in data.
Machine learning promises to change that by allowing researchers to use modern nonlinear and highly dimensional
techniques. Yet, applying those machine learning algorithms to model financial problems is easier said than done:
finance is not a plug-and-play subject as it relates to machine learning.

MlFinLab provides access to the latest cutting edges methods. MlFinLab is thus essential for quants who want to be
ahead of the technology rather than being replaced by it."

\- `Dr. Thomas Raffinot <https://www.linkedin.com/in/thomas-raffinot-b75734b/>`_, Financial Data Scientist at ENGIE Global Markets

----



.. toctree::
    :maxdepth: 2
    :caption: Getting Started
    :hidden:

    getting_started/installation
    additional_information/contact
    getting_started/barriers_to_entry
    getting_started/researcher
    getting_started/datasets
    getting_started/research_tools

.. toctree::
    :maxdepth: 2
    :caption: Feature Engineering
    :hidden:

    implementations/data_structures
    implementations/filters
    implementations/frac_diff
    implementations/structural_breaks
    implementations/microstructural_features


.. toctree::
    :maxdepth: 2
    :caption: Codependence
    :hidden:

    codependence/introduction
    codependence/correlation_based_metrics
    codependence/information_theory_metrics
    codependence/codependence_marti
    codependence/codependence_matrix

.. toctree::
    :maxdepth: 2
    :caption: Labeling
    :hidden:

    labeling/tb_meta_labeling
    labeling/labeling_trend_scanning
    labeling/labeling_tail_sets
    labeling/labeling_fixed_time_horizon
    labeling/labeling_matrix_flags
    labeling/labeling_excess_median
    labeling/labeling_raw_return
    labeling/labeling_vs_benchmark
    labeling/labeling_excess_mean


.. toctree::
    :maxdepth: 2
    :caption: Modelling
    :hidden:

    implementations/sampling
    implementations/sb_bagging
    implementations/feature_importance
    implementations/cross_validation
    implementations/EF3M
    implementations/bet_sizing

.. toctree::
    :maxdepth: 2
    :caption: Clustering
    :hidden:

    implementations/onc
    implementations/feature_clusters

.. toctree::
    :maxdepth: 2
    :caption: Backtest Overfitting
    :hidden:

    implementations/backtesting
    implementations/backtest_statistics

.. toctree::
    :maxdepth: 2
    :caption: Portfolio Optimization
    :hidden:

    portfolio_optimisation/risk_metrics
    portfolio_optimisation/returns_estimation
    portfolio_optimisation/risk_estimators
    portfolio_optimisation/mean_variance
    portfolio_optimisation/critical_line_algorithm
    portfolio_optimisation/hierarchical_risk_parity
    portfolio_optimisation/hierarchical_equal_risk_contribution
    portfolio_optimisation/nested_clustered_optimisation
    portfolio_optimisation/theory_implied_correlation

.. toctree::
    :maxdepth: 5
    :caption: Online Portfolio Selection
    :hidden:

    online_portfolio_selection/introduction
    online_portfolio_selection/benchmarks
    online_portfolio_selection/momentum
    online_portfolio_selection/mean_reversion
    online_portfolio_selection/pattern_matching
    online_portfolio_selection/universal_portfolio

.. toctree::
    :maxdepth: 2
    :caption: Additional Information
    :hidden:

    additional_information/contributing
    additional_information/license
