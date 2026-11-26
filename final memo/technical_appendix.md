# Technical appendix

The four analytical pages use the prior model at commit `fd6efcf`. The model and statistical report remain in `AI_model`. This analysis extends their straight-line capital charge with annual capital recovery and adds a conditional Québec welfare ledger. The 2025 export benchmark remains constant across the cost and financing cases.

## Inputs and definitions

| Input | Unit | Definition and evidence |
| --- | --- | --- |
| Export benchmark | C$/MWh | Sum of value divided by sum of volume across the 12 original CER Québec export Total rows in 2025. C$595,817,584.507 ÷ 4,192,156.136 MWh = C$142.1267636934/MWh. No avoidable cost has been verified. The 2015–2025 annual weighted average was C$52.96/MWh and the highest annual price was in 2025. The benchmark describes gross receipts. Marginal export value, avoided supply cost, transmission availability and seasonal scarcity may differ. [1] |
| GPU count and annual availability | GPU, hours | Eight H100 GPUs and 8,760 hours. The count is a specification. Continuous availability is a scenario assumption. [3, 4] |
| Paid utilization | Share | Share of all available GPU-hours paid by assumed foreign buyers. The load model equates paid use to average busy share. There are no observed contract utilization or downtime data. |
| GPU rental rate | C$/GPU-hour | On-demand low/base/high C$5.673381 / C$6.668711 / C$8.7517945. Together AI, Lambda and CoreWeave catalog offers observed November 25, 2026. The preemptible C$2.8438 stress quote is a distinct service. USD quotes use C$1.4219/US$ that day. No realized discount, customer geography, or comparable Québec transaction was verified. [2, 4] |
| Server idle/busy and rated design draw | kW | 1.86 idle throughout. Low/base/high busy 4.68/7.92/8.43, measured on one HGX H100 node under different workloads. Rated DGX H100 design draw 10.2 for facility sizing. [3] |
| PUE | Facility energy / IT energy | Low/base/high 1.20/1.30/1.56. An efficient scenario, a local bound used as a point proxy, and the Uptime global mean. No project-specific measured PUE. [3, 4] |
| Installed hardware | C$/server | Low/base/high approximately C$434,282 / C$460,618 / C$530,445. Thinkmate’s US$300,107 January 10, 2025 quote uses same-date FX 1.4422. Low adds one posted-price switch per 32 nodes. Base adds two per 16 nodes and 5% installation. High takes the higher of the quote with two per eight nodes or Epoch’s bundled launch estimate, then adds 10% installation. Epoch’s historical quote conversion uses the October 2022 FX mean 1.36995. The network ratios and installation markups are inherited assumptions. [2, 4] |
| Hardware useful life | Years | 6 / 6 / 3. The six-year accounting reference comes from CoreWeave, with a three-year obsolescence stress. [4] |
| Facility capex | C$/design IT kW | 16,721.544 / 16,721.544 / 25,025.44. Toronto construction at US$11.76/W and broader US/Canada development at US$17.6m/MW, translated at 1.4219. The high case interprets reported capacity as IT capacity. Facility capex is sized at rated 10.2 kW per server and excludes GPU hardware. Construction proxies already include mechanical and electrical work. [4] |
| Facility useful life | Years | 30 / 20 / 12. Blended accounting-informed choices anchored to building, core system and leasehold disclosures. [4] |
| Non-power operating cost | C$/server-year | 3,529 / 4,411 / 7,058. Original model allocates US$7.3m in KPMG US annual labour, maintenance and security benchmarks by 10.2 kW ÷ 30,000 kW. It translates at 1.4219 and adds 0%, 25%, or 100% for recurring costs outside those components. The assumed linear allocation from benchmark facility size is a comparison convention. [4, 6] |
| Cost of capital | Annual rate | 0%, 5%, 8%, 10%, 15%. Eight percent is the illustrative base for both asset classes. Constant annual cash costs, zero salvage and no tax shield, inflation/escalation, financing structure, or construction schedule. [7] |
| Site and domestic inputs | Various | 500 identical servers, or 5.10 MW nameplate IT. Ownership shares, labour-income premiums, supply cost, administration, tax, supplier surplus and grants are explicitly scenario inputs. [7] |

## Capital, output and pricing equations

- Gross rental revenue = GPUs × available hours × paid utilization × rental price.
- Annual electricity in MWh = PUE × hours × [idle kW + utilization × (busy kW − idle kW)] ÷ 1,000.
- Each asset’s capital charge = upfront cost × CRF. For rate `r` and life `n`, CRF = `r / (1 − (1+r)^(-n))`. CRF at zero is `1/n`. Facility upfront cost = design IT kW × facility cost per design IT kW.
- AI advantage = revenue − hardware recovery − facility recovery − non-power opex − annual MWh × gross export benchmark. Advantage per MWh divides by annual MWh. The tariff belongs in the commercial calculation. The opportunity-cost calculation uses forgone exports instead.
- Private profit deducts the applicable tariff bill and the same three non-power costs. Minimum rental price = annual non-power costs plus tariff bill, divided by paid GPU-hours. The results include this threshold at 50% and 100% utilization. Break-even utilization is the positive-utilization root of private profit. Blank means profit stays negative through full use, including at 100%. Thresholds are annual model outcomes, not investment guarantees.

### Tariff scenarios

A applies C$68.20/MWh and B applies C$130/MWh. Both are equivalent average case inputs taken from Hydro-Québec’s customer-profile example, B-0004 Table 2, in constant 2026 dollars. A serves as a preferential proxy. B serves as a proposed average comparison. Actual economic-cost pricing would need site-specific incremental energy, capacity and interconnection costs.

C applies the proposed C$32.704/kW-month and C$0.08710/kWh in B-0076 §§5.54–5.56. The new facility is assumed to have authorized demand of 500 × 10.2 kW × scenario PUE, exceeding the proposed 5,000 kW eligibility threshold. Each month repeats the assumed coincident peak of 500 × busy kW × PUE for positive paid use. At zero it draws idle load. This monthly pattern makes the 75% winter ratchet nonbinding. At base PUE the modeled authorized demand is 6,630 kW and the recurring busy peak is 5,148 kW.

The §5.57 charge is C$92.28 for each kW by which the highest annual realized demand falls below 60% of the projected agreement demand. This application sets the projected maximum equal to authorized design load. It is inactive in the positive-use base and high cases and applies in the low case. This term is new relative to the earlier model. The steady-state scenario excludes ramp-up surcharge, power-factor, voltage and loss adjustments, transition terms, interruption credits and taxes. See the docket for regulatory status and applicability. [5]

Preferential-only windows begin at the break-even paid share for A and end before the comparator breaks even. Below that window neither tariff covers costs. Above it both do, at the same rental quote and costs. This defines a commercial counterfactual, with financing and grid access held fixed. The three observed rental quotes are offers to customers with different service terms.

## Domestic welfare and counterfactuals

The welfare ledger uses the 8% base configuration. The induced example is the midpoint between A and B break-even. The either-tariff comparison uses 50% paid use. The neither case uses 15% paid use and zero realized site flows because investment does not occur. This uses a feasible export alternative as the no-build counterfactual; changes in alternative uses or extra system costs change the decision.

| Term | Treatment |
| --- | --- |
| Québec retained profits | Québec ownership share × (company pre-tax profit after a modeled grant − Québec incremental tax). External, half-local and fully local are assumptions. Capital recovery includes a required capital return, so no separate opportunity-cost charge for the same capital enters this ledger. |
| Incremental permanent labour earnings | Québec earnings minus workers’ alternative earnings. Use 0%, 10%, or 25% of the KPMG operating-payroll proxy, or approximately C$0 / C$96,689 / C$241,723 per site-year. Québec Job Bank occupational wages provide local context but cannot determine payroll. Construction labour is temporary, unmeasured and excluded. Count its incremental labour surplus once, during construction, if documented. |
| Supplier surplus | Québec supplier revenue net of the resources and alternatives needed to deliver it. No evidence for the site, so the scenarios assign zero and report the gap that additional benefits would need to fill. |
| Québec government revenue | Incremental Québec tax receipts. The scenario field represents a share of positive pre-tax site profit with any grant. Zero in the published cases due to unavailable evidence. Deduct the same tax before computing residents’ retained earnings. |
| Public utility revenue and export loss | Add utility gross tariff receipts and subtract forgone gross export receipts for the same energy. Add only extra costs specific to the AI load or site connection if they were not already paid by the firm or counted in the export counterfactual. |
| Public subsidies and administrative costs | Explicit grants enter private profits and are a public expense. The tariff discount is reflected in private profit and utility receipts. The listed A–B bill gap measures the scale of the transfer and is excluded as a separate subtraction. The adverse scenario charges C$0.50m in annual supply/grid costs and C$0.10m in annual administration as illustrative stresses. |
| Imported hardware | Hardware spending is already reflected in capital recovery. No separate import deduction. |

Conditional welfare = retained profit + incremental labour income + supplier surplus + incremental Québec tax + utility receipts − forgone exports − extra supply/infrastructure − public administration − explicit grants. Minimum domestic benefits = max(0, forgone exports + extra public costs − utility receipts). Additional benefits needed = max(0, negative conditional welfare). Reported results are conditional annual changes versus exports. They do not estimate a C$ welfare effect under a province-wide programme, a local multiplier, or impacts on reliability and ratepayers. For a project that already builds, the relevant policy increment is welfare under A minus welfare under B, holding project behavior fixed.

## References

1. Canada Energy Regulator, *Electricity – Imports and Exports*. Original monthly and annual files are preserved in the repository. [Dataset](https://open.canada.ca/data/dataset/5c358f51-bc8c-4565-854d-9d2e35e6b178)
2. Lambda, Together AI, CoreWeave, Runpod and Bank of Canada. Catalog snapshots and the Valet FX series are linked from the upstream registry. [Registry](../sources/source_registry.csv)
3. NVIDIA DGX H100 data sheet, Latif et al. table 1, Cologix MTL10-H site specification and Uptime 2025 PUE survey. [Power observations](../data/raw/server_specifications/power-observations.csv) · [Latif et al.](https://arxiv.org/abs/2412.08602v2)
4. Existing eight-H100 model parameters, calculation summary and reports. Hardware sources include Thinkmate via Signal65, DirectDial, Epoch AI and CoreWeave. Facility sources include Turner & Townsend, Cushman & Wakefield, Equinix and CoreWeave. [Model parameters](../AI_model/data/processed/model_parameters.csv) · [Statistical report](../AI_model/reports/statistical_report.pdf) · [Upstream summary](../AI_model/results/summary.json)
5. Régie de l’énergie docket R-4333-2026. [B-0004, table 2](https://www.regie-energie.qc.ca/fr/participants/dossiers/R-4333-2026/doc/R-4333-2026-B-0004-Dem-Piece-2026_02_19.pdf) · [B-0076, §§5.52–5.57](https://www.regie-energie.qc.ca/fr/participants/dossiers/R-4333-2026/doc/R-4333-2026-B-0076-Dem-PieceRev-2026_08_04.pdf) · [Docket](https://www.regie-energie.qc.ca/fr/participants/dossiers/r-4333-2026)
6. KPMG, *Benchmarking CapEx and OpEx in the global data centre market*, 2025 charts for labour, repair and maintenance, and security at a 30 MW site. Québec wage context from ESDC and Statistics Canada, NOC 22220. [KPMG](https://assets.kpmg.com/content/dam/kpmgsites/sg/pdf/2026/05/benchmarking-capex-and-opex-in-the-global-data-centre-market.pdf.coredownload.inline.pdf) · [Job Bank](https://www.jobbank.gc.ca/wagereport/location/qc)
7. This analysis. [Settings](data/analysis_settings.json) · [Welfare assumptions](data/welfare_scenarios.csv) · [Full calculation tables](results/)
