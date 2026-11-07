import re
with open('poketcg2-en/src/data/decks.asm', 'r', encoding='latin-1') as f:
    c = f.read()

m = re.search(r'StarterDeck:\s*\n\s*deck_list_start([\s\S]*?)deck_list_end', c)
if m:
    print(m.group(0))
