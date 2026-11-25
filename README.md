# ECON 342 research data

Source collection for comparing Québec electricity exports and AI computing exports. The repository contains public source snapshots and evidence tables collected on November 25, 2026.

| Location | Contents |
| --- | --- |
| [Electricity](data/raw/electricity/) | CER monthly and annual trade CSVs, publisher dictionary, and Hydro-Québec annual reports for 2015–2025 |
| [GPU pricing](data/raw/gpu_pricing/) | H100 catalog observations for Lambda, Runpod, Together AI and CoreWeave |
| [Server specifications](data/raw/server_specifications/) | H100 specifications, measured idle and training power, empirical paper, and PUE references |
| [Hardware costs](data/raw/hardware_costs/) | Thinkmate configuration quote, Epoch AI CSV, switch pricing and CoreWeave accounting life |
| [Facility costs](data/raw/facility_costs/) | Construction, infrastructure and accounting-life benchmarks |
| [Operating costs](data/raw/operating_costs/) | Québec occupational wages and U.S. staffing, maintenance and security benchmarks |
| [Exchange rates](data/raw/exchange_rates/) | Bank of Canada Valet daily averages and legacy noon rates |
| [Sources](sources/) | [Source registry](sources/source_registry.csv), [availability by variable](sources/data_availability.csv), and [data dictionary](sources/data_dictionary.md) |

The monthly CER source contains all 132 Québec export periods for 2015–2025. Public observations establish a dated H100 server quote and selected component and facility benchmarks. The availability table identifies gaps including avoidable export costs, H100 installation labour, standalone Québec cooling and electrical costs, and a full Québec facility operating budget.

## Verify and restore source files

Python 3 and internet access are sufficient for downloading missing original files. The verification command works offline.

```sh
python3 scripts/download_data.py --verify
python3 scripts/download_data.py --root /tmp/econ342-source-snapshots
python3 scripts/download_data.py --source hq_2025
```

The script uses the source registry and checks SHA-256. Publishers can revise files at the same URL. A checksum mismatch is reported and the archive is preserved. Reference pages and reports are linked in the registry. For commercial references, the observation CSVs preserve dated factual values while the publisher retains the source material.

Hydro-Québec annual reports are reproduced with attribution under the notices in the PDFs. CER files are used under the Open Government Licence – Canada. Bank of Canada Valet files are unchanged and attributed to the Bank of Canada. Additional licence and attribution details appear in the registry.
