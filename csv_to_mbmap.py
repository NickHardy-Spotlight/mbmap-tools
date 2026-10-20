#!/usr/bin/env python3
"""
Rebuild an mbmap JSON file from an edited registers CSV.

The top-level fields (vendor, model, byte_order, notes, ...) are copied from the
original JSON; only the "registers" list is replaced with the CSV contents.
Every CSV column becomes a key on each register, including any columns you added.
Empty cells are left out of that register.

Usage:
    python csv_to_mbmap.py registers.csv original.mbmap.json output.mbmap.json
"""
import argparse
import csv
import json
import sys

# Columns that must be integers.
INT_COLUMNS = {"address"}


def convert_value(column, text):
    """Turn a CSV cell (always a string) into the right JSON type."""
    text = text.strip()
    if column in INT_COLUMNS:
        return int(text, 0)  # base 0 also accepts hex like 0x07CF
    # Added columns: numbers and true/false become real JSON values,
    # everything else stays a string. Use --no-infer to keep all as strings.
    return text


def infer(text):
    low = text.lower()
    if low == "true":
        return True
    if low == "false":
        return False
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        return text


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv_file")
    ap.add_argument("template_json", help="original mbmap JSON (header fields are copied from it)")
    ap.add_argument("output_json")
    ap.add_argument("--no-infer", action="store_true",
                    help="keep values in added columns as strings instead of converting numbers/booleans")
    ap.add_argument("--bump-revision", action="store_true",
                    help="add 1 to the top-level 'revision' field")
    args = ap.parse_args()

    with open(args.template_json, encoding="utf-8") as f:
        doc = json.load(f)

    registers = []
    # utf-8-sig strips the BOM Excel adds; newline="" is what the csv module expects
    with open(args.csv_file, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            sys.exit("CSV has no header row.")
        columns = [c.strip() for c in reader.fieldnames if c and c.strip()]

        for line_no, row in enumerate(reader, start=2):  # line 1 is the header
            row = {(k or "").strip(): (v or "") for k, v in row.items()}
            if not any(v.strip() for v in row.values()):
                continue  # skip fully blank rows Excel often leaves at the end
            reg = {}
            for col in columns:
                text = row.get(col, "").strip()
                if text == "":
                    continue
                try:
                    if col in INT_COLUMNS:
                        reg[col] = convert_value(col, text)
                    else:
                        reg[col] = text if args.no_infer else infer(text)
                except ValueError:
                    sys.exit(f"Line {line_no}: bad value {text!r} in column '{col}'")
            for required in ("name", "area", "address", "type"):
                if required not in reg:
                    sys.exit(f"Line {line_no}: missing required value for '{required}'")
            registers.append(reg)

    doc["registers"] = registers
    if args.bump_revision and isinstance(doc.get("revision"), int):
        doc["revision"] += 1

    with open(args.output_json, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Wrote {len(registers)} registers to {args.output_json}")
    print("Columns used:", ", ".join(columns))


if __name__ == "__main__":
    main()
