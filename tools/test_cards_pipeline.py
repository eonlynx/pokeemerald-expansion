import re
import glob
from collections import Counter, defaultdict

# Let's write the complete deck splitting and card deduplication logic
def test_full_pipeline():
    # 1. Moves
    moves_set = set()
    with open('include/constants/moves.h', 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            m = re.search(r'\b(MOVE_[A-Z0-9_]+)\b', line)
            if m: moves_set.add(m.group(1))

    # 2. Species
    species_map = {}
    with open('include/constants/species.h', 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            m = re.search(r'\bSPECIES_([A-Z0-9_]+)\b', line)
            if m:
                name = m.group(1).replace('_', '').upper()
                species_map[name] = "SPECIES_" + m.group(1)

    # 3. Texts
    texts = {}
    text_files = glob.glob('poketcg/src/text/text*.asm') + glob.glob('poketcg2-en/src/text/text*.asm')
    for tf in text_files:
        with open(tf, 'r', encoding='latin-1') as f:
            content = f.read()
        for block in re.split(r'\n(?=[A-Za-z0-9_]+:)', content):
            lines = block.strip().splitlines()
            if not lines: continue
            m_lbl = re.match(r'^([A-Za-z0-9_]+):', lines[0])
            if not m_lbl: continue
            lbl = m_lbl.group(1)
            full_text = []
            for l in lines[1:]:
                l_str = l.strip()
                if l_str.startswith('text "') or l_str.startswith('line "'):
                    m_txt = re.match(r'^(?:text|line)\s+"([^"]*)"', l_str)
                    if m_txt: full_text.append(m_txt.group(1))
                elif l_str.startswith('done'): break
            if full_text and lbl not in texts:
                texts[lbl] = " ".join(full_text)

    # 4. Energy enums
    energy_name_to_enum = {
        'GRASS': 'ENERGY_GRASS', 'FIRE': 'ENERGY_FIRE', 'WATER': 'ENERGY_WATER',
        'LIGHTNING': 'ENERGY_LIGHTNING', 'PSYCHIC': 'ENERGY_PSYCHIC',
        'FIGHTING': 'ENERGY_FIGHTING', 'DARKNESS': 'ENERGY_DARKNESS',
        'METAL': 'ENERGY_METAL', 'COLORLESS': 'ENERGY_COLORLESS'
    }
    type_to_energy_enum = {
        'TYPE_PKMN_GRASS': 'ENERGY_GRASS', 'TYPE_PKMN_FIRE': 'ENERGY_FIRE',
        'TYPE_PKMN_WATER': 'ENERGY_WATER', 'TYPE_PKMN_LIGHTNING': 'ENERGY_LIGHTNING',
        'TYPE_PKMN_PSYCHIC': 'ENERGY_PSYCHIC', 'TYPE_PKMN_FIGHTING': 'ENERGY_FIGHTING',
        'TYPE_PKMN_COLORLESS': 'ENERGY_COLORLESS', 'TYPE_PKMN_DARKNESS': 'ENERGY_DARKNESS',
        'TYPE_PKMN_METAL': 'ENERGY_METAL',
    }
    weakness_to_energy_enum = {
        'WR_FIRE': 'ENERGY_FIRE', 'WR_GRASS': 'ENERGY_GRASS', 'WR_LIGHTNING': 'ENERGY_LIGHTNING',
        'WR_WATER': 'ENERGY_WATER', 'WR_FIGHTING': 'ENERGY_FIGHTING', 'WR_PSYCHIC': 'ENERGY_PSYCHIC',
        'WR_DARKNESS': 'ENERGY_DARKNESS', 'WR_METAL': 'ENERGY_METAL',
        'NONE': 'NUM_ENERGY_TYPES', '0': 'NUM_ENERGY_TYPES'
    }
    known_supporters = {
        'PROFESSOR_OAK', 'BILL', 'LASS', 'GAMBLER', 'MR_FUJI',
        'IMPOSTER_PROFESSOR_OAK', 'SABRINA', 'ERIKA', 'BLAINE', 'BROCK',
        'MISTY', 'LT_SURGE', 'KOGA', 'GIOVANNI'
    }
    item_equiv_map = {
        'POTION': 'ITEM_POTION', 'SUPER_POTION': 'ITEM_SUPER_POTION',
        'FULL_HEAL': 'ITEM_FULL_HEAL', 'REVIVE': 'ITEM_REVIVE',
        'POKE_BALL': 'ITEM_POKE_BALL', 'ENERGY_SEARCH': 'ITEM_POKE_BALL',
    }

    # 5. Extract cards strictly from poketcg2-en (the canonical full 445 card set)
    cards_list = []
    seen_labels = set()
    label_to_card = {}
    alias_map = {} # Maps old GB1 labels & uppercase aliases to new card dict

    def parse_card_file(file_path):
        with open(file_path, 'r', encoding='latin-1') as f:
            content = f.read()

        card_chunks = re.split(r'\n(?=[A-Za-z0-9_]+Card:)', content)
        for chunk in card_chunks:
            lines = chunk.strip().splitlines()
            if not lines: continue
            m_card = re.match(r'^([A-Za-z0-9_]+)Card:', lines[0])
            if not m_card: continue
            label = m_card.group(1)
            if label.upper() in seen_labels:
                continue

            card_type_raw = None
            name_lbl = None
            rarity_raw = 'CIRCLE'
            hp = 0
            stage_raw = 'BASIC'
            preevo_lbl = None
            retreat = 0
            weakness_raw = 'NONE'
            pkmn_id_const = None
            atk1_name = None
            atk1_dmg = 0
            atk1_is_power = False
            atk1_costs = {e: 0 for e in energy_name_to_enum.values()}
            atk2_name = None
            atk2_dmg = 0
            atk2_costs = {e: 0 for e in energy_name_to_enum.values()}

            in_atk = 0
            for l in lines[1:]:
                l_code = l.split(';')[0].strip()
                if not l_code: continue

                if l_code.startswith('db TYPE_'):
                    parts = l_code.split()
                    card_type_raw = parts[1]
                elif l_code.startswith('tx '):
                    parts = l_code.split()
                    t_lbl = parts[1]
                    if name_lbl is None:
                        name_lbl = t_lbl
                    elif card_type_raw and 'TYPE_PKMN' in card_type_raw and preevo_lbl is None and ('STAGE' in stage_raw or 'EVOLUTION' in stage_raw):
                        preevo_lbl = t_lbl
                    elif in_atk == 1 and atk1_name is None:
                        atk1_name = texts.get(t_lbl, t_lbl)
                    elif in_atk == 2 and atk2_name is None:
                        atk2_name = texts.get(t_lbl, t_lbl)
                elif 'attack 1' in l:
                    in_atk = 1
                elif 'attack 2' in l:
                    in_atk = 2
                elif l_code.startswith('energy '):
                    e_parts = l_code[7:].split(',')
                    curr_cost_dict = atk1_costs if in_atk == 1 else atk2_costs
                    i = 0
                    while i < len(e_parts):
                        etype = e_parts[i].strip()
                        if etype == '0': break
                        cnt = 1
                        if i + 1 < len(e_parts) and e_parts[i+1].strip().isdigit():
                            cnt = int(e_parts[i+1].strip())
                            i += 2
                        else:
                            i += 1
                        if etype in energy_name_to_enum:
                            curr_cost_dict[energy_name_to_enum[etype]] += cnt
                elif l_code.startswith('db ') and 'hp' in l:
                    m_hp = re.search(r'db\s+(\d+)', l_code)
                    if m_hp: hp = int(m_hp.group(1))
                elif l_code.startswith('db ') and ('BASIC' in l_code or 'STAGE' in l_code):
                    m_st = re.search(r'db\s+([A-Z0-9_]+)', l_code)
                    if m_st: stage_raw = m_st.group(1)
                elif l_code.startswith('db ') and 'retreat cost' in l:
                    m_ret = re.search(r'db\s+(\d+)', l_code)
                    if m_ret: retreat = int(m_ret.group(1))
                elif l_code.startswith('db WR_'):
                    m_w = re.search(r'db\s+(WR_[A-Z0-9_]+|NONE)', l_code)
                    if m_w: weakness_raw = m_w.group(1)
                elif l_code.startswith('db ') and ('STAR' in l_code or 'DIAMOND' in l_code or 'CIRCLE' in l_code or 'PROMO' in l_code):
                    m_r = re.search(r'db\s+([A-Z0-9_|]+)', l_code)
                    if m_r: rarity_raw = m_r.group(1)
                elif l_code.startswith('db ') and ('damage' in l or 'damage' in l_code):
                    m_d = re.search(r'db\s+(\d+)', l_code)
                    if m_d:
                        dmg = int(m_d.group(1))
                        if in_atk == 1: atk1_dmg = dmg
                        elif in_atk == 2: atk2_dmg = dmg
                elif 'POKEMON_POWER' in l_code:
                    atk1_is_power = True
                elif l_code.startswith('db ') or l_code.startswith('dw '):
                    # Check for constant ID symbol like dw BULBASAUR_LV12
                    parts = l_code.split()
                    if len(parts) >= 2 and re.match(r'^[A-Z0-9_]+$', parts[1]) and not any(k in parts[1] for k in ['STAGE', 'TYPE', 'NONE', 'DAMAGE', 'ATK_', 'WR_', 'GFX', 'COLORLESS', 'GRASS', 'FIRE', 'WATER', 'LIGHTNING', 'PSYCHIC', 'FIGHTING']):
                        pkmn_id_const = parts[1]

            if not card_type_raw or 'ENERGY' in card_type_raw or 'Energy' in label:
                continue

            seen_labels.add(label.upper())

            card_name = texts.get(name_lbl, label)
            card_name = card_name.replace('â™€', ' F').replace('â™‚', ' M').replace('♀', ' F').replace('♂', ' M')
            card_name = card_name.replace('Lv ', 'Lv').replace('Lv.', 'Lv')
            if 'PokeBall' in label or 'PokeBall' in str(name_lbl):
                card_name = "Poké Receiver"

            card_type_enum = "CARD_TYPE_POKEMON_BASIC"
            if 'TYPE_TRAINER' in card_type_raw:
                if any(s in label.upper() or s in str(pkmn_id_const) for s in known_supporters):
                    card_type_enum = "CARD_TYPE_TRAINER_SUPPORTER"
                else:
                    card_type_enum = "CARD_TYPE_TRAINER_ITEM"
            elif 'STAGE1' in stage_raw:
                card_type_enum = "CARD_TYPE_POKEMON_STAGE1"
            elif 'STAGE2' in stage_raw:
                card_type_enum = "CARD_TYPE_POKEMON_STAGE2"
            else:
                card_type_enum = "CARD_TYPE_POKEMON_BASIC"

            species_const = "SPECIES_NONE"
            if 'TYPE_PKMN' in card_type_raw:
                clean_s = re.sub(r'Lv\d+', '', label).replace('Card', '').replace('_', '').upper()
                for p in ['DARK', 'ROCKETS', 'BLAINES', 'BROCKS', 'MISTYS', 'LTSURGES', 'SABRINAS', 'ERIKAS', 'KOGAS', 'GIOVANNIS', 'GRS']:
                    if clean_s.startswith(p):
                        clean_s = clean_s[len(p):]
                species_const = species_map.get(clean_s, "SPECIES_NONE")
                if species_const == "SPECIES_NONE":
                    for sm_k, sm_v in species_map.items():
                        if sm_k in clean_s or clean_s in sm_k:
                            species_const = sm_v
                            break

            preevo_species_const = "SPECIES_NONE"
            if preevo_lbl:
                preevo_text = texts.get(preevo_lbl, preevo_lbl).replace(' ', '').upper()
                preevo_species_const = species_map.get(preevo_text, "SPECIES_NONE")

            energy_type_enum = type_to_energy_enum.get(card_type_raw, "ENERGY_COLORLESS")
            weakness_enum = weakness_to_energy_enum.get(weakness_raw, "NUM_ENERGY_TYPES")
            is_shiny = "TRUE" if any(r in rarity_raw for r in ['STAR', 'PROMO', 'GB', 'HOLO']) or 'Lv' in label else "FALSE"

            equiv_item = "ITEM_NONE"
            for k_item, v_item in item_equiv_map.items():
                if k_item in label.upper() or (pkmn_id_const and k_item in str(pkmn_id_const)):
                    equiv_item = v_item
                    break

            def map_move(m_name):
                if not m_name: return "MOVE_NONE"
                cl = re.sub(r'[^A-Za-z0-9]', '', m_name).upper()
                if f"MOVE_{cl}" in moves_set: return f"MOVE_{cl}"
                return "MOVE_TACKLE"

            move1_const = map_move(atk1_name) if atk1_name and not atk1_is_power else "MOVE_NONE"
            move2_const = map_move(atk2_name) if atk2_name else "MOVE_NONE"

            weight = 50
            if 'STAR' in rarity_raw: weight = 10
            elif 'DIAMOND' in rarity_raw: weight = 25
            elif 'PROMO' in rarity_raw: weight = 5

            card_obj = {
                'label': label,
                'const_name': f"CARD_{label.upper()}",
                'name': card_name,
                'species': species_const,
                'preevo_species': preevo_species_const,
                'equiv_item': equiv_item,
                'card_type': card_type_enum,
                'energy_type': energy_type_enum,
                'weakness_type': weakness_enum,
                'retreat_cost': retreat,
                'max_hp': hp,
                'pokemon_power': 1 if atk1_is_power else 0,
                'move1': move1_const,
                'move2': move2_const,
                'move1_costs': atk1_costs,
                'move2_costs': atk2_costs,
                'encounter_weight': weight,
                'is_shiny': is_shiny,
                'pkmn_id_const': pkmn_id_const or label.upper()
            }
            cards_list.append(card_obj)
            label_to_card[label] = card_obj
            label_to_card[label.upper()] = card_obj
            if pkmn_id_const:
                label_to_card[pkmn_id_const] = card_obj

    parse_card_file('poketcg2-en/src/data/cards1.asm')
    parse_card_file('poketcg2-en/src/data/cards2.asm')
    print(f"Loaded {len(cards_list)} unique non-energy cards.")

    # Assign 1..N cardIds
    for idx, c in enumerate(cards_list, start=1):
        c['cardId'] = idx

    # Build fallback mapping for TCG1 symbols: e.g. BULBASAUR -> BulbasaurLv13
    for c in cards_list:
        lbl_clean = re.sub(r'Lv\d+', '', c['label']).upper()
        if lbl_clean not in label_to_card:
            label_to_card[lbl_clean] = c

    return cards_list, label_to_card

test_full_pipeline()
