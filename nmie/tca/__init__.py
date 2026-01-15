"""TCA module - Transaction Cost Analysis."""
from nmie.tca.decompose_cost import CostDecomposition, decompose_cost, aggregate_decompositions
from nmie.tca.regimes import RegimeSlice, compute_regime_slices
from nmie.tca.diagnostics import FailureBucket, identify_failure_buckets
from nmie.tca.explain import Explanation, explain_is, explain_cost_decomposition, GLOSSARY
from nmie.tca.artifacts import (
    write_tca_summary, write_tca_orders, write_regime_slices,
    write_simulator_sensitivity, write_executive_note
)
