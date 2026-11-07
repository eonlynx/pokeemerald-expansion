import glob, re

from inspect_cards_tcg1_tcg2 import tcg2_1, tcg2_2

common = set(tcg2_1.keys()).intersection(set(tcg2_2.keys()))
print(f"Intersection between cards1 and cards2 in TCG2: {len(common)}")
if common:
    print("Common labels:", common)
