import glob, re

# Check poketcg cards vs poketcg2-en cards
with open('poketcg/src/data/cards.asm', 'r', encoding='latin-1') as f:
    tcg1_content = f.read()

with open('poketcg2-en/src/data/cards1.asm', 'r', encoding='latin-1') as f:
    tcg2_1 = f.read()

with open('poketcg2-en/src/data/cards2.asm', 'r', encoding='latin-1') as f:
    tcg2_2 = f.read()

tcg1_cards = re.findall(r'([A-Za-z0-9_]+Card):', tcg1_content)
tcg2_cards = re.findall(r'([A-Za-z0-9_]+Card):', tcg2_1) + re.findall(r'([A-Za-z0-9_]+Card):', tcg2_2)

print(f"TCG1 cards count: {len(tcg1_cards)}")
print(f"TCG2 cards count: {len(tcg2_cards)}")

# Check if TCG2 has cards that are identical to TCG1
# In TCG2, cards1.asm and cards2.asm hold the entire set of Pokemon Card GB2!
