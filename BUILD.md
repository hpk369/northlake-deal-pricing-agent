# BUILD · Deal Pricing & RAROC Agent: build files

Northlake Bank (fictional). Synthetic data only. Constants version `2026.11-v1`, hurdle 15%, committee floor 12%.

| File | What it's for | Plan note |
|---|---|---|
| `knowledge/constants.yaml` | Every number (hurdle, rates, floors, limits). Change it here, then re-run the scripts | P2 03 |
| `raroc_reference.py` | Python mirror of the Price Deal flow. `python3 raroc_reference.py C-0142 revolver 50000000 3 125 25` | P2 04 |
| `generator/generate_clients.py` → `data/clients.csv` | 50 clients; checks the 5 path clients land on their routes | P2 02 |
| `knowledge/build_knowledge.py` → `knowledge/*.docx` (+ `.md`) | The 3 policy documents to upload to the agent | P2 03 |
| `dataverse/tables.md` | Clients + Deal Approvals columns and the CSV import steps (manual route) | P2 02 |
| `dataverse/create_tables.py` | Creates both tables in the solution and loads the 50 clients via the Web API, signed in as hpk@ (Azure CLI) | P2 02 |
| `flows/price_deal_build_guide.md` | Price Deal agent flow, every action and expression | P2 04 |
| `flows/route_approval_build_guide.md` | Route Approval cloud flow + Get Deal Status agent flow | P2 05 |
| `agent/instructions.md` | Description, instructions, tool descriptions, welcome message, settings | P2 06 |
| `tests/raroc_cases.csv`, `tests/test_raroc.py` | 10 flow cases with expected outputs; pytest suite | P2 04, P2 07 |
| `tests/conversation_cases.md` | 15 agent cases + scorecard | P2 07 |

Rebuild everything after changing constants:
```bash
cd p2
python3 generator/generate_clients.py
python3 tests/make_cases.py
python3 knowledge/build_knowledge.py
python3 -m pytest -q tests
```

## Build order (Sun Nov 22)
1. Solution `NorthlakeDealPricing` (prefix `nlk`), set as preferred solution
2. `dataverse/tables.md`: both tables, import `data/clients.csv`
3. Upload the 3 `.docx` files; ask the policy questions
4. `flows/price_deal_build_guide.md`; run F01–F10
5. `flows/route_approval_build_guide.md`; approve F03 end to end
6. `agent/instructions.md`; suggested prompts + red team
7. `tests/conversation_cases.md` on the published site
8. Export the solution (P2 08)

## Design choices beyond the plan notes
- A **policy exception** (spread below floor, upfront fee below 15 bp, tenor above maximum) always goes to the Pricing Committee, even above the hurdle (LPP 6.2, AM 2.1). Auto-approving an exception would undercut the control story.
- **Cross-sell** shows only when both deal and relationship RAROC are below hurdle, and the revenue needed is grossed up for the 40% cost ratio: (hurdle × total capital − total risk-adjusted return) ÷ (1 − 0.40).
- Decisions use RAROC **rounded to 4 dp** in both the flow and the reference, so they can't disagree at the boundary.
- Text columns instead of Choice, Decimal (USD) instead of Currency, and `nlk_clientcode` as the Clients primary column: see `dataverse/tables.md`.
