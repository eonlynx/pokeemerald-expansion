import re
from inspect_cards_tcg1_tcg2 import tcg1, tcg2

unmatched_tcg1 = set(tcg1.keys()) - set(tcg2.keys())
remaining = []
for u in unmatched_tcg1:
    candidates = [k for k in tcg2.keys() if k.startswith(u) and 'Lv' in k]
    if not candidates:
        remaining.append(u)
print("Remaining non-Lv unmatched:", remaining)
