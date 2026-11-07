#!/usr/bin/env python3
"""
tools/update_item_descriptions.py
Replaces all Spanish item descriptions in src/data/items.h with concise,
proper English descriptions that respect the GBA bag text boundaries:
- <= 3 lines
- <= 34 characters per line
"""
import re

ENGLISH_DESCRIPTIONS = {
    'ITEM_TCG_PROF_OAK': [
        'Discard your hand',
        'and draw up to 5',
        'cards from deck.',
    ],
    'ITEM_TCG_BILL': [
        'Draw 2 cards from',
        'your deck.',
    ],
    'ITEM_TCG_SWITCH': [
        'Switch active mon',
        'with 1 benched mon',
        'without retreat cost.',
    ],
    'ITEM_TCG_GUST_OF_WIND': [
        "Switch opponent's",
        'active mon with 1',
        'of their bench mons.',
    ],
    'ITEM_TCG_ENERGY_REMOVAL': [
        'Discard 1 energy',
        "attached to opponent's",
        'active Pokémon.',
    ],
    'ITEM_TCG_SUPER_ENERGY_REMOVAL': [
        'Discard 1 own energy',
        'to discard 2 from',
        "opponent's Pokémon.",
    ],
    'ITEM_TCG_PLUSPOWER': [
        'Adds +10 damage to',
        "active mon's next",
        'attack this turn.',
    ],
    'ITEM_TCG_DEFENDER': [
        'Reduces damage taken',
        'by -20 during next',
        "opponent's turn.",
    ],
    'ITEM_TCG_SCOOP_UP': [
        'Return 1 benched',
        'Pokémon and attached',
        'cards to your hand.',
    ],
    'ITEM_TCG_SUPER_SCOOP_UP': [
        'Flip a coin. If heads,',
        'return 1 Pokémon and',
        'its cards to hand.',
    ],
    'ITEM_TCG_COMPUTER_SEARCH': [
        'Discard 2 cards to',
        'search your deck',
        'for any 1 card.',
    ],
    'ITEM_TCG_GAMBLER': [
        'Flip coin: heads draws',
        '8 cards; tails draws',
        'only 1 card.',
    ],
    'ITEM_TCG_MAINTENANCE': [
        'Shuffle 2 cards from',
        'hand into deck to',
        'draw 1 card.',
    ],
    'ITEM_TCG_ITEM_FINDER': [
        'Discard 2 cards to',
        'recover 1 Item from',
        'your discard pile.',
    ],
    'ITEM_TCG_DEVOLUTION_SPRAY': [
        'Devolve 1 of your',
        'Pokémon to its',
        'previous stage.',
    ],
    'ITEM_TCG_CLEFAIRY_DOLL': [
        'Doll with 10 HP that',
        'acts as a Basic mon.',
        'Gives no prize.',
    ],
    'ITEM_TCG_MYSTERIOUS_FOSSIL': [
        'Fossil with 10 HP',
        'that can evolve into',
        'Omanyte or Kabuto.',
    ],
    'ITEM_TCG_POKEMON_TRADER': [
        'Trade 1 Pokémon in',
        'hand for 1 Pokémon',
        'from your deck.',
    ],
    'ITEM_TCG_POKEMON_BREEDER': [
        'Evolve a Basic mon',
        'directly to Stage 2',
        'from your hand.',
    ],
    'ITEM_TCG_POKEMON_CENTER': [
        'Heal all damage from',
        'all your Pokémon,',
        'discarding energies.',
    ],
    'ITEM_TCG_LASS': [
        'Both players shuffle',
        'all Trainer cards in',
        'hand into deck.',
    ],
    'ITEM_TCG_MR_FUJI': [
        'Shuffle 1 benched mon',
        'and all its attached',
        'cards into deck.',
    ],
    'ITEM_TCG_IMPOSTER_PROF_OAK': [
        'Opponent shuffles',
        'hand into deck and',
        'draws 4 cards.',
    ],
    'ITEM_TCG_IMPOSTER_OAK_REVENGE': [
        'Discard 1 card. If foe',
        'has >4 cards in hand,',
        'reduce to 4.',
    ],
    'ITEM_TCG_RECYCLE': [
        'Flip a coin. If heads,',
        'put 1 discard card on',
        'top of your deck.',
    ],
    'ITEM_TCG_NIGHTLY_GARBAGE_RUN': [
        'Shuffle up to 3 mons',
        'or energies from the',
        'discard into deck.',
    ],
    'ITEM_TCG_ROCKET_SNEAK_ATTACK': [
        "Look at foe's hand and",
        'shuffle 1 Trainer',
        'card into their deck.',
    ],
    'ITEM_TCG_HERE_COMES_TEAM_ROCKET': [
        'Both players play',
        'with Prize cards face',
        'up for the battle.',
    ],
    'ITEM_TCG_ROCKET_TRAP': [
        'Flip coin: if heads,',
        'opponent shuffles 1',
        'random card to deck.',
    ],
    'ITEM_TCG_BOSS_WAY': [
        'Search deck for 1 Dark',
        'Evolution card and',
        'put it into hand.',
    ],
    'ITEM_TCG_GOOP_GAS_ATTACK': [
        'All Pokémon Powers stop',
        'working until the end',
        'of next turn.',
    ],
    'ITEM_TCG_BILLS_TELEPORTER': [
        'Flip a coin. If heads,',
        'draw 4 cards from',
        'your deck.',
    ],
    'ITEM_TCG_BILLS_PC': [
        'Search your deck for',
        'an Evolution card and',
        'put it into hand.',
    ],
    'ITEM_TCG_CHALLENGE': [
        'Ask foe to bench mons',
        'or draw 2 cards if',
        'they decline.',
    ],
    'ITEM_TCG_SLEEP': [
        'Flip coin: if heads,',
        'the defending mon is',
        'now Asleep.',
    ],
    'ITEM_TCG_COMPUTER_ERROR': [
        'Both players may draw',
        'up to 5 cards from',
        'their decks.',
    ],
    'ITEM_TCG_DIGGER': [
        'Flip coins to deal',
        'damage to active or',
        'bench Pokémon.',
    ],
    'ITEM_TCG_FOSSIL_EXCAVATION': [
        'Put 1 Mysterious Fossil',
        'from deck or discard',
        'into your hand.',
    ],
    'ITEM_TCG_IMAKUNI': [
        'Your Active Pokémon is',
        'now Confused.',
        'Play at your own risk!',
    ],
    'ITEM_TCG_POKEMON_RETRANSFER': [
        'Put an Evolution card',
        'from discard pile on',
        'top of your deck.',
    ],
    'ITEM_TCG_POKE_RECEIVER': [
        'Flip a coin. If heads,',
        'search deck for 1 Basic',
        'Pokémon.',
    ],
}

def validate_limits():
    for k, lines in ENGLISH_DESCRIPTIONS.items():
        assert len(lines) <= 3, f"{k} has {len(lines)} lines > 3"
        for l in lines:
            assert len(l) <= 34, f"{k} line too long: '{l}' ({len(l)} > 34)"
    print("All descriptions pass line and character limits.")

def update_items_h():
    validate_limits()
    with open('src/data/items.h', 'r', encoding='utf-8') as f:
        content = f.read()

    for item_const, lines in ENGLISH_DESCRIPTIONS.items():
        # Match the entry for item_const
        pattern = re.compile(
            r'(\[' + re.escape(item_const) + r'\]\s*=\s*\{.*?\.description\s*=\s*COMPOUND_STRING\()(.*?)(\),)',
            re.DOTALL
        )
        match = pattern.search(content)
        if match:
            # Format lines:
            # "line1\n"
            # "line2\n"
            # "line3"
            parts = []
            for i, line in enumerate(lines):
                if i < len(lines) - 1:
                    parts.append(f'"{line}\\n"')
                else:
                    parts.append(f'"{line}"')
            formatted_desc = "\n            ".join(parts)
            replacement = match.group(1) + "\n            " + formatted_desc + match.group(3)
            content = content[:match.start()] + replacement + content[match.end():]
        else:
            print(f"Warning: could not find {item_const} in items.h")

    with open('src/data/items.h', 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print("Updated src/data/items.h successfully!")

if __name__ == '__main__':
    update_items_h()
