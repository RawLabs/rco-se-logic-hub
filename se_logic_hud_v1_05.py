#!/usr/bin/env python3
"""
SE Logic HUD (V1.05) — Raw Cast Orbital
Single-command blueprint logic snapshot (no flow graphs; names-only).

Input:
  - bp.sbc

Output (auto-versioned by blueprint title + timestamp):
  - SE_Logic_HUD_<BlueprintTitle>_<YYYYMMDD-HHMM>.md
  - SE_Logic_HUD_<BlueprintTitle>_<YYYYMMDD-HHMM>.log.txt

Optional:
  --out <filename.md>      Override the auto output name (still writes a log)
  --debug-csv              Write a flat debug CSV (builders only)

What it extracts (V1.05):
  - Timer blocks: toolbar actions (Toolbar/Slots/Slot/Data)
  - Event controllers: toolbar actions (Toolbar/Slots/Slot/Data)
  - Resolves BlockEntityId -> CustomName where possible
  - Flags missing targets (unresolved BlockEntityId)
  - Splits missing into:
      * Likely Detached AQR Module (expected greyed-out) vs
      * Likely Broken Link (grey cube candidates)

Run:
  python3 se_logic_hud_v1_05.py bp.sbc
  python3 se_logic_hud_v1_05.py bp.sbc --debug-csv
  python3 se_logic_hud_v1_05.py bp.sbc --out SE_Logic_HUD.md
"""

from __future__ import annotations

import sys
import csv
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Tuple, Optional

# Space Engineers blueprint XML uses xsi:type
NS = {"xsi": "http://www.w3.org/2001/XMLSchema-instance"}
XSI_TYPE_ATTR = f"{{{NS['xsi']}}}type"


# -------------------------
# Small utilities (XML + strings)
# -------------------------

def local(tag: str) -> str:
    """Strip XML namespace from tag name."""
    return tag.split("}", 1)[1] if "}" in tag else tag


def clean(s) -> str:
    """Normalize whitespace."""
    if s is None:
        return ""
    return " ".join(str(s).strip().split())


def child_text(node, tagname: str, default: str = "") -> str:
    """Get direct child text by local tag name."""
    for c in node:
        if local(c.tag) == tagname:
            return clean(c.text or "")
    return default


def first_child(node, tagname: str):
    """Get first direct child by local tag name."""
    for c in node:
        if local(c.tag) == tagname:
            return c
    return None


def iter_children(node, tagname: str):
    """Iterate direct children by local tag name."""
    for c in node:
        if local(c.tag) == tagname:
            yield c


def sanitize_filename(s: str) -> str:
    """
    Keep filenames OS-friendly.
    Allow: A-Z a-z 0-9 dash underscore
    Convert spaces to underscore.
    """
    s = clean(s).replace(" ", "_")
    s = "".join(ch for ch in s if ch.isalnum() or ch in ("-", "_"))
    return s or "Blueprint"


# -------------------------
# Logging (console + file)
# -------------------------

class Logger:
    def __init__(self, log_path: Path):
        self.log_path = log_path
        self._lines: List[str] = []

    def write(self, msg: str) -> None:
        line = msg.rstrip("\n")
        print(line)
        self._lines.append(line)

    def flush_to_disk(self) -> None:
        self.log_path.write_text("\n".join(self._lines).strip() + "\n", encoding="utf-8")


# -------------------------
# Missing-target classification (your rule)
# -------------------------

def classify_missing_source(source_name: str, rows_for_source: List[dict]) -> str:
    """
    Return: 'LIKELY_DETACHED_AQR' | 'LIKELY_BROKEN_LINK'

    Your rule-of-thumb:
      If the controller name is AQR-* (or group targets include AQR-*),
      treat missing block targets as intended detached module control by default.
    """
    s = (source_name or "").upper()
    if "AQR-" in s:
        return "LIKELY_DETACHED_AQR"

    for r in rows_for_source:
        tgt = (r.get("target") or "").upper()
        if tgt.startswith("GROUP:") and "AQR-" in tgt:
            return "LIKELY_DETACHED_AQR"

    return "LIKELY_BROKEN_LINK"


# -------------------------
# Core extraction
# -------------------------

def build_block_index(root) -> Dict[str, dict]:
    """
    Build EntityId -> {name, type} for placed blocks.
    Names are pulled from CustomName first (player-visible).
    """
    idx: Dict[str, dict] = {}
    for b in root.iter():
        if local(b.tag) != "MyObjectBuilder_CubeBlock":
            continue
        ent = child_text(b, "EntityId", "")
        if not ent:
            continue
        name = (
            child_text(b, "CustomName", "")
            or child_text(b, "DisplayName", "")
            or child_text(b, "SubtypeName", "")
        )
        idx[ent] = {
            "name": name if name else "(unnamed block)",
            "type": b.attrib.get(XSI_TYPE_ATTR, ""),
        }
    return idx


def parse_toolbar_slots(block, block_index: Dict[str, dict], source_type: str, source_name: str) -> List[dict]:
    """
    Parse Toolbar/Slots/Slot/Data.

    Data xsi:type:
      - MyObjectBuilder_ToolbarItemTerminalBlock: target via BlockEntityId
      - MyObjectBuilder_ToolbarItemTerminalGroup: target via GroupName
    """
    rows: List[dict] = []

    toolbar = first_child(block, "Toolbar")
    if toolbar is None:
        return rows

    slots = first_child(toolbar, "Slots")
    if slots is None:
        return rows

    for slot in iter_children(slots, "Slot"):
        slot_index = child_text(slot, "Index", "")

        data = first_child(slot, "Data")
        if data is None:
            # Grey cube / blank slot
            rows.append({
                "source_type": source_type,
                "source_name": source_name,
                "slot_index": slot_index,
                "action": "<EMPTY SLOT>",
                "target": "n/a",
                "target_kind": "none",
                "flag": "EMPTY_SLOT",
            })
            continue

        data_type = data.attrib.get(XSI_TYPE_ATTR, "")
        action = child_text(data, "Action", "") or "n/a"

        block_ent = child_text(data, "BlockEntityId", "")
        group_name = child_text(data, "GroupName", "")

        target_kind = "unknown"
        target_name = "n/a"
        flag = ""

        if data_type == "MyObjectBuilder_ToolbarItemTerminalGroup" and group_name:
            target_kind = "group"
            target_name = f"GROUP:{group_name}"

        elif data_type == "MyObjectBuilder_ToolbarItemTerminalBlock" and block_ent:
            target_kind = "block"
            if block_ent in block_index:
                target_name = block_index[block_ent]["name"]
            else:
                target_name = "(missing target)"
                flag = "MISSING_TARGET"

        # Append parameter values (compact) if present
        params = first_child(data, "Parameters")
        if params is not None:
            vals: List[str] = []
            for p in params.iter():
                if local(p.tag) == "Value" and (p.text is not None):
                    vals.append(clean(p.text))
            if vals:
                action = f"{action} ({', '.join(vals)})"

        rows.append({
            "source_type": source_type,
            "source_name": source_name,
            "slot_index": slot_index,
            "action": action,
            "target": target_name,
            "target_kind": target_kind,
            "flag": flag,
        })

    return rows


def extract_controllers(root, block_index: Dict[str, dict]):
    """
    Return:
      timers: Dict[timer_name -> rows]
      events: Dict[event_controller_name -> rows]
    """
    timers: Dict[str, List[dict]] = defaultdict(list)
    events: Dict[str, List[dict]] = defaultdict(list)

    for b in root.iter():
        if local(b.tag) != "MyObjectBuilder_CubeBlock":
            continue

        xtype = b.attrib.get(XSI_TYPE_ATTR, "")
        name = child_text(b, "CustomName", "").strip()
        if not name:
            continue  # unnamed blocks are noise for HUD

        if xtype == "MyObjectBuilder_TimerBlock":
            timers[name].extend(parse_toolbar_slots(b, block_index, "Timer", name))

        elif xtype == "MyObjectBuilder_EventControllerBlock":
            events[name].extend(parse_toolbar_slots(b, block_index, "EventController", name))

    return timers, events


# -------------------------
# Blueprint title extraction (for output naming)
# -------------------------

def extract_blueprint_title(root, bp_path: Path) -> str:
    """
    Best-effort blueprint title discovery.
    - First try any <DisplayName> tag anywhere (common in SE exports)
    - Fallback to filename stem
    """
    for n in root.iter():
        if local(n.tag) == "DisplayName" and (n.text and clean(n.text)):
            return clean(n.text)
    return bp_path.stem


# -------------------------
# Render HUD
# -------------------------

def render_hud(timers: Dict[str, List[dict]], events: Dict[str, List[dict]], generated_at: str) -> str:
    # Collect attrition + missing lists (grouped by controller so we preserve slot order)
    empty_slots = 0
    missing_detached_by_source: Dict[Tuple[str, str], List[Tuple[str, str]]] = defaultdict(list)  # (type,name)->[(slot,action)]
    missing_broken_by_source: Dict[Tuple[str, str], List[Tuple[str, str]]] = defaultdict(list)

    def collect(source_type: str, source_name: str, rows: List[dict]):
        nonlocal empty_slots
        missing_class = classify_missing_source(source_name, rows)
        for r in rows:
            if r.get("flag") == "EMPTY_SLOT":
                empty_slots += 1
            if r.get("flag") == "MISSING_TARGET":
                key = (source_type, source_name)
                item = (r.get("slot_index", ""), r.get("action", ""))
                if missing_class == "LIKELY_DETACHED_AQR":
                    missing_detached_by_source[key].append(item)
                else:
                    missing_broken_by_source[key].append(item)

    for name, rows in timers.items():
        collect("Timer", name, rows)
    for name, rows in events.items():
        collect("EventController", name, rows)

    missing_detached_count = sum(len(v) for v in missing_detached_by_source.values())
    missing_broken_count = sum(len(v) for v in missing_broken_by_source.values())

    lines: List[str] = []
    lines.append("# SE Logic HUD (V1.05) — Raw Cast Orbital")
    lines.append("")
    lines.append(f"- Generated: `{generated_at}`")
    lines.append(f"- Timers: `{len(timers)}`")
    lines.append(f"- Event Controllers: `{len(events)}`")
    lines.append(f"- Attrition: `{empty_slots}` empty slots")
    lines.append(
        f"- Missing targets split: `{missing_detached_count}` likely detached (AQR-module), "
        f"`{missing_broken_count}` likely broken links"
    )
    lines.append("")

    # Repair list (top)
    lines.append("## Repair List — Missing Targets")
    lines.append("")

    lines.append("### Likely Detached AQR Module (greyed out expected)")
    if not missing_detached_by_source:
        lines.append("- none")
    else:
        for (st, sn) in sorted(missing_detached_by_source.keys(), key=lambda k: k[1].lower()):
            for slot_idx, act in missing_detached_by_source[(st, sn)]:
                lines.append(f"- {st}: {sn} :: Slot {slot_idx} :: {act} → (missing target)")
    lines.append("")

    lines.append("### Likely Broken Links (grey cube candidates)")
    if not missing_broken_by_source:
        lines.append("- none")
    else:
        for (st, sn) in sorted(missing_broken_by_source.keys(), key=lambda k: k[1].lower()):
            for slot_idx, act in missing_broken_by_source[(st, sn)]:
                lines.append(f"- {st}: {sn} :: Slot {slot_idx} :: {act} → (missing target)")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Timers
    lines.append("## Timers (A→Z)")
    lines.append("")
    for name in sorted(timers.keys(), key=lambda s: s.lower()):
        lines.append(f"### Timer: {name}")
        lines.append("")
        lines.append("Actions:")
        rows = timers[name]
        if not rows:
            lines.append("- n/a")
        else:
            missing_class = classify_missing_source(name, rows)
            for r in rows:
                suffix = ""
                if r.get("flag") == "MISSING_TARGET":
                    suffix = " ⚪ likely detached" if missing_class == "LIKELY_DETACHED_AQR" else " 🧱 likely broken"
                lines.append(f"- Slot {r.get('slot_index','')}: {r.get('action','')} → {r.get('target','')}{suffix}")
        lines.append("")

    # Events
    lines.append("## Event Controllers (A→Z)")
    lines.append("")
    for name in sorted(events.keys(), key=lambda s: s.lower()):
        lines.append(f"### Event Controller: {name}")
        lines.append("")
        lines.append("Actions:")
        rows = events[name]
        if not rows:
            lines.append("- n/a")
        else:
            missing_class = classify_missing_source(name, rows)
            for r in rows:
                suffix = ""
                if r.get("flag") == "MISSING_TARGET":
                    suffix = " ⚪ likely detached" if missing_class == "LIKELY_DETACHED_AQR" else " 🧱 likely broken"
                lines.append(f"- Slot {r.get('slot_index','')}: {r.get('action','')} → {r.get('target','')}{suffix}")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def write_debug_csv(timers: Dict[str, List[dict]], events: Dict[str, List[dict]], out_csv: Path) -> None:
    cols = ["source_type", "source_name", "slot_index", "action", "target", "target_kind", "flag"]
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()

        for name, rows in timers.items():
            for r in rows:
                w.writerow({
                    "source_type": "Timer",
                    "source_name": name,
                    **{k: r.get(k, "") for k in cols if k not in ("source_type", "source_name")},
                })

        for name, rows in events.items():
            for r in rows:
                w.writerow({
                    "source_type": "EventController",
                    "source_name": name,
                    **{k: r.get(k, "") for k in cols if k not in ("source_type", "source_name")},
                })


# -------------------------
# Main
# -------------------------

def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python3 se_logic_hud_v1_05.py bp.sbc [--out <file.md>] [--debug-csv]")
        return 2

    bp_path = Path(sys.argv[1]).expanduser().resolve()
    if not bp_path.exists():
        print(f"ERROR: file not found: {bp_path}")
        return 2

    # Simple args (KISS; avoids argparse complexity for workshop users)
    out_override: Optional[str] = None
    debug_csv = False

    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] == "--out" and i + 1 < len(args):
            out_override = args[i + 1]
            i += 2
        elif args[i] == "--debug-csv":
            debug_csv = True
            i += 1
        else:
            print(f"Unknown arg: {args[i]}")
            print("Usage: python3 se_logic_hud_v1_05.py bp.sbc [--out <file.md>] [--debug-csv]")
            return 2

    # Parse XML
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    timestamp = datetime.now().strftime("%Y%m%d-%H%M")

    # We create logger after we know blueprint title (but we need root first), so:
    # Parse first, then name files, then log.
    try:
        tree = ET.parse(bp_path)
        root = tree.getroot()
    except Exception as e:
        print(f"FAIL: XML parse error: {e}")
        return 1

    bp_title = sanitize_filename(extract_blueprint_title(root, bp_path))
    default_out = f"SE_Logic_HUD_{bp_title}_{timestamp}.md"
    out_name = out_override if out_override else default_out

    log_name = f"SE_Logic_HUD_{bp_title}_{timestamp}.log.txt"
    log_path = bp_path.parent / log_name
    log = Logger(log_path)

    log.write(f"RCO SE Logic HUD v1.05")
    log.write(f"TIME: {generated_at}")
    log.write(f"INPUT: {bp_path}")
    log.write(f"OUT:   {bp_path.parent / out_name}")
    log.write("")

    # Index + extract
    log.write("LOAD: bp.sbc")
    log.write("PARSE: XML OK")

    block_index = build_block_index(root)
    log.write(f"INDEX: blocks indexed = {len(block_index)}")

    timers, events = extract_controllers(root, block_index)
    log.write(f"EXTRACT: timers = {len(timers)}, event controllers = {len(events)}")

    # Compute missing summary for log
    missing_total = 0
    missing_detached = 0
    missing_broken = 0
    empty_slots = 0

    for name, rows in timers.items():
        cls = classify_missing_source(name, rows)
        for r in rows:
            if r.get("flag") == "EMPTY_SLOT":
                empty_slots += 1
            if r.get("flag") == "MISSING_TARGET":
                missing_total += 1
                if cls == "LIKELY_DETACHED_AQR":
                    missing_detached += 1
                else:
                    missing_broken += 1

    for name, rows in events.items():
        cls = classify_missing_source(name, rows)
        for r in rows:
            if r.get("flag") == "EMPTY_SLOT":
                empty_slots += 1
            if r.get("flag") == "MISSING_TARGET":
                missing_total += 1
                if cls == "LIKELY_DETACHED_AQR":
                    missing_detached += 1
                else:
                    missing_broken += 1

    log.write(f"RESOLVE: missing targets = {missing_total} (detached={missing_detached}, broken={missing_broken}), empty slots = {empty_slots}")

    # Render + write HUD
    hud_text = render_hud(timers, events, generated_at)
    out_path = bp_path.parent / out_name
    out_path.write_text(hud_text, encoding="utf-8")
    log.write(f"WRITE: {out_path.name}")

    # Optional debug CSV
    if debug_csv:
        dbg_path = bp_path.parent / f"SE_Logic_HUD_{bp_title}_{timestamp}.debug.csv"
        write_debug_csv(timers, events, dbg_path)
        log.write(f"WRITE: {dbg_path.name} (debug)")

    log.write("DONE: SUCCESS")
    log.flush_to_disk()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
