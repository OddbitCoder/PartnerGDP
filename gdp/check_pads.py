#!/usr/bin/env python3
"""
kicad_pcb_pad_via_stats.py

Parse a KiCad .kicad_pcb file and report pad and via statistics.

Examples of produced keys:
- Pads:  'circle size:1.4 drill:0.8'
- Pads:  'oval size:1.6x0.9 drill:oval 1.0x0.6'
- Vias:  'via size:0.8 drill:0.4'

Usage:
  python kicad_pcb_pad_via_stats.py path/to/board.kicad_pcb
  python kicad_pcb_pad_via_stats.py path/to/board.kicad_pcb --csv stats.csv
"""

from __future__ import annotations
import argparse
import collections
import re
from typing import Tuple, Dict, List, Optional

PadKey = str
ViaKey = str

# ---------- Helpers ----------

def _norm_num(s: str) -> str:
    """Normalize a KiCad numeric string to a compact form (strip trailing zeros)."""
    try:
        f = float(s)
        # Format with up to 6 decimals, strip trailing zeros and possible trailing dot
        t = f"{f:.6f}".rstrip("0").rstrip(".")
        return t if t else "0"
    except ValueError:
        return s

def _join_size(a: Optional[str], b: Optional[str]) -> str:
    if a and b and a != b:
        return f"{_norm_num(a)}x{_norm_num(b)}"
    elif a and b:
        # equal -> print single
        return _norm_num(a)
    elif a:
        return _norm_num(a)
    return ""

def _extract_block(text: str, start_idx: int) -> Tuple[str, int]:
    """
    Given text and an index pointing at '(' of a (pad ...) or (via ...),
    return the full S-expression block and the index just after it.
    """
    depth = 0
    i = start_idx
    while i < len(text):
        c = text[i]
        if c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0:
                # include this ')'
                return text[start_idx:i+1], i+1
        i += 1
    # If we get here, parentheses were unbalanced; return to end
    return text[start_idx:], len(text)

def _first_tokens(expr: str, n: int = 5) -> List[str]:
    """
    Tokenize the first line-ish of an S-expression to get early fields.
    For pads, we want tokens like: (pad "1" thru_hole circle ...
    """
    # Replace newlines to avoid accidental line truncation
    head = expr[:200].replace("\n", " ")
    # crude tokenization respecting simple quotes
    tokens = re.findall(r'"[^"]*"|\S+', head)
    return tokens[:n]

# ---------- Extractors ----------

def parse_pad(expr: str) -> Optional[PadKey]:
    """
    Build a normalized key for a (pad ...) block.
    Pad header format (v6/v7/v8):
      (pad "<number>" <type> <shape> ... (size a b) ... (drill ...) ...)
    We’ll key by: "<shape> size:<AxB> drill:<...>" (drill omitted if absent).
    """
    tokens = _first_tokens(expr, n=6)
    if not tokens or tokens[0] != "(pad":
        return None

    # Expect something like: (pad "1" thru_hole circle
    # shape is usually tokens[4], but pad names can contain spaces in quotes.
    # Tokens: 0:(pad 1:"…"? 2:type 3:shape ...
    # We’ll scan the first few tokens after (pad and quoted name to find type+shape.
    # Find first non-quoted after (pad and name
    i = 1
    # name (quoted or not)
    if i < len(tokens) and tokens[i].startswith('"'):
        i += 1
    # type
    pad_type = tokens[i] if i < len(tokens) else ""
    i += 1
    # shape
    shape = tokens[i] if i < len(tokens) else ""
    shape = shape.strip(')"(')

    # size (size a b)
    m_size = re.search(r"\(size\s+([^\s\)]+)(?:\s+([^\s\)]+))?\)", expr)
    size_a = size_b = None
    if m_size:
        size_a, size_b = m_size.group(1), m_size.group(2) or m_size.group(1)

    # drill forms:
    # (drill 0.8)
    # (drill oval 0.8 1.0)
    # (drill (offset x y) 0.8)  -> rare; we’ll still try to capture numbers
    drill_str = ""
    m_drill_simple = re.search(r"\(drill\s+([0-9eE\.\+\-]+)\s*\)", expr)
    m_drill_oval = re.search(r"\(drill\s+oval\s+([^\s\)]+)\s+([^\s\)]+)\s*\)", expr)
    if m_drill_oval:
        d1, d2 = m_drill_oval.group(1), m_drill_oval.group(2)
        drill_str = f"oval {_norm_num(d1)}x{_norm_num(d2)}"
    elif m_drill_simple:
        d = m_drill_simple.group(1)
        drill_str = _norm_num(d)
    else:
        # try any two numbers in (drill ...) if odd form
        m_drill_any = re.search(r"\(drill[^\)]*?([0-9eE\.\+\-]+)(?:\s+([0-9eE\.\+\-]+))?", expr)
        if m_drill_any:
            if m_drill_any.group(2):
                drill_str = f"{_norm_num(m_drill_any.group(1))}x{_norm_num(m_drill_any.group(2))}"
            else:
                drill_str = _norm_num(m_drill_any.group(1))

    size_key = _join_size(size_a, size_b) if (size_a or size_b) else ""
    parts = [shape.lower() if shape else "unknown",]
    if size_key:
        parts.append(f"size:{size_key}")
    if drill_str:
        parts.append(f"drill:{drill_str}")
    return " ".join(parts) if parts else None


def parse_via(expr: str) -> Optional[ViaKey]:
    """
    Build a normalized key for a (via ...) block.
    Typical:
      (via (at x y) (size 0.8) (drill 0.4) (layers "F.Cu" "B.Cu"))
    Keyed as: 'via size:<s> drill:<d>'
    """
    if not expr.lstrip().startswith("(via"):
        return None

    # size
    m_size = re.search(r"\(size\s+([^\s\)]+)\s*\)", expr)
    size_str = _norm_num(m_size.group(1)) if m_size else ""

    # drill
    drill_str = ""
    m_drill_simple = re.search(r"\(drill\s+([0-9eE\.\+\-]+)\s*\)", expr)
    m_drill_oval = re.search(r"\(drill\s+oval\s+([^\s\)]+)\s+([^\s\)]+)\s*\)", expr)
    if m_drill_oval:
        d1, d2 = m_drill_oval.group(1), m_drill_oval.group(2)
        drill_str = f"oval {_norm_num(d1)}x{_norm_num(d2)}"
    elif m_drill_simple:
        d = m_drill_simple.group(1)
        drill_str = _norm_num(d)
    else:
        m_drill_any = re.search(r"\(drill[^\)]*?([0-9eE\.\+\-]+)(?:\s+([0-9eE\.\+\-]+))?", expr)
        if m_drill_any:
            if m_drill_any.group(2):
                drill_str = f"{_norm_num(m_drill_any.group(1))}x{_norm_num(m_drill_any.group(2))}"
            else:
                drill_str = _norm_num(m_drill_any.group(1))

    parts = ["via"]
    if size_str:
        parts.append(f"size:{size_str}")
    if drill_str:
        parts.append(f"drill:{drill_str}")
    return " ".join(parts)


# ---------- Scanner ----------

def scan_file(text: str) -> Tuple[Dict[PadKey, int], Dict[ViaKey, int]]:
    """
    Scan the entire file text, pull out (pad ...) and (via ...) blocks, and count keys.
    """
    pad_counts = collections.Counter()
    via_counts = collections.Counter()

    i = 0
    while i < len(text):
        # Quick find next '(' to avoid scanning every char
        j = text.find('(', i)
        if j == -1:
            break

        # Look ahead to decide type
        # We accept whitespace between '(' and token
        k = j + 1
        while k < len(text) and text[k].isspace():
            k += 1

        # Fetch next few letters
        token = text[k:k+3].lower()  # 'pad' or 'via'
        if token.startswith("pad") or token.startswith("via"):
            expr, end_idx = _extract_block(text, j)

            if token.startswith("pad"):
                key = parse_pad(expr)
                if key:
                    pad_counts[key] += 1
            elif token.startswith("via"):
                key = parse_via(expr)
                if key:
                    via_counts[key] += 1

            i = end_idx
        else:
            i = j + 1

    return dict(pad_counts), dict(via_counts)


# ---------- Output ----------

def print_report(pads: Dict[PadKey, int], vias: Dict[ViaKey, int]) -> None:
    def sorted_items(d):
        # Sort by count desc, then key asc
        return sorted(d.items(), key=lambda kv: (-kv[1], kv[0]))

    if pads:
        print("PAD STATISTICS")
        print("==============")
        for key, count in sorted_items(pads):
            print(f"{count:6}  {key}")
        print()

    if vias:
        print("VIA STATISTICS")
        print("==============")
        for key, count in sorted_items(vias):
            print(f"{count:6}  {key}")

def write_csv(path: str, pads: Dict[PadKey, int], vias: Dict[ViaKey, int]) -> None:
    import csv
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["type", "key", "count"])
        for k, c in sorted(pads.items(), key=lambda kv: (-kv[1], kv[0])):
            w.writerow(["pad", k, c])
        for k, c in sorted(vias.items(), key=lambda kv: (-kv[1], kv[0])):
            w.writerow(["via", k, c])

# ---------- Main ----------

def main():
    ap = argparse.ArgumentParser(description="Extract pad and via statistics from a KiCad .kicad_pcb file.")
    ap.add_argument("pcb", help="Path to .kicad_pcb file")
    ap.add_argument("--csv", help="Optional path to write CSV summary")
    args = ap.parse_args()

    with open(args.pcb, "r", encoding="utf-8") as fh:
        text = fh.read()

    pads, vias = scan_file(text)
    print_report(pads, vias)

    if args.csv:
        write_csv(args.csv, pads, vias)
        print(f"\nCSV written to: {args.csv}")

if __name__ == "__main__":
    main()
