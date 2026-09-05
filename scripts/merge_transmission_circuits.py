#!/usr/bin/env python3
"""Merge OSM transmission segments jadi full electrical circuits.

OSM transmission ter-fragmentasi jadi banyak `way` (segment per span/section)
— satu circuit Cirebon→Indramayu 45 km bisa jadi 15 way OSM terpisah.
Reconciler phase 2 hanya bisa resolve segment yang ujungnya persis di
substation (17% dari total). Sisanya "partial" atau "unresolved".

Phase 3 algorithm — graph traversal:
  1. Build node graph: setiap koordinat endpoint = node (rounded ke ~1m).
  2. Build adjacency: node → list of (feature_idx, other_endpoint_node).
  3. Mark substation terminals: node dalam radius X km dari substation
     baseline dianggap terminal.
  4. Untuk tiap feature dengan `endpoint_confidence != both`:
     BFS/walk sepanjang chain segments (same voltage) sampai reach terminal.
     Berhenti kalau ketemu:
       - Terminal (substation) → circuit complete
       - Node dengan degree > 2 (T-junction) → stop, tandai partial
       - Voltage transition → stop
       - Sudah visited → cycle, stop

Setiap segment yang jadi bagian dari circuit → tag properties:
    circuit_id           unique ID
    circuit_from_id      substation ID di ujung awal
    circuit_to_id        substation ID di ujung akhir
    circuit_from_name    substation name
    circuit_to_name      substation name
    circuit_length_km    total length semua segments
    circuit_segment_count jumlah segments yang di-merge

Output: overwrite baseline `transmission_{region}.geojson` in-place
(properties additive). Idempotent.

Usage:
    # Prereq: sudah run enrich_transmission_endpoints
    python3 scripts/merge_transmission_circuits.py --region jamali
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from _shared.name_stem import haversine_km  # noqa: E402


# ------------------------------------------------------------
# Node key: round coord to ~1m precision (5 decimals)
# ------------------------------------------------------------
def node_key(lon: float, lat: float) -> tuple[float, float]:
    return (round(lon, 5), round(lat, 5))


def voltage_int(voltage_str: str) -> Optional[int]:
    """Extract first int voltage untuk chain-walk comparison."""
    import re
    if not voltage_str:
        return None
    m = re.search(r"\d+", str(voltage_str))
    return int(m.group()) if m else None


# ------------------------------------------------------------
# Load substation coords for terminal detection
# ------------------------------------------------------------
def load_substation_pins(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    with path.open(encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            try:
                lat = float(r.get("lat") or "")
                lon = float(r.get("lon") or "")
            except ValueError:
                continue
            name = (r.get("name") or "").strip()
            if not name:
                continue
            out.append({
                "id": (r.get("id") or "").strip(),
                "name": name,
                "lat": lat, "lon": lon,
            })
    return out


def mark_terminals(nodes: set, subs: list[dict],
                    max_km: float = 3.0
                    ) -> dict[tuple, dict]:
    """Untuk setiap node, cari substation terdekat dalam radius.

    Return {node_key: {id, name, distance_km}} untuk terminal nodes only.
    """
    terminals: dict[tuple, dict] = {}
    for n in nodes:
        lon, lat = n
        best = None
        best_d = max_km + 1
        for s in subs:
            d = haversine_km((lon, lat), (s["lon"], s["lat"]))
            if d < best_d:
                best_d = d
                best = s
        if best is not None and best_d <= max_km:
            terminals[n] = {
                "id": best["id"],
                "name": best["name"],
                "distance_km": best_d,
            }
    return terminals


# ------------------------------------------------------------
# Graph traversal
# ------------------------------------------------------------
def walk_chain(start_feat_idx: int, start_node: tuple,
                start_voltage: Optional[int],
                adjacency: dict[tuple, list[tuple[int, tuple]]],
                feat_voltage: list[Optional[int]],
                terminals: dict[tuple, dict],
                feat_length: list[float],
                ) -> Optional[dict]:
    """Walk chain of segments dari start_node melalui feature start_feat_idx,
    ke terminal di ujung lain.

    Return dict {segments, other_terminal, total_length} kalau chain
    valid, atau None.

    Rules:
      - Berhenti kalau ketemu terminal (substation)
      - Berhenti kalau node current punya degree != 2 (T-junction / dead end)
      - Voltage harus konsisten sepanjang chain (skip kalau beda)
    """
    visited_feats: set[int] = {start_feat_idx}
    chain_feats: list[int] = [start_feat_idx]
    total_len: float = feat_length[start_feat_idx]

    # Traverse dari start_node ke ujung lain dari start_feat_idx
    # First find "other end" of start_feat via adjacency lookup
    current_node = None
    for feat_idx, other in adjacency.get(start_node, []):
        if feat_idx == start_feat_idx:
            current_node = other
            break
    if current_node is None:
        return None

    # Walk until terminal / dead-end / T-junction
    max_steps = 100
    for _ in range(max_steps):
        # Cek: apakah current_node adalah terminal?
        if current_node in terminals:
            return {
                "segments": chain_feats,
                "other_terminal_node": current_node,
                "total_length_km": total_len,
            }
        # Non-terminal: cek degree
        neighbors = adjacency.get(current_node, [])
        # Filter: same voltage + belum visited
        unvisited = [
            (fi, on) for (fi, on) in neighbors
            if fi not in visited_feats
            and (feat_voltage[fi] is None or start_voltage is None
                 or feat_voltage[fi] == start_voltage)
        ]
        if len(unvisited) != 1:
            # Dead end, T-junction, atau voltage mismatch
            return None
        next_feat_idx, next_node = unvisited[0]
        visited_feats.add(next_feat_idx)
        chain_feats.append(next_feat_idx)
        total_len += feat_length[next_feat_idx]
        current_node = next_node
    return None


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------
def merge(region: str, project_root: Path, max_km: float) -> int:
    processed = project_root / "data/processed"
    gj_path = processed / f"transmission_{region}.geojson"
    sub_path = processed / f"substation_master_{region}.csv"

    if not gj_path.exists():
        print(f"[merge_circ] missing: {gj_path}", file=sys.stderr)
        return 2
    if not sub_path.exists():
        print(f"[merge_circ] missing: {sub_path}", file=sys.stderr)
        return 2

    subs = load_substation_pins(sub_path)
    gj = json.loads(gj_path.read_text(encoding="utf-8"))
    features = gj.get("features", [])
    print(f"[merge_circ] region={region}, {len(subs)} substations, "
          f"{len(features)} baseline LineStrings")

    # Build graph
    adjacency: dict[tuple, list[tuple[int, tuple]]] = defaultdict(list)
    feat_endpoints: list[tuple[tuple, tuple]] = []  # (start_node, end_node)
    feat_voltage: list[Optional[int]] = []
    feat_length: list[float] = []
    feat_endpoint_ids: list[tuple[str, str]] = []  # (from_id, to_id) dari phase 2
    all_nodes: set = set()

    for idx, f in enumerate(features):
        coords = ((f.get("geometry") or {}).get("coordinates") or [])
        if len(coords) < 2:
            feat_endpoints.append((None, None))
            feat_voltage.append(None)
            feat_length.append(0.0)
            feat_endpoint_ids.append(("", ""))
            continue
        n1 = node_key(coords[0][0], coords[0][1])
        n2 = node_key(coords[-1][0], coords[-1][1])
        feat_endpoints.append((n1, n2))
        all_nodes.add(n1)
        all_nodes.add(n2)
        adjacency[n1].append((idx, n2))
        adjacency[n2].append((idx, n1))
        props = f.get("properties", {})
        v = voltage_int(props.get("voltage_class")
                        or props.get("voltage_kv_max"))
        feat_voltage.append(v)
        try:
            feat_length.append(float(props.get("length_km") or 0))
        except (TypeError, ValueError):
            feat_length.append(0.0)
        # Pakai from_id/to_id dari phase 2 (per-endpoint, sudah dedupe same-sub)
        feat_endpoint_ids.append((
            (props.get("from_id") or "").strip(),
            (props.get("to_id") or "").strip(),
        ))

    print(f"  graph: {len(all_nodes)} nodes, {sum(len(v) for v in adjacency.values())//2} edges")

    # Terminal detection per NODE menggunakan phase 2's per-feature IDs.
    # Node dianggap terminal untuk substation X kalau ada feature dengan
    # endpoint di node itu yang phase 2-nya tag dengan from_id/to_id = X.
    terminal_by_node: dict[tuple, dict] = {}  # node → {id, name} substation
    sub_by_id = {s["id"]: s for s in subs}
    for idx, f in enumerate(features):
        n1, n2 = feat_endpoints[idx]
        fid, tid = feat_endpoint_ids[idx]
        if n1 is not None and fid and fid in sub_by_id:
            terminal_by_node.setdefault(n1, {"id": fid,
                                              "name": sub_by_id[fid]["name"]})
        if n2 is not None and tid and tid in sub_by_id:
            terminal_by_node.setdefault(n2, {"id": tid,
                                              "name": sub_by_id[tid]["name"]})
    terminals = terminal_by_node
    print(f"  terminal nodes (from phase 2 endpoints): {len(terminals)}")

    # Traverse: untuk tiap feature yang endpoint_confidence != both,
    # coba walk ke terminal di sisi non-terminal.
    circuit_id_counter = 1
    feat_circuit: dict[int, dict] = {}  # feat_idx → circuit info

    for idx, f in enumerate(features):
        if idx in feat_circuit:
            continue  # sudah bagian dari circuit lain
        n1, n2 = feat_endpoints[idx]
        if n1 is None:
            continue
        v_start = feat_voltage[idx]

        # Kalau kedua endpoint sudah terminal → circuit trivial (single segment)
        if n1 in terminals and n2 in terminals:
            circuit_id = f"CIRC-{region.upper()}-{circuit_id_counter:04d}"
            t1 = terminals[n1]
            t2 = terminals[n2]
            feat_circuit[idx] = {
                "circuit_id": circuit_id,
                "from_id": t1["id"], "from_name": t1["name"],
                "to_id": t2["id"], "to_name": t2["name"],
                "length_km": feat_length[idx],
                "segment_count": 1,
            }
            circuit_id_counter += 1
            continue

        # Kalau salah satu endpoint terminal → walk dari yang non-terminal
        for start_node in (n1, n2):
            if start_node in terminals:
                continue
            other_node = n2 if start_node == n1 else n1
            if other_node not in terminals:
                continue  # butuh salah satu ujung terminal
            # Walk dari start_node (non-terminal) melalui idx ke chain lanjutan
            result = walk_chain(idx, start_node, v_start, adjacency,
                                 feat_voltage, terminals, feat_length)
            if result is None:
                continue
            # Circuit found: from = terminals[other_node], to = terminals[result.other_terminal]
            circuit_id = f"CIRC-{region.upper()}-{circuit_id_counter:04d}"
            t_from = terminals[other_node]
            t_to = terminals[result["other_terminal_node"]]
            for seg_idx in result["segments"]:
                feat_circuit[seg_idx] = {
                    "circuit_id": circuit_id,
                    "from_id": t_from["id"], "from_name": t_from["name"],
                    "to_id": t_to["id"], "to_name": t_to["name"],
                    "length_km": result["total_length_km"],
                    "segment_count": len(result["segments"]),
                }
            circuit_id_counter += 1
            break

    # Write back to features. Untuk features yang jadi bagian dari circuit,
    # ALSO overwrite from_id/to_id/from_name/to_name per feature dengan
    # circuit endpoints — supaya downstream reconciler (yang index by
    # frozenset({from_id, to_id})) otomatis pakai endpoints yang benar
    # (via shared-node discovery), bukan hasil phase-2 per-endpoint lookup
    # yang under-count.
    circuit_count = circuit_id_counter - 1
    seg_in_circuit = len(feat_circuit)
    upgraded = 0
    for idx, f in enumerate(features):
        props = f.setdefault("properties", {})
        ci = feat_circuit.get(idx)
        if ci:
            props["circuit_id"] = ci["circuit_id"]
            props["circuit_from_id"] = ci["from_id"]
            props["circuit_from_name"] = ci["from_name"]
            props["circuit_to_id"] = ci["to_id"]
            props["circuit_to_name"] = ci["to_name"]
            props["circuit_length_km"] = round(ci["length_km"], 3)
            props["circuit_segment_count"] = ci["segment_count"]
            # Upgrade per-feature endpoints kalau phase-2 incomplete
            prev_from = (props.get("from_id") or "").strip()
            prev_to = (props.get("to_id") or "").strip()
            if not prev_from or not prev_to:
                props["from_id"] = ci["from_id"]
                props["from_name"] = ci["from_name"]
                props["to_id"] = ci["to_id"]
                props["to_name"] = ci["to_name"]
                props["endpoint_confidence"] = "both"
                upgraded += 1
        else:
            props["circuit_id"] = ""
            props["circuit_from_id"] = ""
            props["circuit_from_name"] = ""
            props["circuit_to_id"] = ""
            props["circuit_to_name"] = ""
            props["circuit_length_km"] = ""
            props["circuit_segment_count"] = ""

    print(f"\n  circuits identified:        {circuit_count}")
    print(f"  segments in a circuit:      {seg_in_circuit} "
          f"({100*seg_in_circuit/len(features):.1f}%)")
    print(f"  segments NOT in a circuit:  {len(features) - seg_in_circuit}")
    print(f"  endpoint IDs upgraded:      {upgraded} "
          f"(phase-2 had them as partial)")

    # Group circuit stats
    from collections import Counter
    circuit_sizes = Counter()
    for ci in feat_circuit.values():
        circuit_sizes[ci["circuit_id"]] = ci["segment_count"]
    if circuit_sizes:
        avg_size = sum(circuit_sizes.values()) / len(circuit_sizes)
        max_size = max(circuit_sizes.values())
        print(f"  avg segments/circuit: {avg_size:.1f}, max: {max_size}")

    gj_path.write_text(json.dumps(gj, ensure_ascii=False), encoding="utf-8")
    print(f"\n  updated {gj_path}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--region", required=True)
    ap.add_argument("--max-km", type=float, default=3.0,
                    help="Radius terminal detection (default 3 km)")
    opts = ap.parse_args()
    return merge(opts.region, Path(__file__).resolve().parents[1],
                  opts.max_km)


if __name__ == "__main__":
    raise SystemExit(main())
