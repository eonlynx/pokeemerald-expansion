#!/usr/bin/env python3
import re

def check():
    with open('src/data/moves_info.h', 'r', encoding='utf-8') as f:
        text = f.read()

    exceeded_moves = []
    # Check TCG moves
    with open('tools/tcg_moves_mechanics_check.txt') as f:
        tcg_moves_text = f.read()
    tcg_moves = set(re.findall(r'^(MOVE_[A-Z0-9_]+)', tcg_moves_text, re.MULTILINE))

    for m in re.finditer(r'\[(MOVE_[A-Z0-9_]+)\]\s*=\s*\{[\s\S]*?\.description\s*=\s*COMPOUND_STRING\(([\s\S]*?)\),', text):
        m_name = m.group(1)
        if m_name not in tcg_moves:
            continue
        desc_raw = m.group(2)
        lines = re.findall(r'"([^"]*)"', desc_raw)
        clean_lines = []
        for l in lines:
            for subl in l.split('\\n'):
                if subl:
                    clean_lines.append(subl)
        if len(clean_lines) > 2:
            exceeded_moves.append((m_name, f"Too many lines: {len(clean_lines)}"))
        for l in clean_lines:
            if len(l) > 32:
                exceeded_moves.append((m_name, f"Line too long ({len(l)}): {l}"))

    print(f"Move descriptions checked: {len(tcg_moves)}. Issues found: {len(exceeded_moves)}")
    if exceeded_moves:
        for x in exceeded_moves:
            print("  ", x)

    # Check item descriptions
    with open('src/data/items.h', 'r', encoding='utf-8') as f:
        i_text = f.read()

    exceeded_items = []
    item_blocks = re.findall(r'(\[(ITEM_[A-Za-z0-9_]+)\]\s*=\s*\{[\s\S]*?\n    \},)', i_text)
    checked_items = 0
    for full_block, item_const in item_blocks:
        if not (item_const.startswith('ITEM_TCG_') or item_const in ['ITEM_POTION', 'ITEM_SUPER_POTION', 'ITEM_FULL_HEAL', 'ITEM_REVIVE', 'ITEM_MAX_REVIVE', 'ITEM_POKE_FLUTE']):
            continue
        checked_items += 1
        desc_m = re.search(r'\.description\s*=\s*COMPOUND_STRING\(([\s\S]*?)\),', full_block)
        if not desc_m:
            continue
        desc_raw = desc_m.group(1)
        lines = re.findall(r'"([^"]*)"', desc_raw)
        clean_lines = []
        for l in lines:
            for subl in l.split('\\n'):
                if subl:
                    clean_lines.append(subl)
        if len(clean_lines) > 3:
            exceeded_items.append((item_const, f"Too many lines: {len(clean_lines)}"))
        for l in clean_lines:
            if len(l) > 34:
                exceeded_items.append((item_const, f"Line too long ({len(l)}): {l}"))

    print(f"TCG item descriptions checked: {checked_items}. Issues found: {len(exceeded_items)}")
    if exceeded_items:
        for x in exceeded_items:
            print("  ", x)

if __name__ == '__main__':
    check()
