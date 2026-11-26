# Final economic analysis

This folder contains the four-page analysis for the ECON 342 policy memo. It uses the 2025 historical electricity benchmark and dated AI price and cost scenarios.

- [Four-page PDF](reports/final_economic_analysis.pdf)
- [Technical appendix](technical_appendix.md)
- [Verification report](verification_report.md)
- [Inputs](data/) and [calculation tables](results/)
- [Break-even exhibit](exhibits/commercial_break_even.pdf)

## Reproduce

From this directory, use Python 3.10+ with pandas, Matplotlib and ReportLab. The verification command also uses the Poppler tools `pdfinfo` and `pdftotext`.

```sh
python -m pip install -r scripts/requirements.txt
python -B scripts/analyze.py
python -B scripts/build_report.py
python -B scripts/verify.py
```

The analysis reads legacy parameters and model code from `../AI_model` and original inputs from `../data/raw`. Generated outputs remain in this directory. `commercial_scenarios.csv` contains the 25%, 50%, 75% and 100% paid-use cases across twelve cost/rental combinations and five financing rates. `break_even.csv` provides tariff-specific use and price thresholds. `viability_windows.csv` shows the ranges where differences in tariffs change eligibility for commercial investment. `domestic_welfare.csv` gives the site-level ledger and benefit thresholds.
