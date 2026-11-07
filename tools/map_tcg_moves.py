#!/usr/bin/env python3
"""
tools/map_tcg_moves.py
Maps all TCG Pokémon attacks to GBA moves.
Generates mapping, descriptions (<= 2 lines, <= 32 chars/line), and logic hooks.
"""

import glob
import re
import os
from collections import defaultdict

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

def load_gba_moves():
    gba_moves = {}
    with open('include/constants/moves.h', 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            m = re.match(r'#define\s+(MOVE_[A-Z0-9_]+)\s+(\d+)', line)
            if m:
                m_const = m.group(1)
                m_id = int(m.group(2))
                # clean name
                clean = m_const.replace('MOVE_', '').replace('_', ' ').title()
                gba_moves[clean.upper().replace(' ', '')] = m_const
                gba_moves[m_const] = m_const
    return gba_moves

def parse_all_card_attacks():
    texts = load_texts()
    gba_moves = load_gba_moves()
    
    card_files = ['poketcg2-en/src/data/cards1.asm', 'poketcg2-en/src/data/cards2.asm', 'poketcg/src/data/cards.asm']
    seen_cards = set()
    card_attacks = []

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
            card_lbl = lines[0].split(':')[0].strip().replace('Card', '')
            if card_lbl.upper() in seen_cards:
                continue
            seen_cards.add(card_lbl.upper())

            in_attack = 0
            cur_atk = {}
            for l in lines:
                raw_l = l
                l_code = l.split(';')[0].strip()
                
                if 'attack 1' in raw_l.lower():
                    in_attack = 1
                    cur_atk = {'card': card_lbl, 'slot': 1, 'name': None, 'desc': None, 'dmg': 0, 'energy': [], 'effect_cmd': None}
                elif 'attack 2' in raw_l.lower():
                    if cur_atk and cur_atk.get('name'):
                        card_attacks.append(cur_atk)
                    in_attack = 2
                    cur_atk = {'card': card_lbl, 'slot': 2, 'name': None, 'desc': None, 'dmg': 0, 'energy': [], 'effect_cmd': None}
                
                if in_attack > 0 and l_code:
                    if l_code.startswith('tx '):
                        sym = l_code.split()[1]
                        if cur_atk['name'] is None:
                            cur_atk['name'] = texts.get(sym, sym).replace('Name', '')
                        elif cur_atk['desc'] is None:
                            cur_atk['desc'] = texts.get(sym, sym)
                    elif l_code.startswith('db ') and 'damage' in raw_l:
                        m_d = re.search(r'db\s+(\d+)', l_code)
                        if m_d:
                            cur_atk['dmg'] = int(m_d.group(1))
                    elif l_code.startswith('dw ') and 'effect commands' in raw_l:
                        m_e = re.search(r'dw\s+([A-Za-z0-9_]+)', l_code)
                        if m_e:
                            cur_atk['effect_cmd'] = m_e.group(1)
                    elif l_code.startswith('energy '):
                        cur_atk['energy'].append(l_code[7:])

            if cur_atk and cur_atk.get('name'):
                card_attacks.append(cur_atk)

    return card_attacks

if __name__ == '__main__':
    attacks = parse_all_card_attacks()
    print(f"Total card attacks collected: {len(attacks)}")
    names = sorted(list(set(a['name'] for a in attacks if a['name'])))
    print(f"Total unique names: {len(names)}")
    for n in names[:25]:
        print(f"  {n}")
