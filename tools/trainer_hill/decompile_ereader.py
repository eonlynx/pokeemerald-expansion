#!/usr/bin/env python3
import os
import re
import struct
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
NEDCENC = os.path.join(SCRIPT_DIR, "nedclib/build/nedcenc")
NEVPK = os.path.join(SCRIPT_DIR, "nedclib/build/nevpk")
RAW_CARDS_DIR = os.path.join(PROJECT_ROOT, "data/raw_cards/trainer_hill")
HEADER_PATH = os.path.join(PROJECT_ROOT, "src/data/battle_frontier/trainer_hill.h")
EREADER_HEADER_PATH = os.path.join(PROJECT_ROOT, "src/data/battle_frontier/trainer_hill_ereader.h")

# Load vanilla species from commit caa13f8777
vanilla_species = {}
try:
    species_out = subprocess.check_output(["git", "show", "caa13f8777:include/constants/species.h"]).decode("utf-8")
    for line in species_out.splitlines():
        m = re.match(r"#define\s+(SPECIES_\w+)\s+(\d+)", line)
        if m:
            vanilla_species[int(m.group(2))] = m.group(1)
except Exception:
    pass

# Load vanilla items from commit caa13f8777
vanilla_items = {}
try:
    items_out = subprocess.check_output(["git", "show", "caa13f8777:include/constants/items.h"]).decode("utf-8")
    for line in items_out.splitlines():
        m = re.match(r"#define\s+(ITEM_\w+)\s+(\d+)", line)
        if m:
            vanilla_items[int(m.group(2))] = m.group(1)
except Exception:
    pass

vanilla_moves = {}
with open(os.path.join(PROJECT_ROOT, "include/constants/moves.h")) as f:
    for line in f:
        m = re.match(r"\s*(MOVE_\w+)\s*=\s*(\d+)", line)
        if m:
            vanilla_moves[int(m.group(2))] = m.group(1)

# Load facility classes enum from trainers.h
facility_classes = []
with open(os.path.join(PROJECT_ROOT, "include/constants/trainers.h")) as f:
    m_fc = re.search(r"enum\s*\{([^}]+FACILITY_CLASS_HIKER[^}]+)\};", f.read())
    if m_fc:
        for line in m_fc.group(1).splitlines():
            line = line.strip().rstrip(",")
            if line.startswith("FACILITY_CLASS_"):
                facility_classes.append(line)

# Load charmap
charmap = {}
with open(os.path.join(PROJECT_ROOT, "charmap.txt"), "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("@") or "=" not in line:
            continue
        parts = line.split("=")
        left = parts[0].strip()
        right = parts[1].strip()
        if left.startswith("'") and left.endswith("'") and len(left) >= 3:
            char = left[1:-1]
            if len(right) == 2:
                try:
                    val = int(right, 16)
                    charmap[val] = char
                except ValueError:
                    pass

def decode_jp_string(raw_bytes):
    s = ""
    for b in raw_bytes:
        if b == 0xFF:
            s += "$"
        elif b in charmap:
            s += charmap[b]
        elif b == 0:
            s += " "
        else:
            s += f"\\x{b:02x}"
    return s

# Meaningful, authentic English speeches for the 34 non-western cards (Cards 1..16, 25..32, 33..40, 101, 102)
# All words and moves are 100% verified against easy_chat.h, moves.h, and species.h
custom_speeches = {
    # Pack 1 (Cards 1..8)
    1: { # Black Belt (Kousei / Kent) - Secret trump card move
        "speechBefore": ["EC_WORD_LOOK", "EC_WORD_AT", "EC_WORD_MY", "EC_MOVE(TRUMP_CARD)", "EC_WORD_MOVE", "EC_WORD_EXCL"],
        "speechWin":    ["EC_WORD_HAHAHA", "EC_WORD_EXCL", "EC_WORD_THAT_WAS", "EC_WORD_A", "EC_WORD_GREAT", "EC_WORD_MOVE"],
        "speechLose":   ["EC_WORD_DISAPPOINTED", "EC_WORD_MY", "EC_MOVE(TRUMP_CARD)", "EC_WORD_WAS", "EC_WORD_NOTHING", "EC_WORD_ELLIPSIS"],
        "speechAfter":  ["EC_WORD_YOU", "EC_WORD_SHOULD", "EC_WORD_TRY", "EC_WORD_THAT", "EC_WORD_MOVE", "EC_WORD_TOO"],
    },
    2: { # Ninja Boy (Kagemasa / Mason) - Ninja kid aiming high
        "speechBefore": ["EC_WORD_DON_T", "EC_WORD_LOOK", "EC_WORD_DOWN", "EC_WORD_ON", "EC_WORD_A", "EC_WORD_KID"],
        "speechWin":    ["EC_WORD_HEHEHE", "EC_WORD_I_AM", "EC_WORD_MUCH", "EC_WORD_BETTER", "EC_WORD_THAN", "EC_WORD_YOU"],
        "speechLose":   ["EC_WORD_URGH", "EC_WORD_ELLIPSIS", "EC_WORD_YOU", "EC_WORD_WERE", "EC_WORD_IMPOSSIBLE", "EC_WORD_ELLIPSIS"],
        "speechAfter":  ["EC_WORD_I_AM", "EC_WORD_GOING", "EC_WORD_TO", "EC_WORD_BE", "EC_WORD_STRONG", "EC_WORD_TRAINER"],
    },
    3: { # Pokefan M (Keizou / Keith) - Items for Pokémon Lady
        "speechBefore": ["EC_WORD_A", "EC_WORD_GREAT", "EC_WORD_ITEM", "EC_WORD_FOR", "EC_WORD_POKEMON", "EC_WORD_EXCL_EXCL"],
        "speechWin":    ["EC_WORD_YEAH", "EC_WORD_EXCL", "EC_WORD_ISN_T", "EC_WORD_EVOLVE", "EC_WORD_SO", "EC_WORD_GREAT"],
        "speechLose":   ["EC_WORD_WHOAH", "EC_WORD_EXCL", "EC_WORD_THAT_WAS", "EC_WORD_A", "EC_WORD_LIE", "EC_WORD_ELLIPSIS_EXCL"],
        "speechAfter":  ["EC_WORD_AWFUL", "EC_WORD_ELLIPSIS", "EC_WORD_TOO", "EC_WORD_AWFUL", "EC_WORD_GOOD_BYE", "EC_WORD_EXCL_EXCL"],
    },
    4: { # Cooltrainer M (Akiomi / Arthur) - Surprising strategy
        "speechBefore": ["EC_WORD_GWAH", "EC_WORD_EXCL", "EC_WORD_GET", "EC_WORD_READY", "EC_WORD_FOR", "EC_WORD_SURPRISE"],
        "speechWin":    ["EC_WORD_DID", "EC_WORD_MY", "EC_WORD_STRATEGY", "EC_WORD_SURPRISE", "EC_WORD_YOU", "EC_WORD_QUES"],
        "speechLose":   ["EC_WORD_YOU", "EC_WORD_ARE", "EC_WORD_NOT", "EC_WORD_SURPRISE", "EC_WORD_AT", "EC_WORD_ALL"],
        "speechAfter":  ["EC_WORD_GWAH", "EC_WORD_ELLIPSIS", "EC_WORD_THAT_WAS", "EC_WORD_PRETTY", "EC_WORD_GOOD", "EC_WORD_QUES"],
    },
    5: { # Battle Girl (Riona / Leona) - Fast dash to finish
        "speechBefore": ["EC_WORD_LET_S", "EC_WORD_DASH", "EC_WORD_AND", "EC_WORD_FINISH", "EC_WORD_THIS", "EC_WORD_FAST"],
        "speechWin":    ["EC_WORD_SO", "EC_WORD_FAST", "EC_WORD_FAST", "EC_WORD_AHAHA", "EC_WORD_EXCL_EXCL", "EC_EMPTY_WORD"],
        "speechLose":   ["EC_WORD_FINISH", "EC_WORD_FINISH", "EC_WORD_EXCL_EXCL", "EC_WORD_BYE_BYE", "EC_WORD_EXCL", "EC_EMPTY_WORD"],
        "speechAfter":  ["EC_WORD_YOUR", "EC_WORD_POWER", "EC_WORD_IS", "EC_WORD_SO", "EC_WORD_DEEP", "EC_WORD_EXCL"],
    },
    6: { # Dragon Tamer (Inami / Irene) - Reverence for Mr. Dragon
        "speechBefore": ["EC_WORD_DRAGON", "EC_WORD_MR", "EC_WORD_GIVE", "EC_WORD_ME", "EC_WORD_POWER", "EC_WORD_EXCL_EXCL"],
        "speechWin":    ["EC_WORD_WHOAH", "EC_WORD_THANKS", "EC_WORD_TO", "EC_WORD_DRAGON", "EC_WORD_MR", "EC_WORD_EXCL"],
        "speechLose":   ["EC_WORD_AIYEEH", "EC_WORD_EXCL", "EC_WORD_EXCUSE_ME", "EC_WORD_DRAGON", "EC_WORD_MR", "EC_WORD_EXCL_EXCL"],
        "speechAfter":  ["EC_WORD_I", "EC_WORD_ADORE", "EC_WORD_DRAGON", "EC_WORD_MR", "EC_WORD_SO", "EC_WORD_MUCH"],
    },
    7: { # Hiker (Yurato / Logan) - Earthquake in solo match
        "speechBefore": ["EC_WORD_AN", "EC_MOVE(EARTHQUAKE)", "EC_WORD_IN", "EC_WORD_THIS", "EC_WORD_MATCH", "EC_WORD_EXCL"],
        "speechWin":    ["EC_WORD_HMM", "EC_WORD_AN", "EC_WORD_OVERWHELMING", "EC_WORD_MATCH", "EC_WORD_FEELING", "EC_WORD_GOOD"],
        "speechLose":   ["EC_WORD_OH_QUES", "EC_WORD_WHY", "EC_WORD_DID", "EC_WORD_I", "EC_WORD_LOSE", "EC_WORD_QUES"],
        "speechAfter":  ["EC_WORD_I", "EC_WORD_REALLY", "EC_WORD_LIKE", "EC_WORD_A", "EC_WORD_GOOD", "EC_WORD_MATCH"],
    },
    8: { # Lady (Sakuya / Skye) - A little strong / destroyed feelings
        "speechBefore": ["EC_WORD_I_AM", "EC_WORD_A_LITTLE", "EC_WORD_TOO_STRONG", "EC_WORD_FOR", "EC_WORD_YOU", "EC_WORD_EXCL"],
        "speechWin":    ["EC_WORD_EEK", "EC_WORD_EXCL", "EC_WORD_WE", "EC_WORD_ARE", "EC_WORD_JUST", "EC_WORD_FABULOUS"],
        "speechLose":   ["EC_WORD_WAAAH", "EC_WORD_EXCL", "EC_WORD_WE", "EC_WORD_WERE", "EC_WORD_TOTALLY", "EC_WORD_USELESS"],
        "speechAfter":  ["EC_WORD_MY", "EC_WORD_FEELING", "EC_WORD_IS", "EC_WORD_DESTROYED", "EC_WORD_ELLIPSIS_EXCL", "EC_EMPTY_WORD"],
    },

    # Pack 2 (Cards 9..16)
    9: { # School Kid F (Komari / Cora) - A little service
        "speechBefore": ["EC_WORD_CAN", "EC_WORD_YOU", "EC_WORD_GIVE_ME", "EC_WORD_A_LITTLE", "EC_WORD_SERVICE", "EC_WORD_QUES"],
        "speechWin":    ["EC_WORD_GIGGLE", "EC_WORD_EXCL", "EC_WORD_THANK_YOU", "EC_WORD_VERY", "EC_WORD_MUCH", "EC_WORD_EXCL"],
        "speechLose":   ["EC_WORD_WHAT", "EC_WORD_WAS", "EC_WORD_THE", "EC_WORD_MEAN", "EC_WORD_OF", "EC_WORD_THAT"],
        "speechAfter":  ["EC_WORD_I_AM", "EC_WORD_GOING", "EC_WORD_HOME", "EC_WORD_NOW", "EC_WORD_BYE_BYE", "EC_WORD_EXCL_EXCL"],
    },
    10: { # Rich Boy (Ragi / Ray) - Arrogant / Cotton Spore
        "speechBefore": ["EC_WORD_HUH_QUES", "EC_WORD_ARE", "EC_WORD_YOU", "EC_WORD_REALLY", "EC_WORD_ANY", "EC_WORD_GOOD"],
        "speechWin":    ["EC_WORD_AHAHA", "EC_WORD_EXCL", "EC_WORD_WILL", "EC_WORD_YOU", "EC_WORD_GIVE_UP", "EC_WORD_QUES"],
        "speechLose":   ["EC_WORD_THAT_WAS", "EC_WORD_TOTALLY", "EC_WORD_HOPELESS", "EC_WORD_AND", "EC_WORD_TOO", "EC_WORD_FAST"],
        "speechAfter":  ["EC_WORD_MY", "EC_MOVE2(COTTON_SPORE)", "EC_WORD_WAS", "EC_WORD_TOTALLY", "EC_WORD_USELESS", "EC_WORD_ELLIPSIS"],
    },
    11: { # Ninja Boy (Kennosuke / Kenny) - Showing a dream / lacks rest
        "speechBefore": ["EC_WORD_I", "EC_WORD_CAN", "EC_WORD_SHOW", "EC_WORD_YOU", "EC_WORD_A", "EC_WORD_DREAM"],
        "speechWin":    ["EC_WORD_GIGGLE", "EC_WORD_THIS", "EC_WORD_IS", "EC_WORD_ALMOST", "EC_WORD_THE", "EC_WORD_END"],
        "speechLose":   ["EC_WORD_DIDN_T", "EC_WORD_YOU", "EC_WORD_HEAR", "EC_WORD_ME", "EC_WORD_TALK", "EC_WORD_QUES"],
        "speechAfter":  ["EC_WORD_I", "EC_WORD_WANT", "EC_MOVE2(REST)", "EC_WORD_EVERY", "EC_WORD_DAY", "EC_WORD_ELLIPSIS"],
    },
    12: { # Psychic M (Ozunu / Owen) - Attacking weakened foes / surrender
        "speechBefore": ["EC_WORD_ATTACK", "EC_WORD_WHEN", "EC_WORD_YOU_RE", "EC_WORD_WEAK", "EC_WORD_AND", "EC_WORD_LOW"],
        "speechWin":    ["EC_WORD_WHY", "EC_WORD_DON_T", "EC_WORD_YOU", "EC_WORD_JUST", "EC_WORD_SURRENDER", "EC_WORD_QUES"],
        "speechLose":   ["EC_WORD_YOU", "EC_WORD_WERE", "EC_WORD_NOT", "EC_WORD_WEAKENED", "EC_WORD_AT", "EC_WORD_ALL"],
        "speechAfter":  ["EC_WORD_YOU_RE", "EC_WORD_A_TINY_BIT", "EC_WORD_COOL", "EC_WORD_AFTER", "EC_WORD_ALL", "EC_WORD_ELLIPSIS"],
    },
    13: { # PKMN Breeder F (Kae / Kay) - Boring battle is no joke / Baton Pass
        "speechBefore": ["EC_WORD_A", "EC_WORD_BORING", "EC_WORD_BATTLE", "EC_WORD_IS", "EC_WORD_NO", "EC_WORD_JOKING"],
        "speechWin":    ["EC_WORD_YOU", "EC_WORD_LOST", "EC_WORD_TO", "EC_WORD_MY", "EC_WORD_GREAT", "EC_WORD_STRATEGY"],
        "speechLose":   ["EC_WORD_YOUR", "EC_WORD_BATTLE", "EC_WORD_STRATEGY", "EC_WORD_WAS", "EC_WORD_INCREDIBLE", "EC_WORD_ELLIPSIS"],
        "speechAfter":  ["EC_WORD_NEXT", "EC_WORD_A", "EC_MOVE2(BATON_PASS)", "EC_WORD_FOR", "EC_WORD_THE", "EC_WORD_VICTORY"],
    },
    14: { # School Kid M (Sakiteru / Sammy) - Signature "Oi, oi, oi hey there !!"
        "speechBefore": ["EC_WORD_OI_OI_OI", "EC_WORD_HEY_THERE", "EC_WORD_EXCL_EXCL", "EC_WORD_PLEASE", "EC_WORD_BATTLE", "EC_WORD_ME"],
        "speechWin":    ["EC_WORD_OI_OI_OI", "EC_WORD_HEY_THERE", "EC_WORD_EXCL_EXCL", "EC_WORD_I_AM", "EC_WORD_SO", "EC_WORD_HAPPY"],
        "speechLose":   ["EC_WORD_OI_OI_OI", "EC_WORD_HEY_THERE", "EC_WORD_ELLIPSIS_EXCL", "EC_WORD_I", "EC_WORD_APOLOGIZE", "EC_WORD_ELLIPSIS"],
        "speechAfter":  ["EC_WORD_AIYEEH", "EC_WORD_EXCUSE_ME", "EC_WORD_I_AM", "EC_WORD_SHAKY", "EC_WORD_ALL", "EC_WORD_OVER"],
    },
    15: { # Aroma Lady (Nukumi / Nina) - Transform into something / still an Egg
        "speechBefore": ["EC_WORD_SEE", "EC_WORD_MY", "EC_WORD_POKEMON", "EC_MOVE2(TRANSFORM)", "EC_WORD_TODAY", "EC_WORD_EXCL"],
        "speechWin":    ["EC_WORD_EEK", "EC_WORD_THAT_WAS", "EC_WORD_PERFECT", "EC_WORD_AND", "EC_WORD_A", "EC_WORD_LEGEND"],
        "speechLose":   ["EC_WORD_GRAAAH", "EC_WORD_WE_RE", "EC_WORD_SHREDDED", "EC_WORD_THIS", "EC_WORD_IS", "EC_WORD_TERRIBLE"],
        "speechAfter":  ["EC_WORD_WE_RE", "EC_WORD_NOT", "EC_WORD_AN", "EC_WORD_EGG", "EC_WORD_GWAH", "EC_WORD_ELLIPSIS"],
    },
    16: { # Youngster (Akitaka / Alan) - Strong without evolving!
        "speechBefore": ["EC_WORD_WE_RE", "EC_WORD_STRONG", "EC_WORD_WITHOUT", "EC_WORD_ANY", "EC_WORD_EVOLVE", "EC_WORD_EXCL_EXCL"],
        "speechWin":    ["EC_WORD_AREN_T", "EC_WORD_WE", "EC_WORD_CUTE", "EC_WORD_AND", "EC_WORD_SUPER", "EC_WORD_STRONG"],
        "speechLose":   ["EC_WORD_HMM", "EC_WORD_OUR", "EC_WORD_PLANS", "EC_WORD_WERE", "EC_WORD_NOTHING", "EC_WORD_ELLIPSIS"],
        "speechAfter":  ["EC_WORD_WE", "EC_WORD_GET", "EC_WORD_STRONG", "EC_WORD_WITHOUT", "EC_WORD_EVOLVE", "EC_WORD_EXCL"],
    },

    # Pack 4 (Cards 25..32)
    25: { # Sailor (Isonosuke / Ian) - Surf feeling / Never forget Surf!
        "speechBefore": ["EC_WORD_THAT_S", "EC_WORD_A", "EC_MOVE2(SURF)", "EC_WORD_FEELING", "EC_WORD_YAHOO", "EC_WORD_EXCL_EXCL"],
        "speechWin":    ["EC_WORD_WE_VE", "EC_WORD_GOT", "EC_WORD_IT", "EC_WORD_EXCL_EXCL", "EC_WORD_YAHOO", "EC_WORD_EXCL"],
        "speechLose":   ["EC_WORD_USELESS", "EC_WORD_EXCL_EXCL", "EC_WORD_WE_RE", "EC_WORD_TOTALLY", "EC_WORD_USELESS", "EC_WORD_EXCL_EXCL"],
        "speechAfter":  ["EC_WORD_DON_T", "EC_WORD_EVER", "EC_WORD_FORGET", "EC_MOVE2(SURF)", "EC_WORD_NO", "EC_WORD_JOKING"],
    },
    26: { # Picnicker (Koeda / Kyle) - If I win I play, if I lose I go home
        "speechBefore": ["EC_WORD_IF_I_WIN", "EC_WORD_I", "EC_WORD_PLAY", "EC_WORD_IF_I_LOSE", "EC_WORD_GO_HOME", "EC_WORD_ELLIPSIS"],
        "speechWin":    ["EC_WORD_YEAH", "EC_WORD_EXCL", "EC_WORD_NOW", "EC_WORD_WE", "EC_WORD_PLAY", "EC_WORD_EXCL_EXCL"],
        "speechLose":   ["EC_WORD_I_AM", "EC_WORD_SHOCKED", "EC_WORD_I_AM", "EC_WORD_GOING", "EC_WORD_HOME", "EC_WORD_ELLIPSIS"],
        "speechAfter":  ["EC_WORD_NO", "EC_WORD_PLAY", "EC_WORD_FOR", "EC_WORD_ME", "EC_WORD_TODAY", "EC_WORD_ELLIPSIS"],
    },
    27: { # Bird Keeper (Isaji / Isaac) - Needs opponent / Too strong vs too weak
        "speechBefore": ["EC_WORD_A", "EC_WORD_BATTLE", "EC_WORD_IS", "EC_WORD_BEGINNING", "EC_WORD_WITH", "EC_WORD_YOU"],
        "speechWin":    ["EC_WORD_FORGET", "EC_WORD_IT", "EC_WORD_WE_RE", "EC_WORD_JUST", "EC_WORD_TOO_STRONG", "EC_WORD_EXCL_EXCL"],
        "speechLose":   ["EC_WORD_I", "EC_WORD_APOLOGIZE", "EC_WORD_WE_RE", "EC_WORD_JUST", "EC_WORD_TOO_WEAK", "EC_WORD_EXCL_EXCL"],
        "speechAfter":  ["EC_WORD_WE_RE", "EC_WORD_JUST", "EC_WORD_TOO_WEAK", "EC_WORD_AFTER", "EC_WORD_ALL", "EC_WORD_ELLIPSIS"],
    },
    28: { # Expert F (Ouka / Olivia) - Final match / surprised at myself
        "speechBefore": ["EC_WORD_THIS", "EC_WORD_IS", "EC_WORD_THE", "EC_WORD_FINAL", "EC_WORD_MATCH", "EC_WORD_EXCL_EXCL"],
        "speechWin":    ["EC_WORD_MYSELF", "EC_WORD_WAS", "EC_WORD_A", "EC_WORD_BIG", "EC_WORD_SURPRISE", "EC_WORD_EXCL"],
        "speechLose":   ["EC_WORD_I", "EC_WORD_DIDN_T", "EC_WORD_KNOW", "EC_WORD_I_AM", "EC_WORD_LOSING", "EC_WORD_EXCL"],
        "speechAfter":  ["EC_WORD_NEVER", "EC_WORD_GIVE_UP", "EC_WORD_IN", "EC_WORD_A", "EC_WORD_MATCH", "EC_WORD_EXCL"],
    },
    29: { # Beauty (Maiko / Maya) - Dancing Pokémon obsession
        "speechBefore": ["EC_WORD_CAN", "EC_WORD_WE", "EC_WORD_ALL", "EC_WORD_DANCE", "EC_WORD_TOGETHER", "EC_WORD_QUES"],
        "speechWin":    ["EC_WORD_WE", "EC_WORD_WON", "EC_WORD_BUT", "EC_WORD_I_AM", "EC_WORD_ALL", "EC_WORD_WOBBLY"],
        "speechLose":   ["EC_WORD_TOO", "EC_WORD_WOBBLY", "EC_WORD_I", "EC_WORD_CAN_T_WIN", "EC_WORD_TODAY", "EC_WORD_EXCL"],
        "speechAfter":  ["EC_WORD_I", "EC_WORD_ADORE", "EC_WORD_A", "EC_WORD_DANCE", "EC_WORD_POKEMON", "EC_WORD_EXCL_EXCL"],
    },
    30: { # Parasol Lady (Akino / Austin) - Dislikes fast battles, loves Curse
        "speechBefore": ["EC_WORD_I", "EC_WORD_DISLIKE", "EC_WORD_A", "EC_WORD_FAST", "EC_WORD_BATTLE", "EC_WORD_ELLIPSIS"],
        "speechWin":    ["EC_WORD_GIGGLE", "EC_WORD_ELLIPSIS", "EC_WORD_A", "EC_MOVE2(CURSE)", "EC_WORD_BATTLE", "EC_WORD_EXCL"],
        "speechLose":   ["EC_WORD_OH_DEAR", "EC_WORD_WAS", "EC_WORD_THAT", "EC_WORD_TOO", "EC_WORD_FAST", "EC_WORD_QUES"],
        "speechAfter":  ["EC_WORD_I", "EC_WORD_WANT", "EC_WORD_A", "EC_MOVE2(CURSE)", "EC_WORD_BATTLE", "EC_WORD_ELLIPSIS"],
    },
    31: { # School Kid M (Okikazu / Oscar) - Kid bravado / becoming friends
        "speechBefore": ["EC_WORD_WHO", "EC_WORD_THINKS", "EC_WORD_THEY", "EC_WORD_CAN", "EC_WORD_WIN", "EC_WORD_QUES"],
        "speechWin":    ["EC_WORD_YOU", "EC_WORD_KNOW", "EC_WORD_NOTHING", "EC_WORD_ABOUT", "EC_WORD_POKEMON", "EC_WORD_EXCL"],
        "speechLose":   ["EC_WORD_OH_YEAH", "EC_WORD_EXCUSE_ME", "EC_WORD_FOR", "EC_WORD_THAT", "EC_WORD_LOSS", "EC_WORD_ELLIPSIS_EXCL"],
        "speechAfter":  ["EC_WORD_CAN", "EC_WORD_WE", "EC_WORD_BE", "EC_WORD_A", "EC_WORD_FRIEND", "EC_WORD_EXCL_EXCL"],
    },
    32: { # Battle Girl (Rikka / Riley) - Loving good Pokémon / no bad Pokémon
        "speechBefore": ["EC_WORD_THERE", "EC_WORD_ARE", "EC_WORD_NO", "EC_WORD_BAD", "EC_WORD_POKEMON", "EC_WORD_EXCL_EXCL"],
        "speechWin":    ["EC_WORD_OUR", "EC_WORD_POKEMON", "EC_WORD_ARE", "EC_WORD_REALLY", "EC_WORD_SO", "EC_WORD_GOOD"],
        "speechLose":   ["EC_WORD_THAT", "EC_WORD_LOSS", "EC_WORD_WAS", "EC_WORD_NOT", "EC_WORD_BEING", "EC_WORD_KIND"],
        "speechAfter":  ["EC_WORD_I", "EC_WORD_JUST", "EC_WORD_ADORE", "EC_WORD_MY", "EC_WORD_POKEMON", "EC_WORD_EXCL"],
    },

    # Pack 5 (Cards 33..40)
    33: { # Camper (Kousuke / Kirk) - Cries non-stop / can't stop
        "speechBefore": ["EC_WORD_DON_T", "EC_WORD_STOP", "EC_WORD_PLEASE", "EC_WORD_STOP", "EC_WORD_CRIES", "EC_WORD_EXCL_EXCL"],
        "speechWin":    ["EC_WORD_HAHAHA", "EC_WORD_IT", "EC_WORD_DID", "EC_WORD_STOP", "EC_WORD_IT_S", "EC_WORD_GREAT"],
        "speechLose":   ["EC_WORD_HOW", "EC_WORD_COULD", "EC_WORD_WE", "EC_WORD_LOSE", "EC_WORD_THIS", "EC_WORD_QUES"],
        "speechAfter":  ["EC_WORD_I_AM", "EC_WORD_ALMOST", "EC_WORD_DROOLING", "EC_WORD_OVER", "EC_WORD_HERE", "EC_WORD_ELLIPSIS"],
    },
    34: { # Guitarist (Neo / Nolan) - Swift level / Master level
        "speechBefore": ["EC_WORD_WHAT", "EC_WORD_IS", "EC_WORD_MY", "EC_MOVE(SWIFT)", "EC_WORD_LEVEL", "EC_WORD_QUES"],
        "speechWin":    ["EC_WORD_YOU_RE", "EC_WORD_ONLY", "EC_WORD_AT", "EC_WORD_CHILD_S_PLAY", "EC_WORD_LEVEL", "EC_WORD_EXCL"],
        "speechLose":   ["EC_WORD_WHOAH", "EC_WORD_ME", "EC_WORD_LOSE", "EC_WORD_IS", "EC_WORD_NO", "EC_WORD_JOKING"],
        "speechAfter":  ["EC_WORD_YOU", "EC_WORD_CAN_T", "EC_WORD_SEE", "EC_WORD_MY", "EC_WORD_MASTER", "EC_WORD_LEVEL"],
    },
    35: { # Rich Boy (Tsugane / Travis) - Spending money on Pokémon / Mother!
        "speechBefore": ["EC_WORD_I", "EC_WORD_USE", "EC_WORD_ALL", "EC_WORD_MY", "EC_WORD_MONEY", "EC_WORD_EXCL_EXCL"],
        "speechWin":    ["EC_WORD_FEELING", "EC_WORD_GOOD", "EC_WORD_WE_RE", "EC_WORD_THE", "EC_WORD_NO_1", "EC_WORD_EXCL"],
        "speechLose":   ["EC_WORD_EXPENSIVE", "EC_WORD_ITEM", "EC_WORD_WAS", "EC_WORD_NOT", "EC_WORD_ENOUGH", "EC_WORD_ELLIPSIS"],
        "speechAfter":  ["EC_WORD_MOTHER", "EC_WORD_WHY", "EC_WORD_DID", "EC_WORD_MY", "EC_WORD_POKEMON", "EC_WORD_LOSE"],
    },
    36: { # Hex Maniac (Kagaho / Calvin) - Scary, spooky, but cool
        "speechBefore": ["EC_WORD_AIYEEH", "EC_WORD_EXCL", "EC_WORD_YOU_RE", "EC_WORD_SO", "EC_WORD_SCARY", "EC_WORD_ELLIPSIS_EXCL"],
        "speechWin":    ["EC_WORD_YOU_RE", "EC_WORD_NOT", "EC_WORD_SCARY", "EC_WORD_JUST", "EC_WORD_TOO_WEAK", "EC_WORD_ELLIPSIS"],
        "speechLose":   ["EC_WORD_AIYEEH", "EC_WORD_YOU", "EC_WORD_WERE", "EC_WORD_SCARY", "EC_WORD_AND", "EC_WORD_TOO_STRONG"],
        "speechAfter":  ["EC_WORD_SCARY", "EC_WORD_SCARY", "EC_WORD_ELLIPSIS", "EC_WORD_EVEN_SO", "EC_WORD_SO", "EC_WORD_COOL"],
    },
    37: { # Beauty (Tsukika / Tara) - Party from morning to night / Fever dance
        "speechBefore": ["EC_WORD_PARTY", "EC_WORD_FROM", "EC_WORD_MORNING", "EC_WORD_UNTIL", "EC_WORD_NIGHT", "EC_WORD_EXCL"],
        "speechWin":    ["EC_WORD_POKEMON", "EC_WORD_FEVER", "EC_WORD_LET_S", "EC_WORD_DANCE", "EC_WORD_TODAY", "EC_WORD_EXCL_EXCL"],
        "speechLose":   ["EC_WORD_DISAPPOINT", "EC_WORD_THE", "EC_WORD_PARTY", "EC_WORD_IS", "EC_WORD_OVER", "EC_WORD_ELLIPSIS"],
        "speechAfter":  ["EC_WORD_TRAIN", "EC_WORD_UNTIL", "EC_WORD_NIGHT", "EC_WORD_AND", "EC_WORD_DANCE", "EC_WORD_MORE"],
    },
    38: { # Ruin Maniac (Edo / Eddie) - Disaster / full of sadness
        "speechBefore": ["EC_WORD_ARE", "EC_WORD_YOU", "EC_WORD_THAT", "EC_WORD_STRONG", "EC_WORD_TRAINER", "EC_WORD_QUES"],
        "speechWin":    ["EC_WORD_OH", "EC_WORD_A", "EC_WORD_DISASTER", "EC_WORD_FOR", "EC_WORD_YOU", "EC_WORD_EXCL"],
        "speechLose":   ["EC_WORD_OH", "EC_WORD_I_AM", "EC_WORD_FULL", "EC_WORD_OF", "EC_WORD_SAD", "EC_WORD_FEELING"],
        "speechAfter":  ["EC_WORD_WHO", "EC_WORD_IS", "EC_WORD_A", "EC_WORD_TRAINER", "EC_WORD_WITHOUT", "EC_WORD_LOSS"],
    },
    39: { # PKMN Breeder M (Kaiji / Kaleb) - Excuse me!! Excuse me!!
        "speechBefore": ["EC_WORD_EXCUSE_ME", "EC_WORD_EXCL_EXCL", "EC_WORD_EXCUSE_ME", "EC_WORD_EXCL_EXCL", "EC_EMPTY_WORD", "EC_EMPTY_WORD"],
        "speechWin":    ["EC_WORD_EXCUSE_ME", "EC_WORD_FOR", "EC_WORD_WIN", "EC_WORD_EXCUSE_ME", "EC_WORD_EXCL_EXCL", "EC_EMPTY_WORD"],
        "speechLose":   ["EC_WORD_TOO_WEAK", "EC_WORD_EXCUSE_ME", "EC_WORD_EXCL_EXCL", "EC_WORD_DISAPPOINTED", "EC_WORD_EXCUSE_ME", "EC_WORD_EXCL_EXCL"],
        "speechAfter":  ["EC_WORD_EXCUSE_ME", "EC_WORD_EXCL_EXCL", "EC_WORD_EXCUSE_ME", "EC_WORD_EXCL_EXCL", "EC_EMPTY_WORD", "EC_EMPTY_WORD"],
    },
    40: { # Bug Catcher (Kiichi / Kevin) - Gym Leaders never concede
        "speechBefore": ["EC_WORD_I_AM", "EC_WORD_SEEK", "EC_WORD_OF", "EC_WORD_THE", "EC_WORD_LEADERS", "EC_WORD_EXCL_EXCL"],
        "speechWin":    ["EC_WORD_TO", "EC_WORD_WIN", "EC_WORD_IS", "EC_WORD_FEELING", "EC_WORD_SO", "EC_WORD_GOOD"],
        "speechLose":   ["EC_WORD_TCH", "EC_WORD_IT_S", "EC_WORD_IMPOSSIBLE", "EC_WORD_TO", "EC_WORD_WIN", "EC_WORD_ELLIPSIS"],
        "speechAfter":  ["EC_WORD_LEADERS", "EC_WORD_WILL", "EC_WORD_NOT", "EC_WORD_CONCEDE", "EC_WORD_A", "EC_WORD_MATCH"],
    },

    # Promo Cards (101, 102)
    101: { # Camper (Soushi / Soren) - Emerald is beautiful / Pokémon colors
        "speechBefore": ["EC_WORD_LOOK", "EC_WORD_WELL", "EC_WORD_AT", "EC_WORD_MY", "EC_WORD_POKEMON", "EC_WORD_EXCL_EXCL"],
        "speechWin":    ["EC_WORD_EMERALD", "EC_WORD_IS", "EC_WORD_SO", "EC_WORD_VERY", "EC_WORD_BEAUTIFUL", "EC_WORD_EXCL_EXCL"],
        "speechLose":   ["EC_WORD_YOU_RE", "EC_WORD_A", "EC_WORD_TRULY", "EC_WORD_STRONG", "EC_WORD_TRAINER", "EC_WORD_EXCL_EXCL"],
        "speechAfter":  ["EC_WORD_WHAT", "EC_WORD_COLOR", "EC_WORD_IS", "EC_WORD_YOUR", "EC_WORD_POKEMON", "EC_WORD_QUES"],
    },
    102: { # School Kid M (Toshinori / Ashton) - I choose you / Never give up / Facade
        "speechBefore": ["EC_WORD_I_CHOOSE_YOU", "EC_WORD_ELLIPSIS", "EC_WORD_THAT_WAS", "EC_WORD_JUST", "EC_WORD_A", "EC_WORD_JOKING"],
        "speechWin":    ["EC_WORD_OH_KAY", "EC_WORD_EXCL_EXCL", "EC_WORD_NEVER", "EC_WORD_GIVE_UP", "EC_WORD_ON", "EC_WORD_VICTORY"],
        "speechLose":   ["EC_WORD_HAHAHA", "EC_WORD_I", "EC_WORD_LOST", "EC_WORD_BUT", "EC_WORD_DON_T", "EC_WORD_GIVE_UP"],
        "speechAfter":  ["EC_WORD_I", "EC_WORD_LOST", "EC_WORD_BUT", "EC_WORD_THIS", "EC_WORD_ISN_T", "EC_MOVE(FACADE)"],
    }
}

def extract_western_trainers_from_source(indent=12):
    """Extracts all 32 Western trainers (Packs 3, 6, 7, 8) directly from trainer_hill.h."""
    with open(HEADER_PATH) as f:
        text = f.read()
    modes = ["sFloors_Normal", "sFloors_Variety", "sFloors_Unique", "sFloors_Expert"]
    western_trainers = {}

    for mode in modes:
        p_start = text.find(f"static const struct TrainerHillFloor {mode}[]")
        if p_start == -1: continue
        p_end = text.find("};", p_start)
        block = text[p_start:p_end]
        
        floor_matches = re.finditer(r"\[(\d+)\]\s*=\s*\{([\s\S]*?\.trainerNum1\s*=\s*(\d+)[\s\S]*?\.trainerNum2\s*=\s*(\d+)[\s\S]*?\.trainers\s*=\s*\{([\s\S]*?)\n\s*\}\s*,\s*\n\s*\.map)", block)
        for fm in floor_matches:
            t1_num = int(fm.group(3))
            t2_num = int(fm.group(4))
            raw = fm.group(5)
            
            # parse [0]
            pos0 = raw.find("[0]")
            b0 = raw.find("{", pos0)
            depth = 1
            p = b0 + 1
            while p < len(raw) and depth > 0:
                if raw[p] == "{": depth += 1
                elif raw[p] == "}": depth -= 1
                p += 1
            body0 = raw[b0+1:p-1]
            
            # parse [1] after p
            pos1 = raw.find("[1]", p)
            b1 = raw.find("{", pos1)
            depth = 1
            p = b1 + 1
            while p < len(raw) and depth > 0:
                if raw[p] == "{": depth += 1
                elif raw[p] == "}": depth -= 1
                p += 1
            body1 = raw[b1+1:p-1]
            
            def format_body(body):
                lines = body.splitlines()
                non_empty = [l for l in lines if l.strip()]
                if not non_empty: return ""
                base_indent = len(non_empty[0]) - len(non_empty[0].lstrip())
                ind = " " * indent
                res = []
                for l in lines:
                    if not l.strip():
                        res.append("")
                    else:
                        content = l[base_indent:] if len(l) >= base_indent and l[:base_indent].isspace() else l.lstrip()
                        res.append(ind + content)
                while res and not res[0].strip():
                    res.pop(0)
                while res and not res[-1].strip():
                    res.pop()
                return "\n".join(res)
            
            western_trainers[t1_num] = format_body(body0)
            western_trainers[t2_num] = format_body(body1)

    return western_trainers

# Localized English names for all Trainer Hill trainers (Packs 1..8 and Promos)
trainer_english_names = {
    # Pack 1 (Cards 1..8)
    1: "KENT",
    2: "MASON",
    3: "KEITH",
    4: "ARTHUR",
    5: "LEONA",
    6: "IRENE",
    7: "LOGAN",
    8: "SKYE",
    # Pack 2 (Cards 9..16)
    9: "CORA",
    10: "RAY",
    11: "KENNY",
    12: "OWEN",
    13: "KAY",
    14: "SAMMY",
    15: "NINA",
    16: "ALAN",
    # Pack 3 (Cards 17..24 - from Western trainer_hill.h)
    17: "ALAINA",
    18: "ALFONSO",
    19: "THEODORE",
    20: "JAYDEN",
    21: "SALVADORE",
    22: "VERONICA",
    23: "KEENAN",
    24: "KRISTINA",
    # Pack 4 (Cards 25..32)
    25: "IAN",
    26: "KYLE",
    27: "ISAAC",
    28: "OLIVIA",
    29: "MAYA",
    30: "AUSTIN",
    31: "OSCAR",
    32: "RILEY",
    # Pack 5 (Cards 33..40)
    33: "KIRK",
    34: "NOLAN",
    35: "TRAVIS",
    36: "CALVIN",
    37: "TARA",
    38: "EDDIE",
    39: "KALEB",
    40: "KEVIN",
    # Pack 6 (Cards 41..48 - from Western trainer_hill.h)
    41: "TERRANCE",
    42: "ELIZABETH",
    43: "ANNABELL",
    44: "COLEMAN",
    45: "ENRIQUE",
    46: "COLLEEN",
    47: "KIMBERLY",
    48: "FRANCISCO",
    # Pack 7 (Cards 49..56 - from Western trainer_hill.h)
    49: "MEREDITH",
    50: "BERNARD",
    51: "ABRAHAM",
    52: "LUC",
    53: "BREYDEN",
    54: "ANIYA",
    55: "STEPHANIE",
    56: "DANE",
    # Pack 8 (Cards 57..64 - from Western trainer_hill.h)
    57: "ALFRED",
    58: "EDIE",
    59: "RODERICK",
    60: "ALICIA",
    61: "TERRENCE",
    62: "CARLOTTA",
    63: "NORA",
    64: "GAV",
    # Promo Cards (101, 102)
    101: "SOREN",
    102: "ASHTON",
}

jp_default_trainers = {
    # Youngster Shigenobu -> Shawn: Talking to trainer lady
    "シゲノブ": {
        "name": "SHAWN",
        "speechBefore": "{ EC_WORD_MISS, EC_WORD_TRAINER, EC_WORD_CAN, EC_WORD_WE, EC_WORD_BATTLE, EC_WORD_QUES }",
        "speechWin":    "{ EC_WORD_MISS, EC_WORD_TRAINER, EC_WORD_WERE, EC_WORD_YOU, EC_WORD_TOO_WEAK, EC_WORD_QUES }",
        "speechLose":   "{ EC_WORD_MISS, EC_WORD_TRAINER, EC_WORD_YOU_RE, EC_WORD_SO, EC_WORD_STRONG, EC_WORD_EXCL_EXCL }",
        "speechAfter":  "{ EC_WORD_THAT_WAS, EC_WORD_EXCITING, EC_WORD_MISS, EC_WORD_TRAINER, EC_WORD_THANK_YOU, EC_WORD_EXCL }",
    },
    # Parasol Lady Akari -> Autumn: Every type of Pokemon / Earthquake
    "アカリ": {
        "name": "AUTUMN",
        "speechBefore": "{ EC_WORD_I, EC_WORD_ADORE, EC_WORD_EVERY, EC_WORD_TYPE, EC_WORD_OF, EC_WORD_POKEMON }",
        "speechWin":    "{ EC_WORD_DID, EC_WORD_I, EC_WORD_SURPRISE, EC_WORD_YOU, EC_WORD_GIGGLE, EC_WORD_EXCL }",
        "speechLose":   "{ EC_WORD_OH_QUES, EC_WORD_WAS, EC_WORD_THAT, EC_WORD_AN, EC_MOVE(EARTHQUAKE), EC_WORD_QUES }",
        "speechAfter":  "{ EC_WORD_YOU, EC_WORD_CAN, EC_WORD_GO, EC_WORD_TO, EC_WORD_THE, EC_WORD_END }",
    },
    # Ninja Boy Shigezou -> Simon: Constrict / Tomorrow is another day
    "シゲゾウ": {
        "name": "SIMON",
        "speechBefore": "{ EC_WORD_I, EC_WORD_WILL, EC_MOVE(CONSTRICT), EC_WORD_UNTIL, EC_WORD_I, EC_WORD_WIN }",
        "speechWin":    "{ EC_WORD_I, EC_WORD_DIDN_T, EC_WORD_NEED, EC_MOVE(CONSTRICT), EC_WORD_TODAY, EC_WORD_EXCL }",
        "speechLose":   "{ EC_WORD_URGH, EC_WORD_I, EC_WORD_HAVE, EC_WORD_NO, EC_WORD_POWER, EC_WORD_ELLIPSIS }",
        "speechAfter":  "{ EC_WORD_TOMORROW, EC_WORD_IS, EC_WORD_ANOTHER, EC_WORD_DAY, EC_WORD_EXCL, EC_EMPTY_WORD }",
    },
    # Beauty Namiko -> Naomi: Don't go easy on me / Good match
    "ナミコ": {
        "name": "NAOMI",
        "speechBefore": "{ EC_WORD_DON_T, EC_WORD_BE, EC_WORD_KIND, EC_WORD_TO, EC_WORD_ME, EC_WORD_EXCL }",
        "speechWin":    "{ EC_WORD_WERE, EC_WORD_YOU, EC_WORD_BEING, EC_WORD_KIND, EC_WORD_OR, EC_WORD_WEAK }",
        "speechLose":   "{ EC_WORD_THAT_WAS, EC_WORD_AWFUL, EC_WORD_I, EC_WORD_CAN_T_WIN, EC_WORD_TODAY, EC_WORD_EXCL }",
        "speechAfter":  "{ EC_WORD_AWW, EC_WORD_BUT, EC_WORD_THAT_WAS, EC_WORD_A, EC_WORD_GOOD, EC_WORD_MATCH }",
    },
}

def extract_jp_default_floors():
    """Extracts the 2 default Japanese floors from trainer_hill.h, updating speeches and names to English, and replacing JP nicknames with English species names."""
    with open(HEADER_PATH) as f:
        text = f.read()
    idx_start = text.find("static const struct TrainerHillFloor sFloors_JPDefault[] = {")
    if idx_start == -1:
        return ""
    idx_end = text.find("};", idx_start) + 2
    jp_block = text[idx_start:idx_end]
    
    # Replace any JP nicknames with English species name
    lines = jp_block.splitlines()
    curr_trainer = None
    curr_species = None
    new_lines = []
    for line in lines:
        m_name = re.search(r'\.name\s*=\s*__\("([^"$]+)', line)
        if m_name:
            curr_trainer = m_name.group(1)
            if curr_trainer in jp_default_trainers:
                indent_prefix = line[:line.find(".name =")]
                eng_name = jp_default_trainers[curr_trainer]["name"]
                line = f'{indent_prefix}.name = _("{eng_name}"),'
            
        if curr_trainer and curr_trainer in jp_default_trainers:
            sp = jp_default_trainers[curr_trainer]
            for key in ["speechBefore", "speechWin", "speechLose", "speechAfter"]:
                if f".{key} =" in line:
                    indent_prefix = line[:line.find(f".{key} =")]
                    line = f"{indent_prefix}.{key} = {sp[key]},"

        m_sp = re.search(r"\.species\s*=\s*SPECIES_(\w+)", line)
        if m_sp:
            curr_species = m_sp.group(1)
        m_nick = re.search(r"\.nickname\s*=\s*__\(\"[^\"]+\"\)", line)
        if m_nick and curr_species:
            line = re.sub(r"\.nickname\s*=\s*__\(\"[^\"]+\"\)", f'.nickname = _("{curr_species}")', line)
        new_lines.append(line)
    return "\n".join(new_lines)

def decompile_raw_card(raw_path):
    bin_path = "/tmp/temp_card.bin"
    vpk_path = "/tmp/temp_card.vpk"
    dec_path = "/tmp/temp_card_dec.bin"
    
    subprocess.run([NEDCENC, "-d", "-i", raw_path, "-o", bin_path], check=True, stdout=subprocess.DEVNULL)
    with open(bin_path, "rb") as f:
        data = f.read()
    idx = data.find(b"vpk0")
    if idx == -1:
        raise ValueError("vpk0 not found")
    with open(vpk_path, "wb") as f:
        f.write(data[idx:])
    subprocess.run([NEVPK, "-d", "-i", vpk_path, "-o", dec_path], check=True, stdout=subprocess.DEVNULL)
    with open(dec_path, "rb") as f:
        decompressed = f.read()
    
    trainerNum = decompressed[0x100]
    raw_name = decompressed[0x104:0x10C]
    name_str = decode_jp_string(raw_name)
    facility_class_id = decompressed[0x10C]
    facility_class = facility_classes[facility_class_id] if facility_class_id < len(facility_classes) else f"FACILITY_CLASS_{facility_class_id}"
    
    mons = []
    for p in range(6):
        m = decompressed[0x140 + p * 44 : 0x140 + (p + 1) * 44]
        species_id, heldItem_id, m1, m2, m3, m4, lvl, pp, hpEV, atkEV, defEV, spdEV, spAtkEV, spDefEV, otId, ivs, personality = struct.unpack("<HHHHHHBBBBBBBBIII", m[:32])
        raw_nick = m[32:43]
        friendship = m[43]
        nick_str = decode_jp_string(raw_nick)
        
        species = vanilla_species.get(species_id, f"{species_id}")
        heldItem = vanilla_items.get(heldItem_id, f"{heldItem_id}") if heldItem_id != 0 else "ITEM_NONE"
        moves = [vanilla_moves.get(mv, f"{mv}") if mv != 0 else "MOVE_NONE" for mv in [m1, m2, m3, m4]]
        hpIV = ivs & 0x1F
        atkIV = (ivs >> 5) & 0x1F
        defIV = (ivs >> 10) & 0x1F
        spdIV = (ivs >> 15) & 0x1F
        spAtkIV = (ivs >> 20) & 0x1F
        spDefIV = (ivs >> 25) & 0x1F
        abilityNum = (ivs >> 31) & 1
        
        mons.append({
            "species": species, "heldItem": heldItem, "moves": moves,
            "hpEV": hpEV, "attackEV": atkEV, "defenseEV": defEV, "speedEV": spdEV, "spAttackEV": spAtkEV, "spDefenseEV": spDefEV,
            "otId": otId, "hpIV": hpIV, "attackIV": atkIV, "defenseIV": defIV, "speedIV": spdIV, "spAttackIV": spAtkIV, "spDefenseIV": spDefIV,
            "abilityNum": abilityNum, "personality": hex(personality), "nickname": nick_str, "friendship": friendship
        })
    
    metatile_data = decompressed[0x248:0x348]
    collision_data = decompressed[0x348:0x368]
    coord0, coord1 = decompressed[0x368], decompressed[0x369]
    dirs = decompressed[0x36A]
    ranges = decompressed[0x36B]
    
    return {
        "trainerNum": trainerNum,
        "name": name_str,
        "facilityClass": facility_class,
        "mons": mons,
        "map": {
            "metatiles": metatile_data,
            "collision": collision_data,
            "coords": (coord0, coord1),
            "dirs": dirs,
            "ranges": ranges
        }
    }

def format_trainer_c(trainer_data, indent=12):
    ind = " " * indent
    lines = []
    
    tnum = trainer_data["trainerNum"]
    if tnum in trainer_english_names:
        trainer_name = trainer_english_names[tnum]
        lines.append(f'{ind}.name = _("{trainer_name}"),')
    else:
        lines.append(f'{ind}.name = __("{trainer_data["name"]}   "),')
    lines.append(f'{ind}.facilityClass = {trainer_data["facilityClass"]},')
    lines.append(f'{ind}.unused = TRUE,')
    
    # Use coherent, tailored English speeches
    if tnum in custom_speeches:
        sp = custom_speeches[tnum]
        lines.append(f'{ind}.speechBefore = {{ { ", ".join(sp["speechBefore"]) } }},')
        lines.append(f'{ind}.speechWin = {{ { ", ".join(sp["speechWin"]) } }},')
        lines.append(f'{ind}.speechLose = {{ { ", ".join(sp["speechLose"]) } }},')
        lines.append(f'{ind}.speechAfter = {{ { ", ".join(sp["speechAfter"]) } }},')
    else:
        lines.append(f'{ind}.speechBefore = {{ EC_EMPTY_WORD }},')
        lines.append(f'{ind}.speechWin = {{ EC_EMPTY_WORD }},')
        lines.append(f'{ind}.speechLose = {{ EC_EMPTY_WORD }},')
        lines.append(f'{ind}.speechAfter = {{ EC_EMPTY_WORD }},')
        
    lines.append(f'{ind}.mons = {{')
    for idx, mon in enumerate(trainer_data["mons"]):
        lines.append(f'{ind}    [{idx}] = {{')
        lines.append(f'{ind}        .species = {mon["species"]},')
        lines.append(f'{ind}        .heldItem = {mon["heldItem"]},')
        lines.append(f'{ind}        .moves = {{ { ", ".join(mon["moves"]) } }},')
        if mon["hpEV"]: lines.append(f'{ind}        .hpEV = {mon["hpEV"]},')
        if mon["attackEV"]: lines.append(f'{ind}        .attackEV = {mon["attackEV"]},')
        if mon["defenseEV"]: lines.append(f'{ind}        .defenseEV = {mon["defenseEV"]},')
        if mon["speedEV"]: lines.append(f'{ind}        .speedEV = {mon["speedEV"]},')
        if mon["spAttackEV"]: lines.append(f'{ind}        .spAttackEV = {mon["spAttackEV"]},')
        if mon["spDefenseEV"]: lines.append(f'{ind}        .spDefenseEV = {mon["spDefenseEV"]},')
        lines.append(f'{ind}        .otId = TRAINER_HILL_OTID,')
        lines.append(f'{ind}        .hpIV = {mon["hpIV"]},')
        lines.append(f'{ind}        .attackIV = {mon["attackIV"]},')
        lines.append(f'{ind}        .defenseIV = {mon["defenseIV"]},')
        lines.append(f'{ind}        .speedIV = {mon["speedIV"]},')
        lines.append(f'{ind}        .spAttackIV = {mon["spAttackIV"]},')
        lines.append(f'{ind}        .spDefenseIV = {mon["spDefenseIV"]},')
        lines.append(f'{ind}        .abilityNum = {mon["abilityNum"]},')
        lines.append(f'{ind}        .personality = {mon["personality"]},')
        
        # Pokemon nicknames: always use the English species name
        species_clean = mon["species"].replace("SPECIES_", "")
        lines.append(f'{ind}        .nickname = _("{species_clean}"),')
            
        lines.append(f'{ind}        .friendship = MAX_FRIENDSHIP')
        lines.append(f'{ind}    }},')
    lines.append(f'{ind}}}')
    return "\n".join(lines)

def format_dummy_trainer_c(indent=12):
    ind = " " * indent
    return f"""{ind}.name = _(""),
{ind}.facilityClass = FACILITY_CLASS_PKMN_TRAINER_BRENDAN,
{ind}.unused = TRUE,
{ind}.speechBefore = {{ EC_EMPTY_WORD }},
{ind}.speechWin = {{ EC_EMPTY_WORD }},
{ind}.speechLose = {{ EC_EMPTY_WORD }},
{ind}.speechAfter = {{ EC_EMPTY_WORD }},
{ind}.mons = {{
{ind}    [0] = {{
{ind}        .species = SPECIES_NONE,
{ind}    }}
{ind}}}"""

dir_names = {0: "DIR_NONE", 1: "DIR_SOUTH", 2: "DIR_NORTH", 3: "DIR_WEST", 4: "DIR_EAST"}

def format_candidate_c(cand_idx, trainer_num, has_map, trainer_body, map_data=None, alt_trainer_name=None):
    if has_map and map_data:
        map_body = f"""        .map = {{
            .metatileData = INCBIN_U8("{map_data['floor_map_rel']}/metatiles.bin"),
            .collisionData = INCBIN_U16("{map_data['floor_map_rel']}/collision.bin"),
            .trainerCoords = {{ COORDS_XY({map_data['c1_x']},{map_data['c1_y']}), COORDS_XY({map_data['c2_x']},{map_data['c2_y']}) }},
            .trainerDirections = TRAINER_DIRS({map_data['dir_t1']}, {map_data['dir_t2']}),
            .trainerRanges = TRAINER_RANGE({map_data['range_t1']}, {map_data['range_t2']})
        }}"""
    else:
        map_body = """        .map = {
            .metatileData = {0},
            .collisionData = {0},
            .trainerCoords = {0},
            .trainerDirections = 0,
            .trainerRanges = 0
        }"""
        
    alt_str = f"&{alt_trainer_name}" if alt_trainer_name else "NULL"
    has_map_str = "TRUE" if has_map else "FALSE"
    return f"""    [{cand_idx}] = {{
        .trainerNum = {trainer_num},
        .hasMap = {has_map_str},
        .trainer = {{
{trainer_body}
        }},
        .altTrainer = {alt_str},
{map_body}
    }},"""

shawn_autumn_mons = """                [0] = {
                    .species = SPECIES_ZIGZAGOON,
                    .heldItem = ITEM_SITRUS_BERRY,
                    .moves = { MOVE_HEADBUTT, MOVE_PIN_MISSILE, MOVE_GROWL, MOVE_TAIL_WHIP },
                    .hpEV = 110,
                    .attackEV = 100,
                    .defenseEV = 100,
                    .speedEV = 100,
                    .spDefenseEV = 100,
                    .otId = TRAINER_HILL_OTID,
                    .hpIV = 5,
                    .attackIV = 5,
                    .defenseIV = 5,
                    .speedIV = 5,
                    .spAttackIV = 5,
                    .spDefenseIV = 5,
                    .abilityNum = 0,
                    .personality = 0x80,
                    .nickname = _("ZIGZAGOON"),
                    .friendship = MAX_FRIENDSHIP
                },
                [1] = {
                    .species = SPECIES_SHROOMISH,
                    .heldItem = ITEM_PECHA_BERRY,
                    .moves = { MOVE_MEGA_DRAIN, MOVE_LEECH_SEED, MOVE_POISON_POWDER, MOVE_GROWTH },
                    .hpEV = 120,
                    .defenseEV = 120,
                    .spAttackEV = 150,
                    .spDefenseEV = 120,
                    .otId = TRAINER_HILL_OTID,
                    .hpIV = 5,
                    .attackIV = 5,
                    .defenseIV = 5,
                    .speedIV = 5,
                    .spAttackIV = 5,
                    .spDefenseIV = 5,
                    .abilityNum = 0,
                    .personality = 0x0,
                    .nickname = _("SHROOMISH"),
                    .friendship = MAX_FRIENDSHIP
                },
                [2] = {
                    .species = SPECIES_SANDSHREW,
                    .heldItem = ITEM_QUICK_CLAW,
                    .moves = { MOVE_SCRATCH, MOVE_POISON_STING, MOVE_SAND_ATTACK, MOVE_SWIFT },
                    .hpEV = 110,
                    .attackEV = 100,
                    .defenseEV = 100,
                    .spDefenseEV = 200,
                    .otId = TRAINER_HILL_OTID,
                    .hpIV = 5,
                    .attackIV = 5,
                    .defenseIV = 5,
                    .speedIV = 5,
                    .spAttackIV = 5,
                    .spDefenseIV = 5,
                    .abilityNum = 0,
                    .personality = 0x80,
                    .nickname = _("SANDSHREW"),
                    .friendship = MAX_FRIENDSHIP
                },
                [3] = {
                    .species = SPECIES_WINGULL,
                    .heldItem = ITEM_CHERI_BERRY,
                    .moves = { MOVE_WATER_GUN, MOVE_WING_ATTACK, MOVE_GROWL, MOVE_SUPERSONIC },
                    .hpEV = 110,
                    .attackEV = 100,
                    .defenseEV = 100,
                    .spAttackEV = 100,
                    .spDefenseEV = 100,
                    .otId = TRAINER_HILL_OTID,
                    .hpIV = 5,
                    .attackIV = 5,
                    .defenseIV = 5,
                    .speedIV = 5,
                    .spAttackIV = 5,
                    .spDefenseIV = 5,
                    .abilityNum = 0,
                    .personality = 0x0,
                    .nickname = _("WINGULL"),
                    .friendship = MAX_FRIENDSHIP
                },
                [4] = {
                    .species = SPECIES_NUMEL,
                    .heldItem = ITEM_FOCUS_BAND,
                    .moves = { MOVE_EMBER, MOVE_DIG, MOVE_TACKLE, MOVE_FOCUS_ENERGY },
                    .hpEV = 110,
                    .attackEV = 100,
                    .defenseEV = 100,
                    .spAttackEV = 100,
                    .spDefenseEV = 100,
                    .otId = TRAINER_HILL_OTID,
                    .hpIV = 5,
                    .attackIV = 5,
                    .defenseIV = 5,
                    .speedIV = 5,
                    .spAttackIV = 5,
                    .spDefenseIV = 5,
                    .abilityNum = 0,
                    .personality = 0x96,
                    .nickname = _("NUMEL"),
                    .friendship = MAX_FRIENDSHIP
                },
                [5] = {
                    .species = SPECIES_SURSKIT,
                    .heldItem = ITEM_PERSIM_BERRY,
                    .moves = { MOVE_BUBBLE_BEAM, MOVE_MUD_SHOT, MOVE_QUICK_ATTACK, MOVE_AGILITY },
                    .hpEV = 100,
                    .attackEV = 100,
                    .defenseEV = 100,
                    .spAttackEV = 100,
                    .spDefenseEV = 100,
                    .otId = TRAINER_HILL_OTID,
                    .hpIV = 5,
                    .attackIV = 5,
                    .defenseIV = 5,
                    .speedIV = 5,
                    .spAttackIV = 5,
                    .spDefenseIV = 5,
                    .abilityNum = 0,
                    .personality = 0x0,
                    .nickname = _("SURSKIT"),
                    .friendship = MAX_FRIENDSHIP
                }"""

simon_naomi_mons = """                [0] = {
                    .species = SPECIES_ELECTRIKE,
                    .heldItem = ITEM_CHERI_BERRY,
                    .moves = { MOVE_SPARK, MOVE_THUNDER_WAVE, MOVE_QUICK_ATTACK, MOVE_ROAR },
                    .hpEV = 120,
                    .attackEV = 120,
                    .speedEV = 120,
                    .spAttackEV = 150,
                    .otId = TRAINER_HILL_OTID,
                    .hpIV = 5,
                    .attackIV = 5,
                    .defenseIV = 5,
                    .speedIV = 5,
                    .spAttackIV = 5,
                    .spDefenseIV = 5,
                    .abilityNum = 1,
                    .personality = 0x0,
                    .nickname = _("ELECTRIKE"),
                    .friendship = MAX_FRIENDSHIP
                },
                [1] = {
                    .species = SPECIES_CORPHISH,
                    .heldItem = ITEM_QUICK_CLAW,
                    .moves = { MOVE_KNOCK_OFF, MOVE_CRABHAMMER, MOVE_TAUNT, MOVE_PROTECT },
                    .hpEV = 100,
                    .attackEV = 110,
                    .defenseEV = 100,
                    .spAttackEV = 100,
                    .spDefenseEV = 100,
                    .otId = TRAINER_HILL_OTID,
                    .hpIV = 5,
                    .attackIV = 5,
                    .defenseIV = 5,
                    .speedIV = 5,
                    .spAttackIV = 5,
                    .spDefenseIV = 5,
                    .abilityNum = 1,
                    .personality = 0x96,
                    .nickname = _("CORPHISH"),
                    .friendship = MAX_FRIENDSHIP
                },
                [2] = {
                    .species = SPECIES_BALTOY,
                    .heldItem = ITEM_PERSIM_BERRY,
                    .moves = { MOVE_PSYBEAM, MOVE_ROCK_TOMB, MOVE_MUD_SLAP, MOVE_HARDEN },
                    .hpEV = 100,
                    .attackEV = 100,
                    .defenseEV = 100,
                    .spAttackEV = 110,
                    .spDefenseEV = 100,
                    .otId = TRAINER_HILL_OTID,
                    .hpIV = 5,
                    .attackIV = 5,
                    .defenseIV = 5,
                    .speedIV = 5,
                    .spAttackIV = 5,
                    .spDefenseIV = 5,
                    .abilityNum = 0,
                    .personality = 0x96,
                    .nickname = _("BALTOY"),
                    .friendship = MAX_FRIENDSHIP
                },
                [3] = {
                    .species = SPECIES_SPHEAL,
                    .heldItem = ITEM_FOCUS_BAND,
                    .moves = { MOVE_ICE_BALL, MOVE_BODY_SLAM, MOVE_WATER_GUN, MOVE_ENCORE },
                    .hpEV = 100,
                    .attackEV = 100,
                    .defenseEV = 100,
                    .spAttackEV = 110,
                    .spDefenseEV = 100,
                    .otId = TRAINER_HILL_OTID,
                    .hpIV = 5,
                    .attackIV = 5,
                    .defenseIV = 5,
                    .speedIV = 5,
                    .spAttackIV = 5,
                    .spDefenseIV = 5,
                    .abilityNum = 0,
                    .personality = 0x80,
                    .nickname = _("SPHEAL"),
                    .friendship = MAX_FRIENDSHIP
                },
                [4] = {
                    .species = SPECIES_SPOINK,
                    .heldItem = ITEM_PERSIM_BERRY,
                    .moves = { MOVE_PSYWAVE, MOVE_FUTURE_SIGHT, MOVE_CONFUSE_RAY, MOVE_MAGIC_COAT },
                    .hpEV = 100,
                    .defenseEV = 100,
                    .speedEV = 100,
                    .spAttackEV = 110,
                    .spDefenseEV = 100,
                    .otId = TRAINER_HILL_OTID,
                    .hpIV = 5,
                    .attackIV = 5,
                    .defenseIV = 5,
                    .speedIV = 5,
                    .spAttackIV = 5,
                    .spDefenseIV = 5,
                    .abilityNum = 1,
                    .personality = 0xf,
                    .nickname = _("SPOINK"),
                    .friendship = MAX_FRIENDSHIP
                },
                [5] = {
                    .species = SPECIES_POOCHYENA,
                    .heldItem = ITEM_PECHA_BERRY,
                    .moves = { MOVE_BITE, MOVE_POISON_FANG, MOVE_SWAGGER, MOVE_SCARY_FACE },
                    .hpEV = 70,
                    .attackEV = 80,
                    .defenseEV = 80,
                    .speedEV = 80,
                    .spAttackEV = 80,
                    .spDefenseEV = 80,
                    .otId = TRAINER_HILL_OTID,
                    .hpIV = 5,
                    .attackIV = 5,
                    .defenseIV = 5,
                    .speedIV = 5,
                    .spAttackIV = 5,
                    .spDefenseIV = 5,
                    .abilityNum = 0,
                    .personality = 0x96,
                    .nickname = _("POOCHYENA"),
                    .friendship = MAX_FRIENDSHIP
                }"""

shawn_body = f"""            .name = _("SHAWN"),
            .facilityClass = FACILITY_CLASS_YOUNGSTER,
            .unused = TRUE,
            .speechBefore = {{ EC_WORD_MISS, EC_WORD_TRAINER, EC_WORD_CAN, EC_WORD_WE, EC_WORD_BATTLE, EC_WORD_QUES }},
            .speechWin = {{ EC_WORD_MISS, EC_WORD_TRAINER, EC_WORD_WERE, EC_WORD_YOU, EC_WORD_TOO_WEAK, EC_WORD_QUES }},
            .speechLose = {{ EC_WORD_MISS, EC_WORD_TRAINER, EC_WORD_YOU_RE, EC_WORD_SO, EC_WORD_STRONG, EC_WORD_EXCL_EXCL }},
            .speechAfter = {{ EC_WORD_THAT_WAS, EC_WORD_EXCITING, EC_WORD_MISS, EC_WORD_TRAINER, EC_WORD_THANK_YOU, EC_WORD_EXCL }},
            .mons = {{
{shawn_autumn_mons}
            }}"""

autumn_body = f"""            .name = _("AUTUMN"),
            .facilityClass = FACILITY_CLASS_PARASOL_LADY,
            .unused = TRUE,
            .speechBefore = {{ EC_WORD_I, EC_WORD_ADORE, EC_WORD_EVERY, EC_WORD_TYPE, EC_WORD_OF, EC_WORD_POKEMON }},
            .speechWin = {{ EC_WORD_DID, EC_WORD_I, EC_WORD_SURPRISE, EC_WORD_YOU, EC_WORD_GIGGLE, EC_WORD_EXCL }},
            .speechLose = {{ EC_WORD_OH_QUES, EC_WORD_WAS, EC_WORD_THAT, EC_WORD_AN, EC_MOVE(EARTHQUAKE), EC_WORD_QUES }},
            .speechAfter = {{ EC_WORD_YOU, EC_WORD_CAN, EC_WORD_GO, EC_WORD_TO, EC_WORD_THE, EC_WORD_END }},
            .mons = {{
{shawn_autumn_mons}
            }}"""

simon_body = f"""            .name = _("SIMON"),
            .facilityClass = FACILITY_CLASS_NINJA_BOY,
            .unused = TRUE,
            .speechBefore = {{ EC_WORD_I, EC_WORD_WILL, EC_MOVE(CONSTRICT), EC_WORD_UNTIL, EC_WORD_I, EC_WORD_WIN }},
            .speechWin = {{ EC_WORD_I, EC_WORD_DIDN_T, EC_WORD_NEED, EC_MOVE(CONSTRICT), EC_WORD_TODAY, EC_WORD_EXCL }},
            .speechLose = {{ EC_WORD_URGH, EC_WORD_I, EC_WORD_HAVE, EC_WORD_NO, EC_WORD_POWER, EC_WORD_ELLIPSIS }},
            .speechAfter = {{ EC_WORD_TOMORROW, EC_WORD_IS, EC_WORD_ANOTHER, EC_WORD_DAY, EC_WORD_EXCL, EC_EMPTY_WORD }},
            .mons = {{
{simon_naomi_mons}
            }}"""

naomi_body = f"""            .name = _("NAOMI"),
            .facilityClass = FACILITY_CLASS_BEAUTY,
            .unused = TRUE,
            .speechBefore = {{ EC_WORD_DON_T, EC_WORD_BE, EC_WORD_KIND, EC_WORD_TO, EC_WORD_ME, EC_WORD_EXCL }},
            .speechWin = {{ EC_WORD_WERE, EC_WORD_YOU, EC_WORD_BEING, EC_WORD_KIND, EC_WORD_OR, EC_WORD_WEAK }},
            .speechLose = {{ EC_WORD_THAT_WAS, EC_WORD_AWFUL, EC_WORD_I, EC_WORD_CAN_T_WIN, EC_WORD_TODAY, EC_WORD_EXCL }},
            .speechAfter = {{ EC_WORD_AWW, EC_WORD_BUT, EC_WORD_THAT_WAS, EC_WORD_A, EC_WORD_GOOD, EC_WORD_MATCH }},
            .mons = {{
{simon_naomi_mons}
            }}"""

def main():
    print("Extracting 32 Western trainers directly from trainer_hill.h...")
    western_trainers = extract_western_trainers_from_source(indent=12)
    print(f"Loaded {len(western_trainers)} Western trainer structs from source.")

    print("Finding all raw card files...")
    a_raw_files = [f for f in os.listdir(RAW_CARDS_DIR) if re.match(r"^card_19_a\d{3}\.raw$", f)]
    p_raw_files = [f for f in os.listdir(RAW_CARDS_DIR) if re.match(r"^card_19_p\d{3}\.raw$", f)]
    
    card_dict = {}
    for f in a_raw_files:
        m = re.match(r"^card_19_a(\d{3})\.raw$", f)
        if m:
            num = int(m.group(1))
            card_dict[("A", num)] = f
            
    for f in p_raw_files:
        m = re.match(r"^card_19_p(\d{3})\.raw$", f)
        if m:
            num = int(m.group(1))
            card_dict[("P", num)] = f

    print(f"Loaded {len(card_dict)} cards from {RAW_CARDS_DIR} ({len(a_raw_files)} Series A, {len(p_raw_files)} Promo P).")

    decompiled_cards = {}
    for key, filename in sorted(card_dict.items()):
        prefix, num = key
        card_id_str = f"{prefix.lower()}{num:03d}"
        path = os.path.join(RAW_CARDS_DIR, filename)
        print(f"Decompiling card {prefix}{num:03d}...", end=" ", flush=True)
        try:
            card_data = decompile_raw_card(path)
            decompiled_cards[key] = card_data
            
            # Export individual map binary files for EVERY card
            card_map_dir_rel = f"graphics/trainer_hill/maps_ereader/card_{card_id_str}"
            card_map_dir_abs = os.path.join(PROJECT_ROOT, card_map_dir_rel)
            os.makedirs(card_map_dir_abs, exist_ok=True)
            with open(os.path.join(card_map_dir_abs, "metatiles.bin"), "wb") as f_out:
                f_out.write(card_data["map"]["metatiles"])
            with open(os.path.join(card_map_dir_abs, "collision.bin"), "wb") as f_out:
                f_out.write(card_data["map"]["collision"])
            
            print(f"OK ({card_data['name']}) -> saved to {card_map_dir_rel}")
        except Exception as e:
            print(f"FAILED: {e}")

    def card_to_map_data(card_data, card_id_str):
        coords = card_data["map"]["coords"]
        c1_x, c1_y = coords[0] & 0xF, (coords[0] >> 4) & 0xF
        c2_x, c2_y = coords[1] & 0xF, (coords[1] >> 4) & 0xF
        dirs = card_data["map"]["dirs"]
        dir_t1 = dir_names.get((dirs & 0xF) + 1, "DIR_SOUTH")
        dir_t2 = dir_names.get(((dirs >> 4) & 0xF) + 1, "DIR_NORTH")
        ranges = card_data["map"]["ranges"]
        range_t1 = ranges & 0xF
        range_t2 = (ranges >> 4) & 0xF
        return {
            "floor_map_rel": f"graphics/trainer_hill/maps_ereader/card_{card_id_str}",
            "c1_x": c1_x, "c1_y": c1_y,
            "c2_x": c2_x, "c2_y": c2_y,
            "dir_t1": dir_t1, "dir_t2": dir_t2,
            "range_t1": range_t1, "range_t2": range_t2
        }

    # 1. Normal Mode Candidates (JP Default 1 + A001..A016) = 17 layouts
    normal_cands = []
    shawn_map = {
        "floor_map_rel": "graphics/trainer_hill/maps_jp/floor_0",
        "c1_x": 8, "c1_y": 2, "c2_x": 8, "c2_y": 7,
        "dir_t1": "DIR_SOUTH", "dir_t2": "DIR_NORTH",
        "range_t1": 2, "range_t2": 3
    }
    normal_cands.append(format_candidate_c(0, 0, True, shawn_body, shawn_map, alt_trainer_name="sTrainer_Autumn"))
    for idx in range(1, 17):
        card_num = idx
        cdata = decompiled_cards[("A", card_num)]
        mdata = card_to_map_data(cdata, f"a{card_num:03d}")
        tbody = format_trainer_c(cdata, indent=12)
        normal_cands.append(format_candidate_c(idx, card_num, True, tbody, mdata))

    # 2. Variety Mode Candidates (JP Default 2 + A017..A032) = 17 layouts
    variety_cands = []
    simon_map = {
        "floor_map_rel": "graphics/trainer_hill/maps_jp/floor_1",
        "c1_x": 4, "c1_y": 6, "c2_x": 7, "c2_y": 9,
        "dir_t1": "DIR_EAST", "dir_t2": "DIR_SOUTH",
        "range_t1": 3, "range_t2": 3
    }
    variety_cands.append(format_candidate_c(0, 0, True, simon_body, simon_map, alt_trainer_name="sTrainer_Naomi"))
    for idx in range(1, 17):
        card_num = 16 + idx
        cdata = decompiled_cards[("A", card_num)]
        mdata = card_to_map_data(cdata, f"a{card_num:03d}")
        tbody = western_trainers[card_num] if card_num in western_trainers else format_trainer_c(cdata, indent=12)
        variety_cands.append(format_candidate_c(idx, card_num, True, tbody, mdata))

    # 3. Unique Mode Candidates (P001 + A033..A048) = 17 layouts
    unique_cands = []
    p1_data = decompiled_cards[("P", 1)]
    p1_map = card_to_map_data(p1_data, "p001")
    p1_body = format_trainer_c(p1_data, indent=12)
    unique_cands.append(format_candidate_c(0, p1_data["trainerNum"], True, p1_body, p1_map))
    for idx in range(1, 17):
        card_num = 32 + idx
        cdata = decompiled_cards[("A", card_num)]
        mdata = card_to_map_data(cdata, f"a{card_num:03d}")
        tbody = western_trainers[card_num] if card_num in western_trainers else format_trainer_c(cdata, indent=12)
        unique_cands.append(format_candidate_c(idx, card_num, True, tbody, mdata))

    # 4. Expert Mode Candidates (P002 + A049..A064) = 17 trainers (15 layouts)
    expert_cands = []
    p2_data = decompiled_cards[("P", 2)]
    p2_map = card_to_map_data(p2_data, "p002")
    p2_body = format_trainer_c(p2_data, indent=12)
    expert_cands.append(format_candidate_c(0, p2_data["trainerNum"], True, p2_body, p2_map))
    for idx in range(1, 17):
        card_num = 48 + idx
        cdata = decompiled_cards.get(("A", card_num))
        if cdata is not None:
            mdata = card_to_map_data(cdata, f"a{card_num:03d}")
            if card_num in (58, 59, 64):
                tbody = format_trainer_c(cdata, indent=12)
            else:
                tbody = western_trainers[card_num] if card_num in western_trainers else format_trainer_c(cdata, indent=12)
            expert_cands.append(format_candidate_c(idx, card_num, True, tbody, mdata))
        else:
            if card_num == 59:
                mdata = {
                    "floor_map_rel": "graphics/trainer_hill/maps_expert/floor_1",
                    "c1_x": 7, "c1_y": 10, "c2_x": 7, "c2_y": 14,
                    "dir_t1": "DIR_SOUTH", "dir_t2": "DIR_NORTH",
                    "range_t1": 3, "range_t2": 3
                }
                tbody = western_trainers[59]
                expert_cands.append(format_candidate_c(idx, 59, True, tbody, mdata))
            else:
                # 58 (Edie) and 64 (Gav): no map
                tbody = western_trainers[card_num]
                expert_cands.append(format_candidate_c(idx, card_num, False, tbody, None))

    c_output_parts = [
        f"static const struct TrainerHillTrainer sTrainer_Autumn = {{\n{autumn_body}\n}};\n",
        f"static const struct TrainerHillTrainer sTrainer_Naomi = {{\n{naomi_body}\n}};\n",
        "const struct TrainerHillCandidate sTrainerHillCandidates_Normal[17] = {\n" + "\n".join(normal_cands) + "\n};\n",
        "const struct TrainerHillCandidate sTrainerHillCandidates_Variety[17] = {\n" + "\n".join(variety_cands) + "\n};\n",
        "const struct TrainerHillCandidate sTrainerHillCandidates_Unique[17] = {\n" + "\n".join(unique_cands) + "\n};\n",
        "const struct TrainerHillCandidate sTrainerHillCandidates_Expert[17] = {\n" + "\n".join(expert_cands) + "\n};\n",
        """const struct TrainerHillCandidate *const sTrainerHillCandidates[NUM_TRAINER_HILL_MODES] = {
    [HILL_MODE_NORMAL]  = sTrainerHillCandidates_Normal,
    [HILL_MODE_VARIETY] = sTrainerHillCandidates_Variety,
    [HILL_MODE_UNIQUE]  = sTrainerHillCandidates_Unique,
    [HILL_MODE_EXPERT]  = sTrainerHillCandidates_Expert,
};
"""
    ]

    all_generated_c = "\n".join(c_output_parts)
    with open(EREADER_HEADER_PATH, "w") as f:
        f.write("// Auto-generated by tools/trainer_hill/decompile_ereader.py\n")
        f.write("// Contains Trainer Hill candidate arrays for Normal, Variety, Unique, Expert modes\n\n")
        f.write(all_generated_c)
    print(f"\nWritten all candidates to {EREADER_HEADER_PATH}!")

if __name__ == "__main__":
    main()
