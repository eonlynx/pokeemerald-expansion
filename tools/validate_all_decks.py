#!/usr/bin/env python3
"""
tools/validate_all_decks.py
Audits all TCG decks in the codebase for:
1. Exact 20-card size.
2. Max 2 copies per card ID and per Pokémon species.
3. At least 1 real Basic Pokémon (excluding Fossils).
4. Strict evolution integrity:
   - Stage 1 requires its specific Basic pre-evolution.
   - Stage 2 requires its Stage 1 AND its Basic pre-evolution.
5. All trainer deck mappings in gTrainerToDeckMap point to valid decks.
"""

import re
import sys
from collections import Counter

def load_cards_info():
    with open('src/data/tcg_cards.h', 'r', encoding='utf-8') as f:
        content = f.read()

    blocks = content.split('    [')
    cards = {}

    for b in blocks[1:]:
        m_id = re.match(r'^(\d+)\]\s*=\s*\{', b)
        if not m_id:
            continue
        cid = int(m_id.group(1))
        
        m_name = re.search(r'\.name\s*=\s*sCardName_\d+', b)
        m_spec = re.search(r'\.species\s*=\s*([A-Za-z0-9_]+)', b)
        m_prev = re.search(r'\.preEvoSpecies\s*=\s*([A-Za-z0-9_]+)', b)
        m_type = re.search(r'\.cardType\s*=\s*([A-Za-z0-9_]+)', b)
        
        cards[cid] = {
            'cardId': cid,
            'species': m_spec.group(1) if m_spec else 'SPECIES_NONE',
            'preEvoSpecies': m_prev.group(1) if m_prev else 'SPECIES_NONE',
            'cardType': m_type.group(1) if m_type else 'CARD_TYPE_POKEMON_BASIC',
        }

    # Also map cardId to name from include/constants/tcg_cards.h
    with open('include/constants/tcg_cards.h', 'r', encoding='utf-8') as f:
        for line in f:
            m = re.match(r'#define\s+CARD_([A-Za-z0-9_]+)\s+(\d+)', line)
            if m:
                cid = int(m.group(2))
                if cid in cards:
                    cards[cid]['name'] = m.group(1)

    return cards

def load_decks():
    with open('src/data/tcg_decks.h', 'r', encoding='utf-8') as f:
        content = f.read()

    thematic_decks = []
    blocks = re.findall(r'\[\d+\]\s*=\s*\{[\s\S]*?\.name\s*=\s*_\("([^"]+)"\)[\s\S]*?\.cards\s*=\s*\{([^\}]+)\}', content)
    for dname, cards_str in blocks:
        card_ids = [int(x.strip()) for x in cards_str.split(',') if x.strip()]
        thematic_decks.append((dname, card_ids))

    return thematic_decks

def load_trainer_map():
    with open('src/data/trainer_tcg_decks.h', 'r', encoding='utf-8') as f:
        content = f.read()

    mappings = re.findall(r'\[([A-Za-z0-9_]+)\]\s*=\s*(\d+)', content)
    return [(t_const, int(idx)) for t_const, idx in mappings]

def validate_all():
    cards = load_cards_info()
    thematic_decks = load_decks()
    trainer_map = load_trainer_map()

    total_decks = len(thematic_decks)
    orphan_errors = 0
    size_errors = 0
    basic_errors = 0
    copy_errors = 0
    mapping_errors = 0

    print(f"Loaded {len(cards)} TCG cards and {total_decks} thematic decks.")
    print("Auditing decks for size, basic count, copy limits, and evolution integrity...\n")

    for d_idx, (dname, deck) in enumerate(thematic_decks):
        # 1. Deck size
        if len(deck) != 20:
            print(f"ERROR: Deck {d_idx} ({dname}) has {len(deck)} cards (expected 20).")
            size_errors += 1

        # 2. Real Basic Pokémon
        has_real_basic = any(
            cards[c]['cardType'] == 'CARD_TYPE_POKEMON_BASIC' and 'FOSSIL' not in cards[c].get('name', '').upper()
            for c in deck
        )
        if not has_real_basic:
            print(f"ERROR: Deck {d_idx} ({dname}) has no real Basic Pokémon (Fossils do not count).")
            basic_errors += 1

        # 3. Copy limits (max 2 per card, max 2 per species)
        card_counts = Counter(deck)
        for cid, cnt in card_counts.items():
            if cnt > 2:
                print(f"ERROR: Deck {d_idx} ({dname}) has {cnt} copies of card {cid}.")
                copy_errors += 1

        species_counts = Counter(cards[c]['species'] for c in deck if cards[c]['species'] != 'SPECIES_NONE')
        for sp, cnt in species_counts.items():
            if cnt > 2:
                print(f"ERROR: Deck {d_idx} ({dname}) has {cnt} copies of species {sp}.")
                copy_errors += 1

        # 4. Evolution integrity
        deck_species = set(cards[c]['species'] for c in deck)
        for c in deck:
            cinfo = cards[c]
            ctype = cinfo['cardType']

            if ctype == 'CARD_TYPE_POKEMON_STAGE1':
                basic_req = cinfo['preEvoSpecies']
                if basic_req not in deck_species:
                    print(f"ERROR: Deck {d_idx} ({dname}) has Stage 1 {cinfo.get('name', c)} missing Basic {basic_req}.")
                    orphan_errors += 1

            elif ctype == 'CARD_TYPE_POKEMON_STAGE2':
                stage1_req = cinfo['preEvoSpecies']
                if stage1_req not in deck_species:
                    print(f"ERROR: Deck {d_idx} ({dname}) has Stage 2 {cinfo.get('name', c)} missing Stage 1 {stage1_req}.")
                    orphan_errors += 1
                else:
                    # Find Stage 1 card and check its Basic pre-evo
                    s1_cards = [cards[x] for x in deck if cards[x]['species'] == stage1_req]
                    basic_req = s1_cards[0]['preEvoSpecies']
                    if basic_req not in deck_species:
                        print(f"ERROR: Deck {d_idx} ({dname}) has Stage 2 {cinfo.get('name', c)} missing Basic {basic_req}.")
                        orphan_errors += 1

    # 5. Trainer mappings
    for t_const, deck_idx in trainer_map:
        if deck_idx >= total_decks:
            print(f"ERROR: Trainer {t_const} maps to out-of-range deck index {deck_idx}.")
            mapping_errors += 1

    total_errors = orphan_errors + size_errors + basic_errors + copy_errors + mapping_errors

    print("-" * 60)
    print(f"Validation Summary:")
    print(f"  Decks checked:              {total_decks}")
    print(f"  Trainer mappings checked:   {len(trainer_map)}")
    print(f"  Evolution orphan errors:    {orphan_errors}")
    print(f"  Size errors:                {size_errors}")
    print(f"  Basic mon errors:           {basic_errors}")
    print(f"  Copy limit errors:          {copy_errors}")
    print(f"  Trainer mapping errors:     {mapping_errors}")
    print("-" * 60)

    if total_errors == 0:
        print(f"[PASS] All {total_decks} decks validated: 0 evolution orphan errors, 0 size errors.")
        return 0
    else:
        print(f"[FAIL] Deck validation found {total_errors} errors!")
        return 1

if __name__ == '__main__':
    sys.exit(validate_all())
