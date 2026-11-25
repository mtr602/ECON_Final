# Data dictionary

## Electricity

The CER files are unchanged original downloads. They are encoded in Windows-1252. In the monthly file, `Period` is the first day of the reporting month in MM/DD/YYYY format. Use `Activity = Exports` and `Source = Québec` for this project. `Destination` is the published U.S. market label or `Total` for the provincial series. Keep totals separate from destination rows to avoid double counting. The 2015–2025 slice has 670 published records, including 132 total rows. The CER confidentiality rules may affect what is shown in destination detail.

| Publisher field | Unit and definition |
| --- | --- |
| `Energy (MW.h)` | MWh of electricity reported |
| `Total Value (CAN$)` | Nominal CAD value reported |
| `Price (CAN$/MW.h)` | Average CAD/MWh as published. The original value is retained. |

The annual CER file uses `Year` as its period. Hydro-Québec's annual consolidated reports use different reporting scopes and may include other Canadian markets, corporate netting and accounting effects. Refer to the report's financial review for scope. Keep corporate external-sales figures distinct from CER international trade.

## GPU prices and server specifications

`h100-rental-prices.csv` records the GPU variant and, where established, the GPU count per offered instance and memory in GB. `quoted_amount` and `quoted_unit` preserve the source basis. `amount_per_gpu_hour` uses the same currency, with the quoted instance price divided by the stated GPU count for CoreWeave. `observation_date` is the day the catalog was read. Posted prices do not establish completed rental transactions, utilization, or capacity available for purchase.

`power-observations.csv` records server draw in kW and facility PUE as a dimensionless ratio of facility energy to IT equipment energy. The condition and qualifier fields preserve workload, statistic, point or bound. The NVIDIA nameplate and the empirical HGX system describe different evidentiary scopes. The Montréal-area PUE is the operator's published specification for MTL10-H.

## Costs and asset lives

The three cost CSVs retain the source units, dates or reference periods, and scope of the observations. `lower` and `upper` in the facility file are bounds, with identical values for point observations. One USD per watt equals 1,000 USD per kW. No exchange-rate conversion, geographic adjustment, cost allocation, or depreciation calculation was applied.

Vendor asking prices, quotes, accounting estimates, wage estimates, and interview-derived benchmarks are identified in `evidence_type`. Useful life is the stated accounting life where applicable. Annual operating benchmarks denominated per 30 MW facility are site totals in the stated scope and currency. The Québec wage series is hourly pay for an occupation.

## Exchange rates

The Bank of Canada Valet CSVs contain source metadata followed by an `OBSERVATIONS` section. `FXUSDCAD` is the daily average number of CAD per USD. `IEXE0101` is the historical noon observation in the same direction. Dates are YYYY-MM-DD. Files preserve the early-2017 overlap and have no filled weekends or holidays.

## Source and availability metadata

`source_registry.csv` links `source_id` to publisher, URL, relevant section, publication date or period, retrieval date, units, reuse status, and SHA-256 for originals. Blank dates mean the publisher did not give a verified date at the recorded precision. Live pages may change. A reference path points to factual observations or supporting context. The reference document remains at its source URL.

`data_availability.csv` lists every requested variable. **Available** indicates verified coverage for the listed scope. **Benchmark** indicates a reported comparison or accounting value. **Partial** indicates a component, proxy, or incomplete detail. **Missing** indicates the requested measure was not established in the reviewed sources. Blank values in the data files mean unavailable at that scope.
