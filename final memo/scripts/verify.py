"""Independently re-compute the published tables without importing the model."""
import csv
import json
import re
import subprocess
from decimal import Decimal as D
from pathlib import Path

MEMO = Path(__file__).resolve().parents[1]
REPO = MEMO.parent


def rows(path, encoding="utf-8"):
    with path.open(encoding=encoding, newline="") as stream:
        return list(csv.DictReader(stream))


def near(actual, expected, tolerance="0.000001"):
    if abs(D(str(actual)) - D(str(expected))) > D(tolerance):
        raise AssertionError((actual, expected))


settings = json.loads((MEMO / "data/analysis_settings.json").read_text())
results = MEMO / "results"
inputs = {r["parameter"]: r for r in rows(REPO / "AI_model/data/processed/model_parameters.csv")}
original = rows(REPO / "data/raw/electricity/electricity-exports-and-imports-monthly.csv", "cp1252")
trade = [r for r in original if r["Period"].endswith("/2025") and
         (r["Activity"], r["Source"], r["Destination"]) == ("Exports", "Québec", "Total")]
assert len(trade) == 12 and len({r["Period"] for r in trade}) == 12
export_value = sum(D(row["Total Value (CAN$)"]) for row in trade)
export_mwh = sum(D(row["Energy (MW.h)"]) for row in trade)
near(export_value, "595817584.507")
near(export_mwh, "4192156.136")
export_rate = export_value / export_mwh
near(inputs["export_value_cad_per_mwh"]["base"], export_rate)
valet = (REPO / "data/raw/exchange_rates/FXUSDCAD.csv").read_text(encoding="utf-8-sig")
fx = dict(re.findall(r'^"(\d{4}-\d{2}-\d{2})","([0-9.]+)"$', valet, flags=re.M))
offers = rows(REPO / "data/raw/gpu_pricing/h100-rental-prices.csv")
lambda_offer, = [item for item in offers if item["provider"] == "Lambda" and item["instance_gpu_count"] == "8"]
near(D(lambda_offer["amount_per_gpu_hour"]) * D(fx[lambda_offer["observation_date"]]),
     inputs["gpu_rental_price_cad_per_gpu_hour"]["base"])


def direct(cost, rental, rate, use, override=None):
    p = {key: D(row[cost]) for key, row in inputs.items()}
    irr = D(str(rate))
    u = D(str(use))
    price = D(override) if override is not None else D(inputs["gpu_rental_price_cad_per_gpu_hour"][rental]) if rental != "stress" else p["stress_gpu_rental_price_cad_per_gpu_hour"]
    h = p["operating_hours_per_year"]
    revenue = h * p["gpu_count"] * price * u
    idle = p["server_idle_kw"]
    busy = p["server_busy_kw"]
    pue = p["pue"]
    kwh = h * (idle * (1-u) + busy*u) * pue
    site_peak = (busy if u else idle) * pue * p["facility_server_count"]
    reserved_kw = p["server_design_kw"] * pue * p["facility_server_count"]
    assert reserved_kw >= 5000
    assert site_peak >= D(".75") * site_peak
    underuse = D("92.28") * max(D(0), reserved_kw*D(".60") - site_peak) / p["facility_server_count"]
    a = kwh * D(".0682")
    b = kwh * D(".130")
    c = kwh * D(".08710") + site_peak / p["facility_server_count"] * D("32.704") * 12 + underuse
    # Divide capex by the present value of a $1 end-of-year annuity.
    def annualize(capex, life):
        pv = sum((1+irr)**(-t) for t in range(1,int(life)+1))
        return capex / pv

    hardware = annualize(p["hardware_capex_cad_per_server"], p["hardware_life_years"])
    facility = annualize(p["facility_capex_cad_per_it_kw"]*p["server_design_kw"], p["facility_life_years"])
    opex = p["nonpower_opex_cad_per_server_year"]
    margin = revenue - hardware - facility - opex
    mwh = kwh / 1000
    exports = mwh * export_rate
    return dict(annual_revenue=revenue, annual_hardware=hardware, annual_facility=facility,
                annual_nonpower_opex=opex, annual_mwh=mwh, export_cad_per_mwh=export_rate,
                forgone_exports=exports, ai_advantage=margin-exports,
                ai_advantage_per_mwh=(margin-exports)/mwh, site_peak_kw=site_peak,
                cd_underuse_charge=underuse, bill_A=a, bill_B=b, bill_C=c, profit_A=margin-a,
                profit_B=margin-b, profit_C=margin-c, subsidy_AB=b-a, bill_gap_CA=c-a)


comparison = rows(results/"export_comparison.csv")
commercial = rows(results/"commercial_scenarios.csv")
assert len(comparison) == 4 and len(commercial) == 240
for row in comparison + commercial:
    expected = direct(row.get("cost_case","base"), row.get("rental_case","base"),
                      row.get("financing_rate",.08), row["utilization"])
    for key, value in expected.items():
        near(row[key], value)
    near(D(row["profit_A"])-D(row["profit_B"]), row["subsidy_AB"])

legacy = json.loads((REPO/"AI_model/results/summary.json").read_text())["base_at_50_pct"]
old = direct("base","base",0,.50)
for new_key, old_key in [
    ("annual_revenue","annual_gpu_revenue_cad"),("annual_mwh","annual_electricity_mwh"),
    ("annual_hardware","annual_hardware_cost_cad"),("annual_facility","annual_facility_cost_cad"),
    ("ai_advantage","annual_relative_advantage_cad"),("profit_A","annual_private_profit_preferential_cad"),
    ("profit_B","annual_private_profit_cd_average_cad"),("profit_C","annual_private_profit_cd_two_part_cad"),
]:
    near(old[new_key], legacy[old_key])

thresholds = rows(results/"break_even.csv")
curves = rows(results/"break_even_curves.csv")
assert len(thresholds) == 180 and len(curves) == 1134
for row in thresholds + curves:
    cost = row["cost_case"]
    tariff = row["tariff"]
    rental = row.get("rental_case","base")
    rate = row.get("financing_rate",.08)
    override = row.get("rent")
    root = row["break_even_utilization"]
    at_full = direct(cost,rental,rate,1,override)
    metric = "profit_"+tariff
    if root:
        near(direct(cost,rental,rate,root,override)[metric], 0)
        assert 0 < D(root) <= 1 and at_full[metric] >= 0
    else:
        assert at_full[metric] < 0
    for use, column in [(.5,"minimum_rent_at_50pct"),(1,"minimum_rent_at_100pct")]:
        near(direct(cost,rental,rate,use,row[column])[metric], 0)

indexed = {(r["cost_case"],r["rental_case"],r["financing_rate"],r["tariff"]):r for r in thresholds}
windows = rows(results/"viability_windows.csv")
assert len(windows) == 120
for row in windows:
    keys = (row["cost_case"],row["rental_case"],row["financing_rate"])
    a = indexed[keys+("A",)]["break_even_utilization"]
    b = indexed[keys+(row["comparator"],)]["break_even_utilization"]
    assert row["preferential_only_from"] == a
    assert row["both_from"] == b
    near(row["neither_until"], a or 1)
    if a:
        near(row["preferential_only_until"], b or 1)

sensitivity = rows(results/"one_way_sensitivity.csv")
profit = lambda use=.5, rate=.08, cost="base", rental="base": direct(cost,rental,rate,use)["profit_B"]
base_profit = profit()
base_pue = D(inputs["pue"]["base"])
r = D(".08")
def annuity(life):
    return sum((1+r)**-t for t in range(1,life+1))

base_capex = D(inputs["hardware_capex_cad_per_server"]["base"])
life = int(D(inputs["hardware_life_years"]["base"]))
adjusted = {
    "Paid utilization": (profit(.25),profit(.75)),
    "On-demand rental quote": (profit(rental="low"),profit(rental="high")),
    "Cost of capital": (profit(rate=0),profit(rate=.15)),
    "Hardware life": (base_profit+base_capex/annuity(life)-base_capex/annuity(3),base_profit),
    "Installed hardware cost": tuple(base_profit+(base_capex-D(inputs["hardware_capex_cad_per_server"][k]))/annuity(life)
                                     for k in ("low","high")),
    "PUE": tuple(base_profit+direct("base","base",.08,.5)["bill_B"]*(1-D(pue)/base_pue) for pue in ("1.20","1.56")),
    "Tariff proxy": (base_profit,direct("base","base",.08,.5)["profit_A"]),
}
assert len(sensitivity) == len(adjusted)
for row in sensitivity:
    lo, hi = sorted(adjusted[row["variable"]])
    near(row["low_profit"],lo)
    near(row["high_profit"],hi)
    near(row["profit_span"],hi-lo)

assumptions = {item["scenario"]: item for item in rows(MEMO/"data/welfare_scenarios.csv")}
welfare = rows(results/"domestic_welfare.csv")
assert len(welfare) == 16
for row in welfare:
    if row["tariff"] == "No build":
        near(row["conditional_quebec_welfare"], 0)
        near(row["site_annual_mwh"], 0)
        continue
    p = assumptions[row["scenario"]]
    tax_share, local_share, wage_share, supplier, supply, admin, grant = map(D, [
        p["quebec_tax_share_of_positive_profit"], p["quebec_ownership"],p["wage_premium_as_share_of_payroll"],
        p["supplier_surplus_cad_year"],p["extra_supply_cost_cad_year"],p["public_admin_cost_cad_year"],p["explicit_grant_cad_year"]])
    t = row["tariff"]
    site = direct("base","base",.08,row["utilization"])
    n = D(500)
    private = site["profit_"+t]*n
    taxes = tax_share*max(0,private+grant)
    retained = local_share*(private+grant-taxes)
    wage_rent = D(4_000_000)*D(fx["2026-11-25"])*D("10.2")*n/30000*wage_share
    utility_receipts = site["bill_"+t]*n
    exports = site["forgone_exports"]*n
    hurdle = exports+supply+admin+grant-utility_receipts
    net = retained+wage_rent+supplier+taxes-hurdle
    for key, value in dict(site_private_profit_before_tax=private,incremental_quebec_tax=taxes,
                           quebec_retained_profit=retained,incremental_labour_income=wage_rent,
                           utility_receipts=utility_receipts,forgone_gross_exports=exports,
                           supplier_surplus=supplier,extra_supply_cost=supply,public_admin_cost=admin,explicit_grant=grant,
                           site_annual_mwh=site["annual_mwh"]*n,
                           implicit_discount_vs_B=site["subsidy_AB"]*n if t=="A" else 0,
                           minimum_domestic_benefits=max(0,hurdle),conditional_quebec_welfare=net,
                           additional_benefits_needed=max(0,-net)).items():
        near(row[key],value)
    if row["investment_case"] == "Preferential only":
        assert site["profit_A"] > 0 > site["profit_B"]

pdf = MEMO/"reports/final_economic_analysis.pdf"
info = subprocess.check_output(["pdfinfo",pdf],text=True)
assert re.search(r"^Pages:\s+4$",info,re.M)
sections = subprocess.check_output(["pdftotext","-layout",pdf,"-"],text=True).split("\f")[:4]
for page, footer in zip(sections,("1/4","2/4","3/4","4/4"),strict=True):
    assert "Sources and assumptions" in page and footer in page
for page, expected in zip(sections,[
        ("142.13","104,335","-10,049","1,874"),
        ("26.56%","27.09%","27.60%","105,010","8,891"),
        ("26.82%","1.47m","1.06m","2.07m"),
        ("1.72m","0.86m","1.06m"),
],strict=True):
    assert all(term in page for term in expected), (expected, page)

print("PASS: raw CER and FX, legacy parity, 244 comparison rows, 1,314 thresholds and prices,")
print("120 viability windows, seven sensitivities, 16 welfare cases, and four-page PDF content.")
