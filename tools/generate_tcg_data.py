#!/usr/bin/env python3
"""
tools/generate_tcg_data.py
Generates canonical TCG Pocket data files from poketcg / poketcg2-en ASM sources
using the comment-driven parser in tools/tcg_asm_parser.py:
  - include/constants/tcg_cards.h
  - src/data/tcg_cards.h
  - src/data/tcg_decks.h
  - src/data/trainer_tcg_decks.h
  - tools/unused_deck_cards.txt
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tcg_asm_parser

# ---------------------------------------------------------------------------
# 1. Exact Trainer Card Metadata (Cards 382..429)
#    Every Trainer card gets its exact Item ID, Card Type (Item vs Supporter),
#    Display Name (renaming Poké Ball -> Poké Receiver, Master Ball -> Master Receiver),
#    and real 3-line English TCG Pocket description (<= 3 lines, <= 34 chars/line).
# ---------------------------------------------------------------------------
TRAINER_CARD_META = {
    'SuperPotion': (
        'Super Potion', 'ITEM_SUPER_POTION', 'CARD_TYPE_TRAINER_ITEM',
        'Discard 1 Energy\nto heal 40 HP\nfrom Active mon.'
    ),
    'ImakuniCard': (
        'Imakuni?', 'ITEM_FOCUS_BAND', 'CARD_TYPE_TRAINER_SUPPORTER',
        'Confuses your own\nActive Pokémon.\nPlay with care!'
    ),
    'ProfessorOak': (
        'Professor Oak', 'ITEM_LINKING_CORD', 'CARD_TYPE_TRAINER_SUPPORTER',
        'Discard your hand\nand draw up to 5\ncards from deck.'
    ),
    'FossilExcavation': (
        'Fossil Excavation', 'ITEM_CLAW_FOSSIL', 'CARD_TYPE_TRAINER_ITEM',
        'Recover 1 Fossil\ncard from deck or\ndiscard to hand.'
    ),
    'Potion': (
        'Potion', 'ITEM_POTION', 'CARD_TYPE_TRAINER_ITEM',
        'Heal 20 HP damage\nfrom your Active\nPokémon.'
    ),
    'Gambler': (
        'Gambler', 'ITEM_LUCKY_EGG', 'CARD_TYPE_TRAINER_SUPPORTER',
        'Shuffle hand in.\nHeads: draw 8.\nTails: draw 1.'
    ),
    'Revive': (
        'Revive', 'ITEM_REVIVE', 'CARD_TYPE_TRAINER_ITEM',
        'Put 1 Basic from\ndiscard onto your\nBench at 50% HP.'
    ),
    'MaxRevive': (
        'Max Revive', 'ITEM_MAX_REVIVE', 'CARD_TYPE_TRAINER_ITEM',
        'Put 1 Basic from\ndiscard onto your\nBench at full HP.'
    ),
    'SuperScoopUp': (
        'Super Scoop Up', 'ITEM_AIR_BALLOON', 'CARD_TYPE_TRAINER_ITEM',
        'Flip a coin.\nIf heads, return\n1 mon to hand.'
    ),
    'DevolutionSpray': (
        'Devolution Spray', 'ITEM_EVERSTONE', 'CARD_TYPE_TRAINER_ITEM',
        'Devolve 1 evolved\nPokémon and cure\nits conditions.'
    ),
    'ItemFinder': (
        'Item Finder', 'ITEM_SCOPE_LENS', 'CARD_TYPE_TRAINER_ITEM',
        'Discard 2 cards\nto recover 1 Item\nfrom discard.'
    ),
    'Challenge': (
        'Challenge!', 'ITEM_CHOICE_BAND', 'CARD_TYPE_TRAINER_ITEM',
        'Draw 2 cards or\nfill your Bench\nwith Basic mons.'
    ),
    'MoonStone': (
        'Moon Stone', 'ITEM_MOON_STONE', 'CARD_TYPE_TRAINER_ITEM',
        'Search your deck\nfor 1 Colorless\nEvolution card.'
    ),
    'Defender': (
        'Defender', 'ITEM_X_DEFENSE', 'CARD_TYPE_TRAINER_ITEM',
        'Reduces next foe\nattack damage to\nActive by 20 HP.'
    ),
    'GustOfWind': (
        'Gust of Wind', 'ITEM_EJECT_BUTTON', 'CARD_TYPE_TRAINER_ITEM',
        'Switch 1 of foe\'s\nBenched Pokémon\nto Active Spot.'
    ),
    'MysteriousFossil': (
        'Mysterious Fossil', 'ITEM_ROOT_FOSSIL', 'CARD_TYPE_POKEMON_BASIC',
        'Play as a 10 HP\nBasic Pokémon.\nEvolves to Fossil.'
    ),
    'FullHeal': (
        'Full Heal', 'ITEM_FULL_HEAL', 'CARD_TYPE_TRAINER_ITEM',
        'Cure all Special\nConditions from\nActive Pokémon.'
    ),
    'ImposterOaksRevenge': (
        'Imposter Revenge', 'ITEM_SMOKE_BALL', 'CARD_TYPE_TRAINER_SUPPORTER',
        'Discard 1 card.\nFoe shuffles hand\nand draws 4.'
    ),
    'ImposterProfessorOak': (
        'Imposter Prof Oak', 'ITEM_ODD_INCENSE', 'CARD_TYPE_TRAINER_SUPPORTER',
        'Foe shuffles hand\ninto their deck\nand draws 4.'
    ),
    'Sleep': (
        'Sleep!', 'ITEM_FLAME_ORB', 'CARD_TYPE_TRAINER_ITEM',
        'Flip a coin.\nIf heads, foe is\nnow Asleep.'
    ),
    'ComputerError': (
        'Computer Error', 'ITEM_RED_CARD', 'CARD_TYPE_TRAINER_SUPPORTER',
        'Both players may\ndraw up to 5 new\ncards from deck.'
    ),
    'ComputerSearch': (
        'Computer Search', 'ITEM_UPGRADE', 'CARD_TYPE_TRAINER_ITEM',
        'Discard 2 cards\nfrom hand to find\nany 1 deck card.'
    ),
    'Digger': (
        'Digger', 'ITEM_SOFT_SAND', 'CARD_TYPE_TRAINER_ITEM',
        'Flip coin: heads\ndeals 10 HP to\nfoe, tails to you.'
    ),
    'ClefairyDoll': (
        'Clefairy Doll', 'ITEM_POKE_DOLL', 'CARD_TYPE_POKEMON_BASIC',
        'Play as a 10 HP\nBasic Pokémon.\nGives 0 Prizes.'
    ),
    'MrFuji': (
        'Mr. Fuji', 'ITEM_SACRED_ASH', 'CARD_TYPE_TRAINER_SUPPORTER',
        'Shuffle 1 of your\nBenched Pokémon\ninto your deck.'
    ),
    'PlusPower': (
        'PlusPower', 'ITEM_X_ATTACK', 'CARD_TYPE_TRAINER_ITEM',
        'Active Pokémon\'s\nattack deals +10\ndamage this turn.'
    ),
    'Switch': (
        'Switch', 'ITEM_ESCAPE_ROPE', 'CARD_TYPE_TRAINER_ITEM',
        'Switch Active mon\nwith 1 Benched\nPokémon for free.'
    ),
    'ScoopUp': (
        'Scoop Up', 'ITEM_EJECT_PACK', 'CARD_TYPE_TRAINER_ITEM',
        'Return 1 of your\nBenched Pokémon\nto your hand.'
    ),
    'PokemonTrader': (
        'Pokémon Trader', 'ITEM_CLEANSE_TAG', 'CARD_TYPE_TRAINER_SUPPORTER',
        'Swap 1 Pokémon in\nyour hand for 1\nin your deck.'
    ),
    'PokemonRecall': (
        'Pokémon Retransfer', 'ITEM_METAL_COAT', 'CARD_TYPE_TRAINER_ITEM',
        'Recover 1 Evolved\nPokémon card from\nyour discard.'
    ),
    'Pokedex': (
        'Pokédex', 'ITEM_DEEP_SEA_TOOTH', 'CARD_TYPE_TRAINER_ITEM',
        'Look at top 5\ncards of deck and\nrearrange them.'
    ),
    'PokemonCenter': (
        'Pokémon Center', 'ITEM_MOOMOO_MILK', 'CARD_TYPE_TRAINER_ITEM',
        'Heal all HP from\nyour Pokémon and\ndiscard Energy.'
    ),
    'PokemonBreeder': (
        'Pokémon Breeder', 'ITEM_SOOTHE_BELL', 'CARD_TYPE_TRAINER_SUPPORTER',
        'Evolve a Basic\nPokémon directly\nto Stage 2.'
    ),
    'PokemonFlute': (
        'Pokémon Flute', 'ITEM_BLUE_FLUTE', 'CARD_TYPE_TRAINER_ITEM',
        'Put 1 Basic from\nfoe discard onto\nfoe\'s Bench.'
    ),
    'TheBosssWay': (
        'The Boss\'s Way', 'ITEM_KINGS_ROCK', 'CARD_TYPE_TRAINER_ITEM',
        'Search your deck\nfor 1 Evolution\ncard to hand.'
    ),
    'GoopGasAttack': (
        'Goop Gas Attack', 'ITEM_TOXIC_ORB', 'CARD_TYPE_TRAINER_ITEM',
        'Blocks all active\nPokémon Powers\nfor 1 full turn.'
    ),
    'Bill': (
        'Bill', 'ITEM_EXP_SHARE', 'CARD_TYPE_TRAINER_SUPPORTER',
        'Draw 2 cards from\nyour deck into\nyour hand.'
    ),
    'BillsTeleporter': (
        'Bill\'s Teleporter', 'ITEM_AMULET_COIN', 'CARD_TYPE_TRAINER_SUPPORTER',
        'Flip a coin.\nIf heads, draw 4\ncards from deck.'
    ),
    'BillsComputer': (
        'Bill\'s PC', 'ITEM_DUBIOUS_DISC', 'CARD_TYPE_TRAINER_ITEM',
        'Search your deck\nfor 1 Evolution\nPokémon card.'
    ),
    'MasterBall': (
        'Master Receiver', 'ITEM_DEEP_SEA_SCALE', 'CARD_TYPE_TRAINER_ITEM',
        'Look at top 7\ndeck cards; take\n1 Pokémon found.'
    ),
    'Lass': (
        'Lass', 'ITEM_DESTINY_KNOT', 'CARD_TYPE_TRAINER_SUPPORTER',
        'Both players\nshuffle Trainer\ncards into deck.'
    ),
    'Maintenance': (
        'Maintenance', 'ITEM_LEFTOVERS', 'CARD_TYPE_TRAINER_ITEM',
        'Shuffle 2 cards\nfrom hand to deck\nand draw 1 card.'
    ),
    'Pokeball': (
        'Poké Receiver', 'ITEM_LIGHT_BALL', 'CARD_TYPE_TRAINER_ITEM',
        'Flip a coin.\nIf heads, draw 1\nBasic from deck.'
    ),
    'NightlyGarbageRun': (
        'Nightly Garbage Run', 'ITEM_FULL_RESTORE', 'CARD_TYPE_TRAINER_ITEM',
        'Shuffle up to 3\ndiscarded Pokémon\ninto your deck.'
    ),
    'Recycle': (
        'Recycle', 'ITEM_ETHER', 'CARD_TYPE_TRAINER_ITEM',
        'Flip a coin.\nIf heads, recover\n1 discarded card.'
    ),
    'RocketsSneakAttack': (
        'Rocket Sneak Atk', 'ITEM_BLACK_GLASSES', 'CARD_TYPE_TRAINER_SUPPORTER',
        'Shuffle 1 Trainer\ncard from foe\'s\nhand into deck.'
    ),
    'HereComesTeamRocket': (
        'Team Rocket!', 'ITEM_RAZOR_CLAW', 'CARD_TYPE_TRAINER_SUPPORTER',
        'Draw 2 cards from\nyour deck into\nyour hand.'
    ),
    'TheRocketsTrap': (
        'The Rocket\'s Trap', 'ITEM_IRON_BALL', 'CARD_TYPE_TRAINER_ITEM',
        'Flip a coin.\nIf heads, shuffle\n3 foe hand cards.'
    ),
    'EnergyRemoval': (
        'Energy Removal', 'ITEM_REPEL', 'CARD_TYPE_TRAINER_ITEM',
        'Discard 1 Energy\nattached to foe\'s\nActive Pokémon.'
    ),
    'SuperEnergyRemoval': (
        'Super Energy Rem.', 'ITEM_SUPER_REPEL', 'CARD_TYPE_TRAINER_ITEM',
        'Discard 1 of your\nEnergy and 2 from\nfoe\'s Active mon.'
    ),
}

# ---------------------------------------------------------------------------
# 2. Concise 2-line Pokémon Power descriptions (<= 2 lines, <= 32 chars/line)
# ---------------------------------------------------------------------------
POWER_DESCRIPTIONS = {
    'Vine Pull': 'Switch 1 foe Benched Pokémon\nto Active when retreating.',
    'Solar Power': 'Remove all special status\nfrom both Active Pokémon.',
    'Energy Trans': 'Move Grass Energy freely\nbetween your Pokémon.',
    'Green Shield': 'Your Grass Pokémon ignore\nWeakness while in play.',
    'Poison Fluid': 'Poisons attacker when hit\nby an opponent\'s attack.',
    'Sneak Attack': 'Deals 10 HP damage to 1 foe\nPokémon when put in play.',
    'Pollen Stench': 'Flip coin: heads Confuses\nföe; tails Confuses yours.',
    'Heal': 'Flip a coin once per turn:\nif heads, heal 10 HP.',
    'Hay Fever': 'Blocks Trainer Item cards\nwhile this Pokémon is up.',
    'Shift': 'Change this Pokémon\'s type\nto match any Pokémon.',
    'Toxic Gas': 'Nullifies all other Pokémon\nPowers while Active.',
    'Sticky Goo': 'Adds +2 Colorless Energy to\nthe foe\'s Retreat Cost.',
    'Poison Mist': 'Flip coin: if heads, poisons\nthe Defending Pokémon.',
    'Gather Fire': 'Move 1 Fire Energy from a\nBenched mon to Active mon.',
    'Energy Burn': 'Converts all attached Energy\ninto Fire Energy.',
    'Firegiver': 'Generates bonus Fire Energy\nwhen put into play.',
    'Rain Dance': 'Attach extra Water Energy to\nyour Water Pokémon.',
    'Cowardice': 'Return this Pokémon to your\nhand before attacking.',
    'Rebirth': 'Heal all damage by discarding\nattached Energy cards.',
    'Final Beam': 'Flip coin when Knocked Out:\nheads deals 20 HP to foe.',
    'Clairvoyance': 'Reveals cards in opponent\'s\nhand while in play.',
    'Prehistoric Dream': 'Flip coin: if heads, boosts\nyour Fossil Pokémon +10.',
    'Fossil Guidance': 'Flip coin: if heads, recover\n1 Fossil from discard.',
    'Aurora Veil': 'Protects your Benched mons\nfrom attack damage.',
    'Quickfreeze': 'Flip coin on play: if heads,\nParalyzes Defending mon.',
    'Magnet': 'Flip coin: if heads, search\ndeck for 1 Magnemite.',
    'Peal of Thunder': 'Deals 30 HP damage to a\nrandom mon when played.',
    'Go Underground': 'Prevents all attack damage\nwhile on your Bench.',
    'Sinkhole': 'Foe flips coin on retreat:\ntails deals 20 HP damage.',
    'Peek': 'Look at top deck card or 1\ncard in opponent\'s hand.',
    'Frenzy': 'Deals +30 damage whenever\nthis Pokémon is Confused.',
    'Strikes Back': 'Deals 10 HP counter damage\nwhen hit by an attack.',
    'Kabuto Armor': 'Halves all attack damage\ndone to this Pokémon.',
    'Fossilize': 'Flip coin: heads devolves 1\nevolved Fossil Pokémon.',
    'Prehistoric Power': 'Prevents playing Evolution\ncards while in play.',
    'Matter Exchange': 'Discard 1 card from hand to\ndraw 1 card from deck.',
    'Damage Swap': 'Move 10 HP damage between\nyour Pokémon in play.',
    'Strange Behavior': 'Transfer 10 HP damage from\nyour Pokémon to Slowbro.',
    'Reel In': 'Recover up to 3 Pokémon\nfrom discard when played.',
    'Transparency': 'Flip coin when attacked: if\nheads, prevent all damage.',
    'Curse': 'Move 10 HP damage between 2\nof opponent\'s Pokémon.',
    'Power of Darkness': 'Flip coin on play: heads\nreturns 1 foe mon to hand.',
    'Play Tricks': 'Redistribute damage among\nopponent\'s Pokémon.',
    'Long-Distance Hypnosis': 'Flip coin: heads puts foe\nto Sleep; tails sleeps you.',
    'Puppet Master': 'Allows Clefairy Doll to use\nHypno\'s attacks.',
    'Dampening Shield': 'Negates Weakness for both\nActive Pokémon in play.',
    'Invisible Wall': 'Blocks attacks that deal\n30 or more HP damage.',
    'Dark Wave': 'Your Dark Pokémon deal +10\nextra attack damage.',
    'Neutralizing Shield': 'Blocks attacks from evolved\nPokémon completely.',
    'Trickery': 'Heal 10 HP and cycle top\ncard of your deck.',
    'Darkness Veil': 'Reduces damage taken by\nyour Dark Pokémon by 10.',
    'Helping Hand': 'Flip coin on Bench: heads\ncures Active mon status.',
    'Retreat Aid': 'Reduces Active Pokémon\'s\nRetreat Cost by 1 Energy.',
    'Thick Skinned': 'Immune to Asleep, Confused,\nParalyzed, and Poisoned.',
    'Guard': 'Prevents Defending Pokémon\nfrom retreating.',
    'Evolutionary Light': 'Search deck for 1 Evolution\ncard once per turn.',
    'Healing Wind': 'Heals 20 HP from each of\nyour Pokémon when played.',
    'Special Delivery': 'Draw 1 card, then put 1\ncard on top of your deck.',
    'Step In': 'Switch this Benched Pokémon\ninto the Active Spot.',
    'Summon Minions': 'Put up to 2 Basic Pokémon\nfrom deck onto Bench.',
}


def wrap_two_lines(text, max_width=32):
    """Wrap text into at most 2 lines of <= max_width chars each."""
    text = text.replace('\n', ' ').strip()
    words = text.split()
    if not words:
        return 'Standard TCG Pocket attack.'
    lines = []
    cur = ''
    for w in words:
        if len(w) > max_width:
            w = w[:max_width]
        if not cur:
            cur = w
        elif len(cur) + 1 + len(w) <= max_width:
            cur += ' ' + w
        else:
            lines.append(cur)
            cur = w
            if len(lines) == 2:
                break
    if len(lines) < 2 and cur:
        lines.append(cur)
    return '\\n'.join(lines[:2])


def synthesize_attack_effect_and_desc(atk, texts):
    """Return (effect_const, two_line_desc) for an ASM attack dict."""
    cat = atk['category']
    flags = set(atk['flags'])
    dmg = atk['damage']
    raw_desc = ' '.join(texts.get(lbl, '') for lbl in atk['desc_lbls']).strip()
    raw_low = raw_desc.lower()

    # Determine effect constant and concise 2-line description (<= 32 chars/line, no cost text, HP instead of damage counters)
    if cat == 'DAMAGE_X':
        eff = 'EFFECT_TCG_MULTI_COIN_HIT'
        if dmg > 0:
            desc = f'Flip coins: deals {dmg} damage\\ntimes number of heads.'
        else:
            desc = 'Flip coins: deals damage\\nfor each heads.'
    elif cat == 'DAMAGE_PLUS':
        if 'ATTACHED_ENERGY_BOOST' in flags or 'energy' in raw_low:
            eff = 'EFFECT_TCG_ENERGY_BOOST'
            desc = 'Deals +10 extra damage for\\neach extra Energy attached.'
        elif 'BOOST_IF_TAKEN_DAMAGE' in flags or 'damage counter' in raw_low:
            eff = 'EFFECT_TCG_RAGE_DAMAGE_BOOST'
            desc = 'Deals +10 extra damage per\\n10 HP damage on this mon.'
        else:
            eff = 'EFFECT_TCG_COIN_DAMAGE_BONUS'
            desc = 'Flip a coin. If heads, this\\nattack deals +20 damage.'
    elif 'HIGH_RECOIL' in flags and dmg >= 40 and ('bench' in raw_low or 'selfdestruct' in atk['name_lbl'].lower()):
        eff = 'EFFECT_TCG_SELFDESTRUCT'
        desc = 'Deals massive damage; this\\nPokémon also takes recoil.'
    elif 'LOW_RECOIL' in flags or 'HIGH_RECOIL' in flags:
        eff = 'EFFECT_TCG_SELF_DAMAGE_COIN'
        if 'flip a coin' in raw_low:
            desc = 'Flip a coin. If tails, this\\nPokémon takes 20 HP recoil.'
        else:
            desc = 'Powerful strike; user also\\ntakes 20 HP recoil damage.'
    elif 'DISCARD_ENERGY' in flags:
        eff = 'EFFECT_TCG_DISCARD_USER_ENERGY'
        desc = 'Discard 1 Energy attached\\nto this Pokémon to attack.'
    elif 'DESTROY_DEFENDER_ENERGY' in raw_low or ('defending' in raw_low and 'energy' in raw_low and 'discard' in raw_low):
        eff = 'EFFECT_TCG_DISCARD_TARGET_ENERGY'
        desc = 'Discards 1 Energy attached\\nto the Defending Pokémon.'
    elif 'DAMAGE_TO_OPPONENT_BENCH' in flags or 'benched' in raw_low:
        eff = 'EFFECT_TCG_BENCH_SNIPER'
        desc = 'Deals 10 HP damage to 1 of\\nopponent\'s Benched Pokémon.'
    elif 'SWITCH_OPPONENT_POKEMON' in flags:
        eff = 'EFFECT_TCG_FORCE_SWITCH'
        desc = 'Switches Defending Pokémon\\nwith 1 of foe\'s Benched.'
    elif 'HEAL_USER' in flags or 'remove all' in raw_low or 'remove a number of damage' in raw_low:
        eff = 'EFFECT_TCG_HEAL_USER'
        desc = 'Heals 20 HP of damage from\\nthis Pokémon.'
    elif 'DRAW_CARD' in flags or 'search your deck' in raw_low or 'draw' in raw_low:
        eff = 'EFFECT_TCG_DRAW_CARD'
        desc = 'Draws 1 card from your deck\\nafter attacking.'
    elif 'INFLICT_POISON' in flags or 'poisoned' in raw_low:
        eff = 'EFFECT_TCG_INFLICT_POISON'
        if 'flip a coin' in raw_low:
            desc = 'Flip a coin. If heads, the\\nDefending mon is Poisoned.'
        else:
            desc = 'The Defending Pokémon is\\nnow Poisoned (10 HP/turn).'
    elif 'INFLICT_PARALYSIS' in flags or 'paralyzed' in raw_low:
        eff = 'EFFECT_TCG_INFLICT_PARALYSIS'
        desc = 'Flip a coin. If heads, the\\nDefending mon is Paralyzed.'
    elif 'INFLICT_SLEEP' in flags or 'asleep' in raw_low:
        eff = 'EFFECT_TCG_INFLICT_SLEEP'
        if 'flip a coin' in raw_low:
            desc = 'Flip a coin. If heads, the\\nDefending mon is Asleep.'
        else:
            desc = 'The Defending Pokémon is\\nnow Asleep.'
    elif 'INFLICT_CONFUSION' in flags or 'confused' in raw_low:
        eff = 'EFFECT_TCG_INFLICT_CONFUSION'
        if 'flip a coin' in raw_low:
            desc = 'Flip a coin. If heads, the\\nDefending mon is Confused.'
        else:
            desc = 'The Defending Pokémon is\\nnow Confused.'
    elif 'NULLIFY_OR_WEAKEN_ATTACK' in flags or 'prevent' in raw_low or 'reduce' in raw_low:
        if 'flip a coin' in raw_low and ('try to attack' in raw_low or 'smokescreen' in atk['name_lbl'].lower() or 'sand' in atk['name_lbl'].lower()):
            eff = 'EFFECT_TCG_BLIND_TARGET'
            desc = 'Foe must flip a coin to hit\\nduring their next turn.'
        elif 'choose 1 of the defending' in raw_low or 'amnesia' in atk['name_lbl'].lower() or 'disable' in atk['name_lbl'].lower() or 'trainer' in raw_low:
            eff = 'EFFECT_TCG_DISABLE_MOVE'
            desc = 'Disables 1 of the foe\'s\\nattacks on their next turn.'
        else:
            eff = 'EFFECT_TCG_SHIELD_NEXT_TURN'
            desc = 'Reduces damage taken during\\nopponent\'s next turn.'
    elif 'BOOST_IF_TAKEN_DAMAGE' in flags:
        eff = 'EFFECT_TCG_RAGE_DAMAGE_BOOST'
        desc = 'Deals +10 extra damage per\\n10 HP damage on this mon.'
    elif 'ATTACHED_ENERGY_BOOST' in flags:
        eff = 'EFFECT_TCG_ENERGY_BOOST'
        desc = 'Deals +10 extra damage for\\neach extra Energy attached.'
    elif 'flip a coin' in raw_low and dmg > 0:
        eff = 'EFFECT_TCG_COIN_DAMAGE_BONUS'
        desc = 'Flip a coin. If heads, this\\nattack deals +20 damage.'
    elif dmg > 0:
        eff = 'EFFECT_HIT'
        desc = f'Deals {dmg} HP damage to the\\nDefending Pokémon.'
    else:
        eff = 'EFFECT_TCG_SHIELD_NEXT_TURN'
        desc = 'Bolsters defense and guards\\nagainst the next attack.'

    # Verify strict <= 2 lines, <= 30 chars/line (so with trailing \n it is <= 31)
    lines = desc.split('\\n')
    lines = [l[:30] for l in lines[:2]]
    return eff, '\\n'.join(lines)


def load_species_and_moves():
    with open('include/constants/species.h', 'r', encoding='utf-8') as f:
        sp_content = f.read()
    species_map = {}
    for m in re.finditer(r'\bSPECIES_([A-Z0-9_]+)\s*=\s*(\d+)', sp_content):
        name, val = m.group(1), int(m.group(2))
        if 0 < val <= 251:
            species_map[name] = f'SPECIES_{name}'
            species_map[name.replace('_', '')] = f'SPECIES_{name}'

    with open('include/constants/moves.h', 'r', encoding='utf-8') as f:
        mv_content = f.read()
    moves_by_norm = {}
    moves_by_id = {}
    for m in re.finditer(r'\b(MOVE_[A-Z0-9_]+)\s*=\s*(\d+)', mv_content):
        mconst, val = m.group(1), int(m.group(2))
        if 1 <= val <= 354:
            norm = mconst[5:].replace('_', '')
            moves_by_norm[norm] = mconst
            moves_by_id[val] = mconst
    return species_map, moves_by_norm, moves_by_id


# Explicit aliases for TCG attack names -> canonical Gen 1-3 MOVE_* constants
EXPLICIT_MOVE_ALIASES = {
    'THUNDERSHOCK': 'MOVE_THUNDER_SHOCK',
    'POISONPOWDER': 'MOVE_POISON_POWDER',
    'STUNSPORE': 'MOVE_STUN_SPORE',
    'SLEEPPOWDER': 'MOVE_SLEEP_POWDER',
    'SOLARBEAM': 'MOVE_SOLAR_BEAM',
    'BUBBLEBEAM': 'MOVE_BUBBLE_BEAM',
    'THUNDERPUNCH': 'MOVE_THUNDER_PUNCH',
    'FIREPUNCH': 'MOVE_FIRE_PUNCH',
    'ICEPUNCH': 'MOVE_ICE_PUNCH',
    'DOUBLESLAP': 'MOVE_DOUBLE_SLAP',
    'SELFDESTRUCT': 'MOVE_SELF_DESTRUCT',
    'SMOKESCREEN': 'MOVE_SMOKESCREEN',
    'SANDATTACK': 'MOVE_SAND_ATTACK',
    'SONICBOOM': 'MOVE_SONIC_BOOM',
    'HYPERBEAM': 'MOVE_HYPER_BEAM',
    'AURORABEAM': 'MOVE_AURORA_BEAM',
    'PSYCHIC': 'MOVE_PSYCHIC',
    'PSYBEAM': 'MOVE_PSYBEAM',
    'DRAGONRAGE': 'MOVE_DRAGON_RAGE',
    'NIGHTSHADE': 'MOVE_NIGHT_SHADE',
    'CONFUSERAY': 'MOVE_CONFUSE_RAY',
    'WINGATTACK': 'MOVE_WING_ATTACK',
    'QUICKATTACK': 'MOVE_QUICK_ATTACK',
    'HORNATTACK': 'MOVE_HORN_ATTACK',
    'FURYATTACK': 'MOVE_FURY_ATTACK',
    'FURYSWIPES': 'MOVE_FURY_SWIPES',
    'DOUBLETEAM': 'MOVE_DOUBLE_TEAM',
    'DOUBLEEDGE': 'MOVE_DOUBLE_EDGE',
    'DOUBLEKICK': 'MOVE_DOUBLE_KICK',
    'JUMPKICK': 'MOVE_JUMP_KICK',
    'HIJUMPKICK': 'MOVE_HIGH_JUMP_KICK',
    'HIGHJUMPKICK': 'MOVE_HIGH_JUMP_KICK',
    'KARATECHOP': 'MOVE_KARATE_CHOP',
    'SEISMICTOSS': 'MOVE_SEISMIC_TOSS',
    'SUBMISSION': 'MOVE_SUBMISSION',
    'ROCKTHROW': 'MOVE_ROCK_THROW',
    'ROCKSLIDE': 'MOVE_ROCK_SLIDE',
    'BONEMERANG': 'MOVE_BONEMERANG',
    'BONECLUB': 'MOVE_BONE_CLUB',
    'PINMISSILE': 'MOVE_PIN_MISSILE',
    'TWINEEDLE': 'MOVE_TWINEEDLE',
    'STRINGSHOT': 'MOVE_STRING_SHOT',
    'LEECHSEED': 'MOVE_LEECH_SEED',
    'LEECHLIFE': 'MOVE_LEECH_LIFE',
    'RAZORLEAF': 'MOVE_RAZOR_LEAF',
    'VINEWHIP': 'MOVE_VINE_WHIP',
    'PETALDANCE': 'MOVE_PETAL_DANCE',
    'MEGADRAIN': 'MOVE_MEGA_DRAIN',
    'GIGADRAIN': 'MOVE_GIGA_DRAIN',
    'FIRESPIN': 'MOVE_FIRE_SPIN',
    'FIREBLAST': 'MOVE_FIRE_BLAST',
    'FLAMETHROWER': 'MOVE_FLAMETHROWER',
    'HYDROPUMP': 'MOVE_HYDRO_PUMP',
    'WATERGUN': 'MOVE_WATER_GUN',
    'CRABHAMMER': 'MOVE_CRABHAMMER',
    'THUNDERWAVE': 'MOVE_THUNDER_WAVE',
    'THUNDERBOLT': 'MOVE_THUNDERBOLT',
    'DRILLPECK': 'MOVE_DRILL_PECK',
    'MIRRORMOVE': 'MOVE_MIRROR_MOVE',
    'SWORDSDANCE': 'MOVE_SWORDS_DANCE',
    'BODYSLAM': 'MOVE_BODY_SLAM',
    'TAKEDOWN': 'MOVE_TAKE_DOWN',
    'TAILWHIP': 'MOVE_TAIL_WHIP',
    'POISONSTING': 'MOVE_POISON_STING',
    'POISONGAS': 'MOVE_POISON_GAS',
    'ACIDARMOR': 'MOVE_ACID_ARMOR',
    'SCREECH': 'MOVE_SCREECH',
    'SUPERSONIC': 'MOVE_SUPERSONIC',
    'MINIMIZE': 'MOVE_MINIMIZE',
    'DEFENSECURL': 'MOVE_DEFENSE_CURL',
    'LIGHTSCREEN': 'MOVE_LIGHT_SCREEN',
    'BARRIER': 'MOVE_BARRIER',
    'RECOVER': 'MOVE_RECOVER',
    'SOFTBOILED': 'MOVE_SOFT_BOILED',
    'DREAMEATER': 'MOVE_DREAM_EATER',
    'LICK': 'MOVE_LICK',
    'SMOG': 'MOVE_SMOG',
    'SLUDGE': 'MOVE_SLUDGE',
    'CLAMP': 'MOVE_CLAMP',
    'SWIFT': 'MOVE_SWIFT',
    'SKULLBASH': 'MOVE_SKULL_BASH',
    'SPIKECANNON': 'MOVE_SPIKE_CANNON',
    'CONSTRICT': 'MOVE_CONSTRICT',
    'AMNESIA': 'MOVE_AMNESIA',
    'KINESIS': 'MOVE_KINESIS',
    'BARRAGE': 'MOVE_BARRAGE',
    'LOVELYKISS': 'MOVE_LOVELY_KISS',
    'SKYATTACK': 'MOVE_SKY_ATTACK',
    'TRANSFORM': 'MOVE_TRANSFORM',
    'DIZZYPUNCH': 'MOVE_DIZZY_PUNCH',
    'SPORE': 'MOVE_SPORE',
    'FLASH': 'MOVE_FLASH',
    'PSYWAVE': 'MOVE_PSYWAVE',
    'SPLASH': 'MOVE_SPLASH',
    'BONERUSH': 'MOVE_BONE_RUSH',
    'CONVERSION2': 'MOVE_CONVERSION_2',
    'SUPERFANG': 'MOVE_SUPER_FANG',
    'HYPERHFANG': 'MOVE_HYPER_FANG',
    'HYPERFANG': 'MOVE_HYPER_FANG',
    'SHARPEN': 'MOVE_SHARPEN',
    'TRIATTACK': 'MOVE_TRI_ATTACK',
    'SLASH': 'MOVE_SLASH',
    'SUBSTITUTE': 'MOVE_SUBSTITUTE',
    'STRUGGLE': 'MOVE_STRUGGLE',
}


def resolve_species(raw_name, species_map):
    if not raw_name:
        return 'SPECIES_NONE'
    clean = raw_name.upper().replace('DARK ', '').replace("TEAM ROCKET'S ", '').replace("'", '').strip()
    if 'NIDORAN' in clean:
        if '♀' in clean or 'F' in clean or '$' in clean:
            return 'SPECIES_NIDORAN_F'
        return 'SPECIES_NIDORAN_M'
    if 'FARFETCH' in clean:
        return 'SPECIES_FARFETCHD'
    if 'MR.' in clean or 'MR ' in clean or 'MIME' in clean:
        return 'SPECIES_MR_MIME'
    clean_alnum = re.sub(r'[^A-Z0-9]', '', clean)
    if clean_alnum in species_map:
        return species_map[clean_alnum]
    for sp_k, sp_v in species_map.items():
        if sp_k in clean_alnum:
            return sp_v
    return 'SPECIES_NONE'


def main():
    texts = tcg_asm_parser.load_texts()
    raw_cards = tcg_asm_parser.parse_cards()
    species_map, moves_by_norm, moves_by_id = load_species_and_moves()

    # Reserve canonical Gen 1-3 moves first, then assign unused move slots (1..354) to TCG-specific attack names
    used_move_consts = set()
    attack_name_to_move_const = {}

    # Pass 1: exact matches & explicit aliases
    all_attack_names = []
    for c in raw_cards:
        for a in c['attacks']:
            if not a['is_power']:
                aname = texts.get(a['name_lbl'], a['name_lbl']).strip()
                if aname not in all_attack_names:
                    all_attack_names.append(aname)

    for aname in all_attack_names:
        norm = re.sub(r'[^A-Z0-9]', '', aname.upper())
        if norm in EXPLICIT_MOVE_ALIASES:
            mc = EXPLICIT_MOVE_ALIASES[norm]
            attack_name_to_move_const[aname] = mc
            used_move_consts.add(mc)
        elif norm in moves_by_norm:
            mc = moves_by_norm[norm]
            attack_name_to_move_const[aname] = mc
            used_move_consts.add(mc)

    # Pool of unused Gen 1-3 move constants (excluding HM/field-special moves if needed, or any 1..354)
    unused_move_pool = [
        moves_by_id[mid] for mid in sorted(moves_by_id.keys())
        if moves_by_id[mid] not in used_move_consts
    ]
    pool_idx = 0
    for aname in all_attack_names:
        if aname not in attack_name_to_move_const:
            if pool_idx < len(unused_move_pool):
                mc = unused_move_pool[pool_idx]
                pool_idx += 1
            else:
                # Cycle through pool > 100 if > 354 unique attack names exist
                mc = moves_by_id[100 + (pool_idx % 250)]
                pool_idx += 1
            attack_name_to_move_const[aname] = mc

    # Assign unique IDs 1..60 to Pokémon Powers
    power_name_to_id = {}
    for c in raw_cards:
        for a in c['attacks']:
            if a['is_power']:
                pname = texts.get(a['name_lbl'], a['name_lbl']).strip()
                if pname not in power_name_to_id:
                    power_name_to_id[pname] = len(power_name_to_id) + 1

    type_map = {
        'TYPE_PKMN_GRASS': 'ENERGY_GRASS',
        'TYPE_PKMN_FIRE': 'ENERGY_FIRE',
        'TYPE_PKMN_WATER': 'ENERGY_WATER',
        'TYPE_PKMN_LIGHTNING': 'ENERGY_LIGHTNING',
        'TYPE_PKMN_PSYCHIC': 'ENERGY_PSYCHIC',
        'TYPE_PKMN_FIGHTING': 'ENERGY_FIGHTING',
        'TYPE_PKMN_DARKNESS': 'ENERGY_DARKNESS',
        'TYPE_PKMN_METAL': 'ENERGY_METAL',
        'TYPE_PKMN_COLORLESS': 'ENERGY_COLORLESS',
    }
    energy_short_name = {
        'ENERGY_GRASS': 'Grass',
        'ENERGY_FIRE': 'Fire',
        'ENERGY_WATER': 'Water',
        'ENERGY_LIGHTNING': 'Lightning',
        'ENERGY_PSYCHIC': 'Psychic',
        'ENERGY_FIGHTING': 'Fighting',
        'ENERGY_DARKNESS': 'Darkness',
        'ENERGY_METAL': 'Metal',
        'ENERGY_COLORLESS': 'Colorless',
        'NUM_ENERGY_TYPES': 'None',
    }
    weak_map = {
        'WR_GRASS': 'ENERGY_GRASS',
        'WR_FIRE': 'ENERGY_FIRE',
        'WR_WATER': 'ENERGY_WATER',
        'WR_LIGHTNING': 'ENERGY_LIGHTNING',
        'WR_PSYCHIC': 'ENERGY_PSYCHIC',
        'WR_FIGHTING': 'ENERGY_FIGHTING',
        'NONE': 'NUM_ENERGY_TYPES',
    }

    cards_out = []
    enum_to_id = {}

    for idx, rc in enumerate(raw_cards):
        cid = idx + 1
        label = rc['label']
        c_enum = 'CARD_' + re.sub(r'(?<!^)(?=[A-Z])', '_', label).upper()
        c_enum = re.sub(r'_+', '_', c_enum)
        if c_enum == 'CARD_POKEBALL':
            c_enum = 'CARD_POKE_RECEIVER'
        enum_to_id[c_enum] = cid
        if rc['id_const']:
            enum_to_id[rc['id_const']] = cid

        raw_name = texts.get(rc['name_lbl'], label).replace('♂', 'M').replace('♀', 'F').replace('$', 'F').strip()

        if rc['type'] == 'TYPE_TRAINER':
            meta = TRAINER_CARD_META.get(label)
            if meta:
                disp_name, equiv_item, ctype, desc_str = meta
            else:
                disp_name = raw_name[:22]
                equiv_item = 'ITEM_TCG_BILL'
                ctype = 'CARD_TYPE_TRAINER_ITEM'
                desc_str = 'Play this Trainer card\\nduring your turn.'
            cards_out.append({
                'cardId': cid,
                'enum': c_enum,
                'label': label,
                'name': disp_name,
                'species': 'SPECIES_NONE',
                'preEvoSpecies': 'SPECIES_NONE',
                'equivItemId': equiv_item,
                'cardType': ctype,
                'energyType': 'ENERGY_COLORLESS',
                'weaknessType': 'NUM_ENERGY_TYPES',
                'retreatCost': 0,
                'maxHp': 10 if ctype == 'CARD_TYPE_POKEMON_BASIC' else 0,
                'pokemonPowerId': 0,
                'powerName': '',
                'powerDesc': '',
                'move1': 'MOVE_NONE',
                'move2': 'MOVE_NONE',
                'move1Damage': 0,
                'move2Damage': 0,
                'move1Effect': 'EFFECT_HIT',
                'move2Effect': 'EFFECT_HIT',
                'move1Name': '',
                'move1Desc': '',
                'move2Name': '',
                'move2Desc': '',
                'move1Cost': {},
                'move2Cost': {},
                'encounterWeight': 0,
                'isRareShiny': 'FALSE',
                'description': desc_str,
            })
            continue

        # Pokémon card
        species = resolve_species(raw_name, species_map)
        if species == 'SPECIES_NONE':
            species = resolve_species(label, species_map)
        if species == 'SPECIES_NONE':
            species = 'SPECIES_BULBASAUR'

        preevo_raw = texts.get(rc['preevo_lbl'], '') if rc['preevo_lbl'] else ''
        pre_evo_species = resolve_species(preevo_raw, species_map) if preevo_raw else 'SPECIES_NONE'

        if rc['stage'] == 'STAGE1':
            ctype = 'CARD_TYPE_POKEMON_STAGE1'
        elif rc['stage'] == 'STAGE2':
            ctype = 'CARD_TYPE_POKEMON_STAGE2'
        else:
            ctype = 'CARD_TYPE_POKEMON_BASIC'
            pre_evo_species = 'SPECIES_NONE'

        # Mystery Fossil Evolutions (Omanyte, Kabuto, Aerodactyl) can be played as Basic if needed or evolve from Fossil
        if pre_evo_species == 'SPECIES_NONE' and ctype != 'CARD_TYPE_POKEMON_BASIC':
            ctype = 'CARD_TYPE_POKEMON_BASIC'

        energy = type_map.get(rc['type'], 'ENERGY_COLORLESS')
        weakness = weak_map.get(rc['weakness'], 'NUM_ENERGY_TYPES')
        retreat = min(rc['retreat'], 4)
        hp = max(rc['hp'], 30)

        # Extract Pokémon Power & up to 2 Attacks
        power_id = 0
        power_name = ''
        power_desc = ''
        atk_list = []
        for a in rc['attacks']:
            if a['is_power']:
                pname = texts.get(a['name_lbl'], a['name_lbl']).strip()
                power_id = power_name_to_id.get(pname, 1)
                power_name = pname[:22]
                pdesc = POWER_DESCRIPTIONS.get(pname)
                if not pdesc:
                    raw_p = ' '.join(texts.get(d, '') for d in a['desc_lbls'])
                    pdesc = wrap_two_lines(raw_p, 32)
                power_desc = pdesc
            else:
                atk_list.append(a)

        def build_atk(a_dict):
            if not a_dict:
                return ('MOVE_NONE', 0, 'EFFECT_HIT', '', '', {})
            aname = texts.get(a_dict['name_lbl'], a_dict['name_lbl']).strip()
            mconst = attack_name_to_move_const.get(aname, 'MOVE_TACKLE')
            dmg = min(max(a_dict['damage'], 0), 250)
            eff, desc = synthesize_attack_effect_and_desc(a_dict, texts)
            cost_out = {}
            for k_c, v_c in a_dict['cost'].items():
                if v_c > 0:
                    cost_out[f'ENERGY_{k_c}'] = v_c
            return (mconst, dmg, eff, aname[:20], desc, cost_out)

        m1, m1_dmg, m1_eff, m1_name, m1_desc, m1_cost = build_atk(atk_list[0] if len(atk_list) >= 1 else None)
        m2, m2_dmg, m2_eff, m2_name, m2_desc, m2_cost = build_atk(atk_list[1] if len(atk_list) >= 2 else None)

        if m1 == 'MOVE_NONE' and power_id == 0:
            m1 = 'MOVE_TACKLE'
            m1_dmg = 10
            m1_name = 'Tackle'
            m1_desc = 'Deals 10 HP damage to the\\nDefending Pokémon.'
            m1_cost = {'ENERGY_COLORLESS': 1}

        is_rare = 'TRUE' if (rc['rarity'] == 'STAR' or ctype == 'CARD_TYPE_POKEMON_STAGE2' or hp >= 90) else 'FALSE'
        weight = 5 if is_rare == 'TRUE' else (20 if ctype == 'CARD_TYPE_POKEMON_STAGE1' else 50)

        # Build informative 2-line Bag description (<= 2 lines, <= 18 chars/line for WIN_DESCRIPTION)
        st_lbl = 'Basic' if ctype == 'CARD_TYPE_POKEMON_BASIC' else ('Stage 1' if ctype == 'CARD_TYPE_POKEMON_STAGE1' else 'Stage 2')
        line1 = f'Base Set No. {cid:03d}'[:18]
        line2 = f'HP:{hp} - {st_lbl} PKMN'[:18]
        bag_desc = f'{line1}\\n{line2}'

        cards_out.append({
            'cardId': cid,
            'enum': c_enum,
            'label': label,
            'name': raw_name[:22],
            'species': species,
            'preEvoSpecies': pre_evo_species,
            'equivItemId': 'ITEM_NONE',
            'cardType': ctype,
            'energyType': energy,
            'weaknessType': weakness,
            'retreatCost': retreat,
            'maxHp': hp,
            'pokemonPowerId': power_id,
            'powerName': power_name,
            'powerDesc': power_desc,
            'move1': m1,
            'move2': m2,
            'move1Damage': m1_dmg,
            'move2Damage': m2_dmg,
            'move1Effect': m1_eff,
            'move2Effect': m2_eff,
            'move1Name': m1_name,
            'move1Desc': m1_desc,
            'move2Name': m2_name,
            'move2Desc': m2_desc,
            'move1Cost': m1_cost,
            'move2Cost': m2_cost,
            'encounterWeight': weight,
            'isRareShiny': is_rare,
            'description': bag_desc,
        })

    # Write include/constants/tcg_cards.h
    os.makedirs('include/constants', exist_ok=True)
    with open('include/constants/tcg_cards.h', 'w', encoding='utf-8', newline='\n') as f:
        f.write('#ifndef GUARD_CONSTANTS_TCG_CARDS_H\n')
        f.write('#define GUARD_CONSTANTS_TCG_CARDS_H\n\n')
        f.write('#define CARD_NONE 0\n')
        for c in cards_out:
            f.write(f"#define {c['enum']} {c['cardId']}\n")
        f.write('\n// Compatibility aliases\n')
        f.write('#define CARD_CHARIZARD CARD_CHARIZARD_LV76\n')
        f.write('#define CARD_PLUSPOWER CARD_PLUS_POWER\n')
        f.write('#define CARD_BILLS_PC CARD_BILLS_COMPUTER\n')
        f.write('#define CARD_POKE_FLUTE CARD_POKEMON_FLUTE\n')
        f.write('#define CARD_IMAKUNI CARD_IMAKUNI_CARD\n')
        f.write('#define CARD_IMPOSTER_PROF_OAK CARD_IMPOSTER_PROFESSOR_OAK\n')
        f.write('#define CARD_IMPOSTER_OAK_REVENGE CARD_IMPOSTER_OAKS_REVENGE\n')
        f.write('#define CARD_POKEMON_RETRANSFER CARD_POKEMON_RECALL\n')
        f.write('#define CARD_ROCKET_SNEAK_ATTACK CARD_ROCKETS_SNEAK_ATTACK\n')
        f.write(f'\n#define NUM_TCG_CARDS {len(cards_out)}\n\n')
        f.write('#endif // GUARD_CONSTANTS_TCG_CARDS_H\n')

    # Write src/data/tcg_cards.h
    def esc_c(s):
        s = s.replace('\r\n', '\n').replace('\r', '\n')
        s = s.replace('\n', '\\n')
        s = s.replace('"', '\\"')
        return s

    os.makedirs('src/data', exist_ok=True)
    with open('src/data/tcg_cards.h', 'w', encoding='utf-8', newline='\n') as f:
        f.write('// Autogenerated by tools/generate_tcg_data.py\n')
        f.write('#include "global.h"\n')
        f.write('#include "tcg.h"\n')
        f.write('#include "constants/species.h"\n')
        f.write('#include "constants/moves.h"\n')
        f.write('#include "constants/items.h"\n')
        f.write('#include "constants/battle_move_effects.h"\n')
        f.write('#include "constants/tcg_cards.h"\n\n')

        for c in cards_out:
            cid = c['cardId']
            f.write(f'static const u8 sCardName_{cid}[] = _("{esc_c(c["name"])}");\n')
            f.write(f'static const u8 sCardDesc_{cid}[] = _("{esc_c(c["description"])}");\n')
            if c['powerName']:
                f.write(f'static const u8 sCardPwrName_{cid}[] = _("{esc_c(c["powerName"])}");\n')
                f.write(f'static const u8 sCardPwrDesc_{cid}[] = _("{esc_c(c["powerDesc"])}");\n')
            if c['move1Name']:
                f.write(f'static const u8 sCardM1Name_{cid}[] = _("{esc_c(c["move1Name"])}");\n')
                f.write(f'static const u8 sCardM1Desc_{cid}[] = _("{esc_c(c["move1Desc"])}");\n')
            if c['move2Name']:
                f.write(f'static const u8 sCardM2Name_{cid}[] = _("{esc_c(c["move2Name"])}");\n')
                f.write(f'static const u8 sCardM2Desc_{cid}[] = _("{esc_c(c["move2Desc"])}");\n')

        f.write('\nconst struct TcgCardInfo gTcgCards[NUM_TCG_CARDS + 1] = {\n')
        f.write('    [0] = {0},\n')
        for c in cards_out:
            cid = c['cardId']
            f.write(f'    [{cid}] = {{\n')
            f.write(f'        .cardId = {cid},\n')
            f.write(f'        .name = sCardName_{cid},\n')
            f.write(f'        .species = {c["species"]},\n')
            f.write(f'        .preEvoSpecies = {c["preEvoSpecies"]},\n')
            f.write(f'        .equivItemId = {c["equivItemId"]},\n')
            f.write(f'        .cardType = {c["cardType"]},\n')
            f.write(f'        .energyType = {c["energyType"]},\n')
            f.write(f'        .weaknessType = {c["weaknessType"]},\n')
            f.write(f'        .retreatCost = {c["retreatCost"]},\n')
            f.write(f'        .maxHp = {c["maxHp"]},\n')
            f.write(f'        .pokemonPowerId = {c["pokemonPowerId"]},\n')
            f.write(f'        .powerName = {f"sCardPwrName_{cid}" if c["powerName"] else "NULL"},\n')
            f.write(f'        .powerDescription = {f"sCardPwrDesc_{cid}" if c["powerName"] else "NULL"},\n')
            f.write(f'        .move1 = {c["move1"]},\n')
            f.write(f'        .move2 = {c["move2"]},\n')
            f.write(f'        .move1Damage = {c["move1Damage"]},\n')
            f.write(f'        .move2Damage = {c["move2Damage"]},\n')
            f.write(f'        .move1Effect = {c["move1Effect"]},\n')
            f.write(f'        .move2Effect = {c["move2Effect"]},\n')
            f.write(f'        .move1Name = {f"sCardM1Name_{cid}" if c["move1Name"] else "NULL"},\n')
            f.write(f'        .move1Description = {f"sCardM1Desc_{cid}" if c["move1Name"] else "NULL"},\n')
            f.write(f'        .move2Name = {f"sCardM2Name_{cid}" if c["move2Name"] else "NULL"},\n')
            f.write(f'        .move2Description = {f"sCardM2Desc_{cid}" if c["move2Name"] else "NULL"},\n')

            c1_str = ', '.join(f'[{k}] = {v}' for k, v in c['move1Cost'].items())
            c2_str = ', '.join(f'[{k}] = {v}' for k, v in c['move2Cost'].items())
            f.write(f'        .move1Cost = {{ .energyCount = {{ {c1_str} }} }},\n')
            f.write(f'        .move2Cost = {{ .energyCount = {{ {c2_str} }} }},\n')
            f.write(f'        .encounterWeight = {c["encounterWeight"]},\n')
            f.write(f'        .isRareShiny = {c["isRareShiny"]},\n')
            f.write(f'        .description = sCardDesc_{cid},\n')
            f.write('    },\n')
        f.write('};\n\n')
        f.write('const u16 gTcgCardCount = NUM_TCG_CARDS;\n')

    # -----------------------------------------------------------------------
    # 3. Build Balanced 20-card Decks (gDefaultDecks[32] & gThematicDecks)
    # -----------------------------------------------------------------------
    card_by_id = {c['cardId']: c for c in cards_out}
    cards_by_species = {}
    for c in cards_out:
        sp = c['species']
        if sp != 'SPECIES_NONE':
            cards_by_species.setdefault(sp, []).append(c['cardId'])

    # Map trainer labels -> cardId
    trainer_id = {c['label']: c['cardId'] for c in cards_out if c['cardType'] in ('CARD_TYPE_TRAINER_ITEM', 'CARD_TYPE_TRAINER_SUPPORTER') or c['label'] in ('MysteriousFossil', 'ClefairyDoll')}

    T_OAK = trainer_id['ProfessorOak']
    T_BILL = trainer_id['Bill']
    T_POTION = trainer_id['Potion']
    T_SPOTION = trainer_id['SuperPotion']
    T_SWITCH = trainer_id['Switch']
    T_GUST = trainer_id['GustOfWind']
    T_PLUS = trainer_id['PlusPower']
    T_DEFEND = trainer_id['Defender']
    T_FHEAL = trainer_id['FullHeal']
    T_RECEIVER = trainer_id['Pokeball']
    T_TRADER = trainer_id['PokemonTrader']
    T_BREEDER = trainer_id['PokemonBreeder']
    T_SCOOP = trainer_id['ScoopUp']
    T_SSCOOP = trainer_id['SuperScoopUp']
    T_REVIVE = trainer_id['Revive']
    T_CSEARCH = trainer_id['ComputerSearch']
    T_IFINDER = trainer_id['ItemFinder']
    T_FUJI = trainer_id['MrFuji']
    T_LASS = trainer_id['Lass']
    T_GAMBLER = trainer_id['Gambler']
    T_FOSSIL = trainer_id['MysteriousFossil']
    T_BOSS = trainer_id['TheBosssWay']
    T_SNEAK = trainer_id['RocketsSneakAttack']
    T_RTRAP = trainer_id['TheRocketsTrap']
    T_GOOP = trainer_id['GoopGasAttack']
    T_SLEEP = trainer_id['Sleep']

    STANDARD_TRAINER_PACK = [T_OAK, T_BILL, T_RECEIVER, T_POTION, T_SWITCH, T_GUST, T_PLUS, T_FHEAL]

    def sp_card(sp_short, idx=0):
        cids = cards_by_species.get(f'SPECIES_{sp_short}', [])
        if not cids:
            return 1
        return cids[min(idx, len(cids) - 1)]

    def finalize_and_validate_deck(raw_list, fallback_trainers=None):
        """Ensure exactly 20 cards, <= 2 copies per cardId & per species, >= 1 Basic, 0 evolution orphans, and balanced trainers."""
        if fallback_trainers is None:
            fallback_trainers = STANDARD_TRAINER_PACK

        deck = []
        cid_cnt = {}
        sp_cnt = {}

        def can_add(cid):
            if cid not in card_by_id:
                return False
            if cid_cnt.get(cid, 0) >= 2:
                return False
            sp = card_by_id[cid]['species']
            if sp != 'SPECIES_NONE' and sp_cnt.get(sp, 0) >= 2:
                return False
            return True

        def add_card(cid):
            if not can_add(cid) or len(deck) >= 20:
                return False
            deck.append(cid)
            cid_cnt[cid] = cid_cnt.get(cid, 0) + 1
            sp = card_by_id[cid]['species']
            if sp != 'SPECIES_NONE':
                sp_cnt[sp] = sp_cnt.get(sp, 0) + 1
            return True

        # First pass: add requested Pokémon & their required pre-evolutions (max 12 Pokémon cards to guarantee 8 Trainer cards)
        for cid in raw_list:
            if cid not in card_by_id:
                continue
            c = card_by_id[cid]
            if c['species'] != 'SPECIES_NONE':
                if len(deck) >= 12:
                    continue
                # Check if it needs pre-evolution
                chain = []
                cur_c = c
                while cur_c['cardType'] in ('CARD_TYPE_POKEMON_STAGE1', 'CARD_TYPE_POKEMON_STAGE2') and cur_c['preEvoSpecies'] != 'SPECIES_NONE':
                    pre_sp = cur_c['preEvoSpecies']
                    if sp_cnt.get(pre_sp, 0) > 0:
                        break
                    pre_cids = cards_by_species.get(pre_sp, [])
                    if not pre_cids:
                        break
                    chain.insert(0, pre_cids[0])
                    cur_c = card_by_id[pre_cids[0]]
                if len(deck) + len(chain) + 1 > 13:
                    continue
                for pre_cid in chain:
                    add_card(pre_cid)
                add_card(cid)

        # Ensure at least 2 real Basic Pokémon
        real_basics = [cid for cid in deck if card_by_id[cid]['cardType'] == 'CARD_TYPE_POKEMON_BASIC' and card_by_id[cid]['species'] != 'SPECIES_NONE']
        if not real_basics:
            add_card(sp_card('BULBASAUR', 0))
            add_card(sp_card('PIDGEY', 0))

        # Second pass: add requested Trainer cards (keeping at least 6 trainer slots if possible)
        for cid in raw_list:
            if cid in card_by_id and card_by_id[cid]['species'] == 'SPECIES_NONE':
                add_card(cid)

        # Fill remaining slots up to 20 with balanced Trainers (Supporters + Items) and extra copies of Basics in deck
        for t_cid in fallback_trainers + [T_OAK, T_BILL, T_RECEIVER, T_POTION, T_SPOTION, T_SWITCH, T_GUST, T_PLUS, T_DEFEND, T_FHEAL, T_SCOOP, T_TRADER]:
            if len(deck) >= 20:
                break
            add_card(t_cid)

        # If still < 20, duplicate Basics already in deck or add Colorless Basics
        for cid in list(deck):
            if len(deck) >= 20:
                break
            if card_by_id[cid]['cardType'] == 'CARD_TYPE_POKEMON_BASIC':
                add_card(cid)

        for extra_sp in ['EEVEE', 'RATTATA', 'PIDGEY', 'SPEAROW', 'MEOWTH', 'KANGASKHAN', 'FARFETCHD', 'DODUO']:
            if len(deck) >= 20:
                break
            add_card(sp_card(extra_sp, 0))

        # Final orphan check: remove any Stage 1/2 whose preEvoSpecies is missing
        changed = True
        while changed:
            changed = False
            present_sp = {card_by_id[cid]['species'] for cid in deck if card_by_id[cid]['species'] != 'SPECIES_NONE'}
            for i, cid in enumerate(list(deck)):
                c = card_by_id[cid]
                if c['cardType'] in ('CARD_TYPE_POKEMON_STAGE1', 'CARD_TYPE_POKEMON_STAGE2') and c['preEvoSpecies'] != 'SPECIES_NONE':
                    if c['preEvoSpecies'] not in present_sp:
                        # Replace with a Trainer or Basic
                        deck.pop(i)
                        cid_cnt[cid] -= 1
                        sp_cnt[c['species']] -= 1
                        for rep in [T_OAK, T_BILL, T_POTION, T_SWITCH, T_GUST, T_PLUS, T_DEFEND, T_FHEAL, sp_card('PIDGEY', 0), sp_card('RATTATA', 0)]:
                            if add_card(rep):
                                break
                        changed = True
                        break

        return deck[:20]

    # 32 Canonical Default Decks (matching Kanto Starters, Gym Leaders, Rival, Elite Four, and Legends)
    curated_default_specs = [
        # 0-1: Bulbasaur Starter & Grass Variant
        ('Bulbasaur Deck', [
            sp_card('BULBASAUR', 0), sp_card('BULBASAUR', 1), sp_card('IVYSAUR', 0), sp_card('VENUSAUR', 0),
            sp_card('CATERPIE', 0), sp_card('METAPOD', 0), sp_card('BUTTERFREE', 0),
            sp_card('ODDISH', 0), sp_card('GLOOM', 0), sp_card('TANGELA', 0), sp_card('PIDGEY', 0), sp_card('PIDGEOTTO', 0),
            T_OAK, T_BILL, T_RECEIVER, T_POTION, T_SWITCH, T_GUST, T_PLUS, T_FHEAL
        ]),
        ('Venusaur Bloom', [
            sp_card('BULBASAUR', 2), sp_card('IVYSAUR', 1), sp_card('VENUSAUR', 1),
            sp_card('BELLSPROUT', 0), sp_card('WEEPINBELL', 0), sp_card('VICTREEBEL', 0),
            sp_card('SCYTHER', 0), sp_card('PINSIR', 0), sp_card('EXEGGCUTE', 0), sp_card('EXEGGUTOR', 0),
            sp_card('PARAS', 0), sp_card('PARASECT', 0),
            T_OAK, T_BILL, T_RECEIVER, T_SPOTION, T_SWITCH, T_BREEDER, T_POTION, T_FHEAL
        ]),
        # 2-3: Charmander Starter & Blaine Fire
        ('Charmander Deck', [
            sp_card('CHARMANDER', 0), sp_card('CHARMANDER', 1), sp_card('CHARMELEON', 0), sp_card('CHARIZARD', 0),
            sp_card('VULPIX', 0), sp_card('NINETALES', 0),
            sp_card('GROWLITHE', 0), sp_card('ARCANINE', 0),
            sp_card('MAGMAR', 0), sp_card('PONYTA', 0), sp_card('RAPIDASH', 0), sp_card('RATTATA', 0),
            T_OAK, T_BILL, T_RECEIVER, T_POTION, T_SWITCH, T_PLUS, T_DEFEND, T_FHEAL
        ]),
        ('Blaine Quiz', [
            sp_card('CHARMANDER', 2), sp_card('CHARMELEON', 0), sp_card('CHARIZARD', 1),
            sp_card('PONYTA', 1), sp_card('RAPIDASH', 1),
            sp_card('GROWLITHE', 1), sp_card('ARCANINE', 1),
            sp_card('VULPIX', 1), sp_card('NINETALES', 1),
            sp_card('MAGMAR', 1), sp_card('FLAREON', 0), sp_card('EEVEE', 0),
            T_OAK, T_BILL, T_RECEIVER, T_SPOTION, T_SWITCH, T_GUST, T_PLUS, T_GAMBLER
        ]),
        # 4-5: Squirtle Starter & Misty Water
        ('Squirtle Deck', [
            sp_card('SQUIRTLE', 0), sp_card('SQUIRTLE', 1), sp_card('WARTORTLE', 0), sp_card('BLASTOISE', 0),
            sp_card('POLIWAG', 0), sp_card('POLIWHIRL', 0), sp_card('POLIWRATH', 0),
            sp_card('STARYU', 0), sp_card('STARMIE', 0),
            sp_card('GOLDEEN', 0), sp_card('SEAKING', 0), sp_card('LAPRAS', 0),
            T_OAK, T_BILL, T_RECEIVER, T_POTION, T_SWITCH, T_GUST, T_PLUS, T_FHEAL
        ]),
        ('Misty Crush', [
            sp_card('STARYU', 1), sp_card('STARMIE', 0),
            sp_card('HORSEA', 0), sp_card('SEADRA', 0),
            sp_card('PSYDUCK', 0), sp_card('GOLDUCK', 0),
            sp_card('TENTACOOL', 0), sp_card('TENTACRUEL', 0),
            sp_card('LAPRAS', 1), sp_card('VAPOREON', 0), sp_card('EEVEE', 0), sp_card('GOLDEEN', 0),
            T_OAK, T_BILL, T_RECEIVER, T_SPOTION, T_SWITCH, T_GUST, T_SCOOP, T_PLUS
        ]),
        # 6-7: Erika Grass Decks
        ('Erika Perfume', [
            sp_card('ODDISH', 0), sp_card('ODDISH', 1), sp_card('GLOOM', 0), sp_card('VILEPLUME', 0),
            sp_card('BELLSPROUT', 1), sp_card('WEEPINBELL', 1), sp_card('VICTREEBEL', 0),
            sp_card('TANGELA', 0), sp_card('TANGELA', 1),
            sp_card('EXEGGCUTE', 0), sp_card('EXEGGUTOR', 0), sp_card('SCYTHER', 0),
            T_OAK, T_BILL, T_RECEIVER, T_POTION, T_SPOTION, T_SWITCH, T_FHEAL, T_DEFEND
        ]),
        ('Flower Power', [
            sp_card('ODDISH', 1), sp_card('GLOOM', 1), sp_card('VILEPLUME', 1),
            sp_card('PARAS', 0), sp_card('PARASECT', 0),
            sp_card('CATERPIE', 0), sp_card('METAPOD', 1), sp_card('BUTTERFREE', 0),
            sp_card('PINSIR', 0), sp_card('SCYTHER', 0), sp_card('VENONAT', 0), sp_card('VENOMOTH', 0),
            T_OAK, T_BILL, T_RECEIVER, T_POTION, T_SWITCH, T_GUST, T_PLUS, T_FHEAL
        ]),
        # 8-9: Lt. Surge Lightning Decks
        ('Surge Shock', [
            sp_card('PIKACHU', 0), sp_card('PIKACHU', 1), sp_card('RAICHU', 0), sp_card('RAICHU', 1),
            sp_card('VOLTORB', 0), sp_card('ELECTRODE', 0),
            sp_card('MAGNEMITE', 0), sp_card('MAGNETON', 0),
            sp_card('ELECTABUZZ', 0), sp_card('ELECTABUZZ', 1), sp_card('SPEAROW', 0), sp_card('FEAROW', 0),
            T_OAK, T_BILL, T_RECEIVER, T_POTION, T_SWITCH, T_GUST, T_PLUS, T_DEFEND
        ]),
        ('Power Gen', [
            sp_card('PIKACHU', 2), sp_card('RAICHU', 2),
            sp_card('MAGNEMITE', 1), sp_card('MAGNETON', 1),
            sp_card('VOLTORB', 1), sp_card('ELECTRODE', 1),
            sp_card('EEVEE', 0), sp_card('JOLTEON', 0),
            sp_card('ZAPDOS', 0), sp_card('ELECTABUZZ', 0), sp_card('PORYGON', 0), sp_card('MEOWTH', 0),
            T_OAK, T_BILL, T_RECEIVER, T_SPOTION, T_SWITCH, T_PLUS, T_DEFEND, T_TRADER
        ]),
        # 10-11: Brock Rock & Fighting Decks
        ('Brock Rock', [
            sp_card('GEODUDE', 0), sp_card('GEODUDE', 1), sp_card('GRAVELER', 0), sp_card('GOLEM', 0),
            sp_card('ONIX', 0), sp_card('ONIX', 1),
            sp_card('RHYHORN', 0), sp_card('RHYDON', 0),
            sp_card('CUBONE', 0), sp_card('MAROWAK', 0),
            sp_card('SANDSHREW', 0), sp_card('SANDSLASH', 0),
            T_OAK, T_BILL, T_RECEIVER, T_POTION, T_SWITCH, T_DEFEND, T_PLUS, T_FHEAL
        ]),
        ('Rock Crusher', [
            sp_card('MACHOP', 0), sp_card('MACHOKE', 0), sp_card('MACHAMP', 0),
            sp_card('HITMONLEE', 0), sp_card('HITMONCHAN', 0),
            sp_card('MANKEY', 0), sp_card('PRIMEAPE', 0),
            sp_card('KABUTO', 0), sp_card('KABUTOPS', 0), T_FOSSIL,
            sp_card('DIGLETT', 0), sp_card('DUGTRIO', 0),
            T_OAK, T_BILL, T_RECEIVER, T_POTION, T_SWITCH, T_GUST, T_PLUS, T_DEFEND
        ]),
        # 12-13: Koga Poison & Ninja Decks
        ('Koga Ninja', [
            sp_card('KOFFING', 0), sp_card('KOFFING', 1), sp_card('WEEZING', 0), sp_card('WEEZING', 1),
            sp_card('GRIMER', 0), sp_card('MUK', 0),
            sp_card('ZUBAT', 0), sp_card('GOLBAT', 0),
            sp_card('VENONAT', 0), sp_card('VENOMOTH', 0),
            sp_card('EKANS', 0), sp_card('ARBOK', 0),
            T_OAK, T_BILL, T_RECEIVER, T_POTION, T_SWITCH, T_GOOP, T_GUST, T_FHEAL
        ]),
        ('Venom Sting', [
            sp_card('WEEDLE', 0), sp_card('KAKUNA', 0), sp_card('BEEDRILL', 0),
            sp_card('NIDORAN_M', 0), sp_card('NIDORINO', 0), sp_card('NIDOKING', 0),
            sp_card('NIDORAN_F', 0), sp_card('NIDORINA', 0), sp_card('NIDOQUEEN', 0),
            sp_card('ZUBAT', 1), sp_card('GOLBAT', 1), sp_card('DITTO', 0),
            T_OAK, T_BILL, T_RECEIVER, T_POTION, T_SWITCH, T_BREEDER, T_PLUS, T_FHEAL
        ]),
        # 14-15: Sabrina Psychic Decks
        ('Sabrina ESP', [
            sp_card('ABRA', 0), sp_card('ABRA', 1), sp_card('KADABRA', 0), sp_card('ALAKAZAM', 0),
            sp_card('MR_MIME', 0), sp_card('JYNX', 0),
            sp_card('SLOWPOKE', 0), sp_card('SLOWBRO', 0),
            sp_card('DROWZEE', 0), sp_card('HYPNO', 0),
            sp_card('MEWTWO', 0), sp_card('CHANSEY', 0),
            T_OAK, T_BILL, T_RECEIVER, T_SPOTION, T_SWITCH, T_SCOOP, T_GUST, T_FHEAL
        ]),
        ('Strange Psy', [
            sp_card('GASTLY', 0), sp_card('GASTLY', 1), sp_card('HAUNTER', 0), sp_card('GENGAR', 0),
            sp_card('DROWZEE', 1), sp_card('HYPNO', 1),
            sp_card('ABRA', 2), sp_card('KADABRA', 1), sp_card('ALAKAZAM', 1),
            sp_card('MR_MIME', 1), sp_card('MEW', 0), sp_card('MEWTWO', 1),
            T_OAK, T_BILL, T_RECEIVER, T_POTION, T_SWITCH, T_SLEEP, T_PLUS, T_TRADER
        ]),
        # 16-17: Giovanni & Team Rocket Decks
        ('Giovanni Boss', [
            sp_card('DIGLETT', 0), sp_card('DIGLETT', 1), sp_card('DUGTRIO', 0), sp_card('DUGTRIO', 1),
            sp_card('RHYHORN', 0), sp_card('RHYDON', 0),
            sp_card('NIDORAN_M', 0), sp_card('NIDORINO', 0), sp_card('NIDOKING', 0),
            sp_card('MEOWTH', 0), sp_card('PERSIAN', 0), sp_card('KANGASKHAN', 0),
            T_OAK, T_BILL, T_RECEIVER, T_BOSS, T_SWITCH, T_GUST, T_PLUS, T_DEFEND
        ]),
        ('Team Rocket', [
            sp_card('EKANS', 1), sp_card('ARBOK', 1),
            sp_card('KOFFING', 2), sp_card('WEEZING', 1),
            sp_card('GRIMER', 1), sp_card('MUK', 1),
            sp_card('ZUBAT', 2), sp_card('GOLBAT', 1),
            sp_card('MEOWTH', 1), sp_card('PERSIAN', 1), sp_card('RATTATA', 1), sp_card('RATICATE', 1),
            T_OAK, T_BILL, T_BOSS, T_SNEAK, T_RTRAP, T_SWITCH, T_GUST, T_PLUS
        ]),
        # 18-21: Rival Progression Decks
        ('Rival Pallet', [
            sp_card('PIDGEY', 0), sp_card('PIDGEOTTO', 0),
            sp_card('RATTATA', 0), sp_card('RATICATE', 0),
            sp_card('SPEAROW', 0), sp_card('FEAROW', 0),
            sp_card('EEVEE', 0), sp_card('ABRA', 0),
            sp_card('SANDSHREW', 0), sp_card('DODUO', 0), sp_card('MEOWTH', 0), sp_card('FARFETCHD', 0),
            T_OAK, T_BILL, T_RECEIVER, T_POTION, T_SWITCH, T_GUST, T_PLUS, T_FHEAL
        ]),
        ('Rival Cerulean', [
            sp_card('PIDGEY', 1), sp_card('PIDGEOTTO', 1), sp_card('PIDGEOT', 0),
            sp_card('ABRA', 0), sp_card('KADABRA', 0),
            sp_card('RATTATA', 1), sp_card('RATICATE', 0),
            sp_card('SANDSHREW', 0), sp_card('SANDSLASH', 0),
            sp_card('GROWLITHE', 0), sp_card('EXEGGCUTE', 0), sp_card('MAGIKARP', 0),
            T_OAK, T_BILL, T_RECEIVER, T_POTION, T_SWITCH, T_GUST, T_PLUS, T_DEFEND
        ]),
        ('Rival Silph', [
            sp_card('PIDGEY', 0), sp_card('PIDGEOTTO', 0), sp_card('PIDGEOT', 0),
            sp_card('ABRA', 0), sp_card('KADABRA', 0), sp_card('ALAKAZAM', 0),
            sp_card('EXEGGCUTE', 0), sp_card('EXEGGUTOR', 0),
            sp_card('GROWLITHE', 0), sp_card('ARCANINE', 0),
            sp_card('MAGIKARP', 0), sp_card('GYARADOS', 0),
            T_OAK, T_BILL, T_RECEIVER, T_SPOTION, T_SWITCH, T_GUST, T_PLUS, T_FHEAL
        ]),
        ('Champion Blue', [
            sp_card('PIDGEY', 1), sp_card('PIDGEOTTO', 1), sp_card('PIDGEOT', 1),
            sp_card('ABRA', 1), sp_card('KADABRA', 1), sp_card('ALAKAZAM', 0),
            sp_card('RHYHORN', 0), sp_card('RHYDON', 0),
            sp_card('EXEGGCUTE', 0), sp_card('EXEGGUTOR', 0),
            sp_card('MAGIKARP', 0), sp_card('GYARADOS', 0),
            T_OAK, T_BILL, T_RECEIVER, T_SPOTION, T_SWITCH, T_GUST, T_PLUS, T_CSEARCH
        ]),
        # 22-23: Lorelei Ice / Water Decks
        ('Lorelei Ice', [
            sp_card('SEEL', 0), sp_card('SEEL', 1), sp_card('DEWGONG', 0), sp_card('DEWGONG', 1),
            sp_card('SHELLDER', 0), sp_card('CLOYSTER', 0),
            sp_card('SLOWPOKE', 0), sp_card('SLOWBRO', 0),
            sp_card('JYNX', 0), sp_card('JYNX', 1),
            sp_card('LAPRAS', 0), sp_card('LAPRAS', 1),
            T_OAK, T_BILL, T_RECEIVER, T_SPOTION, T_SWITCH, T_GUST, T_DEFEND, T_FHEAL
        ]),
        ('Arctic Freeze', [
            sp_card('ARTICUNO', 0), sp_card('ARTICUNO', 1),
            sp_card('SEEL', 0), sp_card('DEWGONG', 0),
            sp_card('SHELLDER', 1), sp_card('CLOYSTER', 1),
            sp_card('KRABBY', 0), sp_card('KINGLER', 0),
            sp_card('VAPOREON', 1), sp_card('EEVEE', 0), sp_card('LAPRAS', 0), sp_card('JYNX', 0),
            T_OAK, T_BILL, T_RECEIVER, T_POTION, T_SWITCH, T_SCOOP, T_PLUS, T_FHEAL
        ]),
        # 24-25: Bruno Fighting Decks
        ('Bruno Might', [
            sp_card('MACHOP', 0), sp_card('MACHOP', 1), sp_card('MACHOKE', 0), sp_card('MACHAMP', 0),
            sp_card('HITMONLEE', 0), sp_card('HITMONLEE', 1),
            sp_card('HITMONCHAN', 0), sp_card('HITMONCHAN', 1),
            sp_card('ONIX', 0), sp_card('ONIX', 1),
            sp_card('MANKEY', 0), sp_card('PRIMEAPE', 0),
            T_OAK, T_BILL, T_RECEIVER, T_POTION, T_SWITCH, T_GUST, T_PLUS, T_DEFEND
        ]),
        ('Muscles Fight', [
            sp_card('MACHOP', 2), sp_card('MACHOKE', 1), sp_card('MACHAMP', 1),
            sp_card('MANKEY', 1), sp_card('PRIMEAPE', 1),
            sp_card('SANDSHREW', 1), sp_card('SANDSLASH', 1),
            sp_card('CUBONE', 1), sp_card('MAROWAK', 1),
            sp_card('HITMONCHAN', 0), sp_card('HITMONLEE', 0), sp_card('KANGASKHAN', 0),
            T_OAK, T_BILL, T_RECEIVER, T_SPOTION, T_SWITCH, T_PLUS, T_DEFEND, T_FHEAL
        ]),
        # 26-27: Agatha Ghost / Poison Decks
        ('Agatha Ghost', [
            sp_card('GASTLY', 0), sp_card('GASTLY', 1), sp_card('HAUNTER', 0), sp_card('GENGAR', 0),
            sp_card('ZUBAT', 0), sp_card('GOLBAT', 0),
            sp_card('EKANS', 0), sp_card('ARBOK', 0),
            sp_card('HAUNTER', 1), sp_card('GENGAR', 1),
            sp_card('MR_MIME', 0), sp_card('JYNX', 0),
            T_OAK, T_BILL, T_RECEIVER, T_POTION, T_SWITCH, T_SLEEP, T_GUST, T_FHEAL
        ]),
        ('Dark Haunter', [
            sp_card('GASTLY', 2), sp_card('HAUNTER', 2), sp_card('GENGAR', 1),
            sp_card('DROWZEE', 1), sp_card('HYPNO', 1),
            sp_card('KOFFING', 1), sp_card('WEEZING', 1),
            sp_card('GRIMER', 1), sp_card('MUK', 1),
            sp_card('ZUBAT', 1), sp_card('GOLBAT', 1), sp_card('DITTO', 0),
            T_OAK, T_BILL, T_BOSS, T_POTION, T_SWITCH, T_SNEAK, T_PLUS, T_FHEAL
        ]),
        # 28-29: Lance Dragon Decks
        ('Lance Dragon', [
            sp_card('DRATINI', 0), sp_card('DRATINI', 1), sp_card('DRAGONAIR', 0), sp_card('DRAGONITE', 0),
            sp_card('MAGIKARP', 0), sp_card('GYARADOS', 0),
            sp_card('CHARMANDER', 0), sp_card('CHARMELEON', 0), sp_card('CHARIZARD', 0),
            sp_card('AERODACTYL', 0), T_FOSSIL, sp_card('LICKITUNG', 0),
            T_OAK, T_BILL, T_RECEIVER, T_SPOTION, T_SWITCH, T_BREEDER, T_PLUS, T_FHEAL
        ]),
        ('Dragon Flame', [
            sp_card('DRATINI', 1), sp_card('DRAGONAIR', 1), sp_card('DRAGONITE', 1),
            sp_card('MAGIKARP', 1), sp_card('GYARADOS', 1),
            sp_card('HORSEA', 1), sp_card('SEADRA', 1),
            sp_card('SNORLAX', 0), sp_card('KANGASKHAN', 1),
            sp_card('TAUROS', 0), sp_card('CHANSEY', 0), sp_card('PORYGON', 0),
            T_OAK, T_BILL, T_RECEIVER, T_SPOTION, T_SWITCH, T_SCOOP, T_PLUS, T_DEFEND
        ]),
        # 30-31: Legendary Grand Master Decks
        ('Legend Birds', [
            sp_card('MOLTRES', 0), sp_card('MOLTRES', 1),
            sp_card('ZAPDOS', 0), sp_card('ZAPDOS', 1),
            sp_card('ARTICUNO', 0), sp_card('ARTICUNO', 1),
            sp_card('AERODACTYL', 0), T_FOSSIL,
            sp_card('KANGASKHAN', 0), sp_card('CHANSEY', 0), sp_card('SNORLAX', 0), sp_card('DITTO', 0),
            T_OAK, T_BILL, T_RECEIVER, T_SPOTION, T_SWITCH, T_SCOOP, T_CSEARCH, T_FHEAL
        ]),
        ('Mythic Mewtwo', [
            sp_card('MEWTWO', 0), sp_card('MEWTWO', 2),
            sp_card('MEW', 0), sp_card('MEW', 1),
            sp_card('ABRA', 0), sp_card('KADABRA', 0), sp_card('ALAKAZAM', 0),
            sp_card('MR_MIME', 0), sp_card('CHANSEY', 1),
            sp_card('SNORLAX', 1), sp_card('DITTO', 0), sp_card('PORYGON', 1),
            T_OAK, T_BILL, T_RECEIVER, T_SPOTION, T_SWITCH, T_CSEARCH, T_IFINDER, T_FHEAL
        ]),
    ]

    default_decks = []
    for idx, (dname, raw_cards_list) in enumerate(curated_default_specs):
        final_cards = finalize_and_validate_deck(raw_cards_list)
        default_decks.append({
            'name': dname[:14],
            'wallpaper': idx % 4,
            'cards': final_cards,
        })

    # Start thematic_decks with the 32 canonical default decks
    thematic_decks = list(default_decks)
    seen_signatures = {tuple(sorted(d['cards'])) for d in thematic_decks}

    # Parse named GBC decks from poketcg and poketcg2-en (skipping Unnamed, Practice, Extra)
    SKIP_DECK_KEYWORDS = ('Unnamed', 'Practice', 'Extra')
    gbc_raw_decks = []
    for dfile in ['poketcg/src/data/decks.asm', 'poketcg2-en/src/data/decks.asm']:
        if not os.path.exists(dfile):
            continue
        content = tcg_asm_parser.read_text(dfile)
        blocks = re.split(r'\n(?=[A-Za-z0-9_]+Deck:)', content)
        for b in blocks:
            m = re.match(r'^([A-Za-z0-9_]+)Deck:', b.strip())
            if not m:
                continue
            dlabel = m.group(1)
            if any(kw in dlabel for kw in SKIP_DECK_KEYWORDS):
                continue
            raw_entries = []
            for line in b.splitlines():
                m_c = re.match(r'^\s*(?:card_item|deck_list_item)\s+([A-Za-z0-9_]+),\s*(\d+)', line)
                if not m_c:
                    m_c = re.match(r'^\s*db\s+(\d+),\s*([A-Za-z0-9_]+)', line)
                    if m_c:
                        cname, count = m_c.group(2), int(m_c.group(1))
                    else:
                        continue
                else:
                    cname, count = m_c.group(1), int(m_c.group(2))
                if 'ENERGY' in cname:
                    continue
                cid = enum_to_id.get(cname) or enum_to_id.get('CARD_' + cname)
                if cid:
                    raw_entries.extend([cid] * min(count, 2))
            if len(raw_entries) >= 8:
                gbc_raw_decks.append((dlabel, raw_entries))

    def deck_multiset_overlap(c_a, c_b):
        from collections import Counter
        ca, cb = Counter(c_a), Counter(c_b)
        return sum((ca & cb).values())

    for idx, (dlabel, raw_entries) in enumerate(gbc_raw_decks):
        clean_title = re.sub(r'(?<!^)(?=[A-Z])', ' ', dlabel).strip()[:14]
        pokes = [cid for cid in raw_entries if card_by_id[cid]['species'] != 'SPECIES_NONE']
        trainers = [cid for cid in raw_entries if card_by_id[cid]['species'] == 'SPECIES_NONE']

        # Variant 1: First 12 Pokémon + 8 Trainers
        v1_cards = finalize_and_validate_deck(pokes[:12] + trainers[:8])
        sig1 = tuple(sorted(v1_cards))
        cur_used = {cid for d in thematic_decks for cid in d['cards']}
        max_ov1 = max((deck_multiset_overlap(v1_cards, d['cards']) for d in thematic_decks), default=0)
        if sig1 not in seen_signatures and (max_ov1 < 15 or any(c not in cur_used for c in v1_cards)):
            seen_signatures.add(sig1)
            thematic_decks.append({
                'name': clean_title,
                'wallpaper': len(thematic_decks) % 4,
                'cards': v1_cards,
            })

        # Only build Variant 2 if there are >= 5 genuinely different Pokémon cards remaining
        rem_pokes = [cid for cid in pokes[8:] if cid not in pokes[:6]]
        if len(set(rem_pokes)) >= 5:
            v2_cards = finalize_and_validate_deck(rem_pokes[:12] + trainers[::-1][:8])
            sig2 = tuple(sorted(v2_cards))
            cur_used = {cid for d in thematic_decks for cid in d['cards']}
            max_ov2 = max((deck_multiset_overlap(v2_cards, d['cards']) for d in thematic_decks), default=0)
            if sig2 not in seen_signatures and max_ov2 < 14 and any(c not in cur_used for c in v2_cards):
                seen_signatures.add(sig2)
                thematic_decks.append({
                    'name': (clean_title[:11] + ' II')[:14],
                    'wallpaper': len(thematic_decks) % 4,
                    'cards': v2_cards,
                })

    # Pack remaining unused cards (that have valid pre-evolutions) into clean thematic decks
    bucket_titles = {
        'ENERGY_GRASS': 'Kanto Forest',
        'ENERGY_FIRE': 'Volcano Blaze',
        'ENERGY_WATER': 'Cerulean Wave',
        'ENERGY_LIGHTNING': 'Power Plant',
        'ENERGY_PSYCHIC': 'Saffron Mind',
        'ENERGY_FIGHTING': 'Dojo Mastery',
        'ENERGY_COLORLESS': 'Normal Safari',
    }
    bucket_counters = {}
    for _round in range(8):
        used_cids = {cid for d in thematic_decks for cid in d['cards']}
        unused_pokes = [
            c['cardId'] for c in cards_out
            if c['cardId'] not in used_cids and c['species'] != 'SPECIES_NONE'
        ]
        unused_trainers = [
            c['cardId'] for c in cards_out
            if c['cardId'] not in used_cids and c['species'] == 'SPECIES_NONE'
        ]
        if not unused_pokes and not unused_trainers:
            break
        theme_buckets = {}
        for cid in unused_pokes:
            et = card_by_id[cid]['energyType']
            theme_buckets.setdefault(et, []).append(cid)
        if not theme_buckets and unused_trainers:
            theme_buckets['ENERGY_COLORLESS'] = [sp_card('SNORLAX', 0), sp_card('CHANSEY', 0), sp_card('KANGASKHAN', 0), sp_card('DITTO', 0)]
        added_any = False
        for et, cids in theme_buckets.items():
            btitle = bucket_titles.get(et, 'Kanto Master')
            for i in range(0, len(cids), 4):
                chunk = cids[i:i + 4]
                t_pack = (unused_trainers[:4] + STANDARD_TRAINER_PACK)[:8]
                d_cards = finalize_and_validate_deck(chunk + t_pack, fallback_trainers=t_pack)
                if any(u in d_cards for u in chunk + unused_trainers):
                    sig = tuple(sorted(d_cards))
                    if sig not in seen_signatures:
                        seen_signatures.add(sig)
                        b_idx = bucket_counters.get(et, 0) + 1
                        bucket_counters[et] = b_idx
                        thematic_decks.append({
                            'name': f'{btitle[:11]} {b_idx}'[:14],
                            'wallpaper': len(thematic_decks) % 4,
                            'cards': d_cards,
                        })
                        added_any = True
                        unused_trainers = [t for t in unused_trainers if t not in d_cards]
        if not added_any:
            break

    # Write src/data/tcg_decks.h
    with open('src/data/tcg_decks.h', 'w', encoding='utf-8', newline='\n') as f:
        f.write('// Autogenerated by tools/generate_tcg_data.py\n')
        f.write('#include "global.h"\n')
        f.write('#include "tcg.h"\n')
        f.write('#include "constants/tcg_cards.h"\n\n')
        f.write('const struct TcgDeck gDefaultDecks[MAX_DEFAULT_DECKS] = {\n')
        for idx, d in enumerate(default_decks):
            c_str = ', '.join(str(x) for x in d['cards'])
            f.write(f'    [{idx}] = {{\n')
            f.write(f'        .name = _("{esc_c(d["name"])}"),\n')
            f.write(f'        .wallpaper = {d["wallpaper"]},\n')
            f.write(f'        .cards = {{ {c_str} }},\n')
            f.write('    },\n')
        f.write('};\n\n')
        f.write(f'const u16 gDefaultDeckCount = {len(default_decks)};\n\n')

        f.write(f'const struct TcgDeck gThematicDecks[{len(thematic_decks)}] = {{\n')
        for idx, d in enumerate(thematic_decks):
            c_str = ', '.join(str(x) for x in d['cards'])
            f.write(f'    [{idx}] = {{\n')
            f.write(f'        .name = _("{esc_c(d["name"])}"),\n')
            f.write(f'        .wallpaper = {d["wallpaper"]},\n')
            f.write(f'        .cards = {{ {c_str} }},\n')
            f.write('    },\n')
        f.write('};\n\n')
        f.write(f'const u16 gThematicDeckCount = {len(thematic_decks)};\n')

    # Write tools/unused_deck_cards.txt
    final_used = {cid for d in thematic_decks for cid in d['cards']} | {cid for d in default_decks for cid in d['cards']}
    with open('tools/unused_deck_cards.txt', 'w', encoding='utf-8', newline='\n') as f:
        f.write('# Cards not currently assigned to any deck\n')
        unused_cnt = 0
        for c in cards_out:
            if c['cardId'] not in final_used:
                f.write(f"{c['cardId']}: {c['enum']} ({c['name']} - {c['cardType']})\n")
                unused_cnt += 1
        f.write(f'\nTotal unused cards: {unused_cnt} / {len(cards_out)}\n')

    # -----------------------------------------------------------------------
    # 4. Build Deterministic Trainer-to-Deck Mapping (src/data/trainer_tcg_decks.h)
    # -----------------------------------------------------------------------
    # Explicit canonical assignments for Gym Leaders, Elite Four, Boss Giovanni, and Rival
    EXPLICIT_TRAINER_IDS = {
        314: 10, # TRAINER_LEADER_BROCK -> Brock Rock
        315: 5,  # TRAINER_LEADER_MISTY -> Misty Crush
        316: 8,  # TRAINER_LEADER_LT_SURGE -> Surge Shock
        317: 6,  # TRAINER_LEADER_ERIKA -> Erika Perfume
        318: 12, # TRAINER_LEADER_KOGA -> Koga Ninja
        319: 3,  # TRAINER_LEADER_BLAINE -> Blaine Quiz
        320: 14, # TRAINER_LEADER_SABRINA -> Sabrina ESP
        248: 16, # TRAINER_BOSS_GIOVANNI -> Giovanni Boss
        249: 17, # TRAINER_BOSS_GIOVANNI_2 -> Team Rocket
        250: 16, # TRAINER_LEADER_GIOVANNI -> Giovanni Boss
        310: 22, # TRAINER_ELITE_FOUR_LORELEI -> Lorelei Ice
        311: 24, # TRAINER_ELITE_FOUR_BRUNO -> Bruno Might
        312: 26, # TRAINER_ELITE_FOUR_AGATHA -> Agatha Ghost
        313: 28, # TRAINER_ELITE_FOUR_LANCE -> Lance Dragon
        326: 19, 327: 19, 328: 19, # Rival SS Anne
        329: 19, 330: 19, 331: 19, # Rival Pokemon Tower
        332: 20, 333: 20, 334: 20, # Rival Silph
        335: 20, 336: 20, 337: 20, # Rival Route 22 Late
        338: 21, 339: 21, 340: 21, # Champion Blue
    }

    deck_species_sets = []
    for d in thematic_decks:
        sp_set = {card_by_id[cid]['species'] for cid in d['cards'] if card_by_id[cid]['species'] != 'SPECIES_NONE'}
        deck_species_sets.append(sp_set)

    trainer_party_species = {}
    for pfile in ['src/data/trainer_parties.h', 'src/data/trainers.h']:
        if not os.path.exists(pfile):
            continue
        pcontent = open(pfile, 'r', encoding='utf-8', errors='ignore').read()
        for idx_t, block in enumerate(re.split(r'\n(?=\s*\[TRAINER_)', pcontent)):
            sps = re.findall(r'SPECIES_[A-Z0-9_]+', block)
            if sps and idx_t < 624:
                trainer_party_species[idx_t] = set(sps)

    with open('src/data/trainer_tcg_decks.h', 'w', encoding='utf-8', newline='\n') as f:
        f.write('// Autogenerated by tools/generate_tcg_data.py\n')
        f.write('// Static deterministic mapping of 624 FRLG trainers to thematic TCG decks\n')
        f.write('#include "global.h"\n')
        f.write('#include "constants/opponents.h"\n\n')
        f.write('const u16 gTrainerToDeckMap[624] = {\n')
        for tid in range(624):
            if tid in EXPLICIT_TRAINER_IDS:
                best_deck = EXPLICIT_TRAINER_IDS[tid]
            else:
                tsp = trainer_party_species.get(tid, set())
                best_deck = tid % len(thematic_decks)
                best_score = -1
                if tsp:
                    for didx, dsp in enumerate(deck_species_sets):
                        score = len(tsp & dsp)
                        if score > best_score:
                            best_score = score
                            best_deck = didx
            f.write(f'    [{tid}] = {best_deck},\n')
        f.write('};\n')

    print(f'[OK] Generated {len(cards_out)} cards, {len(default_decks)} default decks, {len(thematic_decks)} thematic decks ({unused_cnt} unused cards).')


if __name__ == '__main__':
    main()
