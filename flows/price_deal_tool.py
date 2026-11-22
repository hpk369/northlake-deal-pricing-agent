"""Back up and update the Price Deal agent flow through the Dataverse Web API.

    python flows/price_deal_tool.py dump    # saves flows/backup/price_deal_<time>.json (full record) and prints a summary
    python flows/price_deal_tool.py push    # uploads flows/backup/price_deal_new.json (written by Claude) to the flow

Sign-in: Azure CLI as hpk@inkandinfra.com (same as dataverse/create_tables.py).
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import requests

ENV_URL = "https://org895f8ede.crm3.dynamics.com"
EXPECTED_USER = "hpk@inkandinfra.com"
FLOW_NAME = "Price Deal"
HERE = Path(__file__).resolve().parent
BACKUP = HERE / "backup"
NEW_FILE = BACKUP / "price_deal_new.json"


def session() -> requests.Session:
    user = subprocess.check_output(["az", "account", "show", "--query", "user.name", "-o", "tsv"], text=True).strip()
    if user.lower() != EXPECTED_USER:
        raise SystemExit(f"Expected {EXPECTED_USER} but the Azure CLI is signed in as {user}. Run: az logout && az login --tenant inkandinfra.com --allow-no-subscriptions")
    token = json.loads(subprocess.check_output(["az", "account", "get-access-token", "--resource", ENV_URL, "-o", "json"]))
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {token['accessToken']}", "Accept": "application/json",
                      "Content-Type": "application/json; charset=utf-8", "OData-Version": "4.0", "OData-MaxVersion": "4.0"})
    return s


def find(s: requests.Session) -> list[dict]:
    r = s.get(f"{ENV_URL}/api/data/v9.2/workflows", params={"$filter": f"name eq '{FLOW_NAME}'"}, timeout=120)
    if r.status_code != 200:
        raise SystemExit(f"Lookup failed: HTTP {r.status_code}\n{r.text[:2000]}")
    rows = r.json().get("value", [])
    if not rows:
        raise SystemExit(f"No flow named '{FLOW_NAME}' found in {ENV_URL}.")
    return rows


def dump() -> None:
    s = session()
    rows = find(s)
    BACKUP.mkdir(exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    out = BACKUP / f"price_deal_{stamp}.json"
    out.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"Saved {len(rows)} record(s) to {out.relative_to(HERE.parent)}")
    for row in rows:
        cd = json.loads(row.get("clientdata") or "{}")
        actions = cd.get("properties", {}).get("definition", {}).get("actions", {})
        print(f"- workflowid {row['workflowid']} · category {row.get('category')} · state {row.get('statecode')} · "
              f"modified {row.get('modifiedon')} · {len(actions)} top-level actions: {', '.join(actions)}")
    print("\nDone. Tell Claude the dump is saved.")


def push() -> None:
    if not NEW_FILE.exists():
        raise SystemExit(f"{NEW_FILE} not found. Ask Claude to write it first.")
    new = json.loads(NEW_FILE.read_text(encoding="utf-8"))
    s = session()
    rows = [r for r in find(s) if r["workflowid"] == new["workflowid"]]
    if not rows:
        raise SystemExit("The flow in price_deal_new.json no longer exists.")
    if rows[0].get("modifiedon") != new["based_on_modifiedon"]:
        raise SystemExit("The flow was changed since the dump. Run 'dump' again and tell Claude, so nothing you edited is overwritten.")
    url = f"{ENV_URL}/api/data/v9.2/workflows({new['workflowid']})"

    def patch(body: dict, what: str) -> None:
        r = s.patch(url, data=json.dumps(body), timeout=120)
        if r.status_code not in (200, 204):
            raise SystemExit(f"{what} failed: HTTP {r.status_code}\n{r.text[:3000]}")
        print(f"- {what}: ok")

    patch({"clientdata": json.dumps(new["clientdata"], separators=(",", ":"))}, "Upload new definition")
    print("\nPrice Deal updated. Tell Claude, then check it in the designer.")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    {"dump": dump, "push": push}.get(cmd, lambda: sys.exit(__doc__))()
