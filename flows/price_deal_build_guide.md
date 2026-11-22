# Price Deal: agent flow build guide

Agent flow the agent calls as a tool. It validates input, reads the client, computes deal and relationship RAROC **with expressions (never the LLM)**, applies the policy floors and the approval matrix, logs a `Deal Approvals` row, and responds to the agent.

Constants version `2026.11-v1` (`knowledge/constants.yaml`). Expected results for testing: `tests/raroc_cases.csv`.

## Before you start
- **Table names in the Dataverse actions:** the dropdown shows the singular names **Deal Approval** and **Client**. Pick those. Wherever this guide says "Deal Approvals" or "Clients", it means the same tables.
- Tables from `dataverse/tables.md` exist and Clients has 50 rows.
- **Set the preferred solution** so the flow lands in the solution: make.powerapps.com → Solutions → `Northlake Deal Pricing` → **… → Set preferred solution**. Check afterwards that the flow is listed in the solution; if not, use **Add existing → Automation → Cloud flow**.
- Create it from the agent: Copilot Studio → Northlake Deal Pricing Assistant → **Tools → + Add a tool → New tool → Agent flow**. The designer opens with the trigger **When an agent calls the flow** and the action **Respond to the agent**.

## How to enter the expressions
- **Rename every action** exactly as written below (click the action title, or **… → Rename**). The expressions refer to actions by name: `outputs('Size')` reads the action named `Size`. No spaces in names.
- For a Compose: add **Data Operation → Compose**, click in **Inputs**, choose **fx** (Insert expression), paste the expression, click **Add**.
- Add the actions **in the order listed**. Most are Compose actions in one straight line, so the order only matters for what each one references.

---

## 1. Trigger inputs
On **When an agent calls the flow → + Add an input**, add these **in this order** (the order fixes the internal names `text`, `text_1`, `number`, `number_1`, …):

| # | Type | Name | Description (the agent reads this when filling slots) |
|---|---|---|---|
| 1 | Text | `clientId` | Client ID in the format C-0142 (letter C, hyphen, four digits). |
| 2 | Text | `facilityType` | Facility type: revolver (revolving credit facility) or term_loan. |
| 3 | Number | `sizeUSD` | Total commitment in US dollars as a plain number, e.g. 50000000 for $50M. |
| 4 | Number | `tenorYears` | Tenor in years, e.g. 3. |
| 5 | Number | `spreadBp` | Spread over SOFR in basis points, e.g. 125 for SOFR + 125 bp. |
| 6 | Number | `upfrontFeeBp` | Upfront fee in basis points of the commitment, e.g. 25. |
| 7 | Number | `commitFeeBp` | Commitment fee on the undrawn amount in basis points. Optional: if the banker didn't give one, leave it empty and 25 bp is used. |

Make `commitFeeBp` optional (**… → Make the field optional**).

> **Check the internal names:** after adding the inputs, add a temporary Compose, open the dynamic content list, insert `clientId`, and switch to code view (or hover). It should show `triggerBody()?['text']`. If yours differ, use your names in step 2. Then delete the temporary Compose.

## 2. Normalise the inputs (7 × Compose)

| Name | Expression |
|---|---|
| `ClientId` | `toUpper(trim(coalesce(triggerBody()?['text'], '')))` |
| `Facility` | `replace(replace(toLower(trim(coalesce(triggerBody()?['text_1'], ''))), ' ', '_'), '-', '_')` |
| `Size` | `float(coalesce(triggerBody()?['number'], 0))` |
| `Tenor` | `float(coalesce(triggerBody()?['number_1'], 0))` |
| `Spread` | `float(coalesce(triggerBody()?['number_2'], -1))` |
| `Upfront` | `float(coalesce(triggerBody()?['number_3'], -1))` |
| `CommitFee` | `float(coalesce(triggerBody()?['number_4'], 25))` |

## 3. Validate (Compose `ErrorMsg`, then a Condition)

**Compose `ErrorMsg`** (empty string means valid):
```
concat(
 if(and(equals(length(outputs('ClientId')), 6), startsWith(outputs('ClientId'), 'C-'), isInt(replace(outputs('ClientId'), 'C-', ''))), '', 'Client ID must look like C-0142. '),
 if(or(equals(outputs('Facility'), 'revolver'), equals(outputs('Facility'), 'term_loan')), '', 'Facility type must be revolver or term loan. '),
 if(and(greaterOrEquals(outputs('Size'), 1000000), lessOrEquals(outputs('Size'), 2000000000)), '', 'Size must be between $1M and $2B. '),
 if(and(greaterOrEquals(outputs('Tenor'), 1), lessOrEquals(outputs('Tenor'), 7)), '', 'Tenor must be between 1 and 7 years. '),
 if(and(greaterOrEquals(outputs('Spread'), 0), lessOrEquals(outputs('Spread'), 1000)), '', 'Spread must be between 0 and 1,000 bp. '),
 if(and(greaterOrEquals(outputs('Upfront'), 0), lessOrEquals(outputs('Upfront'), 200)), '', 'Upfront fee must be between 0 and 200 bp. '),
 if(and(greaterOrEquals(outputs('CommitFee'), 0), lessOrEquals(outputs('CommitFee'), 200)), '', 'Commitment fee must be between 0 and 200 bp. ')
)
```
If the designer rejects `isInt`, replace that one test with `equals(length(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(outputs('ClientId'),'C-',''),'0',''),'1',''),'2',''),'3',''),'4',''),'5',''),'6',''),'7',''),'8',''),'9','')), 0)`.

**Condition `IfInvalid`**: `outputs('ErrorMsg')` **is not equal to** (empty, leave the right side blank).

**True branch** (3 actions):
1. **Dataverse → Add a new row** named `LogInvalid`. Table `Deal Approvals`. Show all fields and set:
   - Request ID: leave empty (autonumber)
   - Client ID entered: `outputs('ClientId')` · Facility type: `outputs('Facility')` · Size: `outputs('Size')` · Tenor: `outputs('Tenor')` · Spread: `outputs('Spread')` · Upfront fee: `outputs('Upfront')` · Commitment fee: `outputs('CommitFee')`
   - Decision: `Rejected (input)` · Status: `Rejected (input)` · Message: `outputs('ErrorMsg')` · Constants version: `2026.11-v1` · Source: `demo-website` · Product: `Lending`
   - Numbers that came in as text may fail here: if the row fails to save because of a value out of range, set Size, Tenor, Spread and fees to `if(greater(outputs('Size'), 100000000000), 0, outputs('Size'))` and so on, or leave them out. The message keeps the reason.
2. **Respond to the agent** named `RespondInvalid` with the outputs in section 9, set to: status `invalid` · requestId `outputs('LogInvalid')?['body/nlk_requestid']` · summary `concat('Request rejected: ', outputs('ErrorMsg'))` · every other output empty.
3. **Control → Terminate**, status **Succeeded**.

## 4. Daily cap (List rows + Condition)
**Dataverse → List rows** named `Today`: Table `Deal Approvals` · Select columns `nlk_dealapprovalid` · Filter rows:
```
createdon ge @{startOfDay(utcNow())}
```
(type `createdon ge `, then insert the expression `startOfDay(utcNow())`) · Row count `51`.

**Condition `IfCapReached`**: expression `length(outputs('Today')?['body/value'])` **is greater than or equal to** `50`.
- True: **Respond to the agent** `RespondCap` with status `daily_limit` and summary `Daily demo limit of 50 priced requests reached. Please try again tomorrow.` → **Terminate** (Succeeded). Not logged, so the log can't be flooded.

## 5. Get the client
**Dataverse → List rows** named `GetClient`: Table `Clients` · Row count `1` · Filter rows:
```
nlk_clientcode eq '@{outputs('ClientId')}'
```

**Condition `IfUnknown`**: `length(outputs('GetClient')?['body/value'])` **is equal to** `0`.
- True: **Add a new row** `LogUnknown` (same as `LogInvalid`, but Message `concat('Client ', outputs('ClientId'), ' was not found.')`) → **Respond to the agent** `RespondUnknown`: status `unknown_client`, requestId `outputs('LogUnknown')?['body/nlk_requestid']`, summary `concat('Client ', outputs('ClientId'), ' was not found. Check the client ID (format C-0142).')` → **Terminate** (Succeeded).

**Compose `Client`**: `first(outputs('GetClient')?['body/value'])`

## 6. Compute RAROC (Compose actions, in this order)

| Name | Expression | Constant source |
|---|---|---|
| `Rating` | `int(outputs('Client')?['nlk_rating'])` | |
| `Util` | `if(equals(outputs('Facility'), 'revolver'), 0.5, 1.0)` | RM 3.4, RM 3.5 |
| `Drawn` | `mul(outputs('Size'), outputs('Util'))` | RM 3.3 |
| `Undrawn` | `sub(outputs('Size'), outputs('Drawn'))` | RM 3.3 |
| `Revenue` | `add(add(div(mul(outputs('Drawn'), outputs('Spread')), 10000.0), div(mul(outputs('Undrawn'), outputs('CommitFee')), 10000.0)), div(div(mul(outputs('Size'), outputs('Upfront')), 10000.0), outputs('Tenor')))` | RM 3.1, RM 3.2 |
| `EL` | `mul(outputs('Drawn'), float(outputs('Client')?['nlk_elrate']))` | RM 3.7 |
| `Cost` | `mul(outputs('Revenue'), 0.4)` | RM 3.6 |
| `Capital` | `mul(outputs('Size'), float(outputs('Client')?['nlk_capitalrate']))` | RM 3.8 |
| `DealRAR` | `sub(sub(outputs('Revenue'), outputs('EL')), outputs('Cost'))` | RM 2.1 |
| `DealRAROC` | `float(formatNumber(div(outputs('DealRAR'), outputs('Capital')), '0.0000', 'en-US'))` | RM 2.3 |
| `RelRAR` | `sub(sub(float(outputs('Client')?['nlk_relrevenue']), float(outputs('Client')?['nlk_relel'])), float(outputs('Client')?['nlk_relcost']))` | RM 5.1 |
| `TotalRAR` | `add(outputs('RelRAR'), outputs('DealRAR'))` | RM 5.3 |
| `TotalCapital` | `add(float(outputs('Client')?['nlk_relcapital']), outputs('Capital'))` | RM 5.1 |
| `RelRAROC` | `float(formatNumber(div(outputs('TotalRAR'), outputs('TotalCapital')), '0.0000', 'en-US'))` | RM 2.3 |

Why `10000.0` and `float()`: `div()` of two whole numbers does integer division in Power Automate. Keeping one side a decimal avoids that.

## 7. Policy checks and decision (Compose actions)

| Name | Expression | Clause |
|---|---|---|
| `FloorBase` | `if(lessOrEquals(outputs('Rating'), 2), 60, if(lessOrEquals(outputs('Rating'), 4), 85, if(lessOrEquals(outputs('Rating'), 6), 110, if(lessOrEquals(outputs('Rating'), 8), 160, 250))))` | LPP 3.2 |
| `Floor` | `add(outputs('FloorBase'), if(lessOrEquals(outputs('Tenor'), 3), 0, if(lessOrEquals(outputs('Tenor'), 5), 15, 30)))` | LPP 3.3 |
| `MaxTenor` | `if(equals(outputs('Facility'), 'revolver'), 5, 7)` | LPP 5.3, 5.4 |
| `Breaches` | `concat(if(less(outputs('Spread'), outputs('Floor')), '; LPP 3.2', ''), if(less(outputs('Upfront'), 15), '; LPP 4.1', ''), if(greater(outputs('Tenor'), outputs('MaxTenor')), if(equals(outputs('Facility'), 'revolver'), '; LPP 5.3', '; LPP 5.4'), ''))` | LPP 6.1 |
| `PolicyBreach` | `not(equals(outputs('Breaches'), ''))` | |
| `Decision` | `if(outputs('PolicyBreach'), 'Route to pricing committee', if(greaterOrEquals(outputs('DealRAROC'), 0.15), 'Approved', if(and(greaterOrEquals(outputs('DealRAROC'), 0.12), greaterOrEquals(outputs('RelRAROC'), 0.15)), 'Route to segment head', 'Route to pricing committee')))` | AM 1, AM 2.1 |
| `DecisionClause` | `if(outputs('PolicyBreach'), 'AM 2.1', if(greaterOrEquals(outputs('DealRAROC'), 0.15), 'AM 1.1', if(greaterOrEquals(outputs('DealRAROC'), 0.12), if(greaterOrEquals(outputs('RelRAROC'), 0.15), 'AM 1.2', 'AM 1.4'), 'AM 1.3')))` | |
| `PolicyClause` | `concat(outputs('DecisionClause'), outputs('Breaches'), if(outputs('PolicyBreach'), '; LPP 6.2', ''))` | |
| `RowStatus` | `if(equals(outputs('Decision'), 'Approved'), 'Approved', 'Pending')` | |
| `ApproverRole` | `if(equals(outputs('Decision'), 'Route to segment head'), 'Segment head', if(equals(outputs('Decision'), 'Route to pricing committee'), 'Pricing committee', ''))` | AM 3 |

## 8. Cross-sell (RM 7.1)

| Name | Action | Expression |
|---|---|---|
| `RevenueNeeded` | Compose | `if(and(less(outputs('DealRAROC'), 0.15), less(outputs('RelRAROC'), 0.15)), float(formatNumber(max(0, div(sub(mul(0.15, outputs('TotalCapital')), outputs('TotalRAR')), 0.6)), '0', 'en-US')), 0)` |
| `NotHeld` | **Data Operation → Filter array** | From: `createArray('Transaction Banking', 'Rates & FX Hedging', 'DCM', 'ECM', 'M&A Advisory')` · switch to **Edit in advanced mode** and enter `@not(contains(outputs('Client')?['nlk_productsheld'], item()))` |
| `CrossSell` | Compose | `if(greater(outputs('RevenueNeeded'), 0), concat('Relationship RAROC is ', formatNumber(mul(outputs('RelRAROC'), 100), '0.00', 'en-US'), '% vs the 15% hurdle. About $', formatNumber(outputs('RevenueNeeded'), '#,##0', 'en-US'), ' of extra annual fee revenue would lift it to 15% (RM 7.1). Products not held: ', join(body('NotHeld'), ', '), '. Indicative annual revenue by product is in RM 7.3.'), '')` |

## 9. Log the request (Dataverse → Add a new row, named `LogDeal`)
Table `Deal Approvals`. **Show all** and set:

| Field | Value |
|---|---|
| Client (Clients) | `concat('nlk_clients(', outputs('Client')?['nlk_clientid'], ')')` |
| Client ID entered | `outputs('ClientId')` |
| Product | `Lending` |
| Facility type | `outputs('Facility')` |
| Size (USD) · Tenor · Spread · Upfront fee · Commitment fee | `outputs('Size')` · `outputs('Tenor')` · `outputs('Spread')` · `outputs('Upfront')` · `outputs('CommitFee')` |
| Revenue · Expected loss · Cost · Capital | `outputs('Revenue')` · `outputs('EL')` · `outputs('Cost')` · `outputs('Capital')` |
| Deal RAROC · Relationship RAROC | `outputs('DealRAROC')` · `outputs('RelRAROC')` |
| Revenue needed | `outputs('RevenueNeeded')` |
| Policy clause | `outputs('PolicyClause')` |
| Policy breach | `outputs('PolicyBreach')` |
| Decision · Status · Approver role | `outputs('Decision')` · `outputs('RowStatus')` · `outputs('ApproverRole')` |
| Cross-sell | `outputs('CrossSell')` |
| Constants version · Source | `2026.11-v1` · `demo-website` |

If the lookup is rejected, check the table's plural (entity set) name in Tables → Clients → Properties → Advanced → it should be `nlk_clients`.

## 10. Respond to the agent (named `RespondOK`)
Add these **Text** outputs on **every** Respond action (the invalid, cap and unknown ones too; leave unused ones empty):

| Output | Value in `RespondOK` |
|---|---|
| `status` | `ok` |
| `requestId` | `outputs('LogDeal')?['body/nlk_requestid']` |
| `clientName` | `outputs('Client')?['nlk_companyname']` |
| `dealRAROC` | `concat(formatNumber(mul(outputs('DealRAROC'), 100), '0.00', 'en-US'), '%')` |
| `relationshipRAROC` | `concat(formatNumber(mul(outputs('RelRAROC'), 100), '0.00', 'en-US'), '%')` |
| `decision` | `outputs('Decision')` |
| `statusText` | `if(equals(outputs('RowStatus'), 'Approved'), 'Approved', concat('Pending: ', toLower(outputs('ApproverRole'))))` |
| `policyClause` | `outputs('PolicyClause')` |
| `crossSell` | `outputs('CrossSell')` |
| `summary` | see below |

`summary`:
```
concat('Request ', outputs('LogDeal')?['body/nlk_requestid'], ' | ', outputs('ClientId'), ' ', outputs('Client')?['nlk_companyname'], ' | $', formatNumber(outputs('Size'), '#,##0', 'en-US'), ' ', outputs('Tenor'), '-year ', replace(outputs('Facility'), '_', ' '), ' at SOFR + ', outputs('Spread'), ' bp, ', outputs('Upfront'), ' bp upfront | Deal RAROC ', formatNumber(mul(outputs('DealRAROC'), 100), '0.00', 'en-US'), '%, relationship RAROC ', formatNumber(mul(outputs('RelRAROC'), 100), '0.00', 'en-US'), '% vs 15% hurdle | ', if(equals(outputs('RowStatus'), 'Approved'), 'Approved', concat('Pending: ', toLower(outputs('ApproverRole')))), ' | Policy: ', outputs('PolicyClause'))
```

**Save**, then **Publish** the flow. Back in Copilot Studio, the tool's name should be `Price Deal`; paste the tool description from `agent/instructions.md`.

> If the designer won't allow a Respond action inside a Condition branch: create Text **variables** (`vStatus`, `vSummary`, …) at the top, set them in each branch instead of responding, wrap steps 5–9 in a Condition on `vStatus` being empty, and keep one Respond action at the end. Tell me and I'll write that variant out.

---

## Test (gate: all match to 4 dp, run < 10 s)
In the flow designer **Test → Manually**, run each row of `tests/raroc_cases.csv` and compare `dealRAROC`, `relationshipRAROC`, `decision`, `policyClause`:

| Case | Inputs | Deal RAROC | Rel. RAROC | Decision | Clause |
|---|---|---|---|---|---|
| F01 | C-0142 revolver 50,000,000 · 3 · 125 · 25 | 16.00% | 22.73% | Approved | AM 1.1 |
| F02 | C-0124 revolver 150,000,000 · 5 · 120 · 30 | 15.03% | 22.27% | Approved | AM 1.1 |
| F03 | C-0117 term_loan 75,000,000 · 5 · 140 · 20 | 14.28% | 21.89% | Segment head | AM 1.2 |
| F04 | C-0128 term_loan 100,000,000 · 4 · 135 · 25 | 13.95% | 10.89% | Pricing committee | AM 1.4 (needs $754,167) |
| F05 | C-0133 revolver 60,000,000 · 3 · 115 · 20 | 5.58% | 9.44% | Pricing committee | AM 1.3 (needs $981,667) |
| F06 | C-0109 revolver 40,000,000 · 3 · 130 · 20 | 8.60% | 6.03% | Pricing committee | AM 1.3 (needs $896,667) |
| F07 | C-0133 revolver 60,000,000 · 3 · **95** · 20 | 4.58% | 9.10% | Pricing committee | AM 2.1; LPP 3.2; LPP 6.2 |
| F08 | C-0142 revolver 50,000,000 · **6** · 125 · 25 | 15.17% | 22.61% | Pricing committee | AM 2.1; LPP 5.3; LPP 6.2 |
| F09 | C-0142 revolver **5,000,000,000 · 15** · 125 · 25 | — | — | Rejected (input) | size + tenor messages |
| F10 | **C-9999** revolver 50,000,000 · 3 · 125 · 25 | — | — | Rejected (input) | client not found |

Commitment fee 25 bp in every case. F08 shows a deal above the hurdle on RAROC that still goes to committee because the revolver tenor breaks LPP 5.3: a policy exception is never auto-approved.

Then open **run history** for F01 and screenshot the `DealRAROC` Compose output (README: "RAROC computed in the flow, not the LLM").
