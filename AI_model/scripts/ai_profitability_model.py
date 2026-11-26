"""Build a documented annual server-economic model from the repository's source observations."""
from pathlib import Path
import calendar
import itertools
import math
import json
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE.parent
RAW = ROOT / "data/raw"
PROCESSED = BASE / "data/processed"
RESULTS = BASE / "results"
SOURCES = BASE / "sources"

def read(category, file):
    return pd.read_csv(RAW / category / file)

def exact(table, column, value):
    match = table.loc[table[column] == value]
    if len(match) != 1:
        raise ValueError(f"Expected one {column}={value}, got {len(match)}")
    return match.iloc[0]

def trade_data():
    monthly = pd.read_csv(RAW / "electricity/electricity-exports-and-imports-monthly.csv", encoding="cp1252")
    monthly = monthly[(monthly.Activity == "Exports") & (monthly.Source == "Québec") & (monthly.Destination == "Total")].copy()
    monthly["period"] = pd.to_datetime(monthly.Period, format="%d/%m/%Y")
    monthly = monthly[monthly.period.dt.year.between(2015, 2025)].copy()
    monthly = monthly.sort_values("period")
    assert monthly.period.nunique() == len(monthly) == 132
    monthly = monthly.rename(columns={"Energy (MW.h)": "volume_mwh", "Total Value (CAN$)": "revenue_cad", "Price (CAN$/MW.h)": "publisher_price_cad_per_mwh"})
    assert monthly[["volume_mwh", "revenue_cad"]].notna().all().all()
    monthly["implied_price_cad_per_mwh"] = monthly.revenue_cad / monthly.volume_mwh
    monthly["year"] = monthly.period.dt.year
    annual = monthly.groupby("year", as_index=False)[["volume_mwh", "revenue_cad"]].sum()
    annual["implied_price_cad_per_mwh"] = annual.revenue_cad / annual.volume_mwh
    official = pd.read_csv(RAW / "electricity/electricity-exports-and-imports-annual.csv", encoding="cp1252")
    official = official[(official.Activity == "Exports") & (official.Source == "Québec") & (official.Destination == "Total") & official.Year.between(2015, 2025)]
    compare = annual.merge(official, left_on="year", right_on="Year", validate="one_to_one")
    assert len(compare) == 11
    assert (compare.volume_mwh - compare["Energy (MW.h)"]).abs().max() < 0.01
    assert (compare.revenue_cad - compare["Total Value (CAN$)"]).abs().max() < 0.01
    annual["publisher_price_cad_per_mwh"] = compare["Price (CAN$/MW.h)"].values
    monthly[["period", "volume_mwh", "revenue_cad", "implied_price_cad_per_mwh", "publisher_price_cad_per_mwh"]].to_csv(PROCESSED / "electricity_exports_monthly.csv", index=False)
    annual.to_csv(PROCESSED / "electricity_exports_annual.csv", index=False)
    return monthly, annual

def fx_rates():
    file = RAW / "exchange_rates/FXUSDCAD.csv"
    with file.open(encoding="utf-8-sig") as f:
        lines = f.readlines()
    start = next(i for i, line in enumerate(lines) if line.strip() == '"date","FXUSDCAD"')
    frame = pd.read_csv(file, skiprows=start, encoding="utf-8-sig")
    frame["date"] = pd.to_datetime(frame.date)
    return frame.dropna(subset=["FXUSDCAD"]).set_index("date")["FXUSDCAD"]

def build_parameters(monthly, annual):
    registry = pd.read_csv(ROOT / "sources/source_registry.csv").set_index("source_id")
    tariff = pd.read_csv(SOURCES / "tariff_observations.csv").set_index("parameter")
    fx = fx_rates()
    fx_now = float(fx.loc["2026-11-25"])
    fx_quote = float(fx.loc["2025-01-10"])
    fx_epoch = float(fx.loc["2022-10"].mean())
    power = read("server_specifications", "power-observations.csv")
    hardware = read("hardware_costs", "hardware-observations.csv")
    facility = read("facility_costs", "facility-observations.csv")
    opex = read("operating_costs", "operating-observations.csv")
    prices = read("gpu_pricing", "h100-rental-prices.csv")
    prices["cad_per_gpu_hour"] = prices.apply(lambda row: row.amount_per_gpu_hour * float(fx.loc[row.observation_date]), axis=1)
    prices.to_csv(PROCESSED / "gpu_rental_prices_cad.csv", index=False)
    low_rent = exact(prices, "pricing_arrangement", "GPU Clusters, on-demand pay-as-you-go").cad_per_gpu_hour
    base_rent = prices[(prices.provider == "Lambda") & (prices.instance_gpu_count == 8)].iloc[0].cad_per_gpu_hour
    high_rent = exact(prices, "pricing_arrangement", "North America, on-demand").cad_per_gpu_hour
    quote_usd = exact(hardware, "metric", "Eight-GPU server acquisition quote").value
    switch_usd = exact(hardware, "metric", "Networking component posted price").value
    epoch_usd = exact(hardware, "metric", "Release price including server/interconnect allocation").value
    quote_cad = quote_usd * fx_quote
    switch_cad = switch_usd * fx_now
    gross_opex_usd = opex.loc[opex.source_id == "kpmg", "value"].sum() * 1_000_000
    server_kw = float(exact(power, "metric", "Maximum rated power").value)
    opex_cad = gross_opex_usd * fx_now * server_kw / 30_000
    toronto = float(exact(facility, "source_id", "turner").lower) * 1000 * fx_now
    broader = float(exact(facility, "metric", "All-in greenfield development cost per capacity").lower) * 1000 * fx_now
    y25 = exact(annual, "year", 2025)
    export_base = y25.implied_price_cad_per_mwh
    records = []
    def add(parameter, low, base, high, unit, evidence, ids, notes):
        source_urls = []
        for ref in ids:
            source_urls.append(str(registry.loc[ref, "source_url"]) if ref in registry.index else str(tariff.loc[ref, "source_url"]))
        records.append(dict(parameter=parameter, low=low, base=base, high=high, unit=unit,
                            evidence_type=evidence, source_ids=";".join(ids), source_urls=";".join(dict.fromkeys(source_urls)), notes=notes))
    add("gpu_count", 8, 8, 8, "GPUs/server", "specification", ["nvidia","latif"], "Eight H100 GPUs")
    add("operating_hours_per_year", 8760, 8760, 8760, "hours/year", "assumption", [], "365 days, always online")
    add("paid_utilization", 0, .5, 1, "fraction", "scenario assumption", [], "Fraction of GPU hours paid; all customers assumed foreign")
    add("gpu_rental_price_cad_per_gpu_hour", low_rent, base_rent, high_rent, "CAD/GPU-hour", "converted advertised benchmarks", ["together","lambda","coreprice","boc_daily"], "Non-interruptible cluster on-demand, Lambda 8 GPUs, CoreWeave 8 GPUs; 2026-11-25 FX. Realized discounts and selling costs unknown.")
    add("stress_gpu_rental_price_cad_per_gpu_hour", float(prices.loc[~prices.gpu_configuration.str.contains("PCIe"), "cad_per_gpu_hour"].min()), float(prices.loc[~prices.gpu_configuration.str.contains("PCIe"), "cad_per_gpu_hour"].min()), float(prices.loc[~prices.gpu_configuration.str.contains("PCIe"), "cad_per_gpu_hour"].min()), "CAD/GPU-hour", "converted advertised benchmark", ["together","boc_daily"], "Preemptible HGX H100 rate, different service terms; stress only")
    add("server_idle_kw", 1.86, 1.86, 1.86, "kW", "measured benchmark", ["latif"], "Median idle node")
    add("server_busy_kw", 4.68, 7.92, 8.43, "kW", "measured benchmarks", ["latif"], "ResNet batch 512; Llama2-13b; CPU+GPU stress; workload sensitivity")
    add("server_design_kw", server_kw, server_kw, server_kw, "kW", "specification", ["nvidia"], "Rated maximum used for allocation and authorized facility capacity")
    add("pue", 1.20, 1.30, 1.56, "ratio", "benchmark-informed assumption", ["cologix","uptime"], "1.20 efficient scenario; 1.30 local operator upper specification (<1.30); 1.56 survey mean from repository")
    add("hardware_capex_cad_per_server", quote_cad + switch_cad/32, (quote_cad + 2*switch_cad/16)*1.05, max((quote_cad+2*switch_cad/8)*1.10, 8*epoch_usd*fx_epoch*1.10), "CAD/server", "benchmark plus assumptions", ["thinkmate","directdial","epoch","boc_daily"], "Low: vendor quote + one switch/32 nodes, no installation allowance. Base: quote + two switches/16 nodes +5% installation allowance. High: greater of quote + two switches/8 nodes or bundled 2022 launch benchmark, +10% installation. Network ratios and allowances are illustrative, not measured.")
    add("hardware_life_years", 6, 6, 3, "years", "benchmark-informed assumption", ["coreweave"], "Six-year accounting reference; shorter 3-year economic-life stress")
    add("facility_capex_cad_per_it_kw", toronto, toronto, broader, "CAD/IT kW", "regional benchmark proxy", ["turner","cushman","boc_daily"], "Toronto construction 11.76 USD/W; stress US/Canada 17.6m USD/MW assumes quoted capacity is IT capacity. Broader scope includes other development costs; no separate duplicate cooling/electrical add-on. 2026-11-25 FX proxy")
    add("facility_life_years", 30, 20, 12, "years", "benchmark-informed assumption", ["equinix","coreweave"], "Blended lives are scenario choices informed by building/core-system lives")
    add("nonpower_opex_cad_per_server_year", opex_cad, opex_cad*1.25, opex_cad*2, "CAD/server-year", "benchmark plus assumptions", ["kpmg","boc_daily"], "US 30 MW site labour, repair and security total US$7.3m/year, prorated by 10.2 IT kW; assumes 30 MW comparable IT capacity. 0/25/100% allowance for unknown recurring costs; not a Quebec budget")
    add("export_value_cad_per_mwh", annual.implied_price_cad_per_mwh.min(), export_base, monthly.loc[monthly.year==2025, "implied_price_cad_per_mwh"].max(), "CAD/MWh", "observed gross historical benchmark", ["cer_monthly","cer_annual"], "Low: minimum 2015-25 annual implied average; base: 2025 aggregate; high: highest 2025 monthly implied average. Avoidable costs missing; not marginal system cost")
    add("preferential_average", 68.2, 68.2, 68.2, "CAD/MWh", "illustrative tariff average", ["preferential_average"], "Existing modelled mix, hypothetical preferential comparison, not entitlement")
    add("cd_average", 130, 130, 130, "CAD/MWh", "illustrative proposed tariff average", ["cd_average"], "Existing profile-based proposed average, not a universal rate")
    add("cd_demand", 32.704, 32.704, 32.704, "CAD/kW/month", "proposed tariff provision", ["cd_demand"], "Proposed two-part charge")
    add("cd_energy", .0871, .0871, .0871, "CAD/kWh", "proposed tariff provision", ["cd_energy"], "Proposed two-part charge")
    add("cd_ramp_excess", .1742, .1742, .1742, "CAD/kWh", "proposed tariff provision", ["cd_ramp_excess"], "Ramp-up excess charge excluded from stabilized scenario")
    add("cd_winter_ratchet", .75, .75, .75, "fraction", "proposed tariff provision", ["cd_winter_ratchet"], "75% winter peak floor; identical recurring peaks assumed")
    add("facility_server_count", 500, 500, 500, "servers", "illustrative assumption", ["cd_min_authorized_kw"], "Homogeneous qualifying facility; authorized demand set to 500 × rated kW × PUE, peak allocated equally")
    add("fx_2026_11_25", fx_now, fx_now, fx_now, "CAD/USD", "observed", ["boc_daily"], "Used for dated GPU and switch quotes and as current translation for 2026 facility/2025 O&M proxies")
    add("fx_2025_01_10", fx_quote, fx_quote, fx_quote, "CAD/USD", "observed", ["boc_daily"], "Vendor server quote conversion")
    add("fx_2022_10_mean", fx_epoch, fx_epoch, fx_epoch, "CAD/USD", "calculated", ["boc_daily"], "Daily-rate arithmetic mean during historical release month")
    frame = pd.DataFrame(records)
    frame.to_csv(PROCESSED / "model_parameters.csv", index=False)
    return frame.set_index("parameter"), prices

def case_parameters(frame, case="base", rental="base", export="base", pue=None, hardware_life=None, busy=None):
    d = frame[case].astype(float).to_dict()
    d["gpu_rental_price_cad_per_gpu_hour"] = float(frame.loc["stress_gpu_rental_price_cad_per_gpu_hour" if rental=="stress" else "gpu_rental_price_cad_per_gpu_hour", "base" if rental=="stress" else rental])
    d["export_value_cad_per_mwh"] = float(frame.loc["export_value_cad_per_mwh", export])
    if pue is not None:
        d["pue"] = pue
    if hardware_life is not None:
        d["hardware_life_years"] = hardware_life
    if busy is not None:
        d["server_busy_kw"] = busy
    return d

def evaluate(p, utilization, price=None):
    if not 0 <= utilization <= 1:
        raise ValueError("Utilization must be in [0,1]")
    price = p["gpu_rental_price_cad_per_gpu_hour"] if price is None else price
    hours = p["operating_hours_per_year"]
    gpu_hours = p["gpu_count"] * hours
    paid_hours = gpu_hours * utilization
    revenue = paid_hours * price
    average_kw = p["server_idle_kw"] + (p["server_busy_kw"] - p["server_idle_kw"]) * utilization
    mwh = average_kw * p["pue"] * hours / 1000
    hardware = p["hardware_capex_cad_per_server"] / p["hardware_life_years"]
    facility = p["facility_capex_cad_per_it_kw"] * p["server_design_kw"] / p["facility_life_years"]
    nonpower = hardware + facility + p["nonpower_opex_cad_per_server_year"]
    bill_low = mwh * p["preferential_average"]
    bill_cd_proxy = mwh * p["cd_average"]
    # Illustrative steady-state load profile: each month has the same paid
    # share and a simultaneous busy peak (if utilization > 0). New facility,
    # no ramp-up, credits or voltage adjustments. 75% winter ratchet is
    # inactive since the same peak recurs. Not a forecast of actual bills.
    n = int(p["facility_server_count"])
    authorized_kw = n * p["server_design_kw"] * p["pue"]
    assert authorized_kw >= 5000
    peak_kw = n * (p["server_busy_kw"] if utilization > 0 else p["server_idle_kw"]) * p["pue"]
    months = [calendar.monthrange(2025, m)[1] * 24 for m in range(1, 13)]
    assert sum(months) == hours
    monthly_demand = max(peak_kw, p["cd_winter_ratchet"] * peak_kw)
    site_bill = sum(monthly_demand*p["cd_demand"] + n*average_kw*p["pue"]*h*p["cd_energy"] for h in months)
    bill_cd_detail = site_bill / n
    forgone = mwh * p["export_value_cad_per_mwh"]
    profit_low = revenue - nonpower - bill_low
    profit_cd = revenue - nonpower - bill_cd_proxy
    profit_detail = revenue - nonpower - bill_cd_detail
    relative = revenue - nonpower - forgone
    classification = "both" if profit_low >= 0 and profit_cd >= 0 else "preferential_only" if profit_low >= 0 else "neither"
    return dict(paid_utilization=utilization, rental_price_cad_per_gpu_hour=price, annual_gpu_hours=gpu_hours,
                annual_paid_gpu_hours=paid_hours, annual_gpu_revenue_cad=revenue, average_server_power_kw=average_kw,
                annual_electricity_mwh=mwh, annual_hardware_cost_cad=hardware, annual_facility_cost_cad=facility,
                annual_nonpower_opex_cad=p["nonpower_opex_cad_per_server_year"], annual_nonpower_cost_cad=nonpower,
                annual_preferential_bill_cad=bill_low, annual_cd_average_bill_cad=bill_cd_proxy,
                annual_cd_two_part_bill_cad=bill_cd_detail, representative_authorized_kw=authorized_kw,
                facility_monthly_billing_demand_kw=monthly_demand,
                annual_private_profit_preferential_cad=profit_low, annual_private_profit_cd_average_cad=profit_cd,
                annual_private_profit_cd_two_part_cad=profit_detail, annual_forgone_export_revenue_cad=forgone,
                annual_relative_advantage_cad=relative, relative_advantage_cad_per_mwh=relative/mwh,
                commercial_class=classification, ai_outperforms_exports=relative>0)

METRICS = {
    "preferential_average": ("annual_private_profit_preferential_cad", "annual_preferential_bill_cad"),
    "cd_average": ("annual_private_profit_cd_average_cad", "annual_cd_average_bill_cad"),
    "cd_two_part": ("annual_private_profit_cd_two_part_cad", "annual_cd_two_part_bill_cad"),
    "relative_exports": ("annual_relative_advantage_cad", "annual_forgone_export_revenue_cad")
}

def threshold(p, kind, price=None):
    metric, bill = METRICS[kind]
    # Affine above zero, with separate zero point for two-part peak.
    start = evaluate(p, 0, price)[metric]
    if start >= 0:
        return 0.0, "feasible"
    left = evaluate(p, 0.5, price)[metric]
    right = evaluate(p, 1, price)[metric]
    slope = (right-left)*2
    if right < 0 or slope <= 0:
        return None, "infeasible_at_100_percent"
    root = 1-right/slope
    assert 0 < root <= 1
    assert abs(evaluate(p, root, price)[metric]) < 1e-6
    return root, "feasible"

def main():
    for path in [PROCESSED, RESULTS]:
        path.mkdir(parents=True, exist_ok=True)
    monthly, annual = trade_data()
    frame, prices = build_parameters(monthly, annual)
    results = []
    breaks = []
    cases = ["low","base","high"]
    for cost, rental, export in itertools.product(cases, ["stress", *cases], cases):
        p = case_parameters(frame, cost, rental, export)
        label = dict(cost_case=cost, rental_case=rental, export_case=export)
        for index in range(101):
            results.append(label | evaluate(p, index/100))
        for kind, (_, bill) in METRICS.items():
            u, status = threshold(p, kind)
            row = evaluate(p, .5)
            breaks.append(label | dict(metric=kind, break_even_utilization=u, status=status,
                                       rental_price_cad_per_gpu_hour=p["gpu_rental_price_cad_per_gpu_hour"],
                                       minimum_rental_price_at_50pct_cad_per_gpu_hour=(row["annual_nonpower_cost_cad"]+row[bill])/row["annual_paid_gpu_hours"]))
    pd.DataFrame(results).to_csv(RESULTS / "scenario_results.csv", index=False)
    pd.DataFrame(breaks).to_csv(RESULTS / "break_even_results.csv", index=False)
    base = case_parameters(frame)
    one_way = []
    for variable, values in [("pue",[1.2,1.3,1.56]), ("hardware_life_years",[3,4,6]), ("server_busy_kw",[4.68,7.92,8.43]), ("gpu_rental_price_cad_per_gpu_hour",[base["stress_gpu_rental_price_cad_per_gpu_hour"],base["gpu_rental_price_cad_per_gpu_hour"],float(prices.cad_per_gpu_hour.max())]), ("export_value_cad_per_mwh",list(frame.loc["export_value_cad_per_mwh",["low","base","high"]]))]:
        for value in values:
            p = base | {variable: float(value)}
            for kind in METRICS:
                u, status = threshold(p, kind)
                one_way.append(dict(variable=variable,value=value,metric=kind,break_even_utilization=u,status=status))
    pd.DataFrame(one_way).to_csv(RESULTS / "one_way_sensitivity.csv",index=False)
    base_result = evaluate(base,.5)
    # Independent worked example, using user's exact assumptions and no cost amount.
    worked = evaluate(base | {"pue":1.2,"server_busy_kw":7.92},.5,price=5)
    assert abs(worked["annual_gpu_revenue_cad"]-175200)<1e-8
    assert abs(worked["annual_electricity_mwh"]-51.40368)<1e-8
    assert abs(worked["annual_forgone_export_revenue_cad"]-7305.84)<.01
    y25 = exact(annual, "year", 2025)
    assert abs(y25.revenue_cad - 595817584.507)<.02
    assert abs(y25.volume_mwh - 4192156.136)<.01
    assert len(results)==3636 and len(breaks)==144
    for row in results:
        assert math.isclose(row["annual_private_profit_preferential_cad"]-row["annual_private_profit_cd_average_cad"],
                            row["annual_cd_average_bill_cad"]-row["annual_preferential_bill_cad"], abs_tol=1e-8)
        assert math.isclose(row["annual_relative_advantage_cad"],row["relative_advantage_cad_per_mwh"]*row["annual_electricity_mwh"],abs_tol=1e-8)
    summary = {"base_at_50_pct":base_result,"historical": {"months":len(monthly),"years":len(annual),"2025_revenue_cad":float(y25.revenue_cad),"2025_volume_mwh":float(y25.volume_mwh),"2025_implied_value":float(y25.implied_price_cad_per_mwh),"annual_price_mean":float(annual.implied_price_cad_per_mwh.mean()),"annual_price_median":float(annual.implied_price_cad_per_mwh.median()),"annual_price_std_sample":float(annual.implied_price_cad_per_mwh.std()),"annual_price_min":float(annual.implied_price_cad_per_mwh.min()),"annual_price_max":float(annual.implied_price_cad_per_mwh.max()),"all_year_weighted_price":float(annual.revenue_cad.sum()/annual.volume_mwh.sum())},"scenario_rows":len(results),"break_even_rows":len(breaks),"checks":"PASS"}
    (RESULTS / "summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps(summary,indent=2))

if __name__ == "__main__":
    main()
