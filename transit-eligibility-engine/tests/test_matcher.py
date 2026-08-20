import pytest
from src.etl import build_master
from src.matcher import LocalityIndex


@pytest.fixture(scope="module")
def index():
    df = build_master()
    return LocalityIndex(df)


def test_exact_match(index):
    # pick first name
    name = index.df.iloc[0]["name"]
    res = index.resolve(name)
    assert len(res) >= 1
    assert res[0][2] == 100.0


def test_fuzzy_typo(index):
    name = index.df.iloc[0]["name"]
    typo = name[:-1]  # simple typo
    res = index.resolve(typo)
    assert len(res) >= 1
