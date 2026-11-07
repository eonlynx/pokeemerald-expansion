import re
from collections import Counter

with open('src/data/tcg_cards.h', 'r', encoding='utf-8') as f:
    text = f.read()

# Parse card definitions cleanly
cards = {}
for block in text.split('    [')[1:]:
    lines = block.strip().splitlines()
    if not lines: continue
    m_id = re.match(r'^(\d+)\]\s*=\s*\{', lines[0])
    if not m_id: continue
    cid = int(m_id.group(1))
    if cid == 0: continue
    
    spec_m = re.search(r'\.species = ([A-Z0-9_]+)', block)
    preevo_m = re.search(r'\.preEvoSpecies = ([A-Z0-9_]+)', block)
    ctype_m = re.search(r'\.cardType = ([A-Z0-9_]+)', block)
    name_m = re.search(r'sCardName_' + str(cid) + r'\[\] = _\("([^"]*)"\);', text)
    
    cards[cid] = {
        'cardId': cid,
        'name': name_m.group(1) if name_m else '',
        'species': spec_m.group(1) if spec_m else 'SPECIES_NONE',
        'preEvoSpecies': preevo_m.group(1) if preevo_m else 'SPECIES_NONE',
        'cardType': ctype_m.group(1) if ctype_m else 'CARD_TYPE_POKEMON_BASIC'
    }

print(f"Loaded {len(cards)} cards from src/data/tcg_cards.h")

# Load decks
with open('src/data/tcg_decks.h', 'r', encoding='utf-8') as f:
    decks_text = f.read()

deck_blocks = re.findall(r'\[(\d+)\] = \{[\s\S]*?\.name = _\("([^"]*)"\)[\s\S]*?\.cards = \{ ([^\}]+) \}', decks_text)
print(f"Found {len(deck_blocks)} decks in src/data/tcg_decks.h")

errors = []
for idx, dname, cards_str in deck_blocks:
    card_ids = [int(c.strip()) for c in cards_str.split(',') if c.strip()]
    
    # 1. Check size 20
    if len(card_ids) != 20:
        errors.append((dname, f"Deck has {len(card_ids)} cards instead of 20"))
        
    # 2. Check max 2 copies per species
    species_counts = Counter()
    for cid in card_ids:
        sp = cards[cid]['species']
        if sp != 'SPECIES_NONE':
            species_counts[sp] += 1
            if species_counts[sp] > 2:
                errors.append((dname, f"Species {sp} has {species_counts[sp]} copies (>2)"))
                
    # 3. Check at least 1 real basic
    has_real_basic = any(cards[c]['cardType'] == 'CARD_TYPE_POKEMON_BASIC' and 'Fossil' not in cards[c]['name'] for c in card_ids)
    if not has_real_basic:
        errors.append((dname, "No real basic Pokemon"))
        
    # 4. Check evolution chains
    deck_species = set(cards[c]['species'] for c in card_ids)
    for cid in card_ids:
        cinfo = cards[cid]
        if cinfo['cardType'] == 'CARD_TYPE_POKEMON_STAGE1':
            if cinfo['preEvoSpecies'] not in deck_species:
                errors.append((dname, f"Stage 1 {cinfo['name']} missing Basic pre-evo ({cinfo['preEvoSpecies']})"))
        elif cinfo['cardType'] == 'CARD_TYPE_POKEMON_STAGE2':
            # Check Stage 1 in deck
            stage1_candidates = [c for c in card_ids if cards[c]['species'] == cinfo['preEvoSpecies']]
            if not stage1_candidates:
                errors.append((dname, f"Stage 2 {cinfo['name']} missing Stage 1 pre-evo ({cinfo['preEvoSpecies']})"))
            else:
                # Check Basic in deck
                s1_info = cards[stage1_candidates[0]]
                if s1_info['preEvoSpecies'] not in deck_species:
                    errors.append((dname, f"Stage 2 {cinfo['name']} missing Basic pre-evo ({s1_info['preEvoSpecies']})"))

print(f"Validation finished. Total errors found: {len(errors)}")
for err in errors[:25]:
    print("  ", err)
