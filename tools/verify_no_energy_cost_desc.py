#!/usr/bin/env python3
import re

for filepath in ['src/data/moves_info.h', 'src/data/tcg_cards.h']:
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Check for energy cost mentions in descriptions
    matches = re.findall(r'(\.description\s*=\s*[\s\S]*?\),)', text)
    cost_mentions = 0
    for m in matches:
        if any(k in m.lower() for k in ['energy cost', 'cost:', 'energy ready', '1r+', '1w+', '1g+', 'cost ready']):
            cost_mentions += 1
            print(f"Warning in {filepath}: {m[:100]}")
    print(f"{filepath}: {cost_mentions} energy cost mentions found.")
