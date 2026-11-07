#!/usr/bin/env python3
import sys
sys.stdout.reconfigure(encoding='utf-8')
import glob
import re
import os

texts = {}
for p in glob.glob('poketcg2-en/src/text/**/*.asm', recursive=True) + glob.glob('poketcg/src/text/**/*.asm', recursive=True):
    with open(p, 'r', encoding='latin-1') as f:
        content = f.read()
    blocks = re.findall(r'([A-Za-z0-9_]+):([\s\S]*?)(?=\ndone|\n[A-Za-z0-9_]+:|\Z)', content)
    for label, body in blocks:
        lines = []
        for m in re.finditer(r'(?:text|line)\s+"([^"]*)"', body):
            lines.append(m.group(1))
        if lines and label not in texts:
            texts[label] = " ".join(lines)

moves_set = set()
with open('include/constants/moves.h', 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        m = re.search(r'\b(MOVE_[A-Z0-9_]+)\b', line)
        if m:
            moves_set.add(m.group(1))

def map_move_to_constant(move_name):
    if not move_name:
        return "MOVE_NONE"
    clean = re.sub(r'[^A-Za-z0-9]', '', move_name).upper()
    cand = f"MOVE_{clean}"
    if cand in moves_set:
        return cand
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', move_name)
    cand2 = 'MOVE_' + re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).upper().replace(' ', '_').replace('-', '_')
    if cand2 in moves_set:
        return cand2
    replacements = {
        "LEECHSEED": "MOVE_LEECH_SEED", "VINEWHIP": "MOVE_VINE_WHIP",
        "POISONPOWDER": "MOVE_POISON_POWDER", "SOLARBEAM": "MOVE_SOLAR_BEAM",
        "STRINGSHOT": "MOVE_STRING_SHOT", "POISONSTING": "MOVE_POISON_STING",
        "TWINEEDLE": "MOVE_TWINEEDLE", "PINMISSILE": "MOVE_PIN_MISSILE",
        "FURYATTACK": "MOVE_FURY_ATTACK", "FISTOFSTONE": "MOVE_ROCK_THROW",
        "FIREPUNCH": "MOVE_FIRE_PUNCH", "THUNDERPUNCH": "MOVE_THUNDER_PUNCH",
        "ICEPUNCH": "MOVE_ICE_PUNCH", "THUNDERJOLT": "MOVE_THUNDER_SHOCK",
        "AGILITY": "MOVE_AGILITY", "WATERGUN": "MOVE_WATER_GUN",
        "HYDROPUMP": "MOVE_HYDRO_PUMP", "BUBBLEBEAM": "MOVE_BUBBLE_BEAM",
        "WITHDRAW": "MOVE_WITHDRAW", "SUPERFANG": "MOVE_SUPER_FANG",
        "HYPERFANG": "MOVE_HYPER_FANG", "FLAMETHROWER": "MOVE_FLAMETHROWER",
        "FIRESPIN": "MOVE_FIRE_SPIN", "EMBER": "MOVE_EMBER",
        "CONFUSION": "MOVE_CONFUSION", "PSYCHIC": "MOVE_PSYCHIC",
        "NIGHTSHADE": "MOVE_NIGHT_SHADE", "DREAMEATER": "MOVE_DREAM_EATER",
        "HYPNOSIS": "MOVE_HYPNOSIS", "CONFUSERAY": "MOVE_CONFUSE_RAY",
        "BARRAGE": "MOVE_BARRAGE", "EGGBOMB": "MOVE_EGG_BOMB",
        "SELFDESTRUCT": "MOVE_SELF_DESTRUCT", "EXPLOSION": "MOVE_EXPLOSION",
        "SLUDGE": "MOVE_SLUDGE", "SMOG": "MOVE_SMOG",
        "POISONFANG": "MOVE_POISON_FANG", "POISONTAIL": "MOVE_POISON_TAIL",
        "POISONBREATH": "MOVE_SMOG", "POISONSPIT": "MOVE_POISON_STING",
        "ACID": "MOVE_ACID", "BONEMERANG": "MOVE_BONEMERANG",
        "BONECLUB": "MOVE_BONE_CLUB", "EARTHQUAKE": "MOVE_EARTHQUAKE",
        "DIG": "MOVE_DIG", "ROCKTHROW": "MOVE_ROCK_THROW",
        "LIGHTSCREEN": "MOVE_LIGHT_SCREEN", "REFLECT": "MOVE_REFLECT",
        "SWIFT": "MOVE_SWIFT", "HYPERBEAM": "MOVE_HYPER_BEAM",
        "RAZORLEAF": "MOVE_RAZOR_LEAF", "PETALDANCE": "MOVE_PETAL_DANCE",
        "MEGADRAIN": "MOVE_MEGA_DRAIN", "ABSORB": "MOVE_ABSORB",
        "GIGADRAIN": "MOVE_GIGA_DRAIN", "GNAW": "MOVE_BITE",
        "NIBBLE": "MOVE_BITE", "CHOMP": "MOVE_CRUNCH",
        "SLASH": "MOVE_SLASH", "SCRATCH": "MOVE_SCRATCH",
        "POUND": "MOVE_POUND", "SLAP": "MOVE_DOUBLE_SLAP",
        "DOUBLESWIPES": "MOVE_FURY_SWIPES", "FYSWIPES": "MOVE_FURY_SWIPES",
        "FURYCLAWS": "MOVE_FURY_SWIPES", "PECK": "MOVE_PECK",
        "DRILLPECK": "MOVE_DRILL_PECK", "WINGATTACK": "MOVE_WING_ATTACK",
        "FLY": "MOVE_FLY", "GUST": "MOVE_GUST",
        "WHIRLWIND": "MOVE_WHIRLWIND", "RAZORWIND": "MOVE_RAZOR_WIND",
        "BLIZZARD": "MOVE_BLIZZARD", "ICEBEAM": "MOVE_ICE_BEAM",
        "AURORABEAM": "MOVE_AURORA_BEAM", "ICYWIND": "MOVE_ICY_WIND",
        "POWDERHIT": "MOVE_POWDER_SNOW", "THUNDER": "MOVE_THUNDER",
        "THUNDERBOLT": "MOVE_THUNDERBOLT", "SPARK": "MOVE_SPARK",
        "ZAP": "MOVE_SHOCK_WAVE", "BIGEXPLOSION": "MOVE_EXPLOSION",
        "FIREBLAST": "MOVE_FIRE_BLAST", "HEATWAVE": "MOVE_HEAT_WAVE",
        "FLAMEWHEEL": "MOVE_FLAME_WHEEL", "SURF": "MOVE_SURF",
        "WATERFALL": "MOVE_WATERFALL", "DIVE": "MOVE_DIVE",
        "WHIRLPOOL": "MOVE_WHIRLPOOL", "CLAMP": "MOVE_CLAMP",
        "BUBBLE": "MOVE_BUBBLE", "SMOKESCREEN": "MOVE_SMOKESCREEN",
        "HAZE": "MOVE_HAZE", "MIST": "MOVE_MIST",
    }
    if clean in replacements and replacements[clean] in moves_set:
        return replacements[clean]
    for m in moves_set:
        if clean in m:
            return m
    return "MOVE_TACKLE"

# Let's test parse on cards1.asm
with open('poketcg2-en/src/data/cards1.asm', 'r', encoding='latin-1') as f:
    content = f.read()

card_chunks = re.split(r'\n(?=[A-Za-z0-9_]+Card:)', content)
parsed_samples = 0
for chunk in card_chunks[:15]:
    lines = chunk.strip().splitlines()
    if not lines: continue
    m_card = re.match(r'^([A-Za-z0-9_]+)Card:', lines[0])
    if not m_card: continue
    label = m_card.group(1)
    
    in_atk = 0
    atk1_name = None
    atk1_dmg = 0
    atk2_name = None
    atk2_dmg = 0
    atk1_is_power = False

    for l in lines[1:]:
        raw_l = l
        if 'pokemon power' in raw_l.lower():
            atk1_is_power = True
            in_atk = 1
        elif 'attack 1' in raw_l.lower():
            in_atk = 1
        elif 'attack 2' in raw_l.lower():
            in_atk = 2

        l_code = l.split(';')[0].strip()
        if not l_code: continue

        if l_code.startswith('tx '):
            sym = l_code.split()[1]
            if in_atk == 1 and atk1_name is None:
                atk1_name = texts.get(sym, sym).replace('Name', '')
            elif in_atk == 2 and atk2_name is None:
                atk2_name = texts.get(sym, sym).replace('Name', '')
        elif l_code.startswith('db ') and 'damage' in raw_l:
            m_d = re.search(r'db\s+(\d+)', l_code)
            if m_d:
                dmg = int(m_d.group(1))
                if in_atk == 1: atk1_dmg = dmg
                elif in_atk == 2: atk2_dmg = dmg

    m1_const = map_move_to_constant(atk1_name) if atk1_name and not atk1_is_power else "MOVE_NONE"
    m2_const = map_move_to_constant(atk2_name) if atk2_name else "MOVE_NONE"

    print(f"{label}: Power={atk1_is_power} | Atk1: '{atk1_name}' ({atk1_dmg} dmg) -> {m1_const} | Atk2: '{atk2_name}' ({atk2_dmg} dmg) -> {m2_const}")
    parsed_samples += 1
