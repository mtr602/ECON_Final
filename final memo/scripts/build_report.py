"""Render the four-page policy report and the stand-alone break-even exhibit."""
import os
import tempfile
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "econ342-matplotlib"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, Table, TableStyle

from analyze import MEMO, RATE, parameters, read

INK = "#142B38"
TEAL = "#006B66"
MUTED = "#425965"
RULE = "#CEDBD9"
PALE = "#EAF4F1"
PAPER = "#FFFFFF"
LEFT = 43
WIDTH = 526
FONT_DIR = Path(matplotlib.get_data_path()) / "fonts/ttf"
pdfmetrics.registerFont(TTFont("MemoSans", str(FONT_DIR / "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("MemoSans-Bold", str(FONT_DIR / "DejaVuSans-Bold.ttf")))
pdfmetrics.registerFontFamily("MemoSans", normal="MemoSans", bold="MemoSans-Bold")


def results(name):
    return read(MEMO / "results" / name)


def lookup(rows, **match):
    found = [row for row in rows if all(row[key] == str(value) for key, value in match.items())]
    if len(found) != 1:
        raise ValueError(match)
    return found[0]


def number(row, key):
    return float(row[key])


def cad(row, key):
    return f"{number(row, key):,.0f}"


def millions(row, key):
    return f"{number(row, key)/1e6:,.2f}"


def percent(row, key="break_even_utilization"):
    return f"{number(row,key):.2%}" if row[key] else "Infeasible"


def chart():
    rows = results("break_even_curves.csv")
    fig, ax = plt.subplots(figsize=(9, 2.55))
    for cost, tariff, ink, style, name in [
        ("base","A","#04766C","-","Base · A"),
        ("base","B","#234975","--","Base · B"),
        ("base","C","#6F455F",":","Base · C"),
        ("low","B","#89999B","-","Low · B"),
        ("high","B","#AF5E2C","-","High · B"),
    ]:
        data = [row for row in rows if row["cost_case"] == cost and row["tariff"] == tariff]
        ax.plot([number(row,"rent") for row in data],
                [float(row["break_even_utilization"]) if row["break_even_utilization"] else float("nan") for row in data],
                color=ink, linestyle=style, linewidth=1.8, label=name)
    ax.axvline(parameters("base", "base")["gpu_rental_price_cad_per_gpu_hour"], color="#55696D", lw=.8, alpha=.7)
    ax.set(xlim=(2.8,9), ylim=(.15,1.025), xlabel="Rental price (C$ per GPU-hour)",
           ylabel="Break-even paid use")
    ax.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
    ax.grid(axis="y", alpha=.22)
    ax.spines[["top","right"]].set_visible(False)
    ax.tick_params(labelsize=8, length=3)
    ax.xaxis.label.set_size(9)
    ax.yaxis.label.set_size(9)
    ax.legend(ncol=5, frameon=False, fontsize=8, loc="upper center", bbox_to_anchor=(.5,1.21))
    fig.subplots_adjust(left=.10, right=.99, bottom=.19, top=.83)
    for suffix in ("png","pdf"):
        fig.savefig(MEMO / f"exhibits/commercial_break_even.{suffix}", dpi=220)
    plt.close(fig)


class Memo:
    def __init__(self):
        self.pdf = canvas.Canvas(str(MEMO / "reports/final_economic_analysis.pdf"), pagesize=(612,792), invariant=1)
        self.pdf.setTitle("Québec electricity and AI exports | ECON 342")
        self.page = 0

    def para(self, html, size=10, leading=14, ink=INK, gap=8, width=WIDTH, x=LEFT):
        p = Paragraph(html, ParagraphStyle("memo", fontName="MemoSans", fontSize=size, leading=leading,
                                            textColor=colors.HexColor(ink)))
        _, height = p.wrap(width, 700)
        p.drawOn(self.pdf, x, self.y-height)
        self.y -= height + gap

    def start(self, section, title, subtitle):
        self.page += 1
        self.pdf.setFillColor(colors.HexColor(TEAL))
        self.pdf.rect(LEFT,747,32,3,stroke=0,fill=1)
        self.y = 732
        self.para(f"<b>ECON 342  /  {section}</b>",9,11,TEAL,9)
        self.para(title,27,29,INK,10)
        self.para(subtitle,10.5,14,MUTED,13)

    def heading(self, text):
        self.para(f"<b>{text}</b>",12,15,TEAL,5)

    def callout(self, text):
        p = Paragraph(text, ParagraphStyle("callout", fontName="MemoSans", fontSize=10.3,
                                             leading=14, textColor=colors.HexColor(INK)))
        _, height = p.wrap(WIDTH-24,700)
        self.pdf.setFillColor(colors.HexColor(PALE))
        self.pdf.roundRect(LEFT,self.y-height-16,WIDTH,height+16,5,stroke=0,fill=1)
        p.drawOn(self.pdf,LEFT+12,self.y-height-8)
        self.y -= height+27

    def table(self, rows, widths, font=9.2, padding=5, paragraphs=False):
        if paragraphs:
            normal = ParagraphStyle("cell",fontName="MemoSans",fontSize=font,leading=font+3,textColor=colors.HexColor(INK))
            header = ParagraphStyle("header",parent=normal,fontName="MemoSans-Bold",textColor=colors.white)
            rows = [[Paragraph(str(element),header if i==0 else normal) for element in row] for i,row in enumerate(rows)]
        table = Table(rows, colWidths=widths)
        table.setStyle(TableStyle([
            ("FONTNAME",(0,0),(-1,-1),"MemoSans"),
            ("FONTNAME",(0,0),(-1,0),"MemoSans-Bold"),
            ("FONTSIZE",(0,0),(-1,-1),font),
            ("TEXTCOLOR",(0,0),(-1,-1),colors.HexColor(INK)),
            ("TEXTCOLOR",(0,0),(-1,0),colors.white),
            ("BACKGROUND",(0,0),(-1,0),colors.HexColor(INK)),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.HexColor("#F0F5F4"),colors.white]),
            ("ALIGN",(1,0),(-1,-1),"RIGHT" if not paragraphs else "LEFT"),
            ("VALIGN",(0,0),(-1,-1),"TOP"),
            ("TOPPADDING",(0,0),(-1,-1),padding),
            ("BOTTOMPADDING",(0,0),(-1,-1),padding),
            ("LEFTPADDING",(0,0),(-1,-1),8),
            ("RIGHTPADDING",(0,0),(-1,-1),8),
        ]))
        _, height = table.wrap(WIDTH,700)
        table.drawOn(self.pdf,LEFT,self.y-height)
        self.y -= height + 9

    def finish(self, note):
        if self.y < 96:
            raise ValueError(f"Page {self.page} body extends into footer: {self.y}")
        self.pdf.setStrokeColor(colors.HexColor(RULE))
        self.pdf.line(LEFT,90,LEFT+WIDTH,90)
        self.y = 81
        self.para(f"<b>Sources and assumptions</b>  {note}",8,10,MUTED,0)
        if self.y < 41:
            raise ValueError("Source note overlaps footer")
        self.pdf.setFillColor(colors.HexColor(TEAL))
        self.pdf.setFont("MemoSans-Bold",8)
        self.pdf.drawString(LEFT,30,"QUÉBEC ELECTRICITY ALLOCATION")
        self.pdf.drawRightString(LEFT+WIDTH,30,f"{self.page}/4")
        self.pdf.showPage()


def build():
    chart()
    m = Memo()
    rows = results("export_comparison.csv")
    at50 = lookup(rows, utilization=.5)
    m.start("ELECTRICITY OPPORTUNITY COST","AI computing versus power exports",
            "What would one eight-H100 server earn from the same electricity Québec could sell to the United States?")
    m.callout("<b>Observed 2025 benchmark: C$142.13/MWh gross.</b> The 12 CER monthly Québec totals report C$595.82 million on 4.192 TWh. The calculation weights each month by volume. Avoidable export costs are unavailable.")
    m.heading("Annual comparison per server")
    export_table = [["Base case at 8% cost of capital", "25% paid", "50% paid", "75% paid", "100% paid"]]
    for label, key in [
        ("Gross AI rental revenue (C$)","annual_revenue"),("Hardware capital recovery (C$)","annual_hardware"),
        ("Facility capital recovery (C$)","annual_facility"),("Non-power operations (C$)","annual_nonpower_opex"),
        ("Electricity use (MWh)","annual_mwh"),("Forgone exports (C$)","forgone_exports"),
        ("AI advantage over exports (C$)","ai_advantage"),("AI advantage per MWh (C$/MWh)","ai_advantage_per_mwh"),
    ]:
        export_table.append([label]+[f"{number(row,key):.2f}" if key=="annual_mwh" else cad(row,key) for row in rows])
    m.table(export_table,[222,76,76,76,76])
    m.para("AI revenue is modeled at <b>C$6.67 per GPU-hour</b>, based on Lambda’s November 2026 eight-H100 quote and same-day Bank of Canada exchange rate. The model uses 8,760 available hours, 1.30 PUE and measured idle and busy power of 1.86 and 7.92 kW.")
    m.heading("What the comparison means")
    m.para(f"At 25% paid use, the AI option trails the gross export alternative by C${abs(number(rows[0],'ai_advantage')):,.0f} per server-year. At 50%, each server uses {number(at50,'annual_mwh'):.2f} MWh, gives up C${cad(at50,'forgone_exports')} in export receipts, and leaves a modeled advantage of <b>C${cad(at50,'ai_advantage')}</b>. The comparison charges electricity once through forgone exports.")
    m.para("Ricardian comparative advantage depends on opportunity cost. Hydro endowments can support gains from trade in computing if the net value of compute exceeds the value of the power displaced. Rental demand, imported equipment and capital recovery determine whether those gains materialize.")
    m.finish("CER monthly and annual trade data, 2015–25 [1]. Lambda and Bank of Canada [2]. NVIDIA, Latif et al., Cologix and Uptime [3]. Cost inputs from the existing model [4].")

    thresholds = results("break_even.csv")
    def be(cost, rate, tariff):
        return lookup(thresholds, cost_case=cost, rental_case="base", financing_rate=rate, tariff=tariff)

    m.start("PRIVATE RETURNS","Does the discount change viability?",
            "A is the C$68.20/MWh proxy. B is the C$130/MWh proposed average. C uses the proposed Rate CD demand and energy charges.")
    m.table([["Base at 50% paid use and 8% financing","A","B","C"],
             ["Annual electricity bill (C$/server)"]+[cad(at50,"bill_"+t) for t in "ABC"],
             ["Annual commercial profit (C$/server)"]+[cad(at50,"profit_"+t) for t in "ABC"],
             ["Minimum rent at 50% (C$/GPU-hour)"]+[f"{number(be('base',RATE,t),'minimum_rent_at_50pct'):.2f}" for t in "ABC"]],
            [286,80,80,80],font=9,padding=4)
    m.table([["Break-even paid utilization","A","B","C"]]+[
        [f"{cost.title()} cost case · 8%"]+[percent(be(cost,RATE,t)) for t in "ABC"] for cost in ("low","base","high")],
        [286,80,80,80],font=9,padding=4)
    m.para("Base-case break-even under B at <b>0%, 5%, 8%, 10% and 15%</b> financing is "
           + ", ".join(percent(be("base",r,"B")) for r in (0,.05,.08,.1,.15)) + ", respectively.",9,12,gap=3)
    m.pdf.drawImage(str(MEMO/"exhibits/commercial_break_even.png"),LEFT,m.y-145,width=WIDTH,height=145,mask="auto")
    m.y -= 146
    m.para("At the base quote, A alone is viable from <b>26.56% to below 27.09%</b> paid use against B, or to below 27.60% against C. At 50%, A raises profit by C$3,441 versus B and C$5,093 versus C. All three tariffs are profitable in the base case at 50%.",9.3,12.1,gap=6)
    m.para("Across tested ranges, utilization changes annual B profit by C$229k, the on-demand quote by C$108k, hardware life by C$79k and financing by C$64k. Fixed costs fall per sold GPU-hour as utilization rises. Shared infrastructure may offer scale economies, though this model holds per-server costs fixed.",9.3,12.1,gap=5)
    m.para("C applies C$32.704/kW-month and C$0.08710/kWh. The chart omits thresholds above 100%; the high-cost case cannot break even at the C$2.84 preemptible stress quote.",8.7,11.2,gap=1)
    m.finish("Hydro-Québec filings B-0004 Table 2 and B-0076 §§5.52–5.57, dossier R-4333-2026 [5]. Proposed terms and two proxy prices are scenario inputs. Financing uses capital recovery [4].")

    welfare = results("domestic_welfare.csv")
    def site(scenario, case="Preferential only", tariff="A"):
        return lookup(welfare, scenario=scenario, investment_case=case, tariff=tariff)
    middle = site("Half local ownership")
    either = site("Half local ownership","Either tariff","B")
    m.start("QUÉBEC WELFARE","How much value stays in Québec?",
            "A representative 500-server facility has 5.10 MW of rated IT capacity and 6.63 MW of assumed authorized demand at base PUE.")
    m.callout(f"<b>Induced investment example:</b> at {number(middle,'utilization'):.2%} paid use, only A clears the commercial hurdle versus B. The site would use {number(middle,'site_annual_mwh'):,.0f} MWh per year. Utility receipts of C${millions(middle,'utility_receipts')}m offset part of C${millions(middle,'forgone_gross_exports')}m in gross forgone exports.")
    m.table([["Induced site under A · C$m/year","Retained profit","Wage gain","Québec net"],
             *[[name,millions(site(name),"quebec_retained_profit"),millions(site(name),"incremental_labour_income"),
                millions(site(name),"conditional_quebec_welfare")] for name in
              ("External ownership","Half local ownership","Fully local ownership","Half local with extra public costs")]],
            [257,92,82,95])
    m.para(f"Even with half local ownership and a 10% earnings premium over alternative work, the site falls short by <b>C${millions(middle,'additional_benefits_needed')}m/year</b>. Local profits, incremental wages, supplier surplus and tax together must reach C${millions(middle,'minimum_domestic_benefits')}m/year before extra public costs. Adding C$0.50m for supply and grid costs and C$0.10m for administration raises the required total to C$2.07m.")
    m.heading("What counts as a Québec gain")
    m.para("The payroll proxy is C$0.967m/year, scaled from a U.S. facility benchmark. The table credits only the share earned above workers’ alternatives (0%, 10% or 25%). Permanent operating earnings are distinct from temporary construction jobs; construction gains remain unquantified. Supplier gains count only surplus after resource costs. Québec taxes count as public receipts after their deduction from profit. Both are set to zero in the table because site evidence is unavailable.")
    m.para("Private profit already deducts power, hardware, capital recovery and operating costs. Utility receipts return the electricity payment to Québec’s public ledger, where the export alternative and incremental supply costs are charged. Capital recovery charges the opportunity cost of capital; the wage premium deducts labour’s alternative earnings. Any separate grant would enter company cash flow and public cost once.")
    m.para(f"At 50% paid use under B, the half-local scenario yields <b>C${millions(either,'conditional_quebec_welfare')}m/year</b> conditionally. The external-ownership case yields −C$0.34m before unmeasured gains or costs. Québec contributes hydro and potentially labour, but ownership and supplier linkages determine who receives the gains from trade.",9.5,13,gap=4)
    m.finish("Existing server model and KPMG operations benchmark [4, 6]. Ownership, wage premiums and extra public costs are transparent scenarios. Exports valued at the CER gross benchmark [1].")

    m.start("POLICY DECISION","Price scarce power at economic cost",
            "Keep exports as a feasible alternative and reserve preferential pricing for projects that demonstrate additional Québec benefits.")
    m.table([
        ["Policy option","When it is appropriate"],
        ["1. Continue exporting","When exports are the highest-value feasible use after system constraints and export-specific costs. C$142.13/MWh is a historical gross benchmark."],
        ["2. Cost-reflective AI allocation","Use as the default. Price energy, peak capacity and connection costs for the site. Allocate to AI when it clears the full economic hurdle."],
        ["3. Targeted preference","Consider only if support changes the build decision and measured Québec benefits exceed the public and opportunity costs."],
    ],[181,345],font=9.1,padding=5,paragraphs=True)
    m.heading("What the subsidy does at different investment margins")
    m.table([
        ["Investment outcome","Base case against tariff B"],
        ["Builds under either tariff","At 50% paid use, the site is profitable under A and B. A moves C$1.72m/year from the utility to the project. With half local ownership and zero incremental tax, modeled Québec welfare falls by C$0.86m/year."],
        ["Builds only with preference","At 26.82% paid use, A can induce the modeled project. At the midpoint the half-local scenario still needs C$1.06m/year of additional domestic benefit before extra public costs."],
        ["Builds under neither","At 15% paid use, both tariffs leave a commercial loss. The proposed discount induces no site. The no-build comparison has zero incremental project flows."],
    ],[181,345],font=9.1,padding=5,paragraphs=True)
    m.para("<b>Strongest case for cost-reflective pricing.</b> It screens projects against scarce energy and capacity and limits transfers to firms that already clear their investment hurdle. The base preferential-only band is about half a percentage point; rental demand and capital costs move viability much more.")
    m.para("<b>Strongest counterargument.</b> An early facility could create local supplier capability or learning that private investors cannot capture. Revisit the policy if verifiable spillovers and stakeholder gains clear the site-specific welfare threshold, and evidence shows the investment would otherwise fail or locate elsewhere.")
    m.para("<b>Implementation.</b> Require an independent counterfactual bid and grid-cost assessment. Cap and sunset any award, pay against milestones and recover support for missed commitments. Track peak kW, MWh, incremental permanent payroll, Québec-retained profits, net public receipts and cost per induced project.",9.5,13,gap=4)
    m.finish("Policy tests use the commercial and welfare tables [7], observed gross CER receipts [1] and illustrative filing scenarios [5]. Full parameter definitions and verification are in the companion files.")
    m.pdf.save()


if __name__ == "__main__":
    build()
