import re

def inspect_decks(file_path):
    with open(file_path, 'r', encoding='latin-1') as f:
        content = f.read()
    deck_blocks = re.findall(r'([A-Za-z0-9_]+Deck):\s*\n\s*deck_list_start([\s\S]*?)deck_list_end', content)
    res = []
    for dname, dbody in deck_blocks:
        items = re.findall(r'card_item\s+([A-Za-z0-9_]+),\s*(\d+)', dbody)
        energy_count = sum(int(c) for sym, c in items if 'ENERGY' in sym.upper())
        non_energy_items = [(sym, int(c)) for sym, c in items if 'ENERGY' not in sym.upper()]
        non_energy_total = sum(c for _, c in non_energy_items)
        res.append((dname, non_energy_total, energy_count, non_energy_items))
    return res

d1 = inspect_decks('poketcg/src/data/decks.asm')
d2 = inspect_decks('poketcg2-en/src/data/decks.asm')

print(f"TCG1 decks: {len(d1)}")
print("Sample TCG1 non-energy counts:", [x[1] for x in d1[:10]])

print(f"TCG2 decks: {len(d2)}")
print("Sample TCG2 non-energy counts:", [x[1] for x in d2[:10]])
