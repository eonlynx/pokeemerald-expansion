#!/usr/bin/env python3
import re

with open('src/data/tcg_cards.h', 'r', encoding='utf-8') as f:
    text = f.read()

m1s = re.findall(r'\.move1\s*=\s*(MOVE_[A-Z0-9_]+)', text)
m2s = re.findall(r'\.move2\s*=\s*(MOVE_[A-Z0-9_]+)', text)
all_moves = set(m1s + m2s) - {'MOVE_NONE'}

print(f"Total distinct moves used across cards: {len(all_moves)}")
blocks = text.split('    [')
for b in blocks[2:12]:
    m_id = re.search(r'(\d+)\]\s*=\s*\{', b)
    m1 = re.search(r'\.move1\s*=\s*([A-Za-z0-9_]+)', b)
    m2 = re.search(r'\.move2\s*=\s*([A-Za-z0-9_]+)', b)
    if m_id and m1 and m2:
        print(f"  Card {m_id.group(1)}: move1={m1.group(1)}, move2={m2.group(1)}")
