#!/usr/bin/env python3
"""Restore source snapshots or verify tracked originals against their registry."""

import argparse
import csv
import hashlib
import io
import sys
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "sources" / "source_registry.csv"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def verify_file(row, data):
    path = Path(row["repository_path"])
    if path.suffix == ".pdf" and not data.startswith(b"%PDF-"):
        raise ValueError("response is not a PDF")
    if digest(data) != row["sha256"]:
        raise ValueError("SHA-256 differs from the archived snapshot")


def read_cer_months(data):
    rows = csv.DictReader(io.StringIO(data.decode("cp1252")))
    return [
        row for row in rows
        if row["Activity"] == "Exports"
        and row["Source"] == "Québec"
        and 2015 <= int(row["Period"][-4:]) <= 2025
    ]


def verify_coverage(root, selected_ids):
    if "cer_monthly" in selected_ids:
        path = root / "data/raw/electricity/electricity-exports-and-imports-monthly.csv"
        rows = read_cer_months(path.read_bytes())
        expected = {
            f"{month:02d}/01/{year}"
            for year in range(2015, 2026)
            for month in range(1, 13)
        }
        totals = [row for row in rows if row["Destination"] == "Total"]
        if len(totals) != len(expected) or {row["Period"] for row in totals} != expected:
            raise ValueError("CER Québec totals do not cover all 132 months")
    for source_id, series, first, last in (
        ("boc_noon", "IEXE0101", "2015-01-02", "2017-04-28"),
        ("boc_daily", "FXUSDCAD", "2017-01-03", "2026-11-25"),
    ):
        if source_id not in selected_ids:
            continue
        path = root / f"data/raw/exchange_rates/{series}.csv"
        rows = list(csv.reader(io.StringIO(path.read_text(encoding="utf-8-sig"))))
        header = rows.index(["date", series])
        dates = [date for date, value in rows[header + 1:] if value]
        if dates[0] != first or dates[-1] != last:
            raise ValueError(f"{series} coverage differs from the archived range")


def download(row, destination):
    request = Request(row["source_url"], headers={"User-Agent": "ECON342-source-download/1.0"})
    with urlopen(request, timeout=60) as response:
        data = response.read()
    verify_file(row, data)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".part")
    temporary.write_bytes(data)
    temporary.replace(destination)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="Destination root for original files")
    parser.add_argument("--source", action="append", help="Select a source ID. May be repeated.")
    parser.add_argument("--verify", action="store_true", help="Use existing files without making network calls")
    args = parser.parse_args()
    with REGISTRY.open(encoding="utf-8", newline="") as registry:
        rows = {row["source_id"]: row for row in csv.DictReader(registry) if row["storage"] == "original"}
    selected = list(dict.fromkeys(args.source or rows))
    unknown = set(selected) - rows.keys()
    if unknown:
        parser.error("No archived original for " + ", ".join(sorted(unknown)))

    failed = False
    for source_id in selected:
        row = rows[source_id]
        destination = args.root / row["repository_path"]
        try:
            if destination.exists() or args.verify:
                verify_file(row, destination.read_bytes())
            else:
                download(row, destination)
            print(f"Verified {source_id}: {destination}")
        except (OSError, ValueError) as error:
            print(f"{source_id}: {error}", file=sys.stderr)
            failed = True
    if failed:
        return 1
    try:
        verify_coverage(args.root, set(selected))
    except (OSError, ValueError) as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
