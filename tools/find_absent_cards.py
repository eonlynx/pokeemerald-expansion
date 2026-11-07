import re
from inspect_cards_tcg1_tcg2 import tcg1, tcg2

print("Checking if any TCG1 card is genuinely absent from TCG2:")
absent = []
for lbl1, data1 in tcg1.items():
    # Check if exact lbl in tcg2
    if lbl1 in tcg2:
        continue
    # Check if case-insensitive match
    cands = [k for k in tcg2 if k.lower() == lbl1.lower()]
    if cands:
        continue
    # Check if any card in tcg2 has same prefix and same hp
    hp_cands = [k for k in tcg2 if k.startswith(lbl1) and tcg2[k]['hp'] == data1['hp']]
    if hp_cands:
        continue
    absent.append((lbl1, data1['hp']))

print(f"Absent cards count: {len(absent)}")
print("Absent cards:", absent)
