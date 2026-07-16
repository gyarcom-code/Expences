#!/usr/bin/env python3
"""
Adds new rows from the live Google Sheet into history.csv without duplicating
entries that are already archived. Run manually once a year has finished
(e.g. in early January for the year that just ended).

Usage:
  python3 add-year-to-history.py
  python3 add-year-to-history.py --dry-run
  python3 add-year-to-history.py --sheet-id <id> --sheet-name "Ответы на форму"
"""
import argparse
import csv
import re
import urllib.parse
import urllib.request
import json
import os

DEFAULT_SHEET_ID = "1bfJk8VUQPg-GrMkj2qiXoxcs0RxJPmIBN9ujmXFkXMQ"
DEFAULT_SHEET_NAME = "Ответы на форму"
DEFAULT_API_KEY = "AIzaSyBSzdf9aK6jqDZJnX-6br6pBw2chqSwC-U"
DEFAULT_HISTORY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "history.csv")

TIMESTAMP_RE = re.compile(r"\d{2}\.\d{2}\.\d{4}")


def parse_sort_key(ts):
    m = re.match(r"(\d{2})\.(\d{2})\.(\d{4})\s+(\d{1,2}):(\d{2}):(\d{2})", ts)
    if m:
        d, mo, y, h, mi, s = map(int, m.groups())
        return (y, mo, d, h, mi, s)
    m = re.match(r"(\d{2})\.(\d{2})\.(\d{4})", ts)
    d, mo, y = map(int, m.groups())
    return (y, mo, d, 0, 0, 0)


def fetch_sheet_rows(sheet_id, sheet_name, api_key):
    rng = f"'{sheet_name}'!A:D"
    url = (
        f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/"
        f"{urllib.parse.quote(rng)}?key={api_key}"
    )
    with urllib.request.urlopen(url) as resp:
        data = json.load(resp)
    return data.get("values", [])


def rows_to_records(rows):
    records = []
    for row in rows[1:]:
        if not row or len(row) < 3:
            continue
        ts, category, amount = row[0], row[1], row[2]
        comment = row[3] if len(row) > 3 else ""
        if not ts or not category:
            continue
        if not TIMESTAMP_RE.match(str(ts)):
            continue
        records.append({
            "timestamp": str(ts),
            "category": category,
            "amount": amount,
            "comment": comment,
        })
    return records


def record_key(record):
    return (record["timestamp"].strip(), record["category"].strip(), str(record["amount"]).strip(), record["comment"].strip())


def load_history(history_path):
    if not os.path.exists(history_path):
        return []
    with open(history_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [
            {
                "timestamp": row["Timestamp"],
                "category": row["Category"],
                "amount": row["Amount"],
                "comment": row["Comment"],
            }
            for row in reader
        ]


def write_history(history_path, records):
    records = sorted(records, key=lambda r: parse_sort_key(r["timestamp"]))
    with open(history_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Timestamp", "Category", "Amount", "Comment"])
        for r in records:
            writer.writerow([r["timestamp"], r["category"], r["amount"], r["comment"]])
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sheet-id", default=DEFAULT_SHEET_ID, help="Google Sheet ID to read new rows from")
    parser.add_argument("--sheet-name", default=DEFAULT_SHEET_NAME, help="Sheet (tab) name inside the spreadsheet")
    parser.add_argument("--api-key", default=DEFAULT_API_KEY, help="Google Sheets API key")
    parser.add_argument("--history", default=DEFAULT_HISTORY_PATH, help="Path to history.csv")
    parser.add_argument("--dry-run", action="store_true", help="Report what would change without writing the file")
    args = parser.parse_args()

    existing = load_history(args.history)
    existing_keys = {record_key(r) for r in existing}

    source_rows = fetch_sheet_rows(args.sheet_id, args.sheet_name, args.api_key)
    source_records = rows_to_records(source_rows)

    new_records = []
    skipped = 0
    for r in source_records:
        if record_key(r) in existing_keys:
            skipped += 1
        else:
            new_records.append(r)
            existing_keys.add(record_key(r))  # guard against duplicates within the source itself

    print(f"Checked:  {len(source_records)}")
    print(f"New:      {len(new_records)}")
    print(f"Skipped:  {skipped} (already in {os.path.basename(args.history)})")

    if args.dry_run:
        print("\n--dry-run: history.csv was not modified.")
        if new_records:
            print("Rows that would be added:")
            for r in new_records:
                print(" ", r["timestamp"], r["category"], r["amount"], r["comment"])
        return

    if not new_records:
        print("\nNothing to add, history.csv unchanged.")
        return

    combined = existing + new_records
    write_history(args.history, combined)
    print(f"\nWrote {len(combined)} total rows to {args.history}")


if __name__ == "__main__":
    main()
