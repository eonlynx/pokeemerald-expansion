#!/usr/bin/env python3
import re

with open('src/data/items.h', 'r', encoding='utf-8') as f:
    text = f.read()

items_to_check = [
    'ITEM_X_ATTACK', 'ITEM_X_DEFEND', 'ITEM_ZINC', 'ITEM_MAX_ETHER',
    'ITEM_HELIX_FOSSIL', 'ITEM_POKE_DOLL', 'ITEM_ESCAPE_ROPE',
    'ITEM_SUPER_REPEL', 'ITEM_UPGRADE', 'ITEM_VS_SEEKER',
    'ITEM_FAME_CHECKER', 'ITEM_OLD_AMBER', 'ITEM_SILPH_SCOPE',
    'ITEM_ITEMFINDER', 'ITEM_DOWSING_MACHINE'
]

for it in items_to_check:
    m = re.search(r'\[' + it + r'\]\s*=\s*\{([\s\S]*?)\n    \},', text)
    if m:
        ic = re.search(r'\.iconPic\s*=\s*([A-Za-z0-9_]+)', m.group(1))
        pal = re.search(r'\.iconPalette\s*=\s*([A-Za-z0-9_]+)', m.group(1))
        ic_str = ic.group(1) if ic else "NONE"
        pal_str = pal.group(1) if pal else "NONE"
        print(f"{it}: iconPic = {ic_str}, iconPalette = {pal_str}")
    else:
        print(f"{it}: NOT FOUND")
