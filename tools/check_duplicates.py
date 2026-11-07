import re

with open('src/data/tcg_cards.h', 'r', encoding='utf-8') as f:
    text = f.read()

card_blocks = re.findall(r'\[(\d+)\] = \{([\s\S]*?)\n    \},', text)
print(f'Total cards in table: {len(card_blocks)}')

sigs = {}
for cid, body in card_blocks:
    if cid == '0':
        continue
    hp_m = re.search(r'\.maxHp = (\d+)', body)
    m1_m = re.search(r'\.move1 = ([A-Z0-9_]+)', body)
    m2_m = re.search(r'\.move2 = ([A-Z0-9_]+)', body)
    spec_m = re.search(r'\.species = ([A-Z0-9_]+)', body)
    type_m = re.search(r'\.energyType = ([A-Z0-9_]+)', body)
    
    str_m = re.search(r'sCardName_' + cid + r'\[\] = _\("([^"]*)"\);', text)
    cname = str_m.group(1) if str_m else ''
    
    hp = hp_m.group(1) if hp_m else '0'
    m1 = m1_m.group(1) if m1_m else ''
    m2 = m2_m.group(1) if m2_m else ''
    spec = spec_m.group(1) if spec_m else ''
    etype = type_m.group(1) if type_m else ''
    
    # Normalize cname: e.g. "Bulbasaur" vs "Bulbasaur Lv13"
    clean_name = re.sub(r'Lv\s*\d+', '', cname).strip()
    
    sig = (clean_name, hp, m1, m2, spec, etype)
    sigs.setdefault(sig, []).append((cid, cname))

dups = {k: v for k, v in sigs.items() if len(v) > 1}
print(f'Duplicate signatures found: {len(dups)}')
for k, v in list(dups.items())[:15]:
    print(k, v)
