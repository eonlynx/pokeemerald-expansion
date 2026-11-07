import re
from collections import Counter

# Let's write the repair logic
def fix_deck_evolution_chains(card_ids, cards_dict):
    # card_ids is a list of 20 ints
    # cards_dict is map of cid -> card info
    
    # We loop until no orphans remain
    deck = list(card_ids)
    
    # Map species to a Basic cardId
    species_to_basic_id = {}
    species_to_stage1_id = {}
    for cid, cinfo in cards_dict.items():
        if cinfo['cardType'] == 'CARD_TYPE_POKEMON_BASIC' and 'Fossil' not in cinfo['name']:
            species_to_basic_id[cinfo['species']] = cid
        elif cinfo['cardType'] == 'CARD_TYPE_POKEMON_STAGE1':
            species_to_stage1_id[cinfo['species']] = cid

    # Fallback support cards: Bill (418), Potion (386), Switch (408)
    fallback_supports = [418, 386, 408]

    changed = True
    passes = 0
    while changed and passes < 10:
        changed = False
        passes += 1
        
        deck_species = set(cards_dict[c]['species'] for c in deck)
        
        # Check from Stage 2 down to Stage 1
        for idx in range(len(deck)):
            cid = deck[idx]
            cinfo = cards_dict[cid]
            
            if cinfo['cardType'] == 'CARD_TYPE_POKEMON_STAGE2':
                # Check if Stage 1 is in deck
                s1_needed = cinfo['preEvoSpecies']
                if s1_needed not in deck_species:
                    # Try to add Stage 1, or replace this Stage 2 with its Basic or fallback
                    if s1_needed in species_to_stage1_id:
                        # Can we add it? Check if we have a duplicate or non-essential card
                        # Otherwise replace this unplayable Stage 2
                        deck[idx] = species_to_stage1_id[s1_needed]
                        changed = True
                        break
                    else:
                        deck[idx] = 418 # Bill
                        changed = True
                        break
                        
                # Check if Basic is in deck
                s1_cid = [c for c in deck if cards_dict[c]['species'] == s1_needed][0]
                basic_needed = cards_dict[s1_cid]['preEvoSpecies']
                if basic_needed not in deck_species:
                    if basic_needed in species_to_basic_id:
                        deck[idx] = species_to_basic_id[basic_needed]
                        changed = True
                        break
                    else:
                        deck[idx] = 418 # Bill
                        changed = True
                        break

            elif cinfo['cardType'] == 'CARD_TYPE_POKEMON_STAGE1':
                basic_needed = cinfo['preEvoSpecies']
                if basic_needed not in deck_species:
                    if basic_needed in species_to_basic_id:
                        deck[idx] = species_to_basic_id[basic_needed]
                        changed = True
                        break
                    else:
                        deck[idx] = 386 # Potion
                        changed = True
                        break

    # Also enforce max 2 copies per species
    sp_counts = Counter()
    for idx in range(len(deck)):
        cid = deck[idx]
        sp = cards_dict[cid]['species']
        if sp != 'SPECIES_NONE':
            sp_counts[sp] += 1
            if sp_counts[sp] > 2:
                # Replace excess copy with Bill or Potion
                deck[idx] = 418 if deck.count(418) < 2 else 386
                sp_counts[sp] -= 1

    return deck

print("Repair function defined.")
