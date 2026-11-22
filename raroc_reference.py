"""Northlake Bank (fictional) - RAROC reference implementation.

Pure Python mirror of the `Price Deal` Power Automate flow. Every number comes
from knowledge/constants.yaml, so the policy documents, this file and the flow
cannot drift apart. Synthetic. For demonstration only.

Usage:
    python raroc_reference.py C-0142 revolver 50000000 3 125 25
    python raroc_reference.py C-0117 term_loan 75000000 5 140 20 --commit-fee 25
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
CONSTANTS_PATH = HERE / "knowledge" / "constants.yaml"
CLIENTS_PATH = HERE / "data" / "clients.csv"
CLIENT_ID_RE = re.compile(r"^C-\d{4}$")


def load_constants(path: Path = CONSTANTS_PATH) -> dict:
    with open(path, encoding="utf-8") as f:
        c = yaml.safe_load(f)
    c["ratings"] = {int(k): v for k, v in c["ratings"].items()}
    return c


def load_clients(path: Path = CLIENTS_PATH) -> dict[str, dict]:
    with open(path, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    out = {}
    for r in rows:
        out[r["client_id"]] = {
            **r,
            "rating": int(r["rating"]),
            "rel_revenue": float(r["rel_revenue"]),
            "rel_cost": float(r["rel_cost"]),
            "rel_el": float(r["rel_el"]),
            "rel_capital": float(r["rel_capital"]),
            "el_rate": float(r["el_rate"]),
            "capital_rate": float(r["capital_rate"]),
        }
    return out


def r4(x: float) -> float:
    """Round half-up to 4 dp (the flow uses formatNumber(x, '0.0000'))."""
    return float(Decimal(repr(x)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP))


def rating_band(rating: int) -> str:
    return {1: "1-2", 2: "1-2", 3: "3-4", 4: "3-4", 5: "5-6", 6: "5-6",
            7: "7-8", 8: "7-8", 9: "9-10", 10: "9-10"}[rating]


def spread_floor_bp(c: dict, rating: int, tenor: float) -> int:
    base = c["spread_floor_bp"][rating_band(rating)]
    for step in c["tenor_addon_bp"]:
        if tenor <= step["max_tenor"]:
            return base + step["addon"]
    return base + c["tenor_addon_bp"][-1]["addon"]


def relationship_rar(client: dict) -> float:
    """Existing relationship risk-adjusted return (revenue - EL - cost)."""
    return client["rel_revenue"] - client["rel_el"] - client["rel_cost"]


def validate(c: dict, client_id: str, facility_type: str, size: float, tenor: float,
             spread_bp: float, upfront_bp: float, commit_fee_bp: float) -> list[str]:
    v = c["validation"]
    errors = []
    if not CLIENT_ID_RE.match(client_id or ""):
        errors.append("Client ID must look like C-0142.")
    if facility_type not in ("revolver", "term_loan"):
        errors.append("Facility type must be revolver or term loan.")
    if not (v["size_min"] <= size <= v["size_max"]):
        errors.append("Size must be between $1M and $2B.")
    if not (v["tenor_min"] <= tenor <= v["tenor_max"]):
        errors.append("Tenor must be between 1 and 7 years.")
    if not (v["spread_min_bp"] <= spread_bp <= v["spread_max_bp"]):
        errors.append("Spread must be between 0 and 1,000 bp.")
    for name, fee in (("Upfront fee", upfront_bp), ("Commitment fee", commit_fee_bp)):
        if not (v["fee_min_bp"] <= fee <= v["fee_max_bp"]):
            errors.append(f"{name} must be between 0 and 200 bp.")
    return errors


def price_deal(client_id: str, facility_type: str, size: float, tenor: float,
               spread_bp: float, upfront_bp: float, commit_fee_bp: float | None = None,
               clients: dict | None = None, c: dict | None = None) -> dict:
    c = c or load_constants()
    clients = clients if clients is not None else load_clients()
    client_id = (client_id or "").strip().upper()
    facility_type = (facility_type or "").strip().lower().replace(" ", "_")
    if commit_fee_bp is None:
        commit_fee_bp = c["default_commit_fee_bp"]

    errors = validate(c, client_id, facility_type, size, tenor, spread_bp, upfront_bp, commit_fee_bp)
    if errors:
        return {"status": "invalid", "decision": "Rejected (input)", "message": " ".join(errors)}
    if client_id not in clients:
        return {"status": "unknown_client", "decision": "Rejected (input)",
                "message": f"Client {client_id} was not found."}

    cl = clients[client_id]
    util = c["utilisation"][facility_type]
    drawn = size * util
    undrawn = size - drawn

    revenue = (drawn * spread_bp / 10000
               + undrawn * commit_fee_bp / 10000
               + size * upfront_bp / 10000 / tenor)
    el = drawn * cl["el_rate"]
    cost = revenue * c["cost_ratio"]
    capital = size * cl["capital_rate"]
    deal_rar = revenue - el - cost
    deal_raroc = r4(deal_rar / capital)

    rel_rar_existing = relationship_rar(cl)
    total_rar = rel_rar_existing + deal_rar
    total_capital = cl["rel_capital"] + capital
    rel_raroc = r4(total_rar / total_capital)

    # Policy checks (LPP sections 3-5). Any breach is an exception (LPP 6.2).
    cl_ = c["clauses"]
    floor = spread_floor_bp(c, cl["rating"], tenor)
    breaches = []
    if spread_bp < floor:
        breaches.append(cl_["spread_floor"])
    if upfront_bp < c["min_upfront_fee_bp"]:
        breaches.append(cl_["upfront_fee"])
    if tenor > c["max_tenor_years"][facility_type]:
        breaches.append(cl_["revolver_tenor"] if facility_type == "revolver" else cl_["term_loan_tenor"])
    policy_breach = bool(breaches)

    hurdle, floor_raroc = c["hurdle"], c["committee_floor"]
    if policy_breach:
        decision, clause = "Route to pricing committee", cl_["exception_route"]
    elif deal_raroc >= hurdle:
        decision, clause = "Approved", cl_["approved"]
    elif deal_raroc >= floor_raroc and rel_raroc >= hurdle:
        decision, clause = "Route to segment head", cl_["segment_head"]
    elif deal_raroc >= floor_raroc:
        decision, clause = "Route to pricing committee", cl_["committee_relationship"]
    else:
        decision, clause = "Route to pricing committee", cl_["committee_low"]
    policy_clause = "; ".join([clause] + breaches + ([cl_["exception"]] if policy_breach else []))
    row_status = "Approved" if decision == "Approved" else "Pending"

    # Cross-sell (RM 7.1): only when the deal AND the relationship are below hurdle.
    held = [p.strip() for p in cl["products_held"].split(";") if p.strip()]
    not_held = [p["name"] for p in c["products"] if p["name"] not in held]
    revenue_needed = 0.0
    if deal_raroc < hurdle and rel_raroc < hurdle:
        revenue_needed = round(max(0.0, (hurdle * total_capital - total_rar) / (1 - c["cost_ratio"])))

    return {
        "status": "ok",
        "client_id": client_id,
        "client_name": cl["name"],
        "rating": cl["rating"],
        "facility_type": facility_type,
        "revenue": round(revenue, 2),
        "expected_loss": round(el, 2),
        "cost": round(cost, 2),
        "capital": round(capital, 2),
        "deal_raroc": deal_raroc,
        "rel_raroc": rel_raroc,
        "spread_floor_bp": floor,
        "policy_breach": policy_breach,
        "decision": decision,
        "row_status": row_status,
        "policy_clause": policy_clause,
        "revenue_needed": revenue_needed,
        "products_not_held": not_held if revenue_needed else [],
        "constants_version": c["version"],
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("client_id")
    p.add_argument("facility_type", choices=["revolver", "term_loan"])
    p.add_argument("size", type=float)
    p.add_argument("tenor", type=float)
    p.add_argument("spread_bp", type=float)
    p.add_argument("upfront_bp", type=float)
    p.add_argument("--commit-fee", type=float, default=None)
    a = p.parse_args()
    print(json.dumps(price_deal(a.client_id, a.facility_type, a.size, a.tenor,
                                a.spread_bp, a.upfront_bp, a.commit_fee), indent=2))


if __name__ == "__main__":
    main()
