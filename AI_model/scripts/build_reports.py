"""Render the three-page research report, its appendix, and one-page statistical report."""
from pathlib import Path
import json
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, PageBreak, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from xml.sax.saxutils import escape

from ai_profitability_model import case_parameters, threshold

BASE=Path(__file__).resolve().parents[1]
REPORTS=BASE/"reports"
RESULTS=BASE/"results"
PARAM=BASE/"data/processed/model_parameters.csv"
p=pd.read_csv(PARAM).set_index("parameter")
s=json.loads((RESULTS/"summary.json").read_text())
r=s["base_at_50_pct"]
hist=s["historical"]
all_cases=pd.read_csv(RESULTS/"scenario_results.csv")
breaks=pd.read_csv(RESULTS/"break_even_results.csv")
annual=pd.read_csv(BASE/"data/processed/electricity_exports_annual.csv")
REPORTS.mkdir(exist_ok=True)
for name,file in [("Body","DejaVuSans.ttf"),("Bold","DejaVuSans-Bold.ttf"),("Title","DejaVuSerif.ttf")]:
    pdfmetrics.registerFont(TTFont(name,"/usr/share/fonts/truetype/dejavu/"+file))
pdfmetrics.registerFontFamily("Body",normal="Body",bold="Bold")
ink=colors.HexColor("#172D3A")
teal=colors.HexColor("#096F66")
gray=colors.HexColor("#4D656E")
light=colors.HexColor("#EAF5F2")
line=colors.HexColor("#C9D8D6")
styles={
 "k":ParagraphStyle("k",fontName="Bold",fontSize=9,leading=12,textColor=teal,spaceAfter=6),
 "title":ParagraphStyle("title",fontName="Title",fontSize=23,leading=28,textColor=ink,spaceAfter=9),
 "lead":ParagraphStyle("lead",fontName="Body",fontSize=10.0,leading=14,textColor=ink,spaceAfter=8),
 "h":ParagraphStyle("h",fontName="Bold",fontSize=11,leading=14,textColor=teal,spaceBefore=9,spaceAfter=5),
 "b":ParagraphStyle("b",fontName="Body",fontSize=9.1,leading=13,textColor=ink,spaceAfter=7),
 "c":ParagraphStyle("c",fontName="Body",fontSize=8.0,leading=10.6,textColor=ink),
 "th":ParagraphStyle("th",fontName="Bold",fontSize=8.0,leading=10.6,textColor=colors.white),
 "small":ParagraphStyle("small",fontName="Body",fontSize=7.5,leading=10,textColor=gray,spaceAfter=5),
}

def para(story,t,style="b"): story.append(Paragraph(t,styles[style]))
def heading(story,t): para(story,t,"h")
def header(story,k,t,lead):
    para(story,k,"k");para(story,t,"title");para(story,lead,"lead")
def table(story,heads,rows,widths):
    t=Table([[Paragraph(x,styles["th"]) for x in heads]]+[[Paragraph(str(x),styles["c"]) for x in row] for row in rows],colWidths=widths,hAlign="LEFT")
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),teal),("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#F1F6F5")]),("LINEBELOW",(0,1),(-1,-1),.35,line),("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),7),("RIGHTPADDING",(0,0),(-1,-1),7),("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4)]))
    story.append(t)
def box(story,txt):
    t=Table([[Paragraph(txt,styles["b"])]],colWidths=[500])
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),light),("BOX",(0,0),(-1,-1),.5,line),("LEFTPADDING",(0,0),(-1,-1),9),("RIGHTPADDING",(0,0),(-1,-1),9),("TOPPADDING",(0,0),(-1,-1),7),("BOTTOMPADDING",(0,0),(-1,-1),5)]))
    story.append(t)
def money(v): return f"C${v:,.0f}" if v>=0 else f"−C${abs(v):,.0f}"
def pct(v): return "Infeasible" if pd.isna(v) else f"{100*v:.2f}%"
def row_break(cost,metric,rental="base",export="base"):
    return breaks[(breaks.cost_case==cost)&(breaks.metric==metric)&(breaks.rental_case==rental)&(breaks.export_case==export)].iloc[0]
def b(cost,metric,rental="base",export="base"): return pct(row_break(cost,metric,rental,export).break_even_utilization)
def link(label,url): return f'<link href="{escape(url)}" color="#096F66"><u>{escape(label)}</u></link>'
def build(name,story,pages):
    def footer(canvas,doc):
        canvas.saveState();canvas.setStrokeColor(line);canvas.line(56,42,556,42)
        canvas.setFont("Body",8);canvas.setFillColor(gray);canvas.drawString(56,25,"ECON 342  /  Quebec AI computing economics")
        canvas.drawRightString(556,25,f"{doc.page} / {pages}");canvas.restoreState()
    doc=SimpleDocTemplate(str(REPORTS/name),pagesize=(612,792),leftMargin=50,rightMargin=50,topMargin=35,bottomMargin=49,title=name.replace("_"," ").replace(".pdf",""))
    doc.build(story,onFirstPage=footer,onLaterPages=footer)

# Charts use only generated data.
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":9,"axes.spines.top":False,"axes.spines.right":False,"axes.labelcolor":"#172D3A","axes.titlecolor":"#172D3A","xtick.color":"#4D656E","ytick.color":"#4D656E"})
fig,ax=plt.subplots(figsize=(8.0,3.0))
x=np.linspace(2.5,9.2,150)
for case,color in [("low","#2C8F7E"),("base","#22577A"),("high","#B36A32")]:
    params=case_parameters(p,case)
    y=[threshold(params,"relative_exports",price)[0] for price in x]
    ax.plot(x,[np.nan if u is None else 100*u for u in y],label=case.capitalize()+" cost",color=color,lw=2)
ax.axvline(r["rental_price_cad_per_gpu_hour"],color="#7A878A",ls="--",lw=1)
ax.text(r["rental_price_cad_per_gpu_hour"]+.08,94,"Base quote",fontsize=8,color="#59686B")
ax.set(xlabel="Advertised GPU rental price (C$/GPU-hour)",ylabel="Break-even paid use (%)",ylim=(0,100),xlim=(2.5,9.2))
ax.grid(axis="y",alpha=.22);ax.legend(loc="upper right",frameon=False,ncol=1)
fig.tight_layout();fig.savefig(RESULTS/"break_even_curve.png",dpi=180);plt.close(fig)
fig,ax=plt.subplots(figsize=(7.8,1.85))
ax.plot(annual.year,annual.implied_price_cad_per_mwh,marker="o",color="#096F66",lw=2,markersize=3)
ax.set(ylabel="CAD/MWh",xticks=annual.year);ax.tick_params(axis="x",labelrotation=45,labelsize=7)
ax.grid(axis="y",alpha=.22);fig.tight_layout();fig.savefig(RESULTS/"export_price_history.png",dpi=180);plt.close(fig)

story=[]
header(story,"MODEL REPORT  /  1. METHODOLOGY",
       "Profitability of Quebec AI computing","A representative eight-H100 server, one year of operation, and Quebec’s observed 2025 international electricity export benchmark.")
box(story,"<b>Question.</b> At what GPU rental price and paid utilization would computing cover its commercial costs and generate more value than exporting the electricity it uses? Would a lower electricity tariff change the commercial result?")
heading(story,"Model equations")
table(story,["Measure","Annual calculation"],[
 ("AI rental revenue","8 GPUs × 8,760 available hours × paid utilization (u) × hourly rental price (p)."),
 ("Electricity used","[idle kW + (busy kW − idle kW) × u] × PUE × 8,760 ÷ 1,000 MWh."),
 ("Non-power cost","Installed server cost ÷ hardware life + facility cost/IT kW × 10.2 rated kW ÷ facility life + recurring non-power costs."),
 ("Private profit","Revenue − non-power cost − electricity bill. Calculate separately for the two tariffs."),
 ("Relative return","Revenue − non-power cost − (MWh × C$142.1268/MWh). Divide by MWh for the relative advantage per MWh."),
], [135,365])
heading(story,"Core input values")
table(story,["Input","Low cost / base / high cost","Basis"],[
 ("GPU rental price¹",f"C${p.loc['gpu_rental_price_cad_per_gpu_hour','low']:.2f} / C${p.loc['gpu_rental_price_cad_per_gpu_hour','base']:.2f} / C${p.loc['gpu_rental_price_cad_per_gpu_hour','high']:.2f}","Three advertised on-demand quotes"),
 ("Paid use / annual hours","50% base / 8,760 h","Assume available all year"),
 ("Idle / busy power","1.86 / 4.68, 7.92, 8.43 kW","Measured H100 workloads"),
 ("Facility overhead (PUE)","1.20 / 1.30 / 1.56","Local proxy and survey range"),
 ("Installed server cost","C$434k / C$461k / C$530k","Vendor quote; allocations assumed"),
 ("Hardware life","6 / 6 / 3 years","Accounting-life proxy and stress"),
 ("Facility cost per IT kW","C$16.7k / C$16.7k / C$25.0k","Toronto / broader US-Canada proxy"),
 ("Facility life","30 / 20 / 12 years","Blended-life assumptions"),
 ("Non-power opex / server-year","C$3.53k / C$4.41k / C$7.06k","Shared US benchmark + allowances"),
], [154,192,154])
para(story,"¹ Rental price is varied separately from cost cases. Quotes from November 25, 2026, converted at C$1.4219/US$. All paid GPU-hours are assumed to be export sales. Hardware and facility capex are spread evenly over useful lives; no financing return, tax or salvage value is modeled. Appendix lists source dates and limits.","small")
story.append(PageBreak())
header(story,"MODEL REPORT  /  2. BASE-CASE FINDINGS","Annual economics at 50% paid use","Model estimates per representative server. The online H100 price is a published offer, and the operating and cost assumptions are scenarios.")
heading(story,"Revenue, electricity and costs")
table(story,["Metric","Annual result"],[
 ("Paid GPU-hours",f"{r['annual_paid_gpu_hours']:,.0f}"),
 ("GPU rental revenue",money(r["annual_gpu_revenue_cad"])),
 ("Electricity use including overhead",f"{r['annual_electricity_mwh']:.2f} MWh"),
 ("Hardware cost (straight-line)",money(r["annual_hardware_cost_cad"])),
 ("Facility cost (straight-line)",money(r["annual_facility_cost_cad"])),
 ("Recurring non-power operating cost",money(r["annual_nonpower_opex_cad"])),
 ("Total non-power cost",f"<b>{money(r['annual_nonpower_cost_cad'])}</b>"),
], [340,160])
heading(story,"Comparing electricity pricing and alternative use")
table(story,["Electricity comparison","Annual bill or forgone value","Profit or relative return","Break-even paid use"],[
 ("Lower-price proxy (C$68.20/MWh)",money(r["annual_preferential_bill_cad"]),money(r["annual_private_profit_preferential_cad"]),b("base","preferential_average")),
 ("Proposed CD average (C$130/MWh)",money(r["annual_cd_average_bill_cad"]),money(r["annual_private_profit_cd_average_cad"]),b("base","cd_average")),
 ("Illustrative CD two-part bill",money(r["annual_cd_two_part_bill_cad"]),money(r["annual_private_profit_cd_two_part_cad"]),b("base","cd_two_part")),
 ("2025 export alternative (C$142.13/MWh)",money(r["annual_forgone_export_revenue_cad"]),money(r["annual_relative_advantage_cad"]),b("base","relative_exports")),
], [168,111,112,109])
para(story,f"At the base rental price, modelled AI revenue after non-power costs exceeds historical export receipts by <b>{money(r['annual_relative_advantage_cad'])} per server-year</b>, or {money(r['relative_advantage_cad_per_mwh'])}/MWh. The minimum rental price to tie exports at 50% use is C${row_break('base','relative_exports').minimum_rental_price_at_50pct_cad_per_gpu_hour:.2f}/GPU-hour.")
heading(story,"Electricity tariff calculation")
para(story,"The two average prices are Hydro-Québec's illustrative customer-profile values. The revised Rate CD proposal charges C$32.704/kW of billing demand per month plus C$0.08710/kWh. The detailed illustration assumes 500 identical servers, 6.63 MW authorized capacity at base PUE and a recurring simultaneous busy peak of 5.148 MW. Demand and energy are allocated equally per server. No ramp-up, special credits or voltage adjustments are assumed.")
box(story,f"<b>Tariff effect.</b> At 50% utilization the average-rate discount increases annual private profit by {money(r['annual_cd_average_bill_cad']-r['annual_preferential_bill_cad'])}, and reduces the commercial break-even threshold by {(row_break('base','cd_average').break_even_utilization-row_break('base','preferential_average').break_even_utilization)*100:.2f} percentage points. The proposal is a pricing scenario, and these bills are conditional illustrations.")
story.append(PageBreak())
header(story,"MODEL REPORT  /  3. SENSITIVITY AND INTERPRETATION","What changes the result?","Break-even paid utilization required to beat 2025 export receipts, at different rental prices and three benchmark-informed cost cases.")
story.append(Image(str(RESULTS/"break_even_curve.png"),width=500,height=187.5))
para(story,"Figure 1. Curves stop where no break-even is achievable within 100% utilization. All cases use the same 2025 export benchmark; the dashed line is the base on-demand quote.","small")
heading(story,"Break-even paid utilization at C$6.67 per GPU-hour")
table(story,["Cost case","Lower tariff","CD average","CD two-part","Export alternative"],[
 (c.capitalize(),b(c,"preferential_average"),b(c,"cd_average"),b(c,"cd_two_part"),b(c,"relative_exports")) for c in ["low","base","high"]
], [100,100,100,100,100])
heading(story,"Interpretation")
para(story,f"<b>Rental price and hardware costs dominate this comparison.</b> At the base quote, the export break-even rises from {b('low','relative_exports')} to {b('high','relative_exports')} across the cost cases. At the interruptible H100 stress quote of C${p.loc['stress_gpu_rental_price_cad_per_gpu_hour','base']:.2f}, the high-cost case cannot break even even at 100% paid use under either average tariff or the export benchmark.")
para(story,"Holding other base inputs constant, cutting hardware life from six to three years increases the export threshold from 20.27% to 37.04%; varying PUE from 1.20 to 1.56 changes it from 20.18% to 20.48%. Varying the historical export benchmark from C$38.79 to the highest 2025 monthly value of C$435.87/MWh changes it from 19.48% to 22.63%. The 2025 export price is a historical gross average. Actual displaced electricity may be an import, domestic load, new capacity or an export sale.")
heading(story,"Policy relevance and limits")
para(story,"At the base settings the project is viable under both tariff proxies, so the calculation offers limited support for a discount as a prerequisite for investment. The narrow gap between thresholds identifies conditions where support might change private viability. Establishing investment additionality requires actual realized prices, utilization, billing demand, alternative sites and capital costs. The welfare question also requires domestic ownership, retained gains, opportunity costs and system impacts; the profit results alone cannot establish a subsidy case.")
story.append(PageBreak())
header(story,"MODEL REPORT  /  APPENDIX","Data, definitions and provenance","Source references are recorded in the existing repository registry and model_parameters.csv. Listed values are observed, benchmarks, or explicitly modeled allocations.")
table(story,["Data / parameter","Definition, provenance and limitation"],[
 ("CER exports (2015–25)","132 monthly Québec-to-US Total rows with revenue CAD and volume MWh; reconcile to 11 annual rows. 2025 C$595.818m / 4.192m MWh = C$142.13 gross. Avoidable export costs missing. "+link("CER dataset","https://open.canada.ca/data/dataset/5c358f51-bc8c-4565-854d-9d2e35e6b178")),
 ("GPU price and paid utilization","Together on-demand US$3.99, Lambda 8 H100 US$4.69, CoreWeave 8 H100 on-demand US$6.155/GPU-h; Together preemptible US$2.00 stress. 25 Nov 2026 quotes. Paid use is an assumption (0–100%). "+link("Lambda","https://lambda.com/pricing")+" · "+link("Together","https://www.together.ai/pricing")+" · "+link("CoreWeave","https://www.coreweave.com/pricing")),
 ("Exchange rates","Bank of Canada daily USD/CAD 1.4219 (25 Nov 2026), 1.4422 (10 Jan 2025 server quote); October 2022 mean 1.36995 for historical launch cost. Current FX proxy for undated-year construction/O&M. No inflation harmonization. "+link("BoC exchange rates","https://www.bankofcanada.ca/rates/exchange/")),
 ("GPU count, power, PUE","NVIDIA 8 GPUs, 10.2 kW rated. Latif et al. measured idle 1.86, busy 4.68–8.43 kW; base 7.92. PUE 1.20 assumption, 1.30 Cologix local specification (<1.30), 1.56 repository Uptime survey benchmark. Linear utilization-power mapping assumed. "+link("Power study","https://arxiv.org/html/2412.08602v2")),
 ("Installed hardware cost and life","Thinkmate Jan 2025 US$300,107 server; DirectDial Nov 2026 US$33,025 switch. Network allocation 1/32, 2/16, 2/8 switches per server and installation 0/5/10% assumed. High case allows Epoch 2022 bundled $44k/GPU +10%. CoreWeave 6-year accounting life; 3-year stress. "+link("Quote study","https://signal65.com/wp-content/uploads/2025/02/Reshaping-AI-Accelerator-Economic-Landscape_Signal65-Insights.pdf")),
 ("Facility capex and life","Turner & Townsend Toronto 2026 US$11.76/W IT; Cushman 2026 US/Canada US$17.6m/MW development proxy (assume IT capacity), excludes GPUs. 10.2 rated kW allocation. Blended lives 30/20/12 years within/around Equinix infrastructure ranges. "+link("Construction index","https://reports.turnerandtownsend.com/data-centre-construction-cost-index-2026/cost-trends?overlay=The+Americas")),
 ("Non-power operating cost","KPMG 2025 U.S. 30 MW site benchmark US$4m labour + US$2m maintenance + US$1.3m security. Scale by 10.2/30,000 assuming IT capacity; add 0/25/100% for unobserved costs. Québec full operating budget unavailable. "+link("KPMG report","https://assets.kpmg.com/content/dam/kpmgsites/sg/pdf/2026/05/benchmarking-capex-and-opex-in-the-global-data-centre-market.pdf.coredownload.inline.pdf")),
 ("Electricity tariffs","Hydro-Québec R-4333-2026: B-0004 p.11 table 2 (6.82 and 13 cents/kWh); B-0076 pp.3–5 (CD ≥5 MW, demand, energy, ratchet and ramp provisions). Profile proxies and simplified stabilized bill; not verified economic marginal cost. "+link("Original filing","https://www.regie-energie.qc.ca/fr/participants/dossiers/R-4333-2026/doc/R-4333-2026-B-0004-Dem-Piece-2026_02_19.pdf")+" · "+link("Revised rate","https://www.regie-energie.qc.ca/fr/participants/dossiers/R-4333-2026/doc/R-4333-2026-B-0076-Dem-PieceRev-2026_08_04.pdf")),
], [138,362])
para(story,"Full source URLs, parameter ranges and qualifications are in data/processed/model_parameters.csv and sources/tariff_observations.csv. Reproduce with scripts/ai_profitability_model.py, verify_model.py and build_reports.py.","small")
build("ai_model_report.pdf",story,4)

stats=[]
header(stats,"STATISTICAL REPORT  /  ECON 342","Electricity and AI model statistics","Observed international exports, 2015–2025, and conditional server scenarios. All monetary values in nominal CAD unless indicated.")
table(stats,["Observed trade statistic","Value","Observed trade statistic","Value"],[
 ("Monthly rows / years","132 / 11","2025 revenue","C$595.82m"),
 ("2025 export volume","4.192 TWh","2025 weighted price","C$142.13/MWh"),
 ("Annual price mean","C$65.35/MWh","Annual price median","C$49.55/MWh"),
 ("Annual price sample SD","C$34.16/MWh","Annual price range","C$38.79–142.13"),
 ("2015–25 volume-weighted price","C$52.96/MWh","Avoidable export cost","Unavailable"),
], [156,94,156,94])
story_chart=Image(str(RESULTS/"export_price_history.png"),width=500,height=118.6)
stats.append(story_chart)
para(stats,"Figure 1. Annual implied export receipts divided by MWh, CER Total rows. Historical statistics are descriptive; annual mean treats each year equally.","small")
heading(stats,"Model parameter ranges")
table(stats,["Rental price (C$/GPU-h)","Paid use","PUE","Hardware life","Facility life"],[
 ("5.67–8.75; stress 2.84","0–100%","1.20–1.56","3–6 yr","12–30 yr"),
], [145,82,82,94,97])
heading(stats,"Modeled outcomes at 50% utilization and base rental quote")
table(stats,["Cost case","MWh/year","Non-power cost","Profit, lower rate","Profit, CD avg","Relative return"],[
 (c.capitalize(),f"{q.annual_electricity_mwh:.1f}",money(q.annual_nonpower_cost_cad),money(q.annual_private_profit_preferential_cad),money(q.annual_private_profit_cd_average_cad),money(q.annual_relative_advantage_cad))
 for c in ["low","base","high"] for q in [all_cases[(all_cases.cost_case==c)&(all_cases.rental_case=="base")&(all_cases.export_case=="base")&(all_cases.paid_utilization==.5)].iloc[0]]
], [76,68,94,96,82,84])
para(stats,f"Revenue is {money(r['annual_gpu_revenue_cad'])} in all three rows. Base PUE 1.30, hardware C$460,618 and C$16,722/IT kW facility proxy. Base two-part CD profit: {money(r['annual_private_profit_cd_two_part_cad'])}.","small")
table(stats,["Break-even paid use","Low cost","Base cost","High cost"],[
 ("Lower-price scenario",b("low","preferential_average"),b("base","preferential_average"),b("high","preferential_average")),
 ("CD average",b("low","cd_average"),b("base","cd_average"),b("high","cd_average")),
 ("CD two-part",b("low","cd_two_part"),b("base","cd_two_part"),b("high","cd_two_part")),
 ("Export alternative",b("low","relative_exports"),b("base","relative_exports"),b("high","relative_exports")),
], [200,100,100,100])
para(stats,"Underlying scenario grid: 3,636 rows, 144 break-even results. Conditional outputs are not sampled financial outcomes or confidence intervals. Source and assumptions: model report appendix; original CER annual/monthly data, dated GPU quotes, measured server power and industry cost proxies.","small")
build("statistical_report.pdf",stats,1)
