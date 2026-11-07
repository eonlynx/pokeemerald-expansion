import re

with open('src/data/tcg_cards.h', 'r', encoding='utf-8') as f:
    text = f.read()

chunks = re.findall(r'\[(\d+)\] = \{([\s\S]*?)\n    \},', text)
trainers = []
for cid, body in chunks:
    if 'CARD_TYPE_TRAINER' in body:
        name_m = re.search(r'sCardName_' + cid + r'\[\] = _\("([^"]*)"\);', text)
        equiv_m = re.search(r'\.equivItemId = ([A-Z0-9_]+)', body)
        ctype_m = re.search(r'\.cardType = ([A-Z0-9_]+)', body)
        name = name_m.group(1) if name_m else ''
        equiv = equiv_m.group(1) if equiv_m else ''
        ctype = ctype_m.group(1) if ctype_m else ''
        trainers.append((cid, name, ctype, equiv))

print(f"Total Trainer cards: {len(trainers)}")
for t in trainers:
    print(t)
