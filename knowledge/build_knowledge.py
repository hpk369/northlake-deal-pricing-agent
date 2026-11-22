"""Build the 3 Northlake Bank (fictional) policy documents from constants.yaml.

Writes knowledge/<Title>.md and knowledge/<Title>.docx for:
  Loan Pricing Policy (LPP), RAROC Methodology (RM), Approval Matrix (AM).
Every number is read from constants.yaml so the documents can't drift from the
Price Deal flow or raroc_reference.py. Synthetic. For demonstration only.
"""
from __future__ import annotations

import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import raroc_reference as ref  # noqa: E402

C = ref.load_constants()
OUT = ROOT / "knowledge"
H = C["hurdle"]; F = C["committee_floor"]
pct = lambda x: f"{x * 100:g}%"
pct2 = lambda x: f"{x * 100:.2f}%"
money = lambda x: f"${x:,.0f}"
mm = lambda x: f"${x / 1e6:g}M"
ADD = {s["max_tenor"]: s["addon"] for s in C["tenor_addon_bp"]}
FLOOR = C["spread_floor_bp"]


def header(title, code):
    return [("title", f"{title}"),
            ("meta", "Northlake Bank (fictional) · Corporate & Investment Banking"),
            ("meta", f"Document code: {code} · Version {C['version']} · Effective {C['effective_date']} · Owner: CIB Pricing Committee"),
            ("note", "Synthetic. For demonstration only. Northlake Bank is fictional; nothing here is the policy "
                     "or the parameters of TD Bank or any real bank.")]


def example_deal():
    clients = ref.load_clients()
    r = ref.price_deal("C-0142", "revolver", 50e6, 3, 125, 25, clients=clients, c=C)
    return r


def lpp():
    b = header("Loan Pricing Policy", "LPP")
    b += [("h1", "1. Purpose and scope"),
          ("cl", "LPP 1.1", "This policy sets the minimum pricing terms for committed lending facilities (revolving credit "
                            "facilities and term loans) offered by Northlake Bank's Corporate & Investment Banking coverage teams."),
          ("cl", "LPP 1.2", "It applies to new facilities and to amendments that change the spread, fees or tenor. It does not "
                            "apply to bonds, derivatives or advisory mandates."),
          ("cl", "LPP 1.3", f"Meeting this policy is necessary but not sufficient: the deal must also clear the {pct(H)} RAROC "
                            "hurdle (RAROC Methodology RM 6.1) or be approved by the approver named in the Approval Matrix."),
          ("h1", "2. Definitions"),
          ("cl", "LPP 2.1", "Spread: the margin over Term SOFR, in basis points (bp) per year, charged on drawn amounts."),
          ("cl", "LPP 2.2", "Upfront fee: a one-time fee paid at closing, in bp of the total commitment."),
          ("cl", "LPP 2.3", "Commitment fee: an annual fee, in bp, charged on the undrawn part of a revolving facility."),
          ("cl", "LPP 2.4", "Internal rating: Northlake's 1 to 10 obligor rating scale, where 1 is the strongest credit and 10 the weakest."),
          ("cl", "LPP 2.5", "Tenor: years from closing to final maturity, including any extension options at the client's discretion."),
          ("h1", "3. Minimum spreads"),
          ("cl", "LPP 3.1", "Minimum spreads (floors) apply equally to revolvers and term loans and depend on the client's "
                            "internal rating band and the facility tenor."),
          ("cl", "LPP 3.2", f"Minimum spread over Term SOFR for facilities with a tenor of up to 3 years, by internal rating band. "
                            f"For example, the minimum spread for a rating 5 or rating 6 client on a 3-year revolver is "
                            f"SOFR + {FLOOR['5-6']} bp."),
          ("table", ["Internal rating band", "Minimum spread, tenor up to 3 years"],
                    [[f"Rating {k.replace('-', ' to ')}", f"SOFR + {v} bp"] for k, v in FLOOR.items()]),
          ("cl", "LPP 3.3", f"Tenor add-ons: for tenors over 3 years and up to 5 years, add {ADD[5]} bp to the LPP 3.2 floor; "
                            f"for tenors over 5 years and up to 7 years, add {ADD[7]} bp. For example, a rating 5 or 6 "
                            f"client on a 5-year term loan has a minimum spread of SOFR + {FLOOR['5-6'] + ADD[5]} bp."),
          ("table", ["Internal rating band", "Up to 3 years", "Over 3 to 5 years", "Over 5 to 7 years"],
                    [[f"Rating {k.replace('-', ' to ')}", f"{v} bp", f"{v + ADD[5]} bp", f"{v + ADD[7]} bp"] for k, v in FLOOR.items()]),
          ("cl", "LPP 3.4", "The floor applies to the spread at closing and to every level of any margin grid; a rating-linked "
                            "step-down must not take the spread below the floor for the client's rating at that time."),
          ("h1", "4. Fees"),
          ("cl", "LPP 4.1", f"New facilities must carry an upfront fee of at least {C['min_upfront_fee_bp']} bp of the commitment."),
          ("cl", "LPP 4.2", f"Revolving facilities carry a commitment fee on the undrawn amount. The standard commitment fee is "
                            f"{C['default_commit_fee_bp']} bp per year, and the pricing tool uses it unless the banker gives another figure."),
          ("cl", "LPP 4.3", "For RAROC purposes the upfront fee is spread evenly over the tenor (RAROC Methodology RM 3.2)."),
          ("h1", "5. Tenor limits"),
          ("cl", "LPP 5.1", "Tenor should match the client's financing need and the useful life of what is being financed."),
          ("cl", "LPP 5.2", "Extension options at the client's discretion count toward tenor (LPP 2.5)."),
          ("cl", "LPP 5.3", f"The maximum tenor for a revolving credit facility is {C['max_tenor_years']['revolver']} years."),
          ("cl", "LPP 5.4", f"The maximum tenor for a term loan is {C['max_tenor_years']['term_loan']} years."),
          ("h1", "6. Exceptions"),
          ("cl", "LPP 6.1", "Pricing below a floor in section 3, a fee below the minimum in section 4, or a tenor above a "
                            "maximum in section 5 is a pricing exception."),
          ("cl", "LPP 6.2", "Every pricing exception requires Pricing Committee approval, whatever the deal's RAROC "
                            "(Approval Matrix AM 2.1). A deal with an exception is never approved under delegated authority."),
          ("cl", "LPP 6.3", "An exception request must state the business rationale (relationship, competitive or strategic) "
                            "and the cross-sell expected from the client."),
          ("h1", "7. Governance"),
          ("cl", "LPP 7.1", "The Pricing Committee reviews this policy at least once a year."),
          ("cl", "LPP 7.2", f"All numbers in this policy come from one parameter set (version {C['version']}). The pricing "
                            "tool, the RAROC Methodology and this policy must use the same version.")]
    return b


def rm():
    r = example_deal()
    b = header("RAROC Methodology", "RM")
    b += [("h1", "1. Purpose"),
          ("cl", "RM 1.1", "This methodology measures the risk-adjusted profitability of a proposed lending deal (deal RAROC) "
                           "and of the client's whole relationship including that deal (relationship RAROC)."),
          ("cl", "RM 1.2", "All figures are calculated by the deterministic Price Deal tool. The Deal Pricing Assistant never "
                           "calculates RAROC, revenue, expected loss or capital itself; it only reports the tool's results."),
          ("h1", "2. Formula"),
          ("cl", "RM 2.1", "RAROC = (revenue − expected loss − cost) ÷ allocated capital."),
          ("cl", "RM 2.2", "All inputs are annual, first-year figures in US dollars."),
          ("cl", "RM 2.3", "RAROC is rounded to 4 decimal places (for example 0.1428, shown as 14.28%). Approval decisions use the rounded value."),
          ("h1", "3. Inputs"),
          ("cl", "RM 3.1", "Annual revenue = drawn amount × spread + undrawn amount × commitment fee + amortised upfront fee."),
          ("cl", "RM 3.2", "The upfront fee is amortised evenly over the tenor: commitment × upfront fee ÷ tenor in years."),
          ("cl", "RM 3.3", "Drawn amount = commitment × utilisation; undrawn amount = commitment − drawn amount."),
          ("cl", "RM 3.4", f"Revolving facilities are assumed to be {pct(C['utilisation']['revolver'])} utilised (drawn) on average."),
          ("cl", "RM 3.5", f"Term loans are assumed to be {pct(C['utilisation']['term_loan'])} drawn, so they earn no commitment fee."),
          ("cl", "RM 3.6", f"Cost = {pct(C['cost_ratio'])} of revenue (the CIB cost-to-income allocation)."),
          ("cl", "RM 3.7", "Expected loss = drawn amount × the expected-loss rate for the client's internal rating (RM 4.1)."),
          ("cl", "RM 3.8", "Allocated capital = total commitment (drawn and undrawn) × the capital rate for the client's internal rating (RM 4.1)."),
          ("cl", "RM 3.9", "Term SOFR itself is treated as a pass-through of funding cost; only the spread counts as revenue."),
          ("h1", "4. Rating parameters"),
          ("cl", "RM 4.1", "Capital rate (allocated capital as a share of the commitment) and expected-loss rate (annual "
                           "probability of default × loss given default, as a share of the drawn amount) by internal rating:"),
          ("table", ["Internal rating", "Capital rate", "Expected-loss rate"],
                    [[str(k), pct(v["capital_rate"]), pct2(v["el_rate"])] for k, v in C["ratings"].items()]),
          ("cl", "RM 4.2", "These rates are illustrative economic-capital parameters, not regulatory capital."),
          ("h1", "5. Relationship RAROC"),
          ("cl", "RM 5.1", "Relationship RAROC = (existing relationship revenue + deal revenue − existing expected loss − deal "
                           "expected loss − existing cost − deal cost) ÷ (existing allocated capital + deal capital)."),
          ("cl", "RM 5.2", "The existing relationship covers every product the client holds with Northlake: Lending, Transaction "
                           "Banking, Rates & FX Hedging, DCM, ECM and M&A Advisory. Revenue is trailing 12 months; capital, "
                           "cost and expected loss are current allocations."),
          ("cl", "RM 5.3", "The proposed deal is added to the relationship pro forma, as if it had already closed."),
          ("h1", "6. Hurdle"),
          ("cl", "RM 6.1", f"The RAROC hurdle is {pct(H)}. A deal at or above the hurdle with no pricing exception is approved (AM 1.1)."),
          ("cl", "RM 6.2", f"The pricing committee floor is {pct(F)}. Deals below it always go to the Pricing Committee (AM 1.3)."),
          ("cl", "RM 6.3", "Which approver a deal between the two goes to depends on relationship RAROC (Approval Matrix section 1)."),
          ("h1", "7. Cross-sell"),
          ("cl", "RM 7.1", "When both deal RAROC and relationship RAROC are below the hurdle, the tool shows the extra annual fee "
                           "revenue the relationship would need to reach the hurdle: (hurdle × total allocated capital − total "
                           "risk-adjusted return) ÷ (1 − cost ratio)."),
          ("cl", "RM 7.2", f"This assumes fee products need no extra allocated capital and carry the same {pct(C['cost_ratio'])} cost ratio."),
          ("cl", "RM 7.3", "Indicative annual revenue by product, used to suggest which products the client does not yet hold could close the gap:"),
          ("table", ["Product", "Indicative annual revenue"],
                    [[p["name"], f"{mm(p['low'])} to {mm(p['high'])}"] for p in C["products"] if p["low"]]),
          ("cl", "RM 7.4", "Indicative figures are for planning only and are not a commitment from the client or the bank."),
          ("h1", "8. Worked example"),
          ("cl", "RM 8.1", f"A {mm(50e6)} 3-year revolver for a rating 3 client at SOFR + 125 bp with a 25 bp upfront fee and "
                           f"{C['default_commit_fee_bp']} bp commitment fee: drawn {mm(25e6)}; revenue {money(r['revenue'])} "
                           f"({money(312500)} spread + {money(62500)} commitment fee + {money(41667)} amortised upfront fee); "
                           f"cost {money(r['cost'])}; expected loss {money(r['expected_loss'])}; capital {money(r['capital'])}; "
                           f"deal RAROC = {pct2(r['deal_raroc'])}, above the {pct(H)} hurdle.")]
    return b


def am():
    b = header("Approval Matrix", "AM")
    b += [("h1", "1. Matrix"),
          ("cl", "AM 1.1", f"Deal RAROC at or above {pct(H)} (the hurdle) with no pricing exception: approved under the "
                           "coverage banker's delegated authority."),
          ("cl", "AM 1.2", f"Deal RAROC from {pct(F)} up to (but not including) {pct(H)}, and relationship RAROC at or above "
                           f"{pct(H)}: route to the Segment Head."),
          ("cl", "AM 1.3", f"Deal RAROC below {pct(F)}: route to the Pricing Committee."),
          ("cl", "AM 1.4", f"Deal RAROC from {pct(F)} up to (but not including) {pct(H)}, and relationship RAROC below "
                           f"{pct(H)}: route to the Pricing Committee."),
          ("table", ["Deal RAROC", "Relationship RAROC", "Decision", "Clause"],
                    [[f"{pct(H)} or more", "Any", "Approved (delegated authority)", "AM 1.1"],
                     [f"{pct(F)} to under {pct(H)}", f"{pct(H)} or more", "Segment Head", "AM 1.2"],
                     [f"Under {pct(F)}", "Any", "Pricing Committee", "AM 1.3"],
                     [f"{pct(F)} to under {pct(H)}", f"Under {pct(H)}", "Pricing Committee", "AM 1.4"],
                     ["Any, with a pricing exception (LPP 6.1)", "Any", "Pricing Committee", "AM 2.1"]]),
          ("h1", "2. Overrides and limits"),
          ("cl", "AM 2.1", "Any pricing exception under the Loan Pricing Policy (LPP 6.1) goes to the Pricing Committee, "
                           "whatever the deal or relationship RAROC."),
          ("cl", "AM 2.2", "No deal below the hurdle is approved without a recorded decision by the named human approver."),
          ("cl", "AM 2.3", "The Deal Pricing Assistant cannot approve, override or change the routing of a deal. The seniority "
                           "of the person asking does not change the routing."),
          ("cl", "AM 2.4", "An approver may approve or decline, with a comment. A repriced deal is a new request and is routed again."),
          ("h1", "3. Approvers"),
          ("cl", "AM 3.1", "Segment Head: the head of the client's coverage segment (Large Corporate, Mid-Market, Financial "
                           "Institutions or Sponsor)."),
          ("cl", "AM 3.2", "Pricing Committee: the Head of CIB Lending (chair), a Finance delegate and a Risk delegate. "
                           "The chair records the committee's decision."),
          ("cl", "AM 3.3", "Target turnaround: Segment Head, 1 business day; Pricing Committee, 3 business days."),
          ("h1", "4. What counts as the relationship"),
          ("cl", "AM 4.1", "For routing, the relationship is the client's full product relationship as defined in RAROC "
                           "Methodology RM 5.2, with the proposed deal added pro forma (RM 5.3)."),
          ("h1", "5. Audit"),
          ("cl", "AM 5.1", "Every pricing request is logged in the Deal Approvals register with the inputs, deal and "
                           "relationship RAROC, the clauses applied, the decision, the approver, the approver's comment and "
                           "the parameter version."),
          ("cl", "AM 5.2", "Requests rejected for invalid input are logged too, with the reason."),
          ("cl", "AM 5.3", "Register entries are never edited or deleted by automated processes; only the approval outcome fields are updated.")]
    return b


def to_md(blocks):
    out = []
    for blk in blocks:
        k = blk[0]
        if k == "title": out.append(f"# {blk[1]}\n")
        elif k == "meta": out.append(f"{blk[1]}  ")
        elif k == "note": out.append(f"\n> **{blk[1]}**\n")
        elif k == "h1": out.append(f"\n## {blk[1]}\n")
        elif k == "cl": out.append(f"**{blk[1]}** {blk[2]}\n")
        elif k == "table":
            out.append("| " + " | ".join(blk[1]) + " |")
            out.append("|" + "---|" * len(blk[1]))
            out += ["| " + " | ".join(r) + " |" for r in blk[2]]
            out.append("")
    return "\n".join(out) + "\n"


def to_docx(blocks, path):
    d = Document()
    st = d.styles["Normal"]; st.font.name = "Calibri"; st.font.size = Pt(11)
    for name, size in (("Title", 24), ("Heading 1", 14)):
        s = d.styles[name]; s.font.name = "Calibri"; s.font.size = Pt(size); s.font.color.rgb = RGBColor(0x1F, 0x3A, 0x5F)
    for blk in blocks:
        k = blk[0]
        if k == "title":
            d.add_paragraph(blk[1], style="Title")
        elif k == "meta":
            p = d.add_paragraph(); run = p.add_run(blk[1]); run.font.size = Pt(10); run.font.color.rgb = RGBColor(0x55, 0x55, 0x55)
            p.paragraph_format.space_after = Pt(2)
        elif k == "note":
            p = d.add_paragraph(); run = p.add_run(blk[1]); run.bold = True; run.font.color.rgb = RGBColor(0xA0, 0x30, 0x20)
            p.paragraph_format.space_before = Pt(8)
        elif k == "h1":
            d.add_heading(blk[1], level=1)
        elif k == "cl":
            p = d.add_paragraph(); r1 = p.add_run(blk[1] + "  "); r1.bold = True; p.add_run(blk[2])
            p.paragraph_format.space_after = Pt(6)
        elif k == "table":
            t = d.add_table(rows=1, cols=len(blk[1])); t.style = "Table Grid"
            for i, h in enumerate(blk[1]):
                cell = t.rows[0].cells[i]; cell.text = ""; run = cell.paragraphs[0].add_run(h); run.bold = True
            for row in blk[2]:
                cells = t.add_row().cells
                for i, v in enumerate(row): cells[i].text = v
            d.add_paragraph()
    sec = d.sections[0]
    footer = sec.footer.paragraphs[0]
    footer.text = f"Northlake Bank (fictional) · Synthetic, for demonstration only · Parameter version {C['version']}"
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    d.save(path)


if __name__ == "__main__":
    for title, fn in (("Loan Pricing Policy", lpp), ("RAROC Methodology", rm), ("Approval Matrix", am)):
        blocks = fn()
        (OUT / f"{title}.md").write_text(to_md(blocks), encoding="utf-8")
        to_docx(blocks, OUT / f"{title}.docx")
        print("Wrote", title, "-", sum(1 for b in blocks if b[0] == "cl"), "clauses")
