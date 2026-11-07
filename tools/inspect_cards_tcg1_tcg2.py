import re

# Read card definitions
def get_card_info(file_path):
    with open(file_path, 'r', encoding='latin-1') as f:
        content = f.read()
    chunks = re.split(r'\n(?=[A-Za-z0-9_]+Card:)', content)
    cards = {}
    for chunk in chunks:
        lines = chunk.strip().splitlines()
        if not lines: continue
        m = re.match(r'^([A-Za-z0-9_]+)Card:', lines[0])
        if not m: continue
        lbl = m.group(1)
        # extract hp, attacks, etc.
        hp_m = re.search(r'db\s+(\d+)\s*;\s*hp', chunk)
        hp = hp_m.group(1) if hp_m else '0'
        # attacks
        atks = re.findall(r'tx\s+([A-Za-z0-9_]+)', chunk)
        # stage
        stage_m = re.search(r'db\s+([A-Z0-9_]+)\s*;\s*stage', chunk)
        stage = stage_m.group(1) if stage_m else ''
        cards[lbl] = {
            'hp': hp,
            'atks': atks,
            'stage': stage,
            'raw': chunk
        }
    return cards

tcg1 = get_card_info('poketcg/src/data/cards.asm')
tcg2_1 = get_card_info('poketcg2-en/src/data/cards1.asm')
tcg2_2 = get_card_info('poketcg2-en/src/data/cards2.asm')
tcg2 = {**tcg2_1, **tcg2_2}

print(f"TCG1 unique cards: {len(tcg1)}")
print(f"TCG2 unique cards: {len(tcg2)}")

# Check exact label matches
exact_matches = set(tcg1.keys()).intersection(set(tcg2.keys()))
print(f"Exact label matches between TCG1 and TCG2: {len(exact_matches)}")
