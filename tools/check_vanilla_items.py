#!/usr/bin/env python3
import re

with open('src/data/items.h', 'r', encoding='utf-8') as f:
    text = f.read()

for item in ['ITEM_POTION', 'ITEM_SUPER_POTION', 'ITEM_FULL_HEAL', 'ITEM_REVIVE', 'ITEM_MAX_REVIVE', 'ITEM_POKE_BALL', 'ITEM_POKEDEX', 'ITEM_POKE_FLUTE']:
    m = re.search(r'\[' + item + r'\]\s*=\s*\{([\s\S]*?)\n    \},', text)
    if m:
        desc = re.search(r'\.description\s*=\s*COMPOUND_STRING\(([\s\S]*?)\),', m.group(1))
        desc_str = desc.group(1).replace('\n', ' ') if desc else 'NO_DESC'
        print(f"{item}: {desc_str[:80]}")
    else:
        print(f"{item}: NOT FOUND")
