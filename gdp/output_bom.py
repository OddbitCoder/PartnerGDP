#!/usr/bin/env python3
import re
import sys
from pathlib import Path
from collections import defaultdict, Counter

def natural_key(s: str):
    """Return a comparison key that avoids int<->str comparisons."""
    parts = re.findall(r'\d+|\D+', s)
    out = []
    for p in parts:
        if p.isdigit():
            out.append((0, int(p)))
        else:
            out.append((1, p.lower()))
    return tuple(out)

def extract_footprints(text):
    """Yield each complete '(footprint ... )' block from file text."""
    i, n = 0, len(text)
    while True:
        start = text.find('(footprint', i)
        if start == -1:
            break
        depth = 0
        j = start
        in_str = False
        while j < n:
            c = text[j]
            if c == '"' and text[j-1] != '\\':
                in_str = not in_str
            elif not in_str:
                if c == '(':
                    depth += 1
                elif c == ')':
                    depth -= 1
                    if depth == 0:
                        yield text[start:j+1]
                        i = j + 1
                        break
            j += 1
        else:
            yield text[start:]
            break

def parse_ref_val(block):
    """Return (ref, val) from a footprint block, or (None, None)."""
    # KiCad 6/7/8+: properties
    mref = re.search(r'\(property\s+"Reference"\s+"([^"]*)"', block)
    mval = re.search(r'\(property\s+"Value"\s+"([^"]*)"', block)
    if mref and mval:
        return mref.group(1).strip(), mval.group(1).strip()
    # Older: fp_text
    mref = re.search(r'\(fp_text\s+reference\s+([^\s\)]+)', block)
    mval = re.search(r'\(fp_text\s+value\s+([^\s\)]+)', block)
    if mref and mval:
        return mref.group(1).strip('"'), mval.group(1).strip('"')
    return None, None

def count_pads(block):
    """
    Count unique, non-empty pad names in a footprint block.
    Matches quoted and unquoted pad names, e.g. (pad "1" ...), (pad 1 ...), (pad A1 ...).
    """
    pad_names = set()
    for name in re.findall(r'\(pad\s+"?([^"\s\)]+)"?\s', block):
        name = name.strip()
        if name:
            pad_names.add(name)
    return len(pad_names)

def main():
    if len(sys.argv) != 2:
        print(f"Usage: {Path(sys.argv[0]).name} path/to/board.kicad_pcb", file=sys.stderr)
        sys.exit(1)

    pcb_path = Path(sys.argv[1])
    text = pcb_path.read_text(encoding='utf-8', errors='ignore')

    by_value = defaultdict(list)  # value -> [refs]
    ic_pins = {}                  # ref -> pin count for IC* only

    for fp in extract_footprints(text):
        ref, val = parse_ref_val(fp)
        if ref and val:
            by_value[val].append(ref)
            if ref.upper().startswith("IC"):
                ic_pins[ref] = count_pads(fp)

    # Sort references within each value group naturally
    for v in by_value:
        by_value[v].sort(key=natural_key)

    # Sort groups by first reference naturally
    for value in sorted(by_value.keys(), key=lambda v: natural_key(by_value[v][0])):
        refs = by_value[value]
        ref_list = ",".join(refs)
        count = len(refs)

        # If group contains ICs, determine the (common) pin count
        ic_refs = [r for r in refs if r in ic_pins]
        pins_suffix = ""
        if ic_refs:
            counts = [ic_pins[r] for r in ic_refs]
            # Choose the most common count; warn if inconsistent
            most_common, freq = Counter(counts).most_common(1)[0]
            if len(set(counts)) > 1:
                print(
                    f"Warning: Inconsistent pin counts for value '{value}' "
                    f"among {ic_refs}: {counts}. Using {most_common}.",
                    file=sys.stderr
                )
            pins_suffix = f"\tpins={most_common}"

        # Output: <Refs>\t<Count>\t<Value>[\tpins=N]
        print(f"{ref_list}\t{count}\t{value}{pins_suffix}")

if __name__ == "__main__":
    main()
