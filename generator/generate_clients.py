"""Generate 50 synthetic Northlake Bank (fictional) clients -> data/clients.csv.

Seeded (random.seed(22)) so the file is identical on every run. Five "path
clients" are fixed by hand so the demo prompts hit every approval route; the
script checks each one with raroc_reference.py and fails loudly if any drifts.
All names are invented. Synthetic. For demonstration only.
"""
from __future__ import annotations

import csv
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import raroc_reference as ref  # noqa: E402

OUT = ROOT / "data" / "clients.csv"
FIELDS = ["client_id", "name", "segment", "rating", "products_held", "rel_revenue",
          "rel_cost", "rel_el", "rel_capital", "el_rate", "capital_rate"]
SEGMENTS = ["Large Corporate", "Mid-Market", "FI", "Sponsor"]
CAPITAL_RANGE = {"Large Corporate": (6e6, 20e6), "Mid-Market": (2e6, 7e6),
                 "FI": (4e6, 15e6), "Sponsor": (3e6, 10e6)}

# Hand-set path clients: (segment, rating, products, rel_revenue, rel_cost, rel_el, rel_capital)
PATH_CLIENTS = {
    "C-0142": ("Halvorsen Marine Logistics Inc.", "Large Corporate", 3,
               "Lending;Rates & FX Hedging;Transaction Banking;DCM", 4_200_000, 1_850_000, 90_000, 9_500_000),
    "C-0117": ("Quillfeather Industrial Holdings Ltd.", "Large Corporate", 5,
               "Lending;Transaction Banking;Rates & FX Hedging;DCM;M&A Advisory", 6_000_000, 2_400_000, 250_000, 14_000_000),
    "C-0128": ("Tamarack Valley Foods Corp.", "Mid-Market", 5,
               "Lending;Rates & FX Hedging", 1_200_000, 600_000, 100_000, 6_000_000),
    "C-0133": ("Bramblewood Capital Partners Fund IV LP", "Sponsor", 6,
               "Lending;M&A Advisory", 1_800_000, 800_000, 200_000, 7_000_000),
    "C-0109": ("Corvane Precision Components Ltd.", "Mid-Market", 5,
               "Lending", 500_000, 250_000, 60_000, 4_000_000),
}

# Demo deals each path client must land on: (facility, size, tenor, spread, upfront, expected decision, clause starts with)
PATH_DEALS = {
    "C-0142": ("revolver", 50e6, 3, 125, 25, "Approved", "AM 1.1"),
    "C-0117": ("term_loan", 75e6, 5, 140, 20, "Route to segment head", "AM 1.2"),
    "C-0128": ("term_loan", 100e6, 4, 135, 25, "Route to pricing committee", "AM 1.4"),
    "C-0133": ("revolver", 60e6, 3, 115, 20, "Route to pricing committee", "AM 1.3"),
    "C-0109": ("revolver", 40e6, 3, 130, 20, "Route to pricing committee", "AM 1.3"),
}

PREFIXES = ["Aldergrove", "Ashcombe", "Birchmount", "Calloway", "Cedarline", "Dunmore", "Eastvale",
            "Fernhollow", "Glenridge", "Granite Shore", "Harrowgate", "Ironwood", "Juniper Bay",
            "Kestrel", "Larchmere", "Maplecroft", "Moraine", "Nettlefield", "Oakhaven", "Pelham Ridge",
            "Quarry Point", "Redfern", "Saltmarsh", "Silverbirch", "Stonebridge", "Thistledown",
            "Upland", "Verdance", "Westbrook", "Whitlock", "Yarrow", "Zephyr Lake", "Amberly",
            "Brackenridge", "Coldwater", "Driftwood", "Elmstead", "Foxbury", "Gullwing", "Hearthstone",
            "Inverness Row", "Lockhart", "Millbrook", "Northvale", "Orchard Hill"]
SUFFIX = {
    "Large Corporate": ["Energy Corp.", "Industries Inc.", "Resources Ltd.", "Holdings Inc.", "Rail Corp.", "Utilities Ltd."],
    "Mid-Market": ["Manufacturing Ltd.", "Distribution Inc.", "Packaging Corp.", "Foods Ltd.", "Logistics Inc."],
    "FI": ["Financial Group", "Insurance Co.", "Asset Management Inc.", "Credit Union", "Trust Co."],
    "Sponsor": ["Capital Partners LP", "Equity Fund III LP", "Growth Partners LP", "Infrastructure Fund LP"],
}
OPTIONAL_PRODUCTS = ["Transaction Banking", "Rates & FX Hedging", "DCM", "ECM", "M&A Advisory"]


def make_row(cid, name, segment, rating, products, rev, cost, el, cap, c):
    r = c["ratings"][rating]
    return {"client_id": cid, "name": name, "segment": segment, "rating": rating,
            "products_held": products, "rel_revenue": int(rev), "rel_cost": int(cost),
            "rel_el": int(el), "rel_capital": int(cap),
            "el_rate": r["el_rate"], "capital_rate": r["capital_rate"]}


def generate() -> list[dict]:
    c = ref.load_constants()
    rng = random.Random(22)
    names = rng.sample(PREFIXES, len(PREFIXES))
    rows = []
    for n in range(101, 151):
        cid = f"C-{n:04d}"
        if cid in PATH_CLIENTS:
            rows.append(make_row(cid, *PATH_CLIENTS[cid], c))
            continue
        segment = rng.choices(SEGMENTS, weights=[35, 35, 15, 15])[0]
        rating = rng.choices(range(2, 9), weights=[6, 14, 20, 24, 18, 12, 6])[0]
        k = rng.randint(0, 4)
        products = ";".join(["Lending"] + sorted(rng.sample(OPTIONAL_PRODUCTS, k)))
        cap = round(rng.uniform(*CAPITAL_RANGE[segment]), -4)
        target = rng.uniform(0.06, 0.26)                     # relationship RAROC
        cost_ratio = rng.uniform(0.40, 0.50)
        rr = c["ratings"][rating]
        el = round(cap / rr["capital_rate"] * 0.6 * rr["el_rate"], -3)
        rev = round((target * cap + el) / (1 - cost_ratio), -3)
        cost = round(rev * cost_ratio, -3)
        name = f"{names.pop()} {rng.choice(SUFFIX[segment])}"
        rows.append(make_row(cid, name, segment, rating, products, rev, cost, el, cap, c))
    return rows


def check_paths() -> None:
    clients = ref.load_clients(OUT)
    ok = True
    for cid, (ft, size, tenor, spread, upfront, exp_decision, exp_clause) in PATH_DEALS.items():
        r = ref.price_deal(cid, ft, size, tenor, spread, upfront, clients=clients)
        hit = r["decision"] == exp_decision and r["policy_clause"].startswith(exp_clause)
        ok &= hit
        print(f"{'OK ' if hit else 'BAD'} {cid}: deal {r['deal_raroc']:.2%} rel {r['rel_raroc']:.2%} "
              f"-> {r['decision']} ({r['policy_clause']}) needed ${r['revenue_needed']:,.0f}")
    if not ok:
        sys.exit("Path clients drifted from their intended routes.")


if __name__ == "__main__":
    rows = generate()
    OUT.parent.mkdir(exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {len(rows)} clients to {OUT}")
    check_paths()
