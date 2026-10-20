#!/usr/bin/env python3
"""
Extract the registers from an mbmap JSON file into a CSV that opens cleanly in Excel.

Columns are the union of every key used by any register, in order of first
appearance, so nothing is lost even if some registers have extra fields.
Non-text values (numbers, booleans, lists, objects) are written as JSON so that
csv_to_mbmap.py can read them back.

Usage:
    python mbmap_to_csv.py original.mbmap.json registers.csv
"""
import argparse
import csv
import json
import sys


def to_cell(value):
    if isinstance(value, str):
        return value
    # numbers -> 1999, 0.1; booleans -> true/false; lists/dicts -> JSON text
    return json.dumps(value, ensure_ascii=False)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input_json")
    ap.add_argument("output_csv")
    args = ap.parse_args()

    with open(args.input_json, encoding="utf-8") as f:
        doc = json.load(f)

    registers = doc.get("registers")
    if not isinstance(registers, list) or not registers:
        sys.exit("No 'registers' list found in the JSON file.")

    columns = []
    for reg in registers:
        for key in reg:
            if key not in columns:
                columns.append(key)

    # utf-8-sig adds the BOM so Excel reads non-ASCII characters correctly
    with open(args.output_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        for reg in registers:
            writer.writerow([to_cell(reg[c]) if c in reg else "" for c in columns])

    print(f"Wrote {len(registers)} registers to {args.output_csv}")
    print("Columns:", ", ".join(columns))


if __name__ == "__main__":
    main()
