import re
import sys
sys.path.append(r'C:\Users\Felipe\.gemini\antigravity\brain\23c80e6a-9d93-4d61-b44b-991963986a32\scratch')
from test_cards_pipeline import test_full_pipeline

cards_list, label_to_card = test_full_pipeline()

def parse_and_split_decks(file_path):
    with open(file_path, 'r', encoding='latin-1') as f:
        content = f.read()

    deck_blocks = re.findall(r'([A-Za-z0-9_]+Deck):\s*\n\s*deck_list_start([\s\S]*?)deck_list_end', content)
    
    generated_decks = []
    unused_log = []

    for dname, dbody in deck_blocks:
        readable_base = re.sub(r'([a-z])([A-Z])', r'\1 \2', dname.replace('Deck', '')).strip()
        
        # Collect non-energy items
        items = re.findall(r'card_item\s+([A-Za-z0-9_]+),\s*(\d+)', dbody)
        deck_cards_pool = []
        for sym, count_str in items:
            if 'ENERGY' in sym.upper():
                continue
            cnt = int(count_str)
            # Find card
            card = label_to_card.get(sym) or label_to_card.get(sym.upper())
            if not card:
                # Try stripping LV
                cl = re.sub(r'_LV\d+', '', sym.upper())
                card = label_to_card.get(cl)
            if card:
                deck_cards_pool.extend([card['cardId']] * cnt)

        if len(deck_cards_pool) < 10:
            continue

        # Strategy:
        # We want to create Variant 1 and Variant 2 if pool has enough cards (>= 30).
        # Otherwise Variant 1.
        
        # Count pool
        from collections import Counter
        pool_counts = Counter(deck_cards_pool)
        
        # Decide how many variants: if total cards >= 30, create 2 variants!
        num_variants = 2 if len(deck_cards_pool) >= 28 else 1
        
        variants = [[] for _ in range(num_variants)]
        
        # Distribute cards to variants
        # For each unique cardId in pool:
        for cid, total_available in pool_counts.items():
            card_info = cards_list[cid - 1]
            is_fossil = (card_info['name'] == 'Mysterious Fossil' or 'Fossil' in card_info['label'])
            
            if num_variants == 1:
                take = min(2, total_available)
                variants[0].extend([cid] * take)
                leftover = total_available - take
                if leftover > 0:
                    unused_log.append((readable_base, card_info['name'], leftover))
            else:
                # Distribute up to 2 to each variant
                # E.g. if total is 4: 2 to V1, 2 to V2
                # if total is 3: 2 to V1, 1 to V2
                # if total is 2: 1 to V1, 1 to V2
                # if total is 1: give to variant with fewer cards
                v1_take = 0
                v2_take = 0
                if total_available >= 4:
                    v1_take = 2
                    v2_take = 2
                    leftover = total_available - 4
                elif total_available == 3:
                    v1_take = 2
                    v2_take = 1
                    leftover = 0
                elif total_available == 2:
                    v1_take = 1
                    v2_take = 1
                    leftover = 0
                else: # 1
                    if len(variants[0]) <= len(variants[1]):
                        v1_take = 1
                    else:
                        v2_take = 1
                    leftover = 0
                
                variants[0].extend([cid] * v1_take)
                variants[1].extend([cid] * v2_take)
                if leftover > 0:
                    unused_log.append((readable_base, card_info['name'], leftover))

        # Now validate and adjust each variant to exactly 20 cards
        for v_idx in range(num_variants):
            v_cards = variants[v_idx]
            v_name = f"{readable_base} {v_idx + 1}" if num_variants > 1 else readable_base
            
            # Ensure at least 1 real basic
            has_real_basic = any(cards_list[c - 1]['card_type'] == 'CARD_TYPE_POKEMON_BASIC' and 'Fossil' not in cards_list[c - 1]['name'] for c in v_cards)
            if not has_real_basic:
                # Find a basic in the other variant or pool
                basics_in_pool = [c for c in deck_cards_pool if cards_list[c - 1]['card_type'] == 'CARD_TYPE_POKEMON_BASIC' and 'Fossil' not in cards_list[c - 1]['name']]
                if basics_in_pool:
                    v_cards.insert(0, basics_in_pool[0])
            
            # Trim if > 20
            if len(v_cards) > 20:
                # Put excess into unused_log
                excess = v_cards[20:]
                v_cards = v_cards[:20]
                for exc_id in excess:
                    unused_log.append((v_name, cards_list[exc_id - 1]['name'], 1))
            
            # If < 20, we can duplicate basics/items up to 2 copies each
            while len(v_cards) < 20:
                added = False
                for c in list(v_cards):
                    if v_cards.count(c) < 2:
                        v_cards.append(c)
                        added = True
                        if len(v_cards) == 20: break
                if not added:
                    # Borrow from pool or fallback
                    for c in deck_cards_pool:
                        if v_cards.count(c) < 2:
                            v_cards.append(c)
                            added = True
                            if len(v_cards) == 20: break
                if not added:
                    break

            if len(v_cards) == 20:
                generated_decks.append({
                    'name': v_name[:15],
                    'cards': v_cards
                })

    return generated_decks, unused_log

g_decks, u_log = parse_and_split_decks('poketcg/src/data/decks.asm')
print(f"Total 20-card variants generated from poketcg: {len(g_decks)}")
print(f"Total unused card entries logged: {len(u_log)}")
print("Sample generated decks:")
for d in g_decks[:6]:
    print(d['name'], d['cards'])
