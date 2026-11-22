"""Write tests/raroc_cases.csv: the flow test cases with expected outputs from raroc_reference.py."""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import raroc_reference as ref  # noqa: E402

# id, purpose, clientId, facilityType, sizeUSD, tenorYears, spreadBp, upfrontFeeBp, commitFeeBp
CASES = [
    ("F01", "Approved (headline demo)",          "C-0142", "revolver",  50_000_000,    3, 125, 25, 25),
    ("F02", "Approved (second client)",          "C-0124", "revolver",  150_000_000,   5, 120, 30, 25),
    ("F03", "Segment head",                      "C-0117", "term_loan", 75_000_000,    5, 140, 20, 25),
    ("F04", "Committee via relationship",        "C-0128", "term_loan", 100_000_000,   4, 135, 25, 25),
    ("F05", "Committee, deal < 12%",             "C-0133", "revolver",  60_000_000,    3, 115, 20, 25),
    ("F06", "Committee, thin relationship",      "C-0109", "revolver",  40_000_000,    3, 130, 20, 25),
    ("F07", "Spread below floor (LPP 3.2)",      "C-0133", "revolver",  60_000_000,    3, 95,  20, 25),
    ("F08", "Revolver tenor too long (LPP 5.3)", "C-0142", "revolver",  50_000_000,    6, 125, 25, 25),
    ("F09", "Invalid input",                     "C-0142", "revolver",  5_000_000_000, 15, 125, 25, 25),
    ("F10", "Unknown client",                    "C-9999", "revolver",  50_000_000,    3, 125, 25, 25),
]
FIELDS = ["case_id", "purpose", "clientId", "facilityType", "sizeUSD", "tenorYears", "spreadBp",
          "upfrontFeeBp", "commitFeeBp", "exp_status", "exp_dealRAROC", "exp_relRAROC",
          "exp_decision", "exp_rowStatus", "exp_policyClause", "exp_revenueNeeded"]

if __name__ == "__main__":
    out = ROOT / "tests" / "raroc_cases.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(FIELDS)
        for cid, purpose, client, ft, size, tenor, spread, up, cf in CASES:
            r = ref.price_deal(client, ft, size, tenor, spread, up, cf)
            w.writerow([cid, purpose, client, ft, size, tenor, spread, up, cf, r["status"],
                        f'{r["deal_raroc"]:.4f}' if "deal_raroc" in r else "",
                        f'{r["rel_raroc"]:.4f}' if "rel_raroc" in r else "",
                        r["decision"], r.get("row_status", "Rejected (input)"),
                        r.get("policy_clause", ""), r.get("revenue_needed", "")])
            print(cid, r["status"], r.get("deal_raroc"), r.get("rel_raroc"), r["decision"], r.get("policy_clause", r.get("message")), r.get("revenue_needed"))
    print("Wrote", out)
