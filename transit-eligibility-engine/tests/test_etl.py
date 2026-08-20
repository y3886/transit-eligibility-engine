import pytest
from src.etl import build_master


def test_build_master_runs_and_outputs():
    df = build_master()
    # Expect around 1213 rows
    assert 1100 <= len(df) <= 1400
    # No nulls in is_eligible
    assert df["is_eligible"].isnull().sum() == 0
    # Required columns
    for col in ["code", "name", "periphery_cluster", "socio_cluster", "is_eligible"]:
        assert col in df.columns
