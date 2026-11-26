# ECON 342 | AI profitability and electricity opportunity cost

This folder evaluates a representative eight-H100 server using the source observations collected in the repository's existing `data/raw/` and `sources/` folders. All financial results are conditional annual estimates per server. All CAD amounts are nominal unless explicitly stated.

## Reproduce

From the repository root, using Python 3.10+:

```sh
python -m pip install -r AI_model/requirements.txt
python scripts/download_data.py --verify
python AI_model/scripts/ai_profitability_model.py
python AI_model/scripts/verify_model.py
python AI_model/scripts/build_reports.py
```

The PDF scripts use DejaVu Sans and Serif fonts from the standard Linux fonts directory (`/usr/share/fonts/truetype/dejavu/`). A local installation of the fonts is required for PDF rendering.

## Outputs

- `reports/ai_model_report.pdf`: three narrative pages and a one-page data appendix.
- `reports/statistical_report.pdf`: one page of historical descriptive statistics and scenario outcomes.
- `data/processed/model_parameters.csv`: every model parameter, evidence class, scenario value, source ID, URL and assumption.
- `data/processed/electricity_exports_{monthly,annual}.csv`: cleaned CER Quebec international export totals.
- `data/processed/gpu_rental_prices_cad.csv`: dated original listed prices and converted CAD figures.
- `results/scenario_results.csv`: 3 cost cases × 4 rental cases × 3 export benchmarks × 101 utilization levels.
- `results/break_even_results.csv`: 144 threshold records, including two average tariffs, a conditional two-part proposed tariff and the export alternative. The rental price required at 50% paid use is also recorded.
- `results/one_way_sensitivity.csv`: selected independent parameter sensitivity tests.
- `results/verification_report.md`: source reconciliation and independent Decimal arithmetic checks.
- `sources/tariff_observations.csv`: verified tariff evidence from the regulator docket (B-0004, B-0076).

## Interpretation

The low, base and high cost cases are illustrative model bundles, not empirical probability intervals. The three on-demand rental price cases vary separately from the cost assumptions. The preemptible price is an additional stress case with different commercial terms. A cell classified as profitable at both average tariff proxies indicates there is no break-even requirement for a lower price in that scenario. Equality is treated as break-even, and negative returns at full utilization are explicitly marked infeasible.

The 2025 export benchmark is a gross historical revenue/volume ratio. Avoidable export costs, actual Quebec H100 installation and operating costs, realized GPU rental prices, hour-by-hour power and actual site demand are unavailable. The model uses disclosed benchmarks plus transparent scenario assumptions. It omits financing return, taxes and salvage value; simple annualized capital cost is not a complete investment valuation. Some inputs are from different dates without inflation harmonization.

The two flat-price scenarios use profile-based tariff averages from Hydro-Québec's filing. The CD two-part illustration assumes a 500-server stabilized facility with recurrent simultaneous peak draw, equal server allocation and no ramp-up, special credits, voltage adjustment or other additional contractual cost. The actual tariff may differ, and the proposed rate is not assumed to be an approved or verified marginal system cost.

The model compares commercial economics and the historical electricity export opportunity-cost benchmark. The question of domestic welfare and investment additionality requires separate evidence.
