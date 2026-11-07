#!/usr/bin/env python3
"""
tools/inspect_card_attacks.py
Inspects all attacks, damage values, descriptions, and effect categories in poketcg and poketcg2-en.
"""

import glob
import re
import os
from collections import Counter

def load_texts():
    texts = {}
    for p in glob.glob('poketcg2-en/src/text/**/*.asm', recursive=True) + glob.glob('poketcg/src/text/**/*.asm', recursive=True):
        with open(p, 'r', encoding='latin-1') as f:
            content = f.read()

        blocks = re.findall(r'([A-Za-z0-9_]+):([\s\S]*?)(?=\ndone|\n[A-Za-z0-9_]+:|\Z)', content)
        for label, body in blocks:
            lines = []
            for m in re.finditer(r'(?:text|line)\s+"([^"]*)"', body):
                lines.append(m.group(1))
            if lines:
                texts[label] = " ".join(lines)
    return texts

def inspect_attacks():
    texts = load_texts()
    print(f"Loaded {len(texts)} text strings.")

    print(f"Sample Tacklename: {texts.get('TackleName')}")
    print(f"Sample RazorLeafName: {texts.get('RazorLeafName')}")
    print(f"Sample LeechSeed: {texts.get('LeechSeedName')} -> {texts.get('BulbasaursLeechSeedDescription')}")

    # Parse cards1.asm, cards2.asm, cards.asm
    card_files = ['poketcg2-en/src/data/cards1.asm', 'poketcg2-en/src/data/cards2.asm', 'poketcg/src/data/cards.asm']
    
    attacks = []
    
    for fpath in card_files:
        if not os.path.exists(fpath):
            continue
        with open(fpath, 'r', encoding='latin-1') as f:
            content = f.read()

        cards = re.split(r'\n(?=[A-Za-z0-9_]+Card:)', content)
        for c in cards:
            lines = c.splitlines()
            if not lines:
                continue
            card_lbl = lines[0].split(':')[0].strip()
            
            in_attack = 0
            cur_atk = {}
            for l in lines:
                raw_l = l
                l_code = l.split(';')[0].strip()
                
                if 'attack 1' in raw_l.lower():
                    in_attack = 1
                    cur_atk = {'card': card_lbl, 'slot': 1, 'name': None, 'desc': None, 'dmg': 0, 'raw_l': []}
                elif 'attack 2' in raw_l.lower():
                    if cur_atk and cur_atk.get('name'):
                        attacks.append(cur_atk)
                    in_attack = 2
                    cur_atk = {'card': card_lbl, 'slot': 2, 'name': None, 'desc': None, 'dmg': 0, 'raw_l': []}
                
                if in_attack > 0 and l_code:
                    cur_atk['raw_l'].append(l_code)
                    if l_code.startswith('tx '):
                        sym = l_code.split()[1]
                        if cur_atk['name'] is None:
                            cur_atk['name'] = texts.get(sym, sym)
                        elif cur_atk['desc'] is None:
                            cur_atk['desc'] = texts.get(sym, sym)
                    elif l_code.startswith('db ') and 'damage' in raw_l:
                        m_d = re.search(r'db\s+(\d+)', l_code)
                        if m_d:
                            cur_atk['dmg'] = int(m_d.group(1))

            if cur_atk and cur_atk.get('name'):
                attacks.append(cur_atk)

    print(f"Total attacks parsed: {len(attacks)}")
    unique_atk_names = set(a['name'] for a in attacks if a['name'])
    print(f"Total unique attack names: {len(unique_atk_names)}")
    
    for a in sorted(list(unique_atk_names))[:30]:
        print(f"  - {a}")

if __name__ == '__main__':
    inspect_attacks()
