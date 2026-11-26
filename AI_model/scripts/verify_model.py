"""Independent Decimal checks against raw source files and saved results."""
from pathlib import Path
from decimal import Decimal as D
import csv, json

BASE=Path(__file__).resolve().parents[1]
ROOT=BASE.parent
with (ROOT/"data/raw/electricity/electricity-exports-and-imports-monthly.csv").open(encoding="cp1252") as f:
    rows=[r for r in csv.DictReader(f) if r["Period"].endswith("/2025") and r["Activity"]=="Exports" and r["Source"]=="Québec" and r["Destination"]=="Total"]
assert len(rows)==12
volume=sum(D(r["Energy (MW.h)"]) for r in rows)
revenue=sum(D(r["Total Value (CAN$)"]) for r in rows)
export=revenue/volume
with (BASE/"data/processed/model_parameters.csv").open() as f:
    p={r["parameter"]:D(r["base"]) for r in csv.DictReader(f)}
with (BASE/"results/scenario_results.csv").open() as f:
    records=list(csv.DictReader(f))
r=next(r for r in records if r["cost_case"]==r["rental_case"]==r["export_case"]=="base" and D(r["paid_utilization"])==D(".5"))
money=lambda key: D(r[key])
close=lambda a,b: abs(a-b)<D(".00001")
hours=D(8760)
price=D("4.69")*D("1.4219")
energy=D("4.89")*D("1.30")*hours/D(1000)
hardware=(D("300107")*D("1.4422")+D(2)*D("33025")*D("1.4219")/D(16))*D("1.05")/D(6)
facility=D("11.76")*D(1000)*D("1.4219")*D("10.2")/D(20)
opex=D("7300000")*D("1.4219")*D("10.2")/D(30000)*D("1.25")
cost=hardware+facility+opex
gross=D(8)*hours*D(".5")*price
assert close(energy,money("annual_electricity_mwh"))
assert close(cost,money("annual_nonpower_cost_cad"))
assert close(gross,money("annual_gpu_revenue_cad"))
for key,rate in [("annual_private_profit_preferential_cad",D("68.20")),("annual_private_profit_cd_average_cad",D(130)),("annual_relative_advantage_cad",export)]:
    assert close(gross-cost-energy*rate,money(key))
detailed=D("7.92")*D("1.30")*D("32.704")*D(12)+energy*D(1000)*D(".08710")
assert close(detailed,money("annual_cd_two_part_bill_cad"))
with (BASE/"results/break_even_results.csv").open() as f:
    b=list(csv.DictReader(f))
for rate,name in [(D("68.20"),"preferential_average"),(D(130),"cd_average"),(export,"relative_exports")]:
    idle=D("1.86")*D("1.30")*hours/D(1000)
    increment=(D("7.92")-D("1.86"))*D("1.30")*hours/D(1000)
    root=(cost+idle*rate)/(D(8)*hours*price-increment*rate)
    row=next(x for x in b if x["cost_case"]==x["rental_case"]==x["export_case"]=="base" and x["metric"]==name)
    assert close(root,D(row["break_even_utilization"]))
assert len(records)==3636 and len(b)==144
assert not any(r["status"]=="infeasible_at_100_percent" and r["break_even_utilization"] for r in b)
msg=f"""Verification passed
- 12 Quebec 2025 CER monthly total rows; C${revenue:,.3f} / {volume:,.3f} MWh = C${export:.8f}/MWh.
- Independent Decimal recalculation using raw quoted values for FX, server purchase, assigned network/installation scenarios, facility proxy, O&M, revenue, energy, three electricity comparisons and two-part bill.
- Independent closed-form break-even checks for both average tariffs and export alternative.
- 3,636 utilization-price-cost-export scenarios; 144 break-even records. Unreachable cutoffs are null with explicit status.
- The model's internal checks also reconcile 132 months with 11 official annual totals and replicate the original C$175,200 / 51.40368 MWh worked example.

Limitations: verification confirms formulas and source transcription, not the representativeness of assumptions.
"""
(BASE/"results/verification_report.md").write_text(msg,encoding="utf-8")
print(msg)
