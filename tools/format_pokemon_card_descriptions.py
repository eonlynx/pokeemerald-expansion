#!/usr/bin/env python3
import re

def update_descriptions():
    with open('src/data/tcg_cards.h', 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract card info for cards 1 to 381
    card_blocks = re.findall(r'\[(\d+)\]\s*=\s*\{([^}]+)\}', content)
    card_info = {}
    for cid_str, body in card_blocks:
        cid = int(cid_str)
        if cid == 0 or cid > 381:
            continue
        hp_m = re.search(r'\.maxHp\s*=\s*(\d+)', body)
        type_m = re.search(r'\.cardType\s*=\s*([A-Za-z0-9_]+)', body)
        hp = int(hp_m.group(1)) if hp_m else 40
        ctype = type_m.group(1) if type_m else 'CARD_TYPE_POKEMON_BASIC'
        stage = 'Basic'
        if 'STAGE1' in ctype:
            stage = 'Stage 1'
        elif 'STAGE2' in ctype:
            stage = 'Stage 2'
        card_info[cid] = (hp, stage)

    print(f"Loaded info for {len(card_info)} Pokémon cards.")

    # Update sCardDesc_1 .. sCardDesc_381
    for cid in range(1, 382):
        if cid not in card_info:
            continue
        hp, stage = card_info[cid]
        new_desc_text = f"Base Set No. {cid}\\nHP: {hp} - {stage} PKMN"
        # Match across any newlines
        pattern = re.compile(rf'static const u8 sCardDesc_{cid}\[\] = _\([\s\S]*?\);')
        # In string replacement, escape the backslash so it writes \n to the file
        replacement = f'static const u8 sCardDesc_{cid}[] = _("{new_desc_text}");'.replace('\\', '\\\\')
        content, count = pattern.subn(replacement, content, count=1)
        if count == 0:
            print(f"Warning: could not replace sCardDesc_{cid}")

    with open('src/data/tcg_cards.h', 'w', encoding='utf-8') as f:
        f.write(content)

    print("Updated all Pokémon card descriptions in src/data/tcg_cards.h successfully!")

if __name__ == '__main__':
    update_descriptions()
