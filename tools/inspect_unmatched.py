import re

from inspect_cards_tcg1_tcg2 import tcg1, tcg2

unmatched_tcg1 = set(tcg1.keys()) - set(tcg2.keys())
print(f"Unmatched TCG1: {len(unmatched_tcg1)}")
sample = list(unmatched_tcg1)[:20]
print("Sample unmatched:", sample)

# Check if appending or removing Lv matches
found_with_lv = 0
for u in unmatched_tcg1:
    candidates = [k for k in tcg2.keys() if k.startswith(u) and 'Lv' in k]
    if candidates:
        found_with_lv += 1
print(f"Found in TCG2 with Lv suffix: {found_with_lv} / {len(unmatched_tcg1)}")
