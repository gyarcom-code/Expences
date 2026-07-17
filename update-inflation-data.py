#!/usr/bin/env python3
"""
Adds new months to inflation-data.json without duplicating or silently
overwriting existing months. Run manually when new official Ukrstat CPI
data becomes available (usually once a year is enough right after New
Year, but can be run more often).

New month data is NOT scraped automatically from Ukrstat/minfin by this
script — those sources are HTML pages / PDF press releases that need to
be read and cross-checked by a human (or by Claude Code interactively,
as was done when this file was first built) before being trusted. This
script only handles safely merging already-verified numbers into the file
and recomputing the cumulative index.

Usage:
  python3 update-inflation-data.py --data '{"2026-07": 100.5}' --dry-run
  python3 update-inflation-data.py --data '{"2026-07": 100.5, "2026-08": 99.8}'
"""
import argparse
import json
import os

DEFAULT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inflation-data.json")


def parse_key(key):
    year, month = key.split("-")
    return int(year), int(month)


def month_after(key):
    year, month = parse_key(key)
    if month == 12:
        return f"{year + 1}-01"
    return f"{year}-{month + 1:02d}"


def load_data(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data", required=True, help='JSON object: {"YYYY-MM": monthlyChangePercent, ...}')
    parser.add_argument("--path", default=DEFAULT_PATH, help="Path to inflation-data.json")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing the file")
    args = parser.parse_args()

    new_months = json.loads(args.data)
    existing = load_data(args.path)

    latest_key = sorted(existing.keys())[-1]
    latest_index = existing[latest_key]["cumulativeIndex"]

    discrepancies = []
    already_present = []
    to_add = {}

    for key, pct in new_months.items():
        if key in existing:
            if abs(existing[key]["monthlyChangePercent"] - pct) > 1e-9:
                discrepancies.append((key, existing[key]["monthlyChangePercent"], pct))
            else:
                already_present.append(key)
        else:
            to_add[key] = pct

    if discrepancies:
        print("РОЗБІЖНОСТІ — нічого не змінено для цих місяців, потрібне рішення вручну:")
        for key, old, new in discrepancies:
            print(f"  {key}: у файлі {old}, у нових даних {new}")
        print()

    if already_present:
        print(f"Вже є у файлі (значення збігається, нічого не робимо): {', '.join(sorted(already_present))}")

    if not to_add:
        print("Нових місяців для додавання немає.")
        return

    sorted_new_keys = sorted(to_add.keys())

    # New months must continue the chain with no gaps — otherwise the
    # cumulative index can't be computed correctly for the missing months.
    expected = month_after(latest_key)
    for key in sorted_new_keys:
        if key != expected:
            print(f"ПОМИЛКА: очікував місяць {expected}, отримав {key}. Місяці мають йти підряд без "
                  f"пропусків (бо накопичений індекс рахується ланцюжком). Додайте відсутні місяці теж.")
            return
        expected = month_after(key)

    print(f"Буде додано {len(sorted_new_keys)} нов(ий/і/их) місяць(ь/і/ів):")
    cumulative = latest_index
    computed = {}
    for key in sorted_new_keys:
        pct = to_add[key]
        cumulative = cumulative * (pct / 100)
        computed[key] = {"monthlyChangePercent": pct, "cumulativeIndex": round(cumulative, 4)}
        print(f"  {key}: {pct}%  ->  накопичений індекс {computed[key]['cumulativeIndex']}")

    if args.dry_run:
        print("\n--dry-run: файл не змінено.")
        return

    merged = {**existing, **computed}
    with open(args.path, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    all_keys = sorted(merged.keys())
    print(f"\nЗаписано. Додано місяців: {len(sorted_new_keys)} ({', '.join(sorted_new_keys)})")
    print(f"Тепер файл покриває діапазон: {all_keys[0]} — {all_keys[-1]} (всього {len(all_keys)} місяців)")


if __name__ == "__main__":
    main()
