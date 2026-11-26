"""Build the final-memo data using the repository's existing engineering model."""
import csv
import itertools
import json
import sys
from pathlib import Path

MEMO = Path(__file__).resolve().parents[1]
REPO = MEMO.parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO / "AI_model/scripts"))
from ai_profitability_model import evaluate  # noqa: E402

TARIFFS = ("A", "B", "C")
SETTINGS = json.loads((MEMO / "data/analysis_settings.json").read_text())
RATE = SETTINGS["base_financing_rate"]
USES = SETTINGS["reported_utilizations"]


def read(path):
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


PARAMS = {row["parameter"]: row for row in read(REPO / "AI_model/data/processed/model_parameters.csv")}


def parameters(cost, rental):
    p = {name: float(row[cost]) for name, row in PARAMS.items()}
    p["export_value_cad_per_mwh"] = float(PARAMS["export_value_cad_per_mwh"]["base"])
    if rental == "stress":
        p["gpu_rental_price_cad_per_gpu_hour"] = p["stress_gpu_rental_price_cad_per_gpu_hour"]
    else:
        p["gpu_rental_price_cad_per_gpu_hour"] = float(PARAMS["gpu_rental_price_cad_per_gpu_hour"][rental])
    return p


def write(filename, rows):
    with (MEMO / "results" / filename).open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0], lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def crf(rate, life):
    if rate == 0:
        return 1 / life
    return rate / (1 - (1 + rate) ** -life)


def outcome(p, use, rate):
    engineering = evaluate(p, use)
    hardware = p["hardware_capex_cad_per_server"] * crf(rate, p["hardware_life_years"])
    facility = p["facility_capex_cad_per_it_kw"] * p["server_design_kw"] * crf(rate, p["facility_life_years"])
    opex = p["nonpower_opex_cad_per_server_year"]
    revenue = engineering["annual_gpu_revenue_cad"]
    mwh = engineering["annual_electricity_mwh"]
    export = engineering["annual_forgone_export_revenue_cad"]
    margin = revenue - hardware - facility - opex
    authorized = engineering["representative_authorized_kw"]
    peak = engineering["facility_monthly_billing_demand_kw"]
    # Contract scenario: projected ramp-up maximum equals authorized nameplate.
    underuse = max(0, SETTINGS["rate_cd_underuse_threshold"] * authorized - peak)
    underuse *= SETTINGS["rate_cd_underuse_charge_cad_per_kw"] / p["facility_server_count"]
    a = engineering["annual_preferential_bill_cad"]
    b = engineering["annual_cd_average_bill_cad"]
    c = engineering["annual_cd_two_part_bill_cad"] + underuse
    return dict(utilization=use, annual_revenue=revenue, annual_hardware=hardware, annual_facility=facility,
                annual_nonpower_opex=opex, annual_mwh=mwh, export_cad_per_mwh=p["export_value_cad_per_mwh"],
                forgone_exports=export, ai_advantage=margin-export, ai_advantage_per_mwh=(margin-export)/mwh,
                site_peak_kw=peak, cd_underuse_charge=underuse, bill_A=a, bill_B=b, bill_C=c,
                profit_A=margin-a, profit_B=margin-b, profit_C=margin-c,
                subsidy_AB=b-a, bill_gap_CA=c-a)


def root(p, rate, metric):
    # For positive utilization, revenue, energy and the selected profit are affine.
    half = outcome(p, .5, rate)[metric]
    full = outcome(p, 1, rate)[metric]
    if full < 0:
        return None
    return 1 - full / ((full - half) * 2)


def threshold(p, rate, tariff):
    at_half = outcome(p, .5, rate)
    at_full = outcome(p, 1, rate)
    current_price = p["gpu_rental_price_cad_per_gpu_hour"]
    return dict(
        break_even_utilization=root(p, rate, f"profit_{tariff}"),
        minimum_rent_at_50pct=current_price * (1 - at_half[f"profit_{tariff}"] / at_half["annual_revenue"]),
        minimum_rent_at_100pct=current_price * (1 - at_full[f"profit_{tariff}"] / at_full["annual_revenue"]),
    )


def classification(p, rate, comparator):
    a = root(p, rate, "profit_A")
    b = root(p, rate, f"profit_{comparator}")
    if a is None:
        return dict(neither_until=1, preferential_only_from=None, preferential_only_until=None, both_from=None)
    return dict(neither_until=a, preferential_only_from=a, preferential_only_until=b if b is not None else 1,
                both_from=b)


def site_welfare(p, use, tariff, label, assumptions):
    server = outcome(p, use, RATE)
    n = p["facility_server_count"]
    option = {name: float(value) for name, value in assumptions.items() if name != "scenario"}
    pre_tax = server[f"profit_{tariff}"] * n
    grant = option["explicit_grant_cad_year"]
    tax = max(0, pre_tax + grant) * option["quebec_tax_share_of_positive_profit"]
    local = option["quebec_ownership"] * (pre_tax + grant - tax)
    labour = next(float(row["value"]) for row in read(REPO / "data/raw/operating_costs/operating-observations.csv")
                  if row["source_id"] == "kpmg" and row["metric"] == "Staffing/labour")
    payroll = labour * 1_000_000 * p["fx_2026_11_25"] * p["server_design_kw"] * n / SETTINGS["opex_benchmark_it_kw"]
    wage_rent = payroll * option["wage_premium_as_share_of_payroll"]
    supplier = option["supplier_surplus_cad_year"]
    bill = server[f"bill_{tariff}"] * n
    export = server["forgone_exports"] * n
    supply = option["extra_supply_cost_cad_year"]
    admin = option["public_admin_cost_cad_year"]
    net = local + wage_rent + supplier + tax + bill - export - supply - admin - grant
    hurdle = export + supply + admin + grant - bill
    return dict(scenario=assumptions["scenario"], investment_case=label, tariff=tariff, utilization=use,
                server_count=int(n), site_annual_mwh=server["annual_mwh"]*n, site_private_profit_before_tax=pre_tax,
                site_payroll_proxy=payroll, quebec_retained_profit=local, incremental_labour_income=wage_rent,
                supplier_surplus=supplier, incremental_quebec_tax=tax, utility_receipts=bill,
                forgone_gross_exports=export, extra_supply_cost=supply, public_admin_cost=admin, explicit_grant=grant,
                implicit_discount_vs_B=server["subsidy_AB"]*n if tariff == "A" else 0,
                minimum_domestic_benefits=max(0, hurdle), conditional_quebec_welfare=net,
                additional_benefits_needed=max(0, -net))


def main():
    cases = ("low", "base", "high")
    rentals = ("stress", *cases)
    base = parameters("base", "base")
    write("export_comparison.csv", [outcome(base, use, RATE) for use in USES])
    matrix, thresholds, windows = [], [], []
    for cost, rental, rate in itertools.product(cases, rentals, SETTINGS["financing_rates"]):
        p = parameters(cost, rental)
        label = dict(cost_case=cost, rental_case=rental, financing_rate=rate,
                     rental_cad_per_gpu_hour=p["gpu_rental_price_cad_per_gpu_hour"])
        matrix.extend(label | outcome(p, use, rate) for use in USES)
        thresholds.extend(label | dict(tariff=t) | threshold(p, rate, t) for t in TARIFFS)
        windows.extend(label | dict(comparator=t) | classification(p, rate, t) for t in ("B", "C"))
    write("commercial_scenarios.csv", matrix)
    write("break_even.csv", thresholds)
    write("viability_windows.csv", windows)
    write("break_even_curves.csv", [
        dict(cost_case=cost, tariff=t, rent=rent) | threshold(parameters(cost, "base") | {
            "gpu_rental_price_cad_per_gpu_hour": rent}, RATE, t)
        for cost, t, cent in itertools.product(cases, TARIFFS, range(275, 901, 5))
        for rent in [cent / 100]
    ])
    origin = outcome(base, .5, RATE)["profit_B"]
    variants = [
        ("Paid utilization", "25% to 75%", [(base, u, RATE) for u in (.25,.75)]),
        ("Hardware life", "3 to 6 years", [(base | {"hardware_life_years": v}, .5, RATE) for v in (3,6)]),
        ("On-demand rental quote", "low to high", [(parameters("base", v), .5, RATE) for v in ("low","high")]),
        ("Cost of capital", "0% to 15%", [(base, .5, r) for r in (0,.15)]),
        ("Installed hardware cost", "low to high", [(base | {"hardware_capex_cad_per_server": float(PARAMS["hardware_capex_cad_per_server"][v])}, .5,RATE) for v in ("low","high")]),
        ("PUE", "1.20 to 1.56", [(base | {"pue": v}, .5,RATE) for v in (1.2,1.56)]),
    ]
    rows = []
    for variable, tested, inputs in variants:
        lo, hi = sorted(outcome(*item)["profit_B"] for item in inputs)
        rows.append(dict(variable=variable, tested_range=tested, low_profit=lo, high_profit=hi,
                         profit_span=hi-lo, reference_profit=origin))
    rows.append(dict(variable="Tariff proxy", tested_range="A versus B", low_profit=origin,
                     high_profit=outcome(base,.5,RATE)["profit_A"], profit_span=outcome(base,.5,RATE)["subsidy_AB"],
                     reference_profit=origin))
    write("one_way_sensitivity.csv", sorted(rows, key=lambda row: -row["profit_span"]))
    a,b = [root(base, RATE, f"profit_{t}") for t in ("A","B")]
    points = [("Either tariff", .50, "A"), ("Either tariff", .50, "B"),
              ("Preferential only", (a+b)/2, "A"), ("Neither tariff (no build)", .15, None)]
    scenarios = read(MEMO / "data/welfare_scenarios.csv")
    welfare = []
    for label, use, tariff in points:
        for item in scenarios:
            if tariff:
                welfare.append(site_welfare(base, use, tariff, label, item))
            else:
                zero = site_welfare(base, use, "A", label, item)
                welfare.append(dict.fromkeys(zero, 0) | dict(scenario=item["scenario"], investment_case=label,
                               tariff="No build", utilization=use))
    write("domestic_welfare.csv", welfare)


if __name__ == "__main__":
    main()
