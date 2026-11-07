import re

with open('poketcg/src/data/decks.asm', 'r', encoding='latin-1') as f:
    tcg1_decks = f.read()

deck_items = set(re.findall(r'card_item\s+([A-Za-z0-9_]+)', tcg1_decks))
print(f"Total unique card symbols in TCG1 decks: {len(deck_items)}")

# Check against TCG2 non-energy cards
from count_non_energy import all_cards
all_tcg2_set = set(all_cards)
all_tcg2_set_clean = {c.replace('Card', ''): c for c in all_cards}

unmapped = []
for item in deck_items:
    if 'ENERGY' in item.upper():
        continue
    item_clean = item.replace('Card', '')
    if item_clean in all_tcg2_set_clean:
        continue
    # Check if starts with
    cands = [k for k in all_tcg2_set_clean if k.startswith(item_clean)]
    if cands:
        # print(f"Mapped {item_clean} -> {cands}")
        pass
    else:
        unmapped.append(item)

print(f"Unmapped items: {unmapped}")
