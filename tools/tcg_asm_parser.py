#!/usr/bin/env python3
"""
tools/tcg_asm_parser.py
Robust, comment-driven parser for the poketcg / poketcg2-en card, text and
effect data. Shared by tools/rebuild_tcg_data.py.

Unlike the old regex in generate_tcg_data.py, this module reads each field by
its trailing ASM comment (e.g. "; weakness", "; resistance", "; category") so
that resistance / category / flags lines can never be mistaken for weakness or
attack names.
"""
import glob
import os
import re

# poketcg2-en is a superset of the poketcg cards (poketcg only used as fallback)
CARD_FILES = ['poketcg2-en/src/data/cards1.asm', 'poketcg2-en/src/data/cards2.asm']


def read_text(path):
    """Read an ASM file as UTF-8, falling back to latin-1."""
    raw = open(path, 'rb').read()
    try:
        return raw.decode('utf-8')
    except UnicodeDecodeError:
        return raw.decode('latin-1')


def load_texts():
    """Return {label: joined text} for every text block in both decomps."""
    texts = {}
    files = (glob.glob('poketcg2-en/src/text/**/*.asm', recursive=True) +
             glob.glob('poketcg/src/text/**/*.asm', recursive=True))
    for tf in files:
        content = read_text(tf)
        for block in re.split(r'\n(?=[A-Za-z0-9_]+:)', content):
            lines = block.strip().splitlines()
            if not lines:
                continue
            m_lbl = re.match(r'^([A-Za-z0-9_]+):', lines[0])
            if not m_lbl:
                continue
            lbl = m_lbl.group(1)
            parts = []
            for l in lines[1:]:
                s = l.strip()
                m = re.match(r'^(?:text|line)\s+"([^"]*)"', s)
                if m:
                    parts.append(m.group(1))
                elif s.startswith('done'):
                    break
            if parts and lbl not in texts:
                texts[lbl] = ' '.join(parts)
    return texts


def load_effect_commands():
    """Return {EffectCommandsLabel: [command names]} from effect_commands files."""
    cmds = {}
    files = (glob.glob('poketcg2-en/src/engine/**/effect_commands.asm', recursive=True) +
             glob.glob('poketcg2-en/src/**/effect_functions*.asm', recursive=True) +
             glob.glob('poketcg/src/engine/**/effect_commands.asm', recursive=True))
    files += glob.glob('poketcg2-en/src/data/effect_commands.asm')
    files += glob.glob('poketcg/src/data/effect_commands.asm')
    for ef in files:
        try:
            with open(ef, 'r', encoding='latin-1') as f:
                content = f.read()
        except OSError:
            continue
        for block in re.split(r'\n(?=[A-Za-z0-9_]+EffectCommands:)', content):
            m = re.match(r'^([A-Za-z0-9_]+EffectCommands):', block)
            if not m:
                continue
            names = re.findall(r'dbw\s+EFFECTCMDTYPE_\w+,\s*(\w+)', block)
            cmds.setdefault(m.group(1), names)
    return cmds


def _cost(text):
    """'GRASS, 2, COLORLESS, 1' -> {'GRASS':2,'COLORLESS':1}"""
    parts = [p.strip() for p in text.split(',')]
    out = {}
    i = 0
    while i < len(parts):
        t = parts[i]
        if t == '0' or not t:
            break
        n = 1
        if i + 1 < len(parts) and parts[i + 1].isdigit():
            n = int(parts[i + 1])
            i += 2
        else:
            i += 1
        out[t] = out.get(t, 0) + n
    return out


def parse_cards(texts=None):
    """Yield card dicts in canonical order (cards1, cards2, cards; first label wins)."""
    texts = texts or load_texts()
    seen = set()
    cards = []
    for fpath in CARD_FILES:
        if not os.path.exists(fpath):
            continue
        content = read_text(fpath)
        for chunk in re.split(r'\n(?=[A-Za-z0-9_]+Card:)', content):
            lines = chunk.strip().splitlines()
            if not lines:
                continue
            m = re.match(r'^([A-Za-z0-9_]+)Card:', lines[0])
            if not m:
                continue
            label = m.group(1)
            if label.upper() in seen:
                continue
            card = {'label': label, 'attacks': [], 'power': None, 'rarity': 'CIRCLE',
                    'stage': 'BASIC', 'weakness': 'NONE', 'resistance': 'NONE',
                    'retreat': 0, 'hp': 0, 'type': None, 'name_lbl': None,
                    'preevo_lbl': None, 'id_const': None, 'desc_lbl': None,
                    'effect_cmds': None, 'trainer_desc': None}
            cur = None
            for raw in lines[1:]:
                code, _, comment = raw.partition(';')
                code = code.strip()
                comment = comment.strip().lower()
                if not code:
                    # section markers are comment-only lines
                    if comment in ('attack 1', 'attack 2', 'pokemon power'):
                        cur = {'cost': {}, 'name_lbl': None, 'desc_lbls': [], 'damage': 0,
                               'category': 'DAMAGE_NORMAL', 'effect_cmds': None,
                               'flags': [], 'param': 0, 'anim': None}
                        card['attacks'].append(cur)
                    continue
                if comment == 'type':
                    card['type'] = code.split()[1]
                elif comment == 'name' and cur is None:
                    card['name_lbl'] = code.split()[1]
                elif comment == 'rarity':
                    card['rarity'] = code.split(None, 1)[1]
                elif comment == 'hp':
                    card['hp'] = int(code.split()[1])
                elif comment == 'stage':
                    card['stage'] = code.split()[1]
                elif comment == 'pre-evo name' and cur is None:
                    p = code.split()
                    card['preevo_lbl'] = p[1] if p[0] == 'tx' else None
                elif comment == 'retreat cost':
                    card['_after_attacks'] = True
                    card['retreat'] = int(code.split()[1])
                elif comment == 'weakness':
                    card['weakness'] = code.split()[1]
                elif comment == 'resistance':
                    card['resistance'] = code.split()[1]
                elif cur is not None and not card.get('_after_attacks') and comment in (
                        'energies', 'name', 'description', 'description (cont)', 'damage',
                        'category', 'effect commands', 'flags 1', 'flags 2', 'flags 3',
                        'effect param', 'animation'):
                    p = code.split(None, 1)
                    if comment == 'energies':
                        cur['cost'] = _cost(p[1]) if len(p) > 1 else {}
                    elif comment == 'name':
                        cur['name_lbl'] = p[1] if p[0] == 'tx' else None
                    elif comment in ('description', 'description (cont)'):
                        if p[0] == 'tx':
                            cur['desc_lbls'].append(p[1])
                    elif comment == 'damage':
                        cur['damage'] = int(p[1])
                    elif comment == 'category':
                        cur['category'] = p[1]
                    elif comment == 'effect commands':
                        cur['effect_cmds'] = p[1] if p[0] == 'dw' and p[1] != 'NONE' else None
                    elif comment.startswith('flags'):
                        cur['flags'] += [x.strip() for x in p[1].split('|') if x.strip() != 'NONE']
                    elif comment == 'effect param':
                        cur['param'] = int(p[1]) if p[1].isdigit() else 0
                    elif comment == 'animation':
                        cur['anim'] = p[1]
                        # animation is the last attack field of the 2nd attack/power;
                        # after attack 2 the card-level fields follow (retreat...)
                elif comment == 'category' and cur is not None:
                    pass
                elif comment == 'description' and card['type'] == 'TYPE_TRAINER':
                    p = code.split()
                    if p[0] == 'tx':
                        card['trainer_desc'] = p[1]
                elif comment == 'effect commands' and card['type'] == 'TYPE_TRAINER':
                    card['effect_cmds'] = code.split()[1]
                elif card['type'] == 'TYPE_TRAINER' and comment == '' and code.startswith('dw '):
                    card['id_const'] = code.split()[1]
                elif card['type'] and card['type'] != 'TYPE_TRAINER' and code.startswith('dw ') and card['id_const'] is None and comment == '':
                    card['id_const'] = code.split()[1]
            # Trainer cards: "effect commands"/"description" appear with cur None
            if card['type'] == 'TYPE_TRAINER':
                for raw in lines[1:]:
                    code, _, comment = raw.partition(';')
                    code = code.strip()
                    comment = comment.strip().lower()
                    if comment == 'effect commands':
                        card['effect_cmds'] = code.split()[1]
                    elif comment == 'description' and code.startswith('tx'):
                        card['trainer_desc'] = code.split()[1]
            # Pokemon power flag
            for a in card['attacks']:
                a['is_power'] = (a['category'] == 'POKEMON_POWER')
            # Drop empty attack slots
            card['attacks'] = [a for a in card['attacks'] if a['name_lbl']]
            if not card['type'] or 'ENERGY' in card['type'] or (
                    'Energy' in label and label not in ('EnergyRemoval', 'SuperEnergyRemoval')):
                continue
            seen.add(label.upper())
            cards.append(card)
    return cards


def attack_text(texts, lbl):
    t = texts.get(lbl, lbl)
    return t[:-4] if t.endswith('Name') and lbl.endswith('Name') and t == lbl else t


if __name__ == '__main__':
    t = load_texts()
    cs = parse_cards(t)
    print(len(cs), 'cards')
    names = {}
    for c in cs:
        for a in c['attacks']:
            names.setdefault(t.get(a['name_lbl'], a['name_lbl']), set()).add(
                (a['damage'], a['category'], tuple(a['desc_lbls']), a['effect_cmds']))
    print(len(names), 'unique attack names;', sum(len(v) for v in names.values()), 'signatures')
