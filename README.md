# Northlake Deal Pricing Agent

**Live demo: https://deals.inkandinfra.com**

A Microsoft Copilot Studio agent that prices corporate loans for **Northlake Bank, a fictional bank**. All clients, figures and policies are synthetic.

- **Deterministic RAROC:** deal and relationship RAROC are calculated in a Power Automate agent flow (`Price Deal`), never by the language model.
- **Policy answers with citations:** retrieval over three policy documents (Loan Pricing Policy, RAROC Methodology, Approval Matrix), always citing the clause.
- **Human-in-the-loop approvals:** deals below the 15% hurdle, and every policy exception, are routed to a human approver through Power Automate Approvals. The agent can't approve anything.
- **Audit log:** every request, including rejected input, is written to a Dataverse table with both RAROC figures, the policy clause and the final decision.

## Stack
Copilot Studio (generative orchestration) · Power Automate (agent flows + cloud flow) · Dataverse · Power Automate Approvals · Python reference model + pytest (CI) · GitHub Pages on a custom domain

## Try it
Open the [live demo](https://deals.inkandinfra.com) and try:
1. `Offer C-0142 a $50M 3-year revolver at SOFR + 125 bp with a 25 bp upfront fee` → approved, 16.00% deal RAROC
2. `Price a $75M 5-year term loan for C-0117 at SOFR + 140 bp, 20 bp upfront` → pending: segment head, 14.28%
3. `What's the minimum spread for a rating-6 client on a 3-year revolver?` → SOFR + 110 bp (LPP 3.2)

## Repo
| Path | What |
|---|---|
| `raroc_reference.py`, `tests/` | Python mirror of the pricing flow and its test suite |
| `knowledge/` | Constants and the three synthetic policy documents |
| `data/clients.csv`, `generator/` | 50 synthetic clients |
| `dataverse/`, `flows/`, `agent/` | Table spec, flow build guides, agent configuration |
| `docs/` | The demo page served by GitHub Pages |
| `BUILD.md` | How to rebuild everything |

A fuller README with screenshots, a video and the test scorecard is coming.
