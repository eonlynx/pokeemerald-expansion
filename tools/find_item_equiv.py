#!/usr/bin/env python3
with open('tools/generate_tcg_data.py', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if 'ITEM_' in line and ('equiv' in line or 'CARD_' in line or 'POTION' in line):
            print(f"{i+1}: {line.strip()[:100]}")
