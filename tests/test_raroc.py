"""pytest tests for raroc_reference.py. Run from p2/:  python -m pytest -q tests"""
import csv
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import raroc_reference as ref  # noqa: E402

C = ref.load_constants()
CLIENTS = ref.load_clients()


def price(*a, **k):
    return ref.price_deal(*a, clients=CLIENTS, c=C, **k)


def test_headline_hand_calc():
    # $50M 3y revolver, rating 3: drawn 25M
    # revenue = 25M*1.25% + 25M*0.25% + 50M*0.25%/3 = 312,500 + 62,500 + 41,666.67 = 416,666.67
    # cost 40% = 166,666.67 ; EL = 25M*0.04% = 10,000 ; capital = 50M*3% = 1,500,000
    r = price("C-0142", "revolver", 50e6, 3, 125, 25)
    assert r["revenue"] == pytest.approx(416_666.67, abs=0.01)
    assert r["expected_loss"] == 10_000
    assert r["capital"] == 1_500_000
    assert r["deal_raroc"] == 0.16
    assert r["decision"] == "Approved" and r["row_status"] == "Approved"


def test_term_loan_fully_drawn_no_commit_fee():
    r = price("C-0117", "term_loan", 75e6, 5, 140, 20)
    assert r["revenue"] == pytest.approx(75e6 * 0.014 + 75e6 * 0.002 / 5)


def test_input_normalised():
    assert price(" c-0142 ", "Revolver", 50e6, 3, 125, 25)["decision"] == "Approved"


@pytest.mark.parametrize("rating,tenor,floor", [(5, 3, 110), (6, 3, 110), (3, 5, 100), (8, 7, 190), (1, 1, 60)])
def test_spread_floor(rating, tenor, floor):
    assert ref.spread_floor_bp(C, rating, tenor) == floor


def test_floor_breach_goes_to_committee_even_if_raroc_ok():
    # Rating-3 client above hurdle on RAROC but with a 4 bp upfront fee (< LPP 4.1 minimum)
    r = price("C-0142", "revolver", 50e6, 3, 140, 4)
    assert r["policy_breach"] and "LPP 4.1" in r["policy_clause"]
    assert r["decision"] == "Route to pricing committee"
    assert r["policy_clause"].startswith("AM 2.1")


def test_never_approved_below_hurdle():
    for cid in CLIENTS:
        for spread in (60, 100, 150, 250):
            r = price(cid, "revolver", 100e6, 3, spread, 25)
            if r["deal_raroc"] < C["hurdle"]:
                assert r["decision"] != "Approved"


def test_cross_sell_closes_gap():
    r = price("C-0128", "term_loan", 100e6, 4, 135, 25)
    cl = CLIENTS["C-0128"]
    total_cap = cl["rel_capital"] + r["capital"]
    total_rar = ref.relationship_rar(cl) + (r["revenue"] - r["expected_loss"] - r["cost"])
    new_rar = total_rar + r["revenue_needed"] * (1 - C["cost_ratio"])
    assert new_rar / total_cap == pytest.approx(C["hurdle"], abs=1e-5)
    assert "Lending" not in r["products_not_held"] and "Rates & FX Hedging" not in r["products_not_held"]


def test_no_cross_sell_when_relationship_clears():
    r = price("C-0117", "term_loan", 75e6, 5, 140, 20)
    assert r["revenue_needed"] == 0 and r["products_not_held"] == []


@pytest.mark.parametrize("args", [
    ("C-0142", "revolver", 500_000, 3, 125, 25),       # size too small
    ("C-0142", "revolver", 50e6, 8, 125, 25),          # tenor too long
    ("C-0142", "revolver", 50e6, 3, 1200, 25),         # spread too high
    ("C-0142", "revolver", 50e6, 3, 125, 250),         # fee too high
    ("0142", "revolver", 50e6, 3, 125, 25),            # bad ID format
    ("C-0142", "bridge", 50e6, 3, 125, 25),            # bad facility
])
def test_invalid(args):
    r = price(*args)
    assert r["status"] == "invalid" and r["decision"] == "Rejected (input)"


def test_unknown_client():
    assert price("C-9999", "revolver", 50e6, 3, 125, 25)["status"] == "unknown_client"


def test_flow_cases_file_matches_reference():
    with open(ROOT / "tests" / "raroc_cases.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            r = price(row["clientId"], row["facilityType"], float(row["sizeUSD"]), float(row["tenorYears"]),
                      float(row["spreadBp"]), float(row["upfrontFeeBp"]), float(row["commitFeeBp"]))
            assert r["decision"] == row["exp_decision"], row["case_id"]
            if row["exp_dealRAROC"]:
                assert f'{r["deal_raroc"]:.4f}' == row["exp_dealRAROC"], row["case_id"]
                assert f'{r["rel_raroc"]:.4f}' == row["exp_relRAROC"], row["case_id"]
