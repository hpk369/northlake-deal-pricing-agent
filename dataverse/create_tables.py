"""Create the Northlake Dataverse tables and load the 50 clients (Web API).

Builds, inside the solution NorthlakeDealPricing (prefix nlk):
  - nlk_client        (Clients)        11 columns + "Client ID key"
  - nlk_dealapproval  (Deal Approvals) 29 columns, Request ID autonumber DR-{SEQNUM:5}, lookup to Clients
then inserts data/clients.csv (skips client IDs that are already there).
Spec: dataverse/tables.md. Safe to re-run: anything that exists is skipped.

Sign-in: Azure CLI token for hpk@inkandinfra.com.
    brew install azure-cli
    az login --tenant inkandinfra.com --allow-no-subscriptions     # pick hpk@inkandinfra.com
Run (from p2/, inside the venv):
    python dataverse/create_tables.py --dry-run     # prints the plan, no sign-in
    python dataverse/create_tables.py               # creates everything
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import time
from pathlib import Path

ENV_URL = "https://org895f8ede.crm3.dynamics.com"
EXPECTED_USER = "hpk@inkandinfra.com"
SOLUTION = "NorthlakeDealPricing"
PREFIX = "nlk_"
ROOT = Path(__file__).resolve().parents[1]
CLIENTS_CSV = ROOT / "data" / "clients.csv"
LANG = 1033
DEC_MIN, DEC_MAX = -100_000_000_000, 100_000_000_000


# ---------- metadata builders ----------
def label(text: str) -> dict:
    return {"@odata.type": "Microsoft.Dynamics.CRM.Label",
            "LocalizedLabels": [{"@odata.type": "Microsoft.Dynamics.CRM.LocalizedLabel",
                                 "Label": text, "LanguageCode": LANG}]}


def required(level: str = "None") -> dict:
    return {"Value": level, "CanBeChanged": True,
            "ManagedPropertyLogicalName": "canmodifyrequirementlevelsettings"}


def base(schema: str, display: str, odata: str, req: str = "None") -> dict:
    return {"@odata.type": f"Microsoft.Dynamics.CRM.{odata}", "SchemaName": schema,
            "DisplayName": label(display), "Description": label(display), "RequiredLevel": required(req)}


def text(schema, display, max_len, req="None", primary=False, autonumber=None):
    a = base(schema, display, "StringAttributeMetadata", req)
    a.update({"MaxLength": max_len, "FormatName": {"Value": "Text"}})
    if primary:
        a["IsPrimaryName"] = True
    if autonumber:
        a["AutoNumberFormat"] = autonumber
    return a


def memo(schema, display, max_len):
    a = base(schema, display, "MemoAttributeMetadata")
    a.update({"MaxLength": max_len, "Format": "TextArea"})
    return a


def whole(schema, display, lo, hi):
    a = base(schema, display, "IntegerAttributeMetadata")
    a.update({"MinValue": lo, "MaxValue": hi, "Format": "None"})
    return a


def decimal(schema, display, precision):
    a = base(schema, display, "DecimalAttributeMetadata")
    a.update({"Precision": precision, "MinValue": DEC_MIN, "MaxValue": DEC_MAX})
    return a


def yesno(schema, display):
    a = base(schema, display, "BooleanAttributeMetadata")
    a.update({"DefaultValue": False, "OptionSet": {
        "@odata.type": "Microsoft.Dynamics.CRM.BooleanOptionSetMetadata",
        "TrueOption": {"Value": 1, "Label": label("Yes")},
        "FalseOption": {"Value": 0, "Label": label("No")}, "OptionSetType": "Boolean"}})
    return a


def datetime_col(schema, display):
    a = base(schema, display, "DateTimeAttributeMetadata")
    a.update({"Format": "DateAndTime", "DateTimeBehavior": {"Value": "UserLocal"}})
    return a


TABLES = [
    {
        "schema": "nlk_client", "display": "Client", "plural": "Clients",
        "primary": text("nlk_clientcode", "Client ID", 10, req="ApplicationRequired", primary=True),
        "columns": [
            text("nlk_companyname", "Company name", 100),
            text("nlk_segment", "Segment", 30),
            whole("nlk_rating", "Rating", 1, 10),
            text("nlk_productsheld", "Products held", 200),
            decimal("nlk_relrevenue", "Relationship revenue (USD)", 0),
            decimal("nlk_relcost", "Relationship cost (USD)", 0),
            decimal("nlk_relel", "Relationship expected loss (USD)", 0),
            decimal("nlk_relcapital", "Relationship capital (USD)", 0),
            decimal("nlk_elrate", "EL rate", 4),
            decimal("nlk_capitalrate", "Capital rate", 3),
        ],
    },
    {
        "schema": "nlk_dealapproval", "display": "Deal Approval", "plural": "Deal Approvals",
        "primary": text("nlk_requestid", "Request ID", 20, primary=True, autonumber="DR-{SEQNUM:5}"),
        "columns": [
            text("nlk_clientcode", "Client ID entered", 20),
            text("nlk_product", "Product", 30),
            text("nlk_facilitytype", "Facility type", 20),
            decimal("nlk_sizeusd", "Size (USD)", 0),
            decimal("nlk_tenoryears", "Tenor (years)", 1),
            decimal("nlk_spreadbp", "Spread (bp)", 1),
            decimal("nlk_upfrontbp", "Upfront fee (bp)", 1),
            decimal("nlk_commitfeebp", "Commitment fee (bp)", 1),
            decimal("nlk_revenue", "Revenue (USD)", 2),
            decimal("nlk_expectedloss", "Expected loss (USD)", 2),
            decimal("nlk_cost", "Cost (USD)", 2),
            decimal("nlk_capital", "Capital (USD)", 2),
            decimal("nlk_dealraroc", "Deal RAROC", 4),
            decimal("nlk_relraroc", "Relationship RAROC", 4),
            decimal("nlk_revenueneeded", "Revenue needed (USD)", 0),
            text("nlk_policyclause", "Policy clause", 100),
            yesno("nlk_policybreach", "Policy breach"),
            text("nlk_decision", "Decision", 50),
            text("nlk_status", "Status", 30),
            text("nlk_approverrole", "Approver role", 30),
            text("nlk_approver", "Approver", 100),
            memo("nlk_approvercomment", "Approver comment", 2000),
            datetime_col("nlk_decidedon", "Decided on"),
            memo("nlk_crosssell", "Cross-sell", 2000),
            memo("nlk_message", "Message", 1000),
            text("nlk_constantsversion", "Constants version", 20),
            text("nlk_source", "Source", 30),
        ],
    },
]

LOOKUP = {
    "@odata.type": "Microsoft.Dynamics.CRM.OneToManyRelationshipMetadata",
    "SchemaName": "nlk_client_dealapproval",
    "ReferencedEntity": "nlk_client", "ReferencedAttribute": "nlk_clientid",
    "ReferencingEntity": "nlk_dealapproval",
    "AssociatedMenuConfiguration": {"Behavior": "UseCollectionName", "Group": "Details",
                                    "Label": label("Deal Approvals"), "Order": 10000},
    "CascadeConfiguration": {"Assign": "NoCascade", "Delete": "RemoveLink", "Merge": "NoCascade",
                             "Reparent": "NoCascade", "Share": "NoCascade", "Unshare": "NoCascade"},
    "Lookup": {"@odata.type": "Microsoft.Dynamics.CRM.LookupAttributeMetadata",
               "AttributeType": "Lookup", "AttributeTypeName": {"Value": "LookupType"},
               "SchemaName": "nlk_client", "DisplayName": label("Client"),
               "Description": label("Client"), "RequiredLevel": required()},
}

KEY = {"SchemaName": "nlk_clientcodekey", "DisplayName": label("Client ID key"), "KeyAttributes": ["nlk_clientcode"]}

CSV_MAP = {  # csv column -> (dataverse column, type)
    "client_id": ("nlk_clientcode", str), "name": ("nlk_companyname", str), "segment": ("nlk_segment", str),
    "rating": ("nlk_rating", int), "products_held": ("nlk_productsheld", str),
    "rel_revenue": ("nlk_relrevenue", float), "rel_cost": ("nlk_relcost", float),
    "rel_el": ("nlk_relel", float), "rel_capital": ("nlk_relcapital", float),
    "el_rate": ("nlk_elrate", float), "capital_rate": ("nlk_capitalrate", float),
}


# ---------- Web API client ----------
class Dataverse:
    def __init__(self, url: str):
        import requests  # imported here so --dry-run works without it
        self.requests = requests
        self.api = url.rstrip("/") + "/api/data/v9.2/"
        token = json.loads(subprocess.check_output(
            ["az", "account", "get-access-token", "--resource", url.rstrip("/"), "-o", "json"]))
        self.s = requests.Session()
        self.s.headers.update({
            "Authorization": f"Bearer {token['accessToken']}", "Accept": "application/json",
            "Content-Type": "application/json; charset=utf-8", "OData-Version": "4.0",
            "OData-MaxVersion": "4.0", "MSCRM.SolutionUniqueName": SOLUTION,
        })

    def call(self, method: str, path: str, body=None, ok=(200, 201, 204), quiet404=False):
        for attempt in range(4):
            r = self.s.request(method, self.api + path, data=json.dumps(body) if body is not None else None, timeout=300)
            if r.status_code in (429, 503) and attempt < 3:
                time.sleep(int(r.headers.get("Retry-After", 10)))
                continue
            break
        if r.status_code == 404 and quiet404:
            return None
        if r.status_code not in ok:
            raise SystemExit(f"\n{method} {path} failed: HTTP {r.status_code}\n{r.text[:2000]}")
        return r.json() if r.content else {}


def existing_attributes(dv: Dataverse, entity: str) -> set[str]:
    data = dv.call("GET", f"EntityDefinitions(LogicalName='{entity}')/Attributes?$select=LogicalName")
    return {a["LogicalName"] for a in data["value"]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="print the plan without signing in")
    ap.add_argument("--skip-data", action="store_true", help="create tables only, don't load clients.csv")
    args = ap.parse_args()

    rows = list(csv.DictReader(open(CLIENTS_CSV, encoding="utf-8")))
    if args.dry_run:
        for t in TABLES:
            print(f"Table {t['schema']} ({t['plural']}), primary {t['primary']['SchemaName']}"
                  + (f" autonumber {t['primary'].get('AutoNumberFormat')}" if t['primary'].get('AutoNumberFormat') else ""))
            for c in t["columns"]:
                print(f"   {c['SchemaName']:<22} {c['@odata.type'].split('.')[-1].replace('AttributeMetadata', ''):<9} {c['DisplayName']['LocalizedLabels'][0]['Label']}")
        print(f"Lookup nlk_dealapproval.nlk_client -> nlk_client ({LOOKUP['SchemaName']})")
        print(f"Key {KEY['SchemaName']} on nlk_client.nlk_clientcode")
        print(f"Load {len(rows)} clients from {CLIENTS_CSV.name}")
        return

    print(f"Environment {ENV_URL}")
    dv = Dataverse(ENV_URL)

    # 0. Who am I, and does the solution exist?
    me = dv.call("GET", "WhoAmI")
    user = dv.call("GET", f"systemusers({me['UserId']})?$select=domainname")
    print(f"Signed in as {user['domainname']}")
    if user["domainname"].lower() != EXPECTED_USER:
        raise SystemExit(f"Expected {EXPECTED_USER}. Run: az logout && az login --tenant inkandinfra.com --allow-no-subscriptions")
    sol = dv.call("GET", f"solutions?$select=uniquename&$filter=uniquename eq '{SOLUTION}'"
                         "&$expand=publisherid($select=customizationprefix)")["value"]
    if not sol:
        raise SystemExit(f"Solution {SOLUTION} not found. Create it first (guide Phase 1.1).")
    prefix = sol[0]["publisherid"]["customizationprefix"]
    if prefix != PREFIX.rstrip("_"):
        raise SystemExit(f"Solution publisher prefix is '{prefix}', expected 'nlk'.")
    print(f"Solution {SOLUTION} found (prefix {prefix})")

    # 1. Tables and columns
    created = set()
    for t in TABLES:
        name = t["schema"]
        if dv.call("GET", f"EntityDefinitions(LogicalName='{name}')?$select=LogicalName", quiet404=True) is None:
            print(f"Creating table {name} ... (takes up to a minute)")
            dv.call("POST", "EntityDefinitions", {
                "@odata.type": "Microsoft.Dynamics.CRM.EntityMetadata",
                "SchemaName": name, "DisplayName": label(t["display"]),
                "DisplayCollectionName": label(t["plural"]), "Description": label(f"Northlake (fictional) {t['plural']}"),
                "OwnershipType": "UserOwned", "IsActivity": False, "HasActivities": False, "HasNotes": False,
                "PrimaryNameAttribute": t["primary"]["SchemaName"], "Attributes": [t["primary"]],
            })
            created.add(name)
        else:
            print(f"Table {name} exists")
        have = existing_attributes(dv, name)
        for c in t["columns"]:
            if c["SchemaName"] in have:
                continue
            print(f"   + {c['SchemaName']}")
            dv.call("POST", f"EntityDefinitions(LogicalName='{name}')/Attributes", c)

    # 2. Autonumber seed (DR-00001), only on a freshly created table so a re-run can't cause duplicates
    if "nlk_dealapproval" in created:
        dv.call("POST", "SetAutoNumberSeed", {"EntityName": "nlk_dealapproval", "AttributeName": "nlk_requestid", "Value": 1})
        print("Request ID autonumber seed set to 1 (first request DR-00001)")

    # 3. Lookup Deal Approvals -> Clients
    if "nlk_client" in existing_attributes(dv, "nlk_dealapproval"):
        print("Lookup nlk_client exists")
    else:
        print("Creating lookup Deal Approvals -> Clients")
        dv.call("POST", "RelationshipDefinitions", LOOKUP)

    # 4. Alternate key on Client ID
    keys = dv.call("GET", "EntityDefinitions(LogicalName='nlk_client')/Keys?$select=SchemaName")["value"]
    if any(k["SchemaName"] == KEY["SchemaName"] for k in keys):
        print("Key exists")
    else:
        print("Creating key on Client ID")
        dv.call("POST", "EntityDefinitions(LogicalName='nlk_client')/Keys", KEY)

    # 5. Publish
    dv.call("POST", "PublishXml", {"ParameterXml": "<importexportxml><entities><entity>nlk_client</entity>"
                                                   "<entity>nlk_dealapproval</entity></entities></importexportxml>"})
    print("Published")

    # 6. Load clients
    if args.skip_data:
        return
    es = dv.call("GET", "EntityDefinitions(LogicalName='nlk_client')?$select=EntitySetName")["EntitySetName"]
    present = {r["nlk_clientcode"] for r in dv.call("GET", f"{es}?$select=nlk_clientcode")["value"]}
    added = 0
    for r in rows:
        if r["client_id"] in present:
            continue
        body = {col: cast(r[csv_col]) for csv_col, (col, cast) in CSV_MAP.items()}
        dv.call("POST", es, body)
        added += 1
    total = len(dv.call("GET", f"{es}?$select=nlk_clientcode")["value"])
    print(f"Clients: added {added}, total now {total} (entity set {es})")

    # 7. Spot-check
    for cid in ("C-0142", "C-0117", "C-0109"):
        v = dv.call("GET", f"{es}?$filter=nlk_clientcode eq '{cid}'&$select=nlk_rating,nlk_relrevenue,nlk_relcapital,nlk_elrate,nlk_capitalrate,nlk_productsheld")["value"][0]
        print(f"   {cid}: rating {v['nlk_rating']}, rel revenue {v['nlk_relrevenue']:,.0f}, rel capital {v['nlk_relcapital']:,.0f}, "
              f"EL {v['nlk_elrate']}, capital {v['nlk_capitalrate']}, products {v['nlk_productsheld']}")
    print("Done. Check both tables are listed in the solution in make.powerapps.com.")


if __name__ == "__main__":
    main()
