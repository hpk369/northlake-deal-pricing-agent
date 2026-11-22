# Route Approval (cloud flow) and Get Deal Status (agent flow): build guide

Below-hurdle deals and policy exceptions are never approved by the agent. `Price Deal` logs them with Status `Pending`, and this separate cloud flow sends them to a human. It's separate because agent flows must answer within 100 seconds and a human can take hours.

## Before you start
- **Table names in the Dataverse actions:** the dropdown shows the singular names **Deal Approval** and **Client**. Pick those. Wherever this guide says "Deal Approvals" or "Clients", it means the same tables.
- `Price Deal` works and has logged at least one `Pending` row (run test case F03).
- **Billing:** this flow uses the Dataverse trigger, which is a premium connector. In your pay-as-you-go environment each run of a premium cloud flow is billed at **$0.60** through Azure. Check that **Power Automate** is selected as a product on the `Northlake PAYG` billing plan (Power Platform admin center → Licensing → Billing plans → Northlake PAYG → Edit → Products). Because of the trigger filter below, it only runs for Pending rows, so expect a few dollars at most.
- The first time an environment uses Approvals, Power Automate installs the Approvals solution in it. The first approval can take a few minutes to appear.

---

## Part A: Route Approval cloud flow
make.powerapps.com → Solutions → `Northlake Deal Pricing` → **+ New → Automation → Cloud flow → Automated**. Name it `Route Approval`.

### 1. Trigger: Dataverse → When a row is added, modified or deleted
| Field | Value |
|---|---|
| Change type | Added |
| Table name | Deal Approvals |
| Scope | Organization |
| Filter rows | `nlk_status eq 'Pending'` |

### 2. Approvals → Start and wait for an approval (rename it `Approval`)
| Field | Value |
|---|---|
| Approval type | Approve/Reject - First to respond |
| Title | expression `concat(triggerOutputs()?['body/nlk_requestid'], ' · ', triggerOutputs()?['body/nlk_clientcode'], ' · ', triggerOutputs()?['body/nlk_approverrole'])` |
| Assigned to | `hpk@inkandinfra.com` |
| Details | text below |
| Item link | expression `concat('https://<your-org>.crm3.dynamics.com/main.aspx?pagetype=entityrecord&etn=nlk_dealapproval&id=', triggerOutputs()?['body/nlk_dealapprovalid'])` (use your environment URL) |
| Item link description | `Open in Dataverse` |

**Details** (Markdown). Type the text and insert each value with dynamic content or the expression shown:
```
**Northlake Bank (fictional) – pricing approval**
Route: **@{triggerOutputs()?['body/nlk_approverrole']}** (@{triggerOutputs()?['body/nlk_policyclause']})

| Term | Value |
|---|---|
| Client | @{triggerOutputs()?['body/nlk_clientcode']} |
| Facility | @{triggerOutputs()?['body/nlk_facilitytype']} |
| Size (USD) | @{formatNumber(triggerOutputs()?['body/nlk_sizeusd'], '#,##0', 'en-US')} |
| Tenor | @{triggerOutputs()?['body/nlk_tenoryears']} years |
| Spread | SOFR + @{triggerOutputs()?['body/nlk_spreadbp']} bp |
| Upfront fee | @{triggerOutputs()?['body/nlk_upfrontbp']} bp |
| Deal RAROC | @{formatNumber(mul(float(triggerOutputs()?['body/nlk_dealraroc']), 100), '0.00', 'en-US')}% |
| Relationship RAROC | @{formatNumber(mul(float(triggerOutputs()?['body/nlk_relraroc']), 100), '0.00', 'en-US')}% |
| Hurdle | 15% |

Cross-sell: @{triggerOutputs()?['body/nlk_crosssell']}
```

### 3. Condition `IfApproved`
`body('Approval')?['outcome']` **is equal to** `Approve`

### 4. Dataverse → Update a row (one in each branch; name them `SetApproved` / `SetDeclined`)
Table `Deal Approvals` · Row ID `triggerOutputs()?['body/nlk_dealapprovalid']` · set only these fields (never touch the figures; AM 5.3):

| Field | True branch | False branch |
|---|---|---|
| Status | `Approved by approver` | `Declined by approver` |
| Approver | `first(body('Approval')?['responses'])?['responder']?['displayName']` | same |
| Approver comment | `coalesce(first(body('Approval')?['responses'])?['comments'], '')` | same |
| Decided on | `first(body('Approval')?['responses'])?['responseDate']` | same |

Save. The flow is **on** as soon as it's saved.

### Test
1. Run `Price Deal` with F03 (C-0117) from the agent's test pane.
2. Within a minute, the approval appears in **https://make.powerautomate.com → Action items → Approvals** (Northlake Demo environment) and in the **Power Automate mobile app** (signed in as hpk@).
3. Approve with a comment such as "Relationship clears hurdle; approved at 140 bp".
4. The Deal Approvals row shows `Approved by approver`, your name, the comment and the time.

---

## Part B: Get Deal Status agent flow (tool)
Copilot Studio → agent → **Tools → + Add a tool → New tool → Agent flow**. Name it `Get Deal Status`.

1. **Trigger input:** Text `requestId`, description: "Deal request ID in the format DR-00012."
2. **Compose `ReqId`:** `toUpper(trim(coalesce(triggerBody()?['text'], '')))`
3. **Dataverse → List rows** `FindDeal`: Table `Deal Approvals` · Row count `1` · Filter rows `nlk_requestid eq '@{outputs('ReqId')}'`
4. **Compose `Deal`:** `first(outputs('FindDeal')?['body/value'])`
5. **Respond to the agent** (Text outputs):

| Output | Expression |
|---|---|
| `found` | `if(equals(length(outputs('FindDeal')?['body/value']), 0), 'no', 'yes')` |
| `summary` | `if(equals(length(outputs('FindDeal')?['body/value']), 0), concat('No request ', outputs('ReqId'), ' was found.'), concat(outputs('ReqId'), ' | ', outputs('Deal')?['nlk_clientcode'], ' | Deal RAROC ', formatNumber(mul(float(coalesce(outputs('Deal')?['nlk_dealraroc'], 0)), 100), '0.00', 'en-US'), '% | Decision: ', outputs('Deal')?['nlk_decision'], ' | Status: ', outputs('Deal')?['nlk_status'], if(empty(outputs('Deal')?['nlk_approver']), '', concat(' by ', outputs('Deal')?['nlk_approver'])), if(empty(outputs('Deal')?['nlk_approvercomment']), '', concat(' – "', outputs('Deal')?['nlk_approvercomment'], '"'))))` |

The summary doesn't include anything a public user didn't already see, apart from the approver's display name and comment. Use a neutral display name for hpk@ (e.g. "Segment Head (demo)") if you don't want your name on the public demo.

Save and publish. In Copilot Studio, paste the tool description from `agent/instructions.md`.

## Gate
Approved deal (F01) and routed deal (F03) both work end to end, and both rows have the clause, both RAROC figures and the final status.
