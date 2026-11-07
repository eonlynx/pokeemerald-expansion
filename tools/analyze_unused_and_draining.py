#!/usr/bin/env python3
import re
from collections import Counter, defaultdict

def analyze():
    # Load cards
    with open('include/constants/tcg_cards.h', 'r') as f:
        c_text = f.read()
    
    card_const_to_id = {}
    id_to_const = {}
    for m in re.finditer(r'#define\s+(CARD_[A-Z0-9_]+)\s+(\d+)', c_text):
        cid = int(m.group(2))
        card_const_to_id[m.group(1)] = cid
        id_to_const[cid] = m.group(1)

    print(f"Total cards in constants: {len(card_const_to_id)}")

    # Load tcg_decks
    with open('src/data/tcg_decks.h', 'r') as f:
        d_text = f.read()

    decks = []
    for m in re.finditer(r'\[\d+\]\s*=\s*\{[\s\S]*?\.name\s*=\s*_\("([^"]+)"\)[\s\S]*?\.cards\s*=\s*\{([^}]+)\}', d_text):
        name = m.group(1)
        cards = [int(x.strip()) for x in m.group(2).split(',') if x.strip().isdigit()]
        decks.append((name, cards))

    print(f"Total decks in tcg_decks.h: {len(decks)}")

    used_cards = set()
    for name, cards in decks:
        used_cards.update(cards)

    unused = [cid for cid in range(1, len(card_const_to_id) + 1) if cid not in used_cards]
    print(f"Used cards in decks: {len(used_cards)} / {len(card_const_to_id)}")
    print(f"Cards not in ANY deck: {len(unused)}")

if __name__ == '__main__':
    analyze()
