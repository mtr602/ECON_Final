# Verification report

**Result: PASS.** The calculation script and separate Decimal verifier ran successfully. The verifier checks the published tables using the original CER and Bank of Canada files and the prior model parameters. Its calculation uses the present value of a unit annuity to verify capital recovery independently of the production CRF formula.

| Check | Result |
| --- | --- |
| 2025 trade | Exactly 12 unique Québec export Total months. C$595,817,584.507 and 4,192,156.136 MWh reconcile to C$142.1267636934/MWh. |
| Rental conversion | The dated Lambda US$4.69 price and C$1.4219/US$ rate give C$6.668711 per GPU-hour. |
| Capital recovery and legacy comparison | Zero percent reproduces the prior base-case straight-line results at 50% paid use. At 8% the new hardware and facility annual charges are C$99,638.83 and C$17,371.89 per server. |
| Cash flows and tariff bills | All four export comparison rows and 240 commercial rows were checked cell by cell. At 50% use the base annual bills per server are C$3,797.88, C$7,239.35 and C$8,891.01 under A, B and C. The verification uses the literal filing rates and checks the simulated underuse charge against the original contract language. |
| Break-even | All 180 scenario thresholds and 1,134 chart rows were checked at their root or at full utilization when infeasible. Minimum rental prices were checked by substituting them into profit at 50% and 100%. Verified 120 comparative viability windows and all seven sensitivity calculations. |
| Domestic welfare | All 16 rows checked, including the zero-flow no-build case, site energy, imputed wage gains, tariff transfer, retained profits and public balances. The preferential-only example has positive A profit and negative B profit at the same operating point. |
| Report and exhibit | Verified four US Letter pages with embedded fonts, four source notes and page numbers. Rendered and visually inspected every page, including the chart, table boundaries and footer spacing. Checked key numeric statements against PDF text. |
| Upstream preservation | Compared the staged change against the input commit. All project changes are inside the root-level `final memo/` folder, including the report and its supporting files. |

The December 2026 continuation of the Rate CD hearing was listed in the docket when checked. The filing checks establish the scenario rates and provisions. Actual bills, market outcomes, ownership, local payroll and marginal power costs depend on the project.

Run `python -B scripts/verify.py` from this folder to reproduce the independent calculation check.

**PDF SHA-256** `892ac7017bec98fcec6ff1af6a2239d7a3b65790778df4dbf6cc16903acb6a3a`.
