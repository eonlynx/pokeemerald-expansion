import sys
from validate_decks_test import cards, deck_blocks
from test_deck_repair import fix_deck_evolution_chains
from collections import Counter

repaired_count = 0
still_broken = 0
for idx, dname, cards_str in deck_blocks:
    card_ids = [int(c.strip()) for c in cards_str.split(',') if c.strip()]
    fixed = fix_deck_evolution_chains(card_ids, cards)
    
    # Validate fixed
    has_basic = any(cards[c]['cardType'] == 'CARD_TYPE_POKEMON_BASIC' and 'Fossil' not in cards[c]['name'] for c in fixed)
    deck_species = set(cards[c]['species'] for c in fixed)
    
    errs = []
    if not has_basic:
        errs.append('no basic')
    if len(fixed) != 20:
        errs.append(f'size {len(fixed)}')
    
    sp_counts = Counter(cards[c]['species'] for c in fixed if cards[c]['species'] != 'SPECIES_NONE')
    for sp, cnt in sp_counts.items():
        if cnt > 2:
            errs.append(f'{sp} > 2')
        
    for cid in fixed:
        cinfo = cards[cid]
        cname = cinfo['name']
        if cinfo['cardType'] == 'CARD_TYPE_POKEMON_STAGE1':
            if cinfo['preEvoSpecies'] not in deck_species:
                errs.append(f"missing basic for {cname}")
        elif cinfo['cardType'] == 'CARD_TYPE_POKEMON_STAGE2':
            if cinfo['preEvoSpecies'] not in deck_species:
                errs.append(f"missing stage1 for {cname}")
            else:
                s1_cid = [c for c in fixed if cards[c]['species'] == cinfo['preEvoSpecies']][0]
                if cards[s1_cid]['preEvoSpecies'] not in deck_species:
                    errs.append(f"missing basic for {cname}")
                    
    if errs:
        still_broken += 1
        print(f"{dname} still has errors: {errs}")
    else:
        repaired_count += 1

print(f"Repaired successfully: {repaired_count} / {len(deck_blocks)}. Still broken: {still_broken}")
