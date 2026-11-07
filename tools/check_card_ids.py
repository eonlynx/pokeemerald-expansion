#!/usr/bin/env python3
import re

with open('include/constants/tcg_cards.h', 'r', encoding='utf-8') as f:
    text = f.read()

for item in ['POTION', 'SUPER_POTION', 'FULL_HEAL', 'REVIVE', 'POKEDEX', 'POKE_BALL', 'PROFESSOR_OAK', 'BILL', 'SWITCH']:
    m = re.search(r'#define\s+(CARD_' + item + r'[A-Z0-9_]*)\s+(\d+)', text)
    if m:
        print(f"{m.group(1)} = {m.group(2)}")
    else:
        print(f"{item} NOT FOUND")
