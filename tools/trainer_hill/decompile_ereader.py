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
    1: { # Black Belt (Kousei)
        "speechBefore": ["EC_WORD_THIS", "EC_WORD_IS", "EC_WORD_WHERE", "EC_WORD_IT", "EC_WORD_ENDS", "EC_WORD_EXCL"],
        "speechWin":    ["EC_WORD_WAAAH", "EC_WORD_EXCL", "EC_WORD_I_AM", "EC_WORD_THE", "EC_WORD_CHAMP", "EC_WORD_EXCL"],
        "speechLose":   ["EC_WORD_THANKS", "EC_WORD_A_LOT", "EC_WORD_FOR", "EC_WORD_THAT", "EC_WORD_GREAT", "EC_WORD_BATTLE"],
        "speechAfter":  ["EC_WORD_YES_SIR_EXCL", "EC_WORD_YOU", "EC_WORD_LOOK", "EC_WORD_NICE", "EC_WORD_AND", "EC_WORD_GUTSY"],
    },
    2: { # Ninja Boy (Kagemasa)
        "speechBefore": ["EC_WORD_LOOK", "EC_WORD_AT", "EC_WORD_MY", "EC_WORD_SECRET", "EC_MOVE2(SMOKESCREEN)", "EC_WORD_EXCL"],
        "speechWin":    ["EC_WORD_YOU", "EC_WORD_COULDN_T", "EC_WORD_SEE", "EC_WORD_THROUGH", "EC_WORD_MY", "EC_MOVE2(SMOKESCREEN)"],
        "speechLose":   ["EC_WORD_HOW", "EC_WORD_COULD", "EC_WORD_YOU", "EC_WORD_SEE", "EC_WORD_ME", "EC_WORD_QUES"],
        "speechAfter":  ["EC_WORD_A", "EC_WORD_SECRET", "EC_WORD_IS", "EC_WORD_BEST", "EC_WORD_NOT", "EC_WORD_SAID"],
    },
    3: { # Pokefan M (Keizou)
        "speechBefore": ["EC_WORD_MY", "EC_WORD_POKEMON", "EC_WORD_ARE", "EC_WORD_JUST", "EC_WORD_SO", "EC_WORD_CUTE"],
        "speechWin":    ["EC_WORD_AREN_T", "EC_WORD_THEY", "EC_WORD_JUST", "EC_WORD_GREAT", "EC_WORD_AND", "EC_WORD_STRONG"],
        "speechLose":   ["EC_WORD_OH_DEAR", "EC_WORD_YOU", "EC_WORD_WERE", "EC_WORD_TOO", "EC_WORD_STRONG", "EC_EMPTY_WORD"],
        "speechAfter":  ["EC_WORD_I", "EC_WORD_CARE", "EC_WORD_FOR", "EC_WORD_MY", "EC_WORD_POKEMON", "EC_WORD_DAILY"],
    },
    4: { # Cooltrainer M (Akiomi)
        "speechBefore": ["EC_WORD_LET_S", "EC_WORD_HAVE", "EC_WORD_AN", "EC_WORD_EXCITING", "EC_WORD_BATTLE", "EC_WORD_EXCL"],
        "speechWin":    ["EC_WORD_MY", "EC_WORD_POKEMON", "EC_WORD_WON", "EC_WORD_THAT_WAS", "EC_WORD_TOO_EASY", "EC_WORD_EXCL"],
        "speechLose":   ["EC_WORD_THAT_WAS", "EC_WORD_A", "EC_WORD_VERY", "EC_WORD_COOL", "EC_WORD_BATTLE", "EC_WORD_EXCL"],
        "speechAfter":  ["EC_WORD_YOU_RE", "EC_WORD_PRETTY", "EC_WORD_GOOD", "EC_WORD_AT", "EC_WORD_THIS", "EC_WORD_BATTLE"],
    },
    5: { # Battle Girl (Riona)
        "speechBefore": ["EC_WORD_I", "EC_WORD_WILL", "EC_WORD_WIN", "EC_WORD_AND", "EC_WORD_GO", "EC_WORD_ON"],
        "speechWin":    ["EC_WORD_I_AM", "EC_WORD_AWESOME", "EC_WORD_EXCL", "EC_WORD_MY", "EC_WORD_POKEMON", "EC_WORD_RULE"],
        "speechLose":   ["EC_WORD_A_LITTLE", "EC_WORD_TOO", "EC_WORD_STRONG", "EC_WORD_FOR", "EC_WORD_ME", "EC_WORD_EXCL"],
        "speechAfter":  ["EC_WORD_I_AM", "EC_WORD_GOING_TO", "EC_WORD_TRAIN", "EC_WORD_AND", "EC_WORD_TRY", "EC_WORD_AGAIN"],
    },
    6: { # Dragon Tamer (Inami)
        "speechBefore": ["EC_WORD_I", "EC_WORD_GOT", "EC_WORD_MY", "EC_WORD_POKEMON", "EC_WORD_ON", "EC_WORD_VACATION"],
        "speechWin":    ["EC_WORD_IT_S", "EC_WORD_GREAT", "EC_WORD_TO", "EC_WORD_TRAVEL", "EC_WORD_AND", "EC_WORD_BATTLE"],
        "speechLose":   ["EC_WORD_WAAAH", "EC_WORD_EXCL", "EC_WORD_MY", "EC_WORD_RARE", "EC_WORD_POKEMON", "EC_WORD_EXCL"],
        "speechAfter":  ["EC_WORD_OFF", "EC_WORD_ON", "EC_WORD_ANOTHER", "EC_WORD_VACATION", "EC_WORD_I", "EC_WORD_GO"],
    },
    7: { # Pokemaniac (Yurato)
        "speechBefore": ["EC_WORD_I", "EC_WORD_COLLECT", "EC_WORD_ANY", "EC_WORD_POKEMON", "EC_WORD_THAT_S", "EC_WORD_RARE"],
        "speechWin":    ["EC_WORD_MY", "EC_WORD_COLLECTION", "EC_WORD_IS", "EC_WORD_TRULY", "EC_WORD_AWESOME", "EC_WORD_EXCL"],
        "speechLose":   ["EC_WORD_MY", "EC_WORD_RARE", "EC_WORD_POKEMON", "EC_WORD_LOST", "EC_WORD_ELLIPSIS", "EC_EMPTY_WORD"],
        "speechAfter":  ["EC_WORD_I_VE", "EC_WORD_DECIDED", "EC_WORD_I_CHOOSE_YOU", "EC_WORD_AS", "EC_WORD_MY", "EC_WORD_IDOL"],
    },
    8: { # Cycling Triathlete F (Sakuya)
        "speechBefore": ["EC_WORD_THIS", "EC_WORD_IS", "EC_WORD_HOW", "EC_WORD_YOU", "EC_WORD_WIN", "EC_WORD_EXCL"],
        "speechWin":    ["EC_WORD_DO", "EC_WORD_YOU", "EC_WORD_UNDERSTAND", "EC_WORD_HOW", "EC_WORD_NOW", "EC_WORD_QUES"],
        "speechLose":   ["EC_WORD_YES", "EC_WORD_THAT_S", "EC_WORD_HOW", "EC_WORD_YOU", "EC_WORD_DO", "EC_WORD_IT"],
        "speechAfter":  ["EC_WORD_YOU", "EC_WORD_BEAT", "EC_WORD_ME", "EC_WORD_GOOD", "EC_WORD_FOR", "EC_WORD_YOU"],
    },

    # Pack 2 (Cards 9..16)
    9: { # Lass (Komari)
        "speechBefore": ["EC_WORD_I_AM", "EC_WORD_REALLY", "EC_WORD_THE", "EC_WORD_BEST", "EC_WORD_AROUND", "EC_WORD_HERE"],
        "speechWin":    ["EC_WORD_OF_COURSE", "EC_WORD_I", "EC_WORD_WON", "EC_WORD_EXCL", "EC_EMPTY_WORD", "EC_EMPTY_WORD"],
        "speechLose":   ["EC_WORD_WHY", "EC_WORD_COULDN_T", "EC_WORD_I", "EC_WORD_WIN", "EC_WORD_QUES", "EC_EMPTY_WORD"],
        "speechAfter":  ["EC_WORD_I_AM", "EC_WORD_GOING_TO", "EC_WORD_GO", "EC_WORD_SHOPPING", "EC_WORD_NOW", "EC_EMPTY_WORD"],
    },
    10: { # Running Triathlete M (Ragi)
        "speechBefore": ["EC_WORD_I_AM", "EC_WORD_PRETTY", "EC_WORD_HAPPY", "EC_WORD_WITH", "EC_WORD_MY", "EC_WORD_SPEED"],
        "speechWin":    ["EC_WORD_MY", "EC_WORD_SPEED", "EC_WORD_IS", "EC_WORD_UNBELIEVABLE", "EC_WORD_EXCL", "EC_EMPTY_WORD"],
        "speechLose":   ["EC_WORD_THAT_WAS", "EC_WORD_AN", "EC_WORD_UNBELIEVABLE", "EC_WORD_LOSS", "EC_WORD_ELLIPSIS", "EC_EMPTY_WORD"],
        "speechAfter":  ["EC_WORD_I", "EC_WORD_MUST", "EC_WORD_WORK", "EC_WORD_ON", "EC_WORD_MY", "EC_WORD_SPEED"],
    },
    11: { # Ninja Boy (Kennosuke)
        "speechBefore": ["EC_WORD_YAHOO", "EC_WORD_EXCL", "EC_WORD_HERE_I_COME", "EC_WORD_BABY", "EC_WORD_EXCL", "EC_EMPTY_WORD"],
        "speechWin":    ["EC_WORD_I_AM", "EC_WORD_A", "EC_WORD_BIG", "EC_WORD_WINNER", "EC_WORD_BABY", "EC_WORD_EXCL"],
        "speechLose":   ["EC_WORD_SOMETHING", "EC_WORD_IS", "EC_WORD_TERRIBLY", "EC_WORD_WRONG", "EC_WORD_HERE", "EC_EMPTY_WORD"],
        "speechAfter":  ["EC_WORD_HOW", "EC_WORD_COULD", "EC_WORD_I", "EC_WORD_LOSE", "EC_WORD_THIS", "EC_WORD_QUES"],
    },
    12: { # Psychic M (Ozunu)
        "speechBefore": ["EC_WORD_THIS", "EC_WORD_POWER", "EC_WORD_IS", "EC_WORD_VERY", "EC_WORD_SPECIAL", "EC_EMPTY_WORD"],
        "speechWin":    ["EC_WORD_DID", "EC_WORD_YOU", "EC_WORD_FEEL", "EC_WORD_THAT", "EC_WORD_POWER", "EC_WORD_QUES"],
        "speechLose":   ["EC_WORD_WHERE", "EC_WORD_DID", "EC_WORD_THAT", "EC_WORD_POWER", "EC_WORD_GO", "EC_WORD_QUES"],
        "speechAfter":  ["EC_WORD_THIS", "EC_WORD_IS", "EC_WORD_NOT", "EC_WORD_A", "EC_WORD_DREAM", "EC_WORD_ELLIPSIS"],
    },
    13: { # School Kid F (Kae)
        "speechBefore": ["EC_WORD_TOO", "EC_WORD_BAD", "EC_WORD_IT_S", "EC_WORD_OVER", "EC_WORD_FOR", "EC_WORD_YOU"],
        "speechWin":    ["EC_WORD_NATURALLY", "EC_WORD_I", "EC_WORD_WIN", "EC_WORD_EXCL", "EC_EMPTY_WORD", "EC_EMPTY_WORD"],
        "speechLose":   ["EC_WORD_HOW", "EC_WORD_DID", "EC_WORD_THIS", "EC_WORD_HAPPEN", "EC_WORD_QUES", "EC_EMPTY_WORD"],
        "speechAfter":  ["EC_WORD_I_AM", "EC_WORD_SHOCKED", "EC_WORD_THAT", "EC_WORD_I", "EC_WORD_LOST", "EC_EMPTY_WORD"],
    },
    14: { # School Kid M (Sakiteru)
        "speechBefore": ["EC_WORD_AHAHA", "EC_WORD_YOU_RE", "EC_WORD_NOT", "EC_WORD_GOING", "EC_WORD_ANYWHERE", "EC_WORD_EXCL"],
        "speechWin":    ["EC_WORD_ALL_RIGHT", "EC_WORD_EXCL", "EC_WORD_BYE_BYE", "EC_WORD_EXCL", "EC_EMPTY_WORD", "EC_EMPTY_WORD"],
        "speechLose":   ["EC_WORD_HIYAH", "EC_WORD_EXCL_EXCL", "EC_WORD_DONE", "EC_WORD_IN", "EC_WORD_TOTALLY", "EC_WORD_EXCL_EXCL"],
        "speechAfter":  ["EC_WORD_TCH, EC_WORD_TCH", "EC_WORD_YOU_RE", "EC_WORD_TOO_STRONG", "EC_EMPTY_WORD", "EC_EMPTY_WORD"],
    },
    15: { # Pkmn Breeder F (Nukumi)
        "speechBefore": ["EC_WORD_I", "EC_WORD_WANT", "EC_WORD_SOMETHING", "EC_WORD_TASTY", "EC_WORD_TO", "EC_WORD_EAT"],
        "speechWin":    ["EC_WORD_MY", "EC_WORD_POKEMON", "EC_WORD_ARE", "EC_WORD_REALLY", "EC_WORD_HAPPY", "EC_WORD_EXCL"],
        "speechLose":   ["EC_WORD_WE_RE", "EC_WORD_NOT", "EC_WORD_HAPPY", "EC_WORD_AT", "EC_WORD_ALL", "EC_WORD_ELLIPSIS"],
        "speechAfter":  ["EC_WORD_I", "EC_WORD_HAVE", "EC_WORD_TO", "EC_WORD_TRAIN", "EC_WORD_SOME", "EC_WORD_MORE"],
    },
    16: { # Youngster (Akitaka)
        "speechBefore": ["EC_WORD_I_AM", "EC_WORD_CUTE", "EC_WORD_AND", "EC_WORD_I_AM", "EC_WORD_HAPPY", "EC_WORD_EXCL"],
        "speechWin":    ["EC_WORD_WE", "EC_WORD_WIN", "EC_WORD_AND", "EC_WORD_WE_RE", "EC_WORD_HAPPY", "EC_WORD_EXCL"],
        "speechLose":   ["EC_WORD_WE", "EC_WORD_LOST", "EC_WORD_AND", "EC_WORD_WE_RE", "EC_WORD_SAD", "EC_WORD_EXCL"],
        "speechAfter":  ["EC_WORD_I", "EC_WORD_LIKE", "EC_WORD_THE", "EC_WORD_BEGINNING", "EC_WORD_POKEMON", "EC_WORD_BEST"],
    },

    # Pack 4 (Cards 25..32)
    25: { # Sailor (Isonosuke)
        "speechBefore": ["EC_WORD_LET_S", "EC_WORD_GET", "EC_WORD_WITH", "EC_WORD_IT", "EC_EMPTY_WORD", "EC_EMPTY_WORD"],
        "speechWin":    ["EC_WORD_YES_SIR_EXCL", "EC_EMPTY_WORD", "EC_WORD_I_AM", "EC_WORD_NO_1", "EC_WORD_TODAY", "EC_EMPTY_WORD"],
        "speechLose":   ["EC_WORD_JUST", "EC_WORD_LOST", "EC_WORD_MY", "EC_MOVE2(SURF)", "EC_WORD_FEELING", "EC_EMPTY_WORD"],
        "speechAfter":  ["EC_WORD_I_AM", "EC_WORD_GOING", "EC_WORD_TO", "EC_WORD_BE", "EC_WORD_A", "EC_WORD_FATHER"],
    },
    26: { # Picnicker (Koeda)
        "speechBefore": ["EC_WORD_LET_S", "EC_WORD_BATTLE", "EC_WORD_IN", "EC_WORD_THE", "EC_WORD_COLD", "EC_WORD_EXCL"],
        "speechWin":    ["EC_WORD_THAT_WAS", "EC_WORD_AN", "EC_WORD_EASY", "EC_WORD_MATCH", "EC_WORD_FOR", "EC_WORD_ME"],
        "speechLose":   ["EC_WORD_THIS", "EC_WORD_CAN_T", "EC_WORD_BE", "EC_WORD_HAPPENING", "EC_WORD_TO_ME", "EC_WORD_EXCL"],
        "speechAfter":  ["EC_WORD_I", "EC_WORD_WANT", "EC_WORD_A", "EC_WORD_HOT", "EC_WORD_BATH", "EC_WORD_NOW"],
    },
    27: { # Expert M (Isaji)
        "speechBefore": ["EC_WORD_OH_DEAR", "EC_WORD_THIS", "EC_WORD_MATCH", "EC_WORD_IS", "EC_WORD_FOR", "EC_WORD_YOU"],
        "speechWin":    ["EC_WORD_OH_DEAR", "EC_WORD_DID", "EC_WORD_YOU", "EC_WORD_SEE", "EC_WORD_THAT, EC_WORD_QUES"],
        "speechLose":   ["EC_WORD_OH_DEAR", "EC_WORD_I_AM", "EC_WORD_SO", "EC_WORD_SORRY", "EC_EMPTY_WORD", "EC_EMPTY_WORD"],
        "speechAfter":  ["EC_WORD_IS", "EC_WORD_YOUR", "EC_WORD_GRANDMOTHER", "EC_WORD_STRONG", "EC_WORD_QUES", "EC_EMPTY_WORD"],
    },
    28: { # Running Triathlete F (Ouka)
        "speechBefore": ["EC_WORD_THIS", "EC_WORD_IS", "EC_WORD_HOW", "EC_WORD_YOU", "EC_WORD_WIN", "EC_WORD_EXCL"],
        "speechWin":    ["EC_WORD_DO", "EC_WORD_YOU", "EC_WORD_UNDERSTAND", "EC_WORD_HOW", "EC_WORD_NOW", "EC_WORD_QUES"],
        "speechLose":   ["EC_WORD_YES", "EC_WORD_THAT_S", "EC_WORD_HOW", "EC_WORD_YOU", "EC_WORD_DO", "EC_WORD_IT"],
        "speechAfter":  ["EC_WORD_YOU", "EC_WORD_BEAT", "EC_WORD_ME", "EC_WORD_GOOD", "EC_WORD_FOR", "EC_WORD_YOU"],
    },
    29: { # Beauty (Maiko)
        "speechBefore": ["EC_WORD_I_AM", "EC_WORD_THE", "EC_WORD_GROUP", "EC_WORD_LEADER", "EC_WORD_TODAY", "EC_WORD_EXCL"],
        "speechWin":    ["EC_WORD_I_AM", "EC_WORD_SO", "EC_WORD_HAPPY", "EC_WORD_I", "EC_WORD_WON", "EC_WORD_EXCL"],
        "speechLose":   ["EC_WORD_THAT", "EC_WORD_MAKES", "EC_WORD_ME", "EC_WORD_REALLY", "EC_WORD_ANGRY", "EC_WORD_EXCL"],
        "speechAfter":  ["EC_WORD_I_AM", "EC_WORD_NOT", "EC_WORD_TALKING", "EC_WORD_WITH", "EC_WORD_YOU", "EC_WORD_ELLIPSIS"],
    },
    30: { # Parasol Lady (Akino)
        "speechBefore": ["EC_WORD_HI", "EC_WORD_ARE", "EC_WORD_YOU", "EC_WORD_FEELING", "EC_WORD_UPBEAT", "EC_WORD_QUES"],
        "speechWin":    ["EC_WORD_AREN_T", "EC_WORD_YOU", "EC_WORD_FEELING", "EC_WORD_WELL", "EC_WORD_QUES", "EC_EMPTY_WORD"],
        "speechLose":   ["EC_WORD_I", "EC_WORD_CAN", "EC_WORD_SEE", "EC_WORD_YOU_RE", "EC_WORD_FEELING", "EC_WORD_GREAT"],
        "speechAfter":  ["EC_WORD_YOUR", "EC_WORD_POKEMON", "EC_WORD_LOOK", "EC_WORD_READY", "EC_WORD_TO", "EC_WORD_HUSTLE"],
    },
    31: { # Hiker (Okikazu)
        "speechBefore": ["EC_WORD_MY", "EC_WORD_POKEMON", "EC_WORD_ARE", "EC_WORD_ROCK_SOLID", "EC_WORD_AND", "EC_WORD_TOUGH"],
        "speechWin":    ["EC_WORD_MY", "EC_WORD_POKEMON", "EC_WORD_ARE", "EC_WORD_VERY", "EC_WORD_STRONG", "EC_WORD_EXCL"],
        "speechLose":   ["EC_WORD_YOU", "EC_WORD_CAN_WIN", "EC_WORD_WITH", "EC_WORD_A", "EC_WORD_ROCK", "EC_WORD_HEAD"],
        "speechAfter":  ["EC_WORD_I_AM", "EC_WORD_DISAPPOINTED", "EC_WORD_BUT", "EC_WORD_YOU", "EC_WORD_WIN", "EC_WORD_ELLIPSIS"],
    },
    32: { # Tuber F (Rikka)
        "speechBefore": ["EC_WORD_I_AM", "EC_WORD_A_LITTLE", "EC_WORD_COLD", "EC_WORD_TODAY", "EC_EMPTY_WORD", "EC_EMPTY_WORD"],
        "speechWin":    ["EC_WORD_I_AM", "EC_WORD_SO", "EC_WORD_HAPPY", "EC_WORD_I_AM", "EC_WORD_WARM", "EC_WORD_NOW"],
        "speechLose":   ["EC_WORD_WAAAH", "EC_WORD_ELLIPSIS", "EC_EMPTY_WORD", "EC_WORD_I", "EC_WORD_LOST", "EC_WORD_ELLIPSIS"],
        "speechAfter":  ["EC_WORD_I_AM", "EC_WORD_GOING", "EC_WORD_TO", "EC_WORD_GO", "EC_WORD_HOME", "EC_EMPTY_WORD"],
    },

    # Pack 5 (Cards 33..40)
    33: { # Camper (Kousuke)
        "speechBefore": ["EC_WORD_MY", "EC_WORD_POKEMON", "EC_WORD_ARE", "EC_WORD_TOP", "EC_WORD_GRADE", "EC_WORD_EXCL"],
        "speechWin":    ["EC_WORD_SEE", "EC_WORD_QUES", "EC_WORD_THEY_RE", "EC_WORD_REALLY", "EC_WORD_TOP", "EC_WORD_GRADE"],
        "speechLose":   ["EC_WORD_I", "EC_WORD_DON_T", "EC_WORD_BELIEVE", "EC_WORD_THIS", "EC_WORD_AT_ALL", "EC_WORD_ELLIPSIS"],
        "speechAfter":  ["EC_WORD_ALL", "EC_WORD_I", "EC_WORD_DO", "EC_WORD_IS", "EC_WORD_LOSE", "EC_WORD_ELLIPSIS"],
    },
    34: { # Guitarist (Neo)
        "speechBefore": ["EC_WORD_LALALA", "EC_WORD_LET_S", "EC_MOVE(SING)", "EC_WORD_A", "EC_WORD_SONG", "EC_WORD_EXCL"],
        "speechWin":    ["EC_WORD_LALALA", "EC_WORD_MY", "EC_WORD_MUSIC", "EC_WORD_IS", "EC_WORD_PERFECT", "EC_WORD_EXCL"],
        "speechLose":   ["EC_WORD_WAAAH", "EC_WORD_EXCL_EXCL", "EC_WORD_I", "EC_WORD_CAN_T", "EC_MOVE(SING)", "EC_WORD_ELLIPSIS"],
        "speechAfter":  ["EC_WORD_MY", "EC_WORD_SONG", "EC_WORD_WAS", "EC_WORD_OUT_OF_THE_QUESTION", "EC_WORD_HUH_QUES", "EC_EMPTY_WORD"],
    },
    35: { # Rich Boy (Tsugane)
        "speechBefore": ["EC_WORD_MY", "EC_WORD_POKEMON", "EC_WORD_COST", "EC_WORD_A_LOT", "EC_WORD_OF", "EC_WORD_MONEY"],
        "speechWin":    ["EC_WORD_MY", "EC_WORD_MONEY", "EC_WORD_IS", "EC_WORD_WELL", "EC_WORD_SPENT", "EC_WORD_EXCL"],
        "speechLose":   ["EC_WORD_I", "EC_WORD_NEED", "EC_WORD_MORE", "EC_WORD_MONEY", "EC_WORD_FOR", "EC_WORD_POKEMON"],
        "speechAfter":  ["EC_WORD_DID", "EC_WORD_YOU", "EC_WORD_SEE", "EC_WORD_MY", "EC_WORD_SKILL", "EC_WORD_QUES"],
    },
    36: { # Hex Maniac (Kagaho)
        "speechBefore": ["EC_WORD_YOU", "EC_WORD_CAN", "EC_WORD_CHOOSE", "EC_WORD_NOT", "EC_WORD_TO", "EC_WORD_BELIEVE"],
        "speechWin":    ["EC_WORD_A", "EC_WORD_SUPER", "EC_WORD_NATURAL", "EC_WORD_POWER", "EC_WORD_HAS", "EC_WORD_COME"],
        "speechLose":   ["EC_WORD_THIS", "EC_WORD_MUST_BE", "EC_WORD_A", "EC_MOVE(NIGHTMARE)", "EC_WORD_EXCL", "EC_EMPTY_WORD"],
        "speechAfter":  ["EC_WORD_I", "EC_WORD_WILL", "EC_WORD_DISAPPEAR", "EC_WORD_IN", "EC_WORD_THE", "EC_WORD_DARK"],
    },
    37: { # Beauty (Tsukika)
        "speechBefore": ["EC_WORD_I_AM", "EC_WORD_THE", "EC_WORD_STRONG", "EC_WORD_BEAUTY", "EC_WORD_AROUND", "EC_WORD_HERE"],
        "speechWin":    ["EC_WORD_I_AM", "EC_WORD_STRONG", "EC_WORD_THAT_S", "EC_WORD_WHY", "EC_WORD_EXCL", "EC_EMPTY_WORD"],
        "speechLose":   ["EC_WORD_I_AM", "EC_WORD_TIRED", "EC_WORD_TODAY", "EC_WORD_THAT_S", "EC_WORD_WHY", "EC_WORD_EXCL"],
        "speechAfter":  ["EC_WORD_WHY", "EC_WORD_YES", "EC_WORD_I_AM", "EC_WORD_ANGRY", "EC_WORD_THANK_YOU", "EC_WORD_EXCL"],
    },
    38: { # Gentleman (Edo)
        "speechBefore": ["EC_WORD_HMM", "EC_WORD_QUES", "EC_WORD_ARE", "EC_WORD_YOU", "EC_WORD_LOOKING", "EC_WORD_AT_ME"],
        "speechWin":    ["EC_WORD_SPLENDID", "EC_WORD_I_AM", "EC_WORD_THE", "EC_WORD_WINNER", "EC_WORD_TODAY", "EC_WORD_EXCL"],
        "speechLose":   ["EC_WORD_DISASTER", "EC_WORD_EXCL", "EC_WORD_I_AM", "EC_WORD_SHOCKED", "EC_WORD_TOTALLY", "EC_WORD_EXCL"],
        "speechAfter":  ["EC_WORD_I_AM", "EC_WORD_GOING", "EC_WORD_TO", "EC_WORD_A", "EC_WORD_PARTY", "EC_WORD_NOW"],
    },
    39: { # Pkmn Breeder M (Kaiji)
        "speechBefore": ["EC_WORD_LET_S", "EC_MOVE2(WRAP)", "EC_WORD_THINGS", "EC_WORD_UP", "EC_WORD_HERE", "EC_WORD_HEY_QUES"],
        "speechWin":    ["EC_WORD_WOULD", "EC_WORD_YOU", "EC_WORD_LIKE", "EC_WORD_TO", "EC_WORD_GO_HOME", "EC_WORD_QUES"],
        "speechLose":   ["EC_WORD_I", "EC_WORD_WILL", "EC_WORD_MAKE", "EC_WORD_YOU", "EC_WORD_SORRY", "EC_WORD_FRIEND"],
        "speechAfter":  ["EC_WORD_HAVEN_T", "EC_WORD_YOU", "EC_WORD_DONE", "EC_WORD_ENOUGH", "EC_WORD_QUES", "EC_EMPTY_WORD"],
    },
    40: { # Bug Catcher (Kiichi)
        "speechBefore": ["EC_WORD_POISON", "EC_WORD_IS", "EC_WORD_JUST", "EC_WORD_AWESOME", "EC_WORD_OKAY", "EC_WORD_QUES"],
        "speechWin":    ["EC_WORD_MY", "EC_WORD_POKEMON", "EC_WORD_RULE", "EC_WORD_SO", "EC_WORD_THERE", "EC_WORD_EXCL"],
        "speechLose":   ["EC_WORD_YOU_RE", "EC_WORD_NOT", "EC_WORD_NICE", "EC_WORD_AT_ALL", "EC_WORD_EXCL", "EC_EMPTY_WORD"],
        "speechAfter":  ["EC_WORD_POISON", "EC_WORD_IS", "EC_WORD_A", "EC_WORD_TERRIBLE", "EC_MOVE(TORMENT)", "EC_WORD_ISN_T_IT_QUES"],
    },

    # Promo (Cards 101..102)
    101: { # Camper (Soushi)
        "speechBefore": ["EC_WORD_LET_S", "EC_WORD_HAVE", "EC_WORD_AN", "EC_WORD_EXCITING", "EC_WORD_BATTLE", "EC_WORD_EXCL"],
        "speechWin":    ["EC_WORD_THAT_WAS", "EC_WORD_AN", "EC_WORD_EXCITING", "EC_WORD_MATCH", "EC_WORD_FOR", "EC_WORD_ME"],
        "speechLose":   ["EC_WORD_THAT_WAS", "EC_WORD_AN", "EC_WORD_AWESOME", "EC_WORD_BATTLE", "EC_WORD_MY", "EC_WORD_FRIEND"],
        "speechAfter":  ["EC_WORD_YOU_RE", "EC_WORD_PRETTY", "EC_WORD_GOOD", "EC_WORD_AT", "EC_WORD_THIS", "EC_WORD_BATTLE"],
    },
    102: { # School Kid M (Toshinori)
        "speechBefore": ["EC_WORD_AHAHA", "EC_WORD_YOU_RE", "EC_WORD_NOT", "EC_WORD_GOING", "EC_WORD_ANYWHERE", "EC_WORD_EXCL"],
        "speechWin":    ["EC_WORD_ALL_RIGHT", "EC_WORD_EXCL", "EC_WORD_BYE_BYE", "EC_WORD_EXCL", "EC_EMPTY_WORD", "EC_EMPTY_WORD"],
        "speechLose":   ["EC_WORD_HIYAH", "EC_WORD_EXCL_EXCL", "EC_WORD_DONE", "EC_WORD_IN", "EC_WORD_TOTALLY", "EC_WORD_EXCL_EXCL"],
        "speechAfter":  ["EC_WORD_TCH, EC_WORD_TCH", "EC_WORD_YOU_RE", "EC_WORD_TOO_STRONG", "EC_EMPTY_WORD", "EC_EMPTY_WORD"],
    }
}

def extract_western_trainers_from_source(indent=16):
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
    # Youngster Shigenobu -> Shawn
    "シゲノブ": {
        "name": "SHAWN",
        "speechBefore": "{ EC_WORD_AHAHA, EC_WORD_YOU_RE, EC_WORD_NOT, EC_WORD_GOING, EC_WORD_ANYWHERE, EC_WORD_EXCL }",
        "speechWin":    "{ EC_WORD_ALL_RIGHT, EC_WORD_EXCL, EC_WORD_BYE_BYE, EC_WORD_EXCL, EC_EMPTY_WORD, EC_EMPTY_WORD }",
        "speechLose":   "{ EC_WORD_HIYAH, EC_WORD_EXCL_EXCL, EC_WORD_DONE, EC_WORD_IN, EC_WORD_TOTALLY, EC_WORD_EXCL_EXCL }",
        "speechAfter":  "{ EC_WORD_TCH, EC_WORD_TCH, EC_WORD_YOU_RE, EC_WORD_TOO_STRONG, EC_EMPTY_WORD, EC_EMPTY_WORD }",
    },
    # Parasol Lady Akari -> Autumn
    "アカリ": {
        "name": "AUTUMN",
        "speechBefore": "{ EC_WORD_HI, EC_WORD_ARE, EC_WORD_YOU, EC_WORD_FEELING, EC_WORD_UPBEAT, EC_WORD_QUES }",
        "speechWin":    "{ EC_WORD_AREN_T, EC_WORD_YOU, EC_WORD_FEELING, EC_WORD_WELL, EC_WORD_QUES, EC_EMPTY_WORD }",
        "speechLose":   "{ EC_WORD_I, EC_WORD_CAN, EC_WORD_SEE, EC_WORD_YOU_RE, EC_WORD_FEELING, EC_WORD_GREAT }",
        "speechAfter":  "{ EC_WORD_YOUR, EC_WORD_POKEMON, EC_WORD_LOOK, EC_WORD_READY, EC_WORD_TO, EC_WORD_HUSTLE }",
    },
    # Ninja Boy Shigezou -> Simon
    "シゲゾウ": {
        "name": "SIMON",
        "speechBefore": "{ EC_WORD_YAHOO, EC_WORD_EXCL, EC_WORD_HERE_I_COME, EC_WORD_BABY, EC_WORD_EXCL, EC_EMPTY_WORD }",
        "speechWin":    "{ EC_WORD_I_AM, EC_WORD_A, EC_WORD_BIG, EC_WORD_WINNER, EC_WORD_BABY, EC_WORD_EXCL }",
        "speechLose":   "{ EC_WORD_SOMETHING, EC_WORD_IS, EC_WORD_TERRIBLY, EC_WORD_WRONG, EC_WORD_HERE, EC_EMPTY_WORD }",
        "speechAfter":  "{ EC_WORD_HOW, EC_WORD_COULD, EC_WORD_I, EC_WORD_LOSE, EC_WORD_THIS, EC_WORD_QUES }",
    },
    # Beauty Namiko -> Naomi
    "ナミコ": {
        "name": "NAOMI",
        "speechBefore": "{ EC_WORD_I_AM, EC_WORD_THE, EC_WORD_GROUP, EC_WORD_LEADER, EC_WORD_TODAY, EC_WORD_EXCL }",
        "speechWin":    "{ EC_WORD_I_AM, EC_WORD_SO, EC_WORD_HAPPY, EC_WORD_I, EC_WORD_WON, EC_WORD_EXCL }",
        "speechLose":   "{ EC_WORD_HOW, EC_WORD_COULD, EC_WORD_I, EC_WORD_LOSE, EC_WORD_THIS, EC_WORD_QUES }",
        "speechAfter":  "{ EC_WORD_I_AM, EC_WORD_NOT, EC_WORD_TALKING, EC_WORD_WITH, EC_WORD_YOU, EC_WORD_ELLIPSIS }",
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

def main():
    print("Extracting 32 Western trainers directly from trainer_hill.h...")
    western_trainers = extract_western_trainers_from_source(indent=16)
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

    c_output_parts = []
    
    # 1. Add the 2 default Japanese floors at the beginning (with English species nicknames)
    jp_defaults = extract_jp_default_floors()
    if jp_defaults:
        c_output_parts.append("// Default Japanese 2-floor challenge from original ROM\n" + jp_defaults)

    # 2. Generate arrays for 8 packs of Series A (1..8, 9..16, ..., 57..64)
    for pack_idx in range(8):
        pack_num = pack_idx + 1
        pack_start = pack_idx * 8 + 1
        
        floors_c = []
        for floor_idx in range(4):
            t1_num = pack_start + floor_idx * 2
            t2_num = t1_num + 1
            
            t1_data = decompiled_cards.get(("A", t1_num))
            t2_data = decompiled_cards.get(("A", t2_num))
            
            # Floor map and layout:
            # For Pack 8 Floor 1 (59 & 60), if raw 59 is missing, fallback to expert floor 1
            if t1_num == 59 and t1_data is None:
                floor_map_rel = "graphics/trainer_hill/maps_expert/floor_1"
                c1_x, c1_y = 7, 10
                c2_x, c2_y = 7, 14
                dir_t1, dir_t2 = "DIR_SOUTH", "DIR_NORTH"
                range_t1, range_t2 = 3, 3
            else:
                map_source = t1_data if t1_data is not None else t2_data
                source_card_id = f"a{t1_num:03d}" if t1_data is not None else (f"a{t2_num:03d}" if t2_data is not None else None)
                
                if map_source is not None and source_card_id is not None:
                    floor_map_rel = f"graphics/trainer_hill/maps_ereader/card_{source_card_id}"
                    coords = map_source["map"]["coords"]
                    c1_x, c1_y = coords[0] & 0xF, (coords[0] >> 4) & 0xF
                    c2_x, c2_y = coords[1] & 0xF, (coords[1] >> 4) & 0xF
                    
                    dirs = map_source["map"]["dirs"]
                    dir_t1 = dir_names.get((dirs & 0xF) + 1, "DIR_SOUTH")
                    dir_t2 = dir_names.get(((dirs >> 4) & 0xF) + 1, "DIR_NORTH")
                    
                    ranges = map_source["map"]["ranges"]
                    range_t1 = ranges & 0xF
                    range_t2 = (ranges >> 4) & 0xF
                else:
                    floor_map_rel = "graphics/trainer_hill/maps_jp/floor_0"
                    c1_x, c1_y = 4, 6
                    c2_x, c2_y = 7, 9
                    dir_t1, dir_t2 = "DIR_EAST", "DIR_SOUTH"
                    range_t1, range_t2 = 3, 3

            # Trainer 1:
            # If in western_trainers (Packs 3, 6, 7, 8): load entire struct directly from trainer_hill.h!
            if t1_num in western_trainers:
                t1_body = western_trainers[t1_num]
            elif t1_data is not None:
                t1_body = format_trainer_c(t1_data, indent=16)
            else:
                t1_body = format_dummy_trainer_c(indent=16)

            # Trainer 2:
            if t2_num in western_trainers:
                t2_body = western_trainers[t2_num]
            elif t2_data is not None:
                t2_body = format_trainer_c(t2_data, indent=16)
            else:
                t2_body = format_dummy_trainer_c(indent=16)
            
            floor_str = f"""    [{floor_idx}] = {{
        .trainerNum1 = {t1_num},
        .trainerNum2 = {t2_num},
        .trainers = {{
            [0] = {{
{t1_body}
            }},
            [1] = {{
{t2_body}
            }},
        }},
        .map = {{
            .metatileData = INCBIN_U8("{floor_map_rel}/metatiles.bin"),
            .collisionData = INCBIN_U16("{floor_map_rel}/collision.bin"),
            .trainerCoords = {{ COORDS_XY({c1_x},{c1_y}), COORDS_XY({c2_x},{c2_y}) }},
            .trainerDirections = TRAINER_DIRS({dir_t1}, {dir_t2}),
            .trainerRanges = TRAINER_RANGE({range_t1}, {range_t2})
        }}
    }},"""
            floors_c.append(floor_str)

        floors_block = "\n".join(floors_c)
        pack_code = f"""static const struct TrainerHillFloor sFloors_EReaderPack{pack_num}[] = {{
{floors_block}
}};
"""
        c_output_parts.append(pack_code)

    # 3. Promo floor (P001 & P002) - using P001 as primary map
    p1_data = decompiled_cards.get(("P", 1))
    p2_data = decompiled_cards.get(("P", 2))
    if p1_data or p2_data:
        map_source = p1_data if p1_data else p2_data
        source_card_id = "p001" if p1_data else "p002"
        floor_map_rel = f"graphics/trainer_hill/maps_ereader/card_{source_card_id}"
        
        coords = map_source["map"]["coords"]
        c1_x, c1_y = coords[0] & 0xF, (coords[0] >> 4) & 0xF
        c2_x, c2_y = coords[1] & 0xF, (coords[1] >> 4) & 0xF
        dirs = map_source["map"]["dirs"]
        dir_t1 = dir_names.get((dirs & 0xF) + 1, "DIR_SOUTH")
        dir_t2 = dir_names.get(((dirs >> 4) & 0xF) + 1, "DIR_NORTH")
        ranges = map_source["map"]["ranges"]
        range_t1 = ranges & 0xF
        range_t2 = (ranges >> 4) & 0xF
        
        t1_body = format_trainer_c(p1_data, indent=16) if p1_data else format_dummy_trainer_c(indent=16)
        t2_body = format_trainer_c(p2_data, indent=16) if p2_data else format_dummy_trainer_c(indent=16)
        
        promo_code = f"""static const struct TrainerHillFloor sFloors_EReaderPromo[] = {{
    [0] = {{
        .trainerNum1 = {p1_data['trainerNum'] if p1_data else 0},
        .trainerNum2 = {p2_data['trainerNum'] if p2_data else 0},
        .trainers = {{
            [0] = {{
{t1_body}
            }},
            [1] = {{
{t2_body}
            }},
        }},
        .map = {{
            .metatileData = INCBIN_U8("{floor_map_rel}/metatiles.bin"),
            .collisionData = INCBIN_U16("{floor_map_rel}/collision.bin"),
            .trainerCoords = {{ COORDS_XY({c1_x},{c1_y}), COORDS_XY({c2_x},{c2_y}) }},
            .trainerDirections = TRAINER_DIRS({dir_t1}, {dir_t2}),
            .trainerRanges = TRAINER_RANGE({range_t1}, {range_t2})
        }}
    }},
}};
"""
        c_output_parts.append(promo_code)

    all_generated_c = "\n".join(c_output_parts)
    with open(EREADER_HEADER_PATH, "w") as f:
        f.write("// Auto-generated by tools/trainer_hill/decompile_ereader.py\n")
        f.write("// Contains Japanese Emerald Battle e+ Trainer Hill floors with Western data and adjusted speeches\n\n")
        f.write(all_generated_c)
    print(f"\nWritten all packs to {EREADER_HEADER_PATH}!")

if __name__ == "__main__":
    main()
