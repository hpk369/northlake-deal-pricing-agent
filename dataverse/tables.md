# Dataverse tables: build spec

Northlake Bank (fictional). Synthetic data only. Constants version `2026.11-v1`.

> **Quicker route:** `python dataverse/create_tables.py` builds everything below and loads the clients (see guide Phase 2). This file is the spec it follows and the manual fallback.

Create both tables **inside the solution `Northlake Deal Pricing`** (publisher prefix `nlk`), so the solution export includes them:
make.powerapps.com → Northlake Demo → **Solutions → Northlake Deal Pricing → + New → Table → Table (advanced properties)**.

## Changes from the plan note (P2 02)
| Change | Why |
|---|---|
| Primary column of Clients is `nlk_clientcode` (display "Client ID"), not `nlk_clientid` | Dataverse automatically creates `nlk_clientid` as the table's GUID key, so that name is taken |
| Company name column is `nlk_companyname` | Avoids clashing with the default primary column name `nlk_name` |
| Money columns are **Decimal** (USD), not Currency | Currency columns need a transaction currency and exchange rate, and the environment currency is CAD. Deals are quoted in USD over SOFR |
| `decision`, `status`, `segment`, `facility type` are **Text**, not Choice | Flow filters and CSV import work on plain text with no option-value integers to look up. Choice columns can come later |
| Added `nlk_relel` to Clients | Relationship RAROC needs the existing relationship's expected loss as a figure |
| Added `nlk_clientcode`, revenue/EL/cost/capital, `nlk_revenueneeded`, `nlk_policybreach`, `nlk_approverrole`, `nlk_decidedon`, `nlk_message`, `nlk_constantsversion` to Deal Approvals | Full audit trail: every figure can be recomputed, and rejected requests keep their reason |

When you add a column, type the **Display name**, then open **Advanced options** and check the **Schema name** matches the table below (the `nlk_` prefix is added for you; type the part after it). Schema names can't be changed later.

---

## Table 1: Clients

**Properties**
- Display name: `Client` · Plural: `Clients`
- Schema name: `nlk_client`
- **Primary column** tab: Display name `Client ID`, Schema name `nlk_clientcode`, Required

**Columns**

| Display name | Schema name | Data type | Settings | CSV column |
|---|---|---|---|---|
| Client ID (primary) | `nlk_clientcode` | Single line of text | Max 10 | `client_id` |
| Company name | `nlk_companyname` | Single line of text | Max 100 | `name` |
| Segment | `nlk_segment` | Single line of text | Max 30 | `segment` |
| Rating | `nlk_rating` | Whole number | Min 1, Max 10 | `rating` |
| Products held | `nlk_productsheld` | Single line of text | Max 200 | `products_held` |
| Relationship revenue (USD) | `nlk_relrevenue` | Decimal | 0 decimal places | `rel_revenue` |
| Relationship cost (USD) | `nlk_relcost` | Decimal | 0 decimal places | `rel_cost` |
| Relationship expected loss (USD) | `nlk_relel` | Decimal | 0 decimal places | `rel_el` |
| Relationship capital (USD) | `nlk_relcapital` | Decimal | 0 decimal places | `rel_capital` |
| EL rate | `nlk_elrate` | Decimal | **4** decimal places | `el_rate` |
| Capital rate | `nlk_capitalrate` | Decimal | **3** decimal places | `capital_rate` |

**Key** (prevents duplicate imports): Clients → **Keys → + New key** → Display name `Client ID key`, column `Client ID`.

### Import `data/clients.csv`
1. Open the **Clients** table → **Import → Import data** (this opens Power Query).
2. Choose **Text/CSV** → **Upload file** → pick `p2/data/clients.csv` → Next. Check the preview shows 50 rows, comma-delimited, with headers.
3. **Transform data**: make sure `rel_*`, `el_rate`, `capital_rate` are **Decimal number** and `rating` is **Whole number**. If Power Query reads `0.0008` as text, set the column type to Decimal number with locale English (United States).
4. Next → **Load to existing table** → `Client` (nlk_client). Map each CSV column to the column in the table above. Leave anything not listed unmapped.
5. Next → Refresh manually → **Publish**. Wait for the refresh to finish (1–2 minutes).
6. Spot-check: open the table's data view and check C-0142, C-0117 and C-0109 against the CSV:
   - C-0142 · rating 3 · rel revenue 4,200,000 · rel capital 9,500,000 · EL rate 0.0004 · capital rate 0.030
   - C-0117 · rating 5 · rel revenue 6,000,000 · rel capital 14,000,000 · EL rate 0.0015 · capital rate 0.050
   - C-0109 · rating 5 · products `Lending` · rel revenue 500,000 · rel capital 4,000,000

---

## Table 2: Deal Approvals

**Properties**
- Display name: `Deal Approval` · Plural: `Deal Approvals`
- Schema name: `nlk_dealapproval`
- **Primary column** tab: Display name `Request ID`, Schema name `nlk_requestid`
- After the table is saved: edit the **Request ID** column → Data type **Autonumber** → Autonumber type **Custom** → format `DR-{SEQNUM:5}` → seed 1 → Save. The first request becomes `DR-00001`.

**Columns**

| Display name | Schema name | Data type | Settings |
|---|---|---|---|
| Request ID (primary) | `nlk_requestid` | Autonumber | `DR-{SEQNUM:5}` |
| Client | `nlk_client` | **Lookup** | Related table: Client |
| Client ID entered | `nlk_clientcode` | Single line of text | Max 20 (kept even when the client isn't found) |
| Product | `nlk_product` | Single line of text | Max 30 (`Lending`) |
| Facility type | `nlk_facilitytype` | Single line of text | Max 20 (`revolver` / `term_loan`) |
| Size (USD) | `nlk_sizeusd` | Decimal | 0 decimal places, max 100,000,000,000 |
| Tenor (years) | `nlk_tenoryears` | Decimal | 1 decimal place |
| Spread (bp) | `nlk_spreadbp` | Decimal | 1 decimal place |
| Upfront fee (bp) | `nlk_upfrontbp` | Decimal | 1 decimal place |
| Commitment fee (bp) | `nlk_commitfeebp` | Decimal | 1 decimal place |
| Revenue (USD) | `nlk_revenue` | Decimal | 2 decimal places |
| Expected loss (USD) | `nlk_expectedloss` | Decimal | 2 decimal places |
| Cost (USD) | `nlk_cost` | Decimal | 2 decimal places |
| Capital (USD) | `nlk_capital` | Decimal | 2 decimal places |
| Deal RAROC | `nlk_dealraroc` | Decimal | **4** decimal places, min −100 |
| Relationship RAROC | `nlk_relraroc` | Decimal | **4** decimal places, min −100 |
| Revenue needed (USD) | `nlk_revenueneeded` | Decimal | 0 decimal places |
| Policy clause | `nlk_policyclause` | Single line of text | Max 100 |
| Policy breach | `nlk_policybreach` | Yes/No | Default No |
| Decision | `nlk_decision` | Single line of text | Max 50 |
| Status | `nlk_status` | Single line of text | Max 30 |
| Approver role | `nlk_approverrole` | Single line of text | Max 30 |
| Approver | `nlk_approver` | Single line of text | Max 100 |
| Approver comment | `nlk_approvercomment` | Multiple lines of text | Max 2,000 |
| Decided on | `nlk_decidedon` | Date and time | Date and time |
| Cross-sell | `nlk_crosssell` | Multiple lines of text | Max 2,000 |
| Message | `nlk_message` | Multiple lines of text | Max 1,000 (rejection reason) |
| Constants version | `nlk_constantsversion` | Single line of text | Max 20 |
| Source | `nlk_source` | Single line of text | Max 30 (`demo-website`) |

**Allowed text values** (the flows write exactly these strings):
- Decision: `Approved` · `Route to segment head` · `Route to pricing committee` · `Rejected (input)`
- Status: `Approved` · `Pending` · `Approved by approver` · `Declined by approver` · `Rejected (input)`
- Approver role: `Segment head` · `Pricing committee` (empty when approved)

**View for the video:** Deal Approvals → Views → Active Deal Approvals → show Request ID, Client, Facility type, Size, Deal RAROC, Relationship RAROC, Decision, Status, Approver, Policy clause, Created on (sort by Created on, newest first).

## Gate
50 rows in Clients, Deal Approvals exists and is empty, and both tables are listed in the solution.
