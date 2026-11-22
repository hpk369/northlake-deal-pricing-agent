# RAROC Methodology

Northlake Bank (fictional) · Corporate & Investment Banking  
Document code: RM · Version 2026.11-v1 · Effective 2026-11-22 · Owner: CIB Pricing Committee  

> **Synthetic. For demonstration only. Northlake Bank is fictional; nothing here is the policy or the parameters of TD Bank or any real bank.**


## 1. Purpose

**RM 1.1** This methodology measures the risk-adjusted profitability of a proposed lending deal (deal RAROC) and of the client's whole relationship including that deal (relationship RAROC).

**RM 1.2** All figures are calculated by the deterministic Price Deal tool. The Deal Pricing Assistant never calculates RAROC, revenue, expected loss or capital itself; it only reports the tool's results.


## 2. Formula

**RM 2.1** RAROC = (revenue − expected loss − cost) ÷ allocated capital.

**RM 2.2** All inputs are annual, first-year figures in US dollars.

**RM 2.3** RAROC is rounded to 4 decimal places (for example 0.1428, shown as 14.28%). Approval decisions use the rounded value.


## 3. Inputs

**RM 3.1** Annual revenue = drawn amount × spread + undrawn amount × commitment fee + amortised upfront fee.

**RM 3.2** The upfront fee is amortised evenly over the tenor: commitment × upfront fee ÷ tenor in years.

**RM 3.3** Drawn amount = commitment × utilisation; undrawn amount = commitment − drawn amount.

**RM 3.4** Revolving facilities are assumed to be 50% utilised (drawn) on average.

**RM 3.5** Term loans are assumed to be 100% drawn, so they earn no commitment fee.

**RM 3.6** Cost = 40% of revenue (the CIB cost-to-income allocation).

**RM 3.7** Expected loss = drawn amount × the expected-loss rate for the client's internal rating (RM 4.1).

**RM 3.8** Allocated capital = total commitment (drawn and undrawn) × the capital rate for the client's internal rating (RM 4.1).

**RM 3.9** Term SOFR itself is treated as a pass-through of funding cost; only the spread counts as revenue.


## 4. Rating parameters

**RM 4.1** Capital rate (allocated capital as a share of the commitment) and expected-loss rate (annual probability of default × loss given default, as a share of the drawn amount) by internal rating:

| Internal rating | Capital rate | Expected-loss rate |
|---|---|---|
| 1 | 2% | 0.01% |
| 2 | 2.5% | 0.02% |
| 3 | 3% | 0.04% |
| 4 | 4% | 0.08% |
| 5 | 5% | 0.15% |
| 6 | 6% | 0.25% |
| 7 | 7.5% | 0.45% |
| 8 | 9% | 0.80% |
| 9 | 11% | 1.40% |
| 10 | 14% | 2.50% |

**RM 4.2** These rates are illustrative economic-capital parameters, not regulatory capital.


## 5. Relationship RAROC

**RM 5.1** Relationship RAROC = (existing relationship revenue + deal revenue − existing expected loss − deal expected loss − existing cost − deal cost) ÷ (existing allocated capital + deal capital).

**RM 5.2** The existing relationship covers every product the client holds with Northlake: Lending, Transaction Banking, Rates & FX Hedging, DCM, ECM and M&A Advisory. Revenue is trailing 12 months; capital, cost and expected loss are current allocations.

**RM 5.3** The proposed deal is added to the relationship pro forma, as if it had already closed.


## 6. Hurdle

**RM 6.1** The RAROC hurdle is 15%. A deal at or above the hurdle with no pricing exception is approved (AM 1.1).

**RM 6.2** The pricing committee floor is 12%. Deals below it always go to the Pricing Committee (AM 1.3).

**RM 6.3** Which approver a deal between the two goes to depends on relationship RAROC (Approval Matrix section 1).


## 7. Cross-sell

**RM 7.1** When both deal RAROC and relationship RAROC are below the hurdle, the tool shows the extra annual fee revenue the relationship would need to reach the hurdle: (hurdle × total allocated capital − total risk-adjusted return) ÷ (1 − cost ratio).

**RM 7.2** This assumes fee products need no extra allocated capital and carry the same 40% cost ratio.

**RM 7.3** Indicative annual revenue by product, used to suggest which products the client does not yet hold could close the gap:

| Product | Indicative annual revenue |
|---|---|
| Transaction Banking | $0.4M to $1.5M |
| Rates & FX Hedging | $0.3M to $2M |
| DCM | $0.5M to $2M |
| ECM | $1M to $4M |
| M&A Advisory | $1.5M to $6M |

**RM 7.4** Indicative figures are for planning only and are not a commitment from the client or the bank.


## 8. Worked example

**RM 8.1** A $50M 3-year revolver for a rating 3 client at SOFR + 125 bp with a 25 bp upfront fee and 25 bp commitment fee: drawn $25M; revenue $416,667 ($312,500 spread + $62,500 commitment fee + $41,667 amortised upfront fee); cost $166,667; expected loss $10,000; capital $1,500,000; deal RAROC = 16.00%, above the 15% hurdle.

