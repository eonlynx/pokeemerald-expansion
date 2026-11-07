import re
from collections import Counter, defaultdict

# Test card extraction and deck generation logic
# 1. Moves & species
moves_set = set()
with open('include/constants/moves.h', 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        m = re.search(r'\b(MOVE_[A-Z0-9_]+)\b', line)
        if m: moves_set.add(m.group(1))

species_map = {}
with open('include/constants/species.h', 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        m = re.search(r'\bSPECIES_([A-Z0-9_]+)\b', line)
        if m:
            name = m.group(1).replace('_', '').upper()
            species_map[name] = "SPECIES_" + m.group(1)

# Texts
texts = {}
for tf in ['poketcg/src/text/text1.asm', 'poketcg/src/text/text2.asm', 'poketcg/src/text/text3.asm'] + [f'poketcg2-en/src/text/text{i}.asm' for i in range(1, 14)]:
    try:
        with open(tf, 'r', encoding='latin-1') as f:
            content = f.read()
        for block in re.split(r'\n(?=[A-Za-z0-9_]+:)', content):
            lines = block.strip().splitlines()
            if not lines: continue
            m_lbl = re.match(r'^([A-Za-z0-9_]+):', lines[0])
            if not m_lbl: continue
            lbl = m_lbl.group(1)
            full_text = []
            for l in lines[1:]:
                l_str = l.strip()
                if l_str.startswith('text "') or l_str.startswith('line "'):
                    m_txt = re.match(r'^(?:text|line)\s+"([^"]*)"', l_str)
                    if m_txt: full_text.append(m_txt.group(1))
                elif l_str.startswith('done'): break
            if full_text and lbl not in texts:
                texts[lbl] = " ".join(full_text)
    except Exception:
        pass

print(f"Loaded {len(texts)} texts.")
