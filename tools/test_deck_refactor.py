import re, glob
from collections import Counter, defaultdict

# Import pipeline helper
from test_cards_pipeline import test_full_pipeline

cards_list, label_to_card = test_full_pipeline()

def test_deck_refactor():
    deck_sources = ['poketcg/src/data/decks.asm', 'poketcg2-en/src/data/decks.asm']
    
    unique_decks = {}
    for fpath in deck_sources:
        with open(fpath, 'r', encoding='latin-1') as f:
            content = f.read()
        deck_blocks = re.findall(r'([A-Za-z0-9_]+Deck):\s*\n\s*deck_list_start([\s\S]*?)deck_list_end', content)
        for dname, dbody in deck_blocks:
            if dname not in unique_decks:
                unique_decks[dname] = dbody

    print(f"Total unique original 60-card decks found: {len(unique_decks)}")

    thematic_decks = []
    leftover_pool = Counter()

    for dname, dbody in unique_decks.items():
        readable_base = re.sub(r'([a-z])([A-Z])', r'\1 \2', dname.replace('Deck', '')).strip()
        items = re.findall(r'card_item\s+([A-Za-z0-9_]+),\s*(\d+)', dbody)
        
        # Collect non-energy cards by energy type
        deck_cards = []
        cards_by_type = defaultdict(list)
        trainers = []

        for sym, cnt_str in items:
            if 'ENERGY' in sym.upper():
                continue
            cnt = int(cnt_str)
            card = label_to_card.get(sym) or label_to_card.get(sym.upper())
            if not card:
                cl = re.sub(r'_LV\d+', '', sym.upper())
                card = label_to_card.get(cl)
            if card:
                cid = card['cardId']
                if 'TRAINER' in card['card_type']:
                    trainers.extend([cid] * cnt)
                else:
                    etype = card['energy_type']
                    cards_by_type[etype].extend([cid] * cnt)
                deck_cards.extend([cid] * cnt)

        if len(deck_cards) < 10:
            continue

        types_present = sorted(cards_by_type.keys(), key=lambda t: len(cards_by_type[t]), reverse=True)

        # Decide whether to create 1 or 2 variants
        # Variant 1: primary type focus
        # Variant 2: secondary type focus (if >= 8 cards of secondary type), or secondary evolution line
        has_secondary_type = len(types_present) >= 2 and len(cards_by_type[types_present[1]]) >= 6
        
        v1_cards = []
        v2_cards = []

        if has_secondary_type:
            # Dual-type deck: Split by type!
            # V1 takes Type 1 pokemons (up to 2 copies each)
            t1_counts = Counter(cards_by_type[types_present[0]])
            for cid, c_cnt in t1_counts.items():
                v1_cards.extend([cid] * min(2, c_cnt))
                rem = c_cnt - min(2, c_cnt)
                if rem > 0: leftover_pool[cid] += rem

            # V2 takes Type 2 pokemons (up to 2 copies each)
            t2_counts = Counter(cards_by_type[types_present[1]])
            for cid, c_cnt in t2_counts.items():
                v2_cards.extend([cid] * min(2, c_cnt))
                rem = c_cnt - min(2, c_cnt)
                if rem > 0: leftover_pool[cid] += rem

            # Distribute trainers evenly
            tr_counts = Counter(trainers)
            for cid, tr_cnt in tr_counts.items():
                take1 = min(2, tr_cnt // 2 + tr_cnt % 2)
                take2 = min(2, tr_cnt - take1)
                v1_cards.extend([cid] * take1)
                v2_cards.extend([cid] * take2)
                rem = tr_cnt - (take1 + take2)
                if rem > 0: leftover_pool[cid] += rem

        else:
            # Mono-type deck: check if we have enough distinct cards (>= 12 unique) to make 2 distinct lines
            all_pkmn_counts = Counter()
            for t in types_present:
                all_pkmn_counts.update(cards_by_type[t])

            if len(all_pkmn_counts) >= 6:
                # Split pokemon lines into two groups
                pkmn_items = list(all_pkmn_counts.items())
                half = len(pkmn_items) // 2
                group1 = pkmn_items[:half]
                group2 = pkmn_items[half:]

                for cid, c_cnt in group1:
                    v1_cards.extend([cid] * min(2, c_cnt))
                    rem = c_cnt - min(2, c_cnt)
                    if rem > 0: leftover_pool[cid] += rem

                for cid, c_cnt in group2:
                    v2_cards.extend([cid] * min(2, c_cnt))
                    rem = c_cnt - min(2, c_cnt)
                    if rem > 0: leftover_pool[cid] += rem

                # Distribute trainers
                tr_counts = Counter(trainers)
                for cid, tr_cnt in tr_counts.items():
                    take1 = min(2, tr_cnt // 2 + tr_cnt % 2)
                    take2 = min(2, tr_cnt - take1)
                    v1_cards.extend([cid] * take1)
                    v2_cards.extend([cid] * take2)
                    rem = tr_cnt - (take1 + take2)
                    if rem > 0: leftover_pool[cid] += rem
            else:
                # Single variant only (to avoid creating clones!)
                for cid, c_cnt in all_pkmn_counts.items():
                    v1_cards.extend([cid] * min(2, c_cnt))
                    rem = c_cnt - min(2, c_cnt)
                    if rem > 0: leftover_pool[cid] += rem
                for cid, tr_cnt in Counter(trainers).items():
                    v1_cards.extend([cid] * min(2, tr_cnt))
                    rem = tr_cnt - min(2, tr_cnt)
                    if rem > 0: leftover_pool[cid] += rem

        # Function to balance a variant to exactly 20 cards
        def finalize_variant(v_list, name):
            # Ensure at least 1 real basic
            has_basic = any(cards_list[c - 1]['card_type'] == 'CARD_TYPE_POKEMON_BASIC' and 'Fossil' not in cards_list[c - 1]['name'] for c in v_list)
            if not has_basic:
                # Find basic in cards_by_type
                for t in types_present:
                    for cid in cards_by_type[t]:
                        if cards_list[cid - 1]['card_type'] == 'CARD_TYPE_POKEMON_BASIC' and 'Fossil' not in cards_list[cid - 1]['name']:
                            v_list.insert(0, cid)
                            has_basic = True
                            break
                    if has_basic: break

            # Trim to 20 if > 20
            if len(v_list) > 20:
                for c in v_list[20:]:
                    leftover_pool[c] += 1
                v_list = v_list[:20]

            # Pad to 20 if < 20 by using allowed duplicate cards (max 2 copies)
            while len(v_list) < 20:
                added = False
                for c in list(v_list):
                    if v_list.count(c) < 2:
                        v_list.append(c)
                        added = True
                        if len(v_list) == 20: break
                if not added:
                    # Borrow a basic or trainer from deck
                    for c in deck_cards:
                        if v_list.count(c) < 2:
                            v_list.append(c)
                            added = True
                            if len(v_list) == 20: break
                if not added:
                    break

            if len(v_list) == 20:
                return {'name': name[:15], 'cards': v_list}
            return None

        res1 = finalize_variant(v1_cards, f"{readable_base} 1" if v2_cards else readable_base)
        if res1: thematic_decks.append(res1)
        if v2_cards:
            res2 = finalize_variant(v2_cards, f"{readable_base} 2")
            if res2: thematic_decks.append(res2)

    print(f"Generated {len(thematic_decks)} pruned distinct variants.")
    print(f"Leftover cards in pool: {sum(leftover_pool.values())} across {len(leftover_pool)} unique cards.")

    # 4. Synthesize complementary thematic decks from leftover pool
    # Group leftovers by energy type
    leftovers_by_type = defaultdict(list)
    for cid, cnt in leftover_pool.items():
        etype = cards_list[cid - 1]['energy_type']
        leftovers_by_type[etype].extend([cid] * cnt)

    theme_names = {
        'ENERGY_GRASS': 'Grass Bloom',
        'ENERGY_FIRE': 'Fire Surge',
        'ENERGY_WATER': 'Water Torrent',
        'ENERGY_LIGHTNING': 'Lightning Spark',
        'ENERGY_PSYCHIC': 'Psychic Mind',
        'ENERGY_FIGHTING': 'Fight Beatdown',
        'ENERGY_COLORLESS': 'Colorless Aggro',
        'ENERGY_DARKNESS': 'Rocket Darkness',
    }

    comp_decks_created = 0
    for etype, name in theme_names.items():
        pool = leftovers_by_type[etype]
        counts = Counter(pool)
        deck = []
        for cid, cnt in counts.items():
            if deck.count(cid) < 2:
                take = min(2 - deck.count(cid), cnt)
                deck.extend([cid] * take)
                leftover_pool[cid] -= take
                if len(deck) == 20: break

        # Check if reached 20 and has basic
        if len(deck) >= 15:
            # Ensure basic
            if not any(cards_list[c - 1]['card_type'] == 'CARD_TYPE_POKEMON_BASIC' for c in deck):
                # find a basic
                for cid in pool:
                    if cards_list[cid - 1]['card_type'] == 'CARD_TYPE_POKEMON_BASIC':
                        deck.insert(0, cid)
                        break
            while len(deck) < 20:
                for c in list(deck):
                    if deck.count(c) < 2:
                        deck.append(c)
                        if len(deck) == 20: break
                if len(deck) < 20: break
            
            if len(deck) == 20:
                thematic_decks.append({'name': name, 'cards': deck})
                comp_decks_created += 1

    remaining_leftovers = sum(cnt for cnt in leftover_pool.values() if cnt > 0)
    print(f"Created {comp_decks_created} complementary thematic decks!")
    print(f"Remaining final leftovers: {remaining_leftovers}")
    print(f"Total thematic decks final: {len(thematic_decks)}")

test_deck_refactor()
