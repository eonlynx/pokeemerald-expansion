# AGENTS.md - Trainer Hill E-Reader Expansion & Localization

This document summarizes the architecture, objectives, technical decisions, and full progress achieved in the **Trainer Hill** facility within `pokeemerald-expansion`. It serves as a comprehensive reference guide for any AI agent or developer continuing or maintaining this work.

---

## 1. Context & Core Objectives

The project expands Pokémon Emerald's **Trainer Hill** facility by replacing its vanilla static 4-floor layout per game mode with a procedural system powered by all Japanese e-Reader cards (Series A001..A064, P001, P002) and default Japanese trainers (*JP Default*). It features procedural selection of floors/trainers, tag-battle Pokémon team shuffling, and faithful localization of trainer names and Easy Chat speeches.

### Floor / Candidate Distribution by Mode (17 candidates each):
- **Normal:** JP Default 1 + A001 through A016 (17 candidates/layouts)
- **Variety:** JP Default 2 + A017 through A032 (17 candidates/layouts)
- **Unique:** P001 + A033 through A048 (17 candidates/layouts)
- **Expert:** P002 + A049 through A064 (17 candidates; currently 15 layouts available due to missing card dumps for cards 58 and 64)

Each run randomly selects **8 trainers distributed across 4 floors** (2 trainers per floor).

---

## 2. Requirements & Implementations

### 2.1. Handling Missing Cards & Maps (Cards 58, 59, and 64)
- **Card 59 (Roderick):** Its floor layout corresponds to the Expert 2F map; properly bound.
- **Cards 58 (Edie) and 64 (Gav):** Missing `.raw` card dumps.
  - Trainer data (3 Pokémon each) extracted from `src/data/battle_frontier/trainer_hill.h`.
  - **Floor position constraint:** Lacking map dumps, trainers 58 and 64 **can only appear as the second trainer (`trainerNum2` / right-side trainer)** of any floor, never as the first trainer (`trainerNum1`), avoiding requests for non-existent maps.
  - The pipeline is prepared so that if `.raw` dumps for 58 or 64 are added in the future, their maps will automatically load and allow them to appear as first trainers.

### 2.2. JP Default Trainer Fusion & Alternation
- **JP Default 1:** `AUTUMN` and `SHAWN` share their original map. They count as a single candidate slot: their teams are merged (Shawn's 3 Pokémon + Autumn's 3 Pokémon) and one of the two is randomly chosen to occupy Trainer 1 for the floor.
- **JP Default 2:** `SIMON` and `NAOMI` share their original map identically, merging their Pokémon and alternating randomly in the Trainer 1 slot.
- The second trainer of the floor is picked randomly from the remaining candidates in that mode.

### 2.3. No-Repeat Consecutive Floors
- To prevent repetitive experiences when immediately replaying the same mode, trainers who served as the first trainer on each floor (positions 1, 3, 5, and 7 of the previous run) cannot appear as the first trainer in the very next run of that mode (they may still appear as the second trainer).

### 2.4. Pokémon Team Shuffling
- In double/tag battles, only the first 3 Pokémon of each trainer would enter combat under standard rules.
- A team shuffle algorithm was implemented so that each run randomizes the order of all 6 Pokémon on the trainer's team, allowing players to encounter the full breadth of the trainer's roster.

### 2.5. Nickname Standardization
- No Trainer Hill e-Reader Pokémon retains Japanese names or glyphs.
- All nicknames (`.nickname`) default to the uppercase English species name (`_("PIKACHU")`, `_("GROVYLE")`, etc.).
- Original Japanese teams were preserved without corruption (e.g., Toshinori / Ashton keeps his canonical team: Grovyle, Torkoal, Totodile, Pikachu, Corphish, and Charizard).

### 2.6. Trainer Name Localization
- For the **32 Western cards** (Packs 3, 6, 7, and 8: cards 17..24 and 41..64), official Western localized names from `trainer_hill.h` are preserved (`ALAINA`, `THEODORE`, `MEREDITH`, `RODERICK`, etc.).
- For the **34 non-Western and promo cards**, Japanese names were localized into standard English trainer names consistent with the facility's conventions (`KENT`, `MASON`, `KEITH`, `ARTHUR`, `LEONA`, `IRENE`, `LOGAN`, `SKYE`, `SOREN`, `ASHTON`, etc.).
- For JP Default trainers, localized names `SHAWN`, `AUTUMN`, `SIMON`, and `NAOMI` are used.

### 2.7. Authentic Easy Chat Speeches Localization
- Generic or disconnected stock phrases were completely rejected.
- All 24 `u16` Easy Chat words (`speechBefore`, `speechWin`, `speechLose`, `speechAfter`) were directly decompiled from the binary dotcodes of the 34 Japanese cards and from `sFloors_JPDefault`.
- The phrases were decoded via Japanese gojūon alphabetical indices, analyzed for original nuance and personality, and faithfully translated into natural English Easy Chat sentences composed **strictly of valid tokens** from `include/constants/easy_chat.h`:
  - *Card 1 (Kent):* Move trump card theme (`EC_MOVE(TRUMP_CARD)`).
  - *Card 6 (Irene):* Reverence for Lord Dragon (`EC_WORD_DRAGON`, `EC_WORD_MR`).
  - *Card 14 (Sammy):* Signature catchphrase (`EC_WORD_OI_OI_OI`, `EC_WORD_HEY_THERE`).
  - *Card 16 (Alan):* Pride in strength without evolving (`EC_WORD_WITHOUT`, `EC_WORD_EVOLVE`).
  - *Card 25 (Ian):* Surf enthusiasm (`EC_MOVE2(SURF)`, `EC_WORD_FEELING`, `EC_WORD_YAHOO`).
  - *Card 26 (Kyle):* "If I win I play, if I lose I go home" (`EC_WORD_IF_I_WIN`, `EC_WORD_IF_I_LOSE`, `EC_WORD_GO_HOME`).
  - *Card 30 (Austin):* Dislikes quick battles, loves Curse (`EC_MOVE2(CURSE)`).
  - *Card 34 (Nolan):* Swift level / Master level (`EC_MOVE(SWIFT)`, `EC_WORD_LEVEL`).
  - *Card 35 (Travis):* Spending all money on Pokémon and crying to mother (`EC_WORD_MONEY`, `EC_WORD_MOTHER`).
  - *Card 39 (Kaleb):* Constantly apologizing in every phrase (`EC_WORD_EXCUSE_ME`).
  - *Card 101 (Soren):* Emerald's beauty and Pokémon colors (`EC_WORD_EMERALD`, `EC_WORD_BEAUTIFUL`, `EC_WORD_COLOR`).
  - *Card 102 (Ashton):* "I choose you!", never give up, and keeping a brave front (`EC_WORD_I_CHOOSE_YOU`, `EC_MOVE(FACADE)`).
  - *Shawn:* Addressing the "Trainer lady" (`EC_WORD_MISS`, `EC_WORD_TRAINER`).
  - *Autumn:* Loving all Pokémon types and Earthquake (`EC_MOVE(EARTHQUAKE)`).
  - *Simon:* Constrict commitment (`EC_MOVE(CONSTRICT)`) and tomorrow is another day.
  - *Naomi:* Requesting opponents not to go easy on her (`EC_WORD_DON_T`, `EC_WORD_BE`, `EC_WORD_KIND`).

---

## 3. Key Source Files

1. **`tools/trainer_hill/decompile_ereader.py`**:
   - Python pipeline decoding dotcodes in `data/raw_cards/trainer_hill/` via `nedcenc` and `nevpk`.
   - Extracts metatile maps, trainer collision, IVs, EVs, moves, and held items.
   - Enforces English trainer names, replaces Japanese nicknames with species names, and writes faithful Easy Chat phrases.
   - Generates `src/data/battle_frontier/trainer_hill_ereader.h`.

2. **`src/data/battle_frontier/trainer_hill_ereader.h`**:
   - Contains candidate pools for Normal, Variety, Unique, and Expert with metatiles, collisions, coordinates, and full trainer data.

3. **`src/trainer_hill.c`**:
   - Facility gameplay engine: procedural selection of 4 floors (8 trainers), team order shuffling for double battles, and previous-floor anti-repetition guards.

4. **`src/data/battle_frontier/trainer_hill.h`**:
   - Main header including `trainer_hill_ereader.h` and managing base floor tables.

---

## 4. Build & Verification Commands

To regenerate the e-Reader data header:
```bash
python3 tools/trainer_hill/decompile_ereader.py
```

To compile the ROM:
```bash
make modern -j12
```

*(Note: Requires the `devkitARM` toolchain configured under `/opt/devkitpro/devkitARM/bin`).*
