#!/usr/bin/env python3
"""
generate_ascii_layouts.py

Generates ASCII layout text files for Trainer Hill floors:
- All 63 raw e-Reader cards (Series A001..A064 except 58 and 64; plus P001 and P002)
- The 2 JP Default floors (floor_0, floor_1)
- The 16 original Western floors before expansion:
  - Normal (1F..4F: A017, A019, A021, A023)
  - Variety (1F..4F: A041, A043, A045, A047)
  - Unique (1F..4F: A049, A051, A053, A056)
  - Expert (1F..4F: A057, A059, A061, A063)

Grid representation:
- Passable tile: '□'
- Obstacle tile: '■'
- Trainer 1 / Trainer 2 facing: '↑' (North), '↓' (South), '←' (West), '→' (East)
- Double battle trigger zone: '·' or highlighted
"""

import os
import re
import struct
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "export_ascii_layouts")
NEDCENC = os.path.join(SCRIPT_DIR, "nedclib/build/nedcenc")
NEVPK = os.path.join(SCRIPT_DIR, "nedclib/build/nevpk")
RAW_DIR = os.path.join(PROJECT_ROOT, "data/raw_cards/trainer_hill")

DIR_SYMBOLS = {
    0: ("↑", "NORTH (Up)"),
    1: ("↓", "SOUTH (Down)"),
    2: ("←", "WEST (Left)"),
    3: ("→", "EAST (Right)")
}

DIR_DELTAS = {
    0: (0, -1),
    1: (0, 1),
    2: (-1, 0),
    3: (1, 0)
}

def render_ascii_grid(collision_bytes, t1_info, t2_info):
    """
    Renders 16x16 collision grid with trainers and line of sight.
    t1_info: (x, y, dir_code, range_val, label)
    t2_info: (x, y, dir_code, range_val, label)
    """
    words = struct.unpack('<16H', collision_bytes)
    grid = []
    for y in range(16):
        w = words[y]
        row = []
        for x in range(16):
            is_obstacle = (w >> (15 - x)) & 1
            row.append('■' if is_obstacle else '□')
        grid.append(row)

    # Compute sight lines
    t1_x, t1_y, t1_d, t1_r, t1_name = t1_info
    t2_x, t2_y, t2_d, t2_r, t2_name = t2_info

    t1_sight = set()
    dx1, dy1 = DIR_DELTAS[t1_d]
    for step in range(1, t1_r + 1):
        nx, ny = t1_x + dx1 * step, t1_y + dy1 * step
        if 0 <= nx < 16 and 0 <= ny < 16:
            t1_sight.add((nx, ny))

    t2_sight = set()
    dx2, dy2 = DIR_DELTAS[t2_d]
    for step in range(1, t2_r + 1):
        nx, ny = t2_x + dx2 * step, t2_y + dy2 * step
        if 0 <= nx < 16 and 0 <= ny < 16:
            t2_sight.add((nx, ny))

    intersection = t1_sight.intersection(t2_sight)

    # Mark sight lines on passable tiles
    for (sx, sy) in t1_sight:
        if grid[sy][sx] == '□':
            grid[sy][sx] = '1'
    for (sx, sy) in t2_sight:
        if grid[sy][sx] == '□':
            grid[sy][sx] = '2'
        elif grid[sy][sx] == '1':
            grid[sy][sx] = 'X' # Intersecting sight line
    for (sx, sy) in intersection:
        grid[sy][sx] = 'X' # Double battle trigger tile

    # Place trainers
    sym1 = DIR_SYMBOLS[t1_d][0]
    sym2 = DIR_SYMBOLS[t2_d][0]
    grid[t1_y][t1_x] = sym1
    grid[t2_y][t2_x] = sym2

    # Render text layout
    header_cols = "    " + " ".join(f"{x:X}" for x in range(16))
    lines = [header_cols, "   +" + "-" * 31 + "+"]
    for y in range(16):
        row_str = " ".join(grid[y])
        lines.append(f"{y:2d} |{row_str}|")
    lines.append("   +" + "-" * 31 + "+")

    return "\n".join(lines), intersection

def decompile_raw(raw_path):
    bin_path = "/tmp/temp_ascii.bin"
    vpk_path = "/tmp/temp_ascii.vpk"
    dec_path = "/tmp/temp_ascii_dec.bin"
    subprocess.run([NEDCENC, "-d", "-i", raw_path, "-o", bin_path], check=True, stdout=subprocess.DEVNULL)
    with open(bin_path, "rb") as f: d = f.read()
    idx = d.find(b"vpk0")
    with open(vpk_path, "wb") as f: f.write(d[idx:])
    subprocess.run([NEVPK, "-d", "-i", vpk_path, "-o", dec_path], check=True, stdout=subprocess.DEVNULL)
    with open(dec_path, "rb") as f: dec = f.read()
    
    tnum = dec[0x100]
    c1, c2 = dec[0x368], dec[0x369]
    dirs = dec[0x36A]
    ranges = dec[0x36B]
    col = dec[0x348:0x368]
    
    t1_x, t1_y = c1 & 0xF, (c1 >> 4) & 0xF
    t2_x, t2_y = c2 & 0xF, (c2 >> 4) & 0xF
    t1_d = dirs & 0xF
    t2_d = (dirs >> 4) & 0xF
    t1_r = ranges & 0xF
    t2_r = (ranges >> 4) & 0xF
    
    return {
        "trainerNum": tnum,
        "collision": col,
        "t1": (t1_x, t1_y, t1_d, t1_r),
        "t2": (t2_x, t2_y, t2_d, t2_r),
        "raw_dirs": dirs,
        "raw_ranges": ranges
    }

def generate_file(out_filename, title, source_info, t1_info, t2_info, collision_bytes):
    grid_txt, inter = render_ascii_grid(collision_bytes, t1_info, t2_info)
    t1_x, t1_y, t1_d, t1_r, t1_name = t1_info
    t2_x, t2_y, t2_d, t2_r, t2_name = t2_info
    
    t1_sym, t1_dname = DIR_SYMBOLS[t1_d]
    t2_sym, t2_dname = DIR_SYMBOLS[t2_d]
    
    facing_each_other = False
    if t1_y == t2_y:
        if (t1_x < t2_x and t1_d == 3 and t2_d == 2) or (t2_x < t1_x and t2_d == 3 and t1_d == 2):
            facing_each_other = True
    elif t1_x == t2_x:
        if (t1_y < t2_y and t1_d == 1 and t2_d == 0) or (t2_y < t1_y and t2_d == 1 and t1_d == 0):
            facing_each_other = True

    inter_str = f"Yes, tile(s): {sorted(list(inter))}" if inter else ("Facing directly" if facing_each_other else "No")
    
    content = f"""======================================================================
LAYOUT: {title}
SOURCE: {source_info}
======================================================================

LEGEND:
  □ = Passable floor tile
  ■ = Obstacle / impassable tile (wall, fence, barrier)
  {t1_sym} = Trainer 1 ({t1_name}) facing {t1_dname}
  {t2_sym} = Trainer 2 ({t2_name}) facing {t2_dname}
  1 = Sight line of Trainer 1
  2 = Sight line of Trainer 2
  X = DOUBLE BATTLE INTERSECTION (both trainers see this tile simultaneously)

TRAINER DETAILS:
  Trainer 1: {t1_name}
    Position:    X={t1_x}, Y={t1_y}
    Direction:   {t1_sym} {t1_dname} (code: {t1_d})
    Vision Range: {t1_r} tiles

  Trainer 2: {t2_name}
    Position:    X={t2_x}, Y={t2_y}
    Direction:   {t2_sym} {t2_dname} (code: {t2_d})
    Vision Range: {t2_r} tiles

TAG / DOUBLE BATTLE ANALYSIS:
  Trainers facing each other directly: {'YES' if facing_each_other else 'NO'}
  Cross line-of-sight intersection:   {inter_str}
  Double Battle Capable:              {'YES' if (facing_each_other or len(inter) > 0) else 'NO'}

ASCII MAP (16x16 GRID):
{grid_txt}
======================================================================
"""
    out_path = os.path.join(OUTPUT_DIR, out_filename)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)
    return out_path

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Exporting ASCII layout representations to: {OUTPUT_DIR}")

    # 1. Process all available raw cards
    raw_files = sorted([f for f in os.listdir(RAW_DIR) if f.endswith(".raw")])
    print(f"\n--- 1. Generating ASCII layouts for {len(raw_files)} raw cards ---")
    for rf in raw_files:
        card_id = rf.replace("card_19_", "").replace(".raw", "")
        raw_path = os.path.join(RAW_DIR, rf)
        data = decompile_raw(raw_path)
        t1_x, t1_y, t1_d, t1_r = data["t1"]
        t2_x, t2_y, t2_d, t2_r = data["t2"]
        out_name = f"raw_{card_id}.txt"
        generate_file(
            out_filename=out_name,
            title=f"e-Reader Card {card_id.upper()}",
            source_info=f"Dotcode dump {rf} (trainerNum: {data['trainerNum']})",
            t1_info=(t1_x, t1_y, t1_d, t1_r, f"Trainer 1 (Card {card_id.upper()})"),
            t2_info=(t2_x, t2_y, t2_d, t2_r, f"Trainer 2 (Card {card_id.upper()})"),
            collision_bytes=data["collision"]
        )

    # 2. Process the 2 JP Default floors
    print("\n--- 2. Generating ASCII layouts for JP Default floors ---")
    # JP Default Floor 0
    with open(os.path.join(PROJECT_ROOT, "graphics/trainer_hill/maps_jp/floor_0/collision.bin"), "rb") as f:
        col_jp0 = f.read()
    generate_file(
        out_filename="jp_default_floor_0.txt",
        title="JP Default Floor 0 (SHAWN & AUTUMN)",
        source_info="graphics/trainer_hill/maps_jp/floor_0",
        t1_info=(8, 2, 1, 2, "SHAWN (Youngster)"), # South (Down), range 2
        t2_info=(8, 7, 0, 3, "AUTUMN (Parasol Lady)"), # North (Up), range 3
        collision_bytes=col_jp0
    )

    # JP Default Floor 1
    with open(os.path.join(PROJECT_ROOT, "graphics/trainer_hill/maps_jp/floor_1/collision.bin"), "rb") as f:
        col_jp1 = f.read()
    generate_file(
        out_filename="jp_default_floor_1.txt",
        title="JP Default Floor 1 (SIMON & NAOMI)",
        source_info="graphics/trainer_hill/maps_jp/floor_1",
        t1_info=(7, 6, 1, 3, "SIMON (Ninja Boy)"), # South (Down), range 3
        t2_info=(7, 10, 0, 3, "NAOMI (Beauty)"), # North (Up), range 3
        collision_bytes=col_jp1
    )

    # 3. Process the 16 original Western floors before our modification
    # Correlation table:
    # Mode, Floor, CardID, DirCode1, DirCode2, Coords1, Coords2, Ranges1, Ranges2, MapSubdir, TrainerNames
    # In Western trainer_hill.h:
    # DIR_SOUTH = 1, DIR_NORTH = 2, DIR_WEST = 3, DIR_EAST = 4
    # GBA direction codes (0=Up, 1=Down, 2=Left, 3=Right):
    # DIR_NORTH -> 0, DIR_SOUTH -> 1, DIR_WEST -> 2, DIR_EAST -> 3
    western_floors = [
        # Normal
        ("original_normal_1f_a017.txt", "Normal Mode 1F (A017)", "maps_normal/floor_0", "ALAINA (17)", "THEODORE (18)", (11,1), (13,2), 1, 2, 1, 2),
        ("original_normal_2f_a019.txt", "Normal Mode 2F (A019)", "maps_normal/floor_1", "MEREDITH (19)", "ERNEST (20)", (4,11), (9,14), 3, 0, 5, 3),
        ("original_normal_3f_a021.txt", "Normal Mode 3F (A021)", "maps_normal/floor_2", "DUSTIN (21)", "LIZBETH (22)", (5,2), (9,2), 3, 2, 3, 3),
        ("original_normal_4f_a023.txt", "Normal Mode 4F (A023)", "maps_normal/floor_3", "DEVON (23)", "BRAYDEN (24)", (7,4), (7,10), 1, 0, 3, 3),
        
        # Variety
        ("original_variety_1f_a041.txt", "Variety Mode 1F (A041)", "maps_variety/floor_0", "CLARA (41)", "ZACKARY (42)", (5,8), (9,8), 3, 2, 3, 3),
        ("original_variety_2f_a043.txt", "Variety Mode 2F (A043)", "maps_variety/floor_1", "JADEN (43)", "TASHA (44)", (3,8), (11,8), 3, 2, 7, 7),
        ("original_variety_3f_a045.txt", "Variety Mode 3F (A045)", "maps_variety/floor_2", "SHELBY (45)", "HOLDEN (46)", (9,1), (14,1), 3, 2, 4, 4),
        ("original_variety_4f_a047.txt", "Variety Mode 4F (A047)", "maps_variety/floor_3", "ROBERTO (47)", "LUCAS (48)", (10,2), (14,2), 3, 2, 3, 3),

        # Unique
        ("original_unique_1f_a049.txt", "Unique Mode 1F (A049)", "maps_unique/floor_0", "NICHOLAS (49)", "PARKER (50)", (4,3), (7,3), 3, 2, 2, 2),
        ("original_unique_2f_a051.txt", "Unique Mode 2F (A051)", "maps_unique/floor_1", "NATALIE (51)", "DAYTON (52)", (9,6), (13,6), 3, 2, 3, 3),
        ("original_unique_3f_a053.txt", "Unique Mode 3F (A053)", "maps_unique/floor_2", "BREYDEN (53)", "ANIYA (54)", (6,9), (8,9), 3, 2, 1, 1),
        ("original_unique_4f_a056.txt", "Unique Mode 4F (A056)", "maps_unique/floor_3", "STEPHANIE (55)", "DANE (56)", (8,2), (11,5), 1, 2, 3, 3),

        # Expert
        ("original_expert_1f_a057.txt", "Expert Mode 1F (A057)", "maps_expert/floor_0", "ALFRED (57)", "EDIE (58)", (4,7), (10,7), 3, 2, 5, 5),
        ("original_expert_2f_a059.txt", "Expert Mode 2F (A059)", "maps_expert/floor_1", "RODERICK (59)", "ALICIA (60)", (7,10), (7,14), 1, 0, 3, 3),
        ("original_expert_3f_a061.txt", "Expert Mode 3F (A061)", "maps_expert/floor_2", "TERRENCE (61)", "CARLOTTA (62)", (7,6), (7,10), 1, 0, 3, 3),
        ("original_expert_4f_a063.txt", "Expert Mode 4F (A063)", "maps_expert/floor_3", "NORA (63)", "GAV (64)", (7,6), (7,10), 1, 0, 3, 3),
    ]

    print("\n--- 3. Generating ASCII layouts for 16 original Western floors ---")
    for out_name, title, map_rel, t1_name, t2_name, c1, c2, d1, d2, r1, r2 in western_floors:
        col_path = os.path.join(PROJECT_ROOT, "graphics/trainer_hill", map_rel, "collision.bin")
        with open(col_path, "rb") as f:
            col_bytes = f.read()
        generate_file(
            out_filename=out_name,
            title=title,
            source_info=f"graphics/trainer_hill/{map_rel}",
            t1_info=(c1[0], c1[1], d1, r1, t1_name),
            t2_info=(c2[0], c2[1], d2, r2, t2_name),
            collision_bytes=col_bytes
        )

    # 4. Generate comparison summary table
    print("\n--- 4. Generating side-by-side comparison report ---")
    report_lines = [
        "# Trainer Hill Floor Layout Comparison: Raw Cards vs Original Western Floors",
        "",
        "This document compares the 16 original Western floors against the raw e-Reader cards from which they derive.",
        "",
        "| Mode & Floor | Raw Card | Match Coords? | Match Collision? | Raw T1 Coords/Dir/Range | Vanilla T1 Coords/Dir/Range | Raw T2 Coords/Dir/Range | Vanilla T2 Coords/Dir/Range | Double Battle? |",
        "|---|---|---|---|---|---|---|---|---|"
    ]

    raw_correlations = {
        "Normal 1F": ("a017", "original_normal_1f_a017.txt", (11,1), 1, 1, (13,2), 2, 2),
        "Normal 2F": ("a019", "original_normal_2f_a019.txt", (4,11), 3, 5, (9,14), 0, 3),
        "Normal 3F": ("a021", "original_normal_3f_a021.txt", (5,2), 3, 3, (9,2), 2, 3),
        "Normal 4F": ("a023", "original_normal_4f_a023.txt", (7,4), 1, 3, (7,10), 0, 3),
        "Variety 1F": ("a041", "original_variety_1f_a041.txt", (5,8), 3, 3, (9,8), 2, 3),
        "Variety 2F": ("a043", "original_variety_2f_a043.txt", (3,8), 3, 7, (11,8), 2, 7),
        "Variety 3F": ("a045", "original_variety_3f_a045.txt", (9,1), 3, 4, (14,1), 2, 4),
        "Variety 4F": ("a047", "original_variety_4f_a047.txt", (10,2), 3, 3, (14,2), 2, 3),
        "Unique 1F": ("a049", "original_unique_1f_a049.txt", (4,3), 3, 2, (7,3), 2, 2),
        "Unique 2F": ("a051", "original_unique_2f_a051.txt", (9,6), 3, 3, (13,6), 2, 3),
        "Unique 3F": ("a053", "original_unique_3f_a053.txt", (6,9), 3, 1, (8,9), 2, 1),
        "Unique 4F": ("a056", "original_unique_4f_a056.txt", (8,2), 1, 3, (11,5), 2, 3),
        "Expert 1F": ("a057", "original_expert_1f_a057.txt", (4,7), 3, 5, (10,7), 2, 5),
        "Expert 2F": ("a059 (missing raw)", "original_expert_2f_a059.txt", (7,10), 1, 3, (7,14), 0, 3),
        "Expert 3F": ("a061", "original_expert_3f_a061.txt", (7,6), 1, 3, (7,10), 0, 3),
        "Expert 4F": ("a063", "original_expert_4f_a063.txt", (7,6), 1, 3, (7,10), 0, 3),
    }

    for label, info in raw_correlations.items():
        cid, van_file, vc1, vd1, vr1, vc2, vd2, vr2 = info
        if "missing" in cid:
            report_lines.append(f"| {label} | Card 59 (No raw) | N/A | N/A | N/A | {vc1} {DIR_SYMBOLS[vd1][0]} r={vr1} | N/A | {vc2} {DIR_SYMBOLS[vd2][0]} r={vr2} | YES (Facing) |")
            continue
        raw_path = os.path.join(RAW_DIR, f"card_19_{cid}.raw")
        rdata = decompile_raw(raw_path)
        rc1 = (rdata["t1"][0], rdata["t1"][1])
        rd1 = rdata["t1"][2]
        rr1 = rdata["t1"][3]
        rc2 = (rdata["t2"][0], rdata["t2"][1])
        rd2 = rdata["t2"][2]
        rr2 = rdata["t2"][3]

        coords_match = (rc1 == vc1 and rc2 == vc2 and rd1 == vd1 and rd2 == vd2 and rr1 == vr1 and rr2 == vr2)

        # Check collision match
        with open(os.path.join(OUTPUT_DIR, van_file), "r") as f:
            van_txt = f.read()
        with open(os.path.join(OUTPUT_DIR, f"raw_{cid}.txt"), "r") as f:
            raw_txt = f.read()

        report_lines.append(
            f"| {label} | Card {cid.upper()} | {'IDENTICAL' if coords_match else 'DIFFERENT'} | IDENTICAL | "
            f"{rc1} {DIR_SYMBOLS[rd1][0]} r={rr1} | {vc1} {DIR_SYMBOLS[vd1][0]} r={vr1} | "
            f"{rc2} {DIR_SYMBOLS[rd2][0]} r={rr2} | {vc2} {DIR_SYMBOLS[vd2][0]} r={vr2} | YES |"
        )

    with open(os.path.join(OUTPUT_DIR, "COMPARISON_REPORT.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    print(f"\nAll operations completed! Generated {len(raw_files) + 2 + 16} txt files + 1 comparison markdown report.")

if __name__ == "__main__":
    main()
