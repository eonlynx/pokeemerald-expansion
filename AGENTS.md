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
    - *Layout adjustment:* In vanilla `floor_0`, the corridor at (X=7, Y=4) was blocked by an obstacle tile. The obstacle at (7, 4) was replaced with a clean passable floor tile (`0x3B`, identical to (8, 5), also updating (7, 3) to `0x3B` to eliminate the top obstacle corner artifact, while keeping (7, 5) as `0x35` to preserve the natural top edge of the obstacle below) to ensure proper routing and pathing across the floor.
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

### 2.8. Trainer Facing Directions & Double Battle Sight Lines
- **Bug Diagnosis:** In earlier decompilations, imported e-Reader trainers faced directions opposite or inverted from their intended orientations, preventing tag/double battles from triggering.
  - *Root Cause 1 (Trainer Nibble Swap):* Game Freak's macro `#define TRAINER_DIRS(a, b) (((a-1)<<4)|(b-1))` packs `a` into the high nibble (which in `trainer_hill.c` corresponds to `Trainer 2`) and `b` into the low nibble (`Trainer 1`). Passing `(dir_t1, dir_t2)` inverted the trainers' directions.
  - *Root Cause 2 (North/South Inversion):* Raw dotcodes encode movement directly as `0 = Up/North`, `1 = Down/South`, `2 = Left/West`, `3 = Right/East`. Mapping through engine direction constants (`DIR_SOUTH = 1`, `DIR_NORTH = 2`) inverted North and South.
  - *Fix:* `tools/trainer_hill/decompile_ereader.py` was updated to directly output raw hex bytes (`raw_dirs` and `raw_ranges`), matching the hardware format byte-for-byte and ensuring 100% fidelity without macro misalignments.
  - *Verification & Tooling:* An ASCII layout generator (`tools/trainer_hill/generate_ascii_layouts.py`) was created to export visual grids (`□` passable, `■` obstacle, arrows for facing directions, and `X` for double battle line-of-sight intersections) for all 63 raw cards, 2 JP Default floors, and 16 original Western floors. All maps confirm identical collision and trainer placements between Western releases and raw Japanese cards, guaranteeing proper double-battle triggers across all floors.

### 2.9. Level 50 and Open Level Challenge Modes
- **Battle Frontier Parity:** Players can choose between **Level 50** and **Open Level** after selecting any challenge mode (Normal, Variety, Unique, Expert).
- **Pokemon Roster Integrity:** Unlike Battle Frontier facilities which ban mythical/legendary species (`isFrontierBanned`), Trainer Hill retains its original freedom: **no Pokemon or held item is banned**, allowing players to use their full party of up to 6 Pokemon.
- **Level Mechanics:**
  - **Level 50 (`FRONTIER_LVL_50`):** Enemies are scaled to Level 50. If any Pokemon in the player's party exceeds Level 50, entry is denied with a descriptive prompt.
  - **Open Level (`FRONTIER_LVL_OPEN`):** Enemies scale to match the player's highest party level, with a minimum level of 60 (`FRONTIER_MIN_LEVEL_OPEN`).
- **Map Non-Repetition Decoupling:** Floor anti-repetition memory is tracked per mode (Normal, Variety, etc.) independently of the level mode chosen. Switching between Level 50 and Open Level preserves the non-repetition rules.

### 2.10. Battle Points (BP) Rewards System
- **Integration with Battle Frontier:** Rooftop item and TM rewards have been replaced with Battle Points (BP) directly credited to `gSaveBlock2Ptr->frontier.battlePoints` and `cardBattlePoints`, as well as tracking daily gains via `IncrementDailyBattlePoints`.
- **BP Payout Table:** The amount of BP awarded upon completing a challenge depends on the challenge mode and completion time:

| Time | Normal | Variety | Unique | Expert |
| :--- | :--- | :--- | :--- | :--- |
| > 18 min | 2 | 2 | 3 | 4 |
| 16–18 min | 2 | 3 | 4 | 6 |
| 14–16 min | 3 | 4 | 6 | 8 |
| 13–14 min | 4 | 6 | 7 | 10 |
| 12–13 min | 5 | 7 | 9 | 12 |
| < 12 min | 6 | 8 | 10 | 14 |

- **Zero EXP & Zero Prize Money:** Like all Battle Frontier facilities, Trainer Hill awards 0 EXP and 0 battle money upon defeating trainers, ensuring total economic and progression parity.
- **Legacy Cleanup:** Unused item prize list structures and lookup functions (`sPrizeListSets`, `GetPrizeItemId`, `GetPrizeListId`) were safely decommissioned to ensure clean, warning-free compilation.

### 2.11. Frontier Brain Wally & Gauge Credits System
- **Integration as Battle Hill:** Trainer Hill has been rebranded to **Battle Hill** across all scripts, map names, landmarks, and signposts, fully integrating it into the Battle Frontier experience. Facility music across all floors and lobby retains the facility theme `MUS_B_TOWER_RS`, and reception dialogue is harmonized to the Frontier standard (*"Where the agility of TRAINERS is put to the test! Welcome to the BATTLE HILL!"*). The reception menu uses `MULTI_CHALLENGEINFO` (`CHALLENGE / INFO / EXIT`) with full Battle Frontier rules explanation and farewell phrasing.
- **Frontier Brain Integration:** Wally serves as the Frontier Brain of Battle Hill with the official title and class **Hill Prodigy** (`TRAINER_CLASS_HILL_PRODIGY` / `"HILL PRODIGY"`).
- **Gauge Credits Accumulation:**
  - Challengers earn base gauge credits depending on their clear time:
    - `< 12 min`: 1.0 credit (100 internal units)
    - `12–13 min`: 0.8 credits (80 internal units)
    - `13–14 min`: 0.6 credits (60 internal units)
    - `14–16 min`: 0.4 credits (40 internal units)
    - `16–18 min`: 0.2 credits (20 internal units)
    - `> 18 min`: 0.0 credits (0 internal units)
  - Base credits are scaled by the selected mode multiplier:
    - **Normal:** $\times 0.5$
    - **Variety:** $\times 0.75$
    - **Unique:** $\times 1.0$
    - **Expert:** $\times 1.5$
  - Fixed-point integer arithmetic (`credits * 100`) is used to ensure precision without floating-point overhead on the GBA.
  - Gauge credits are stored in `gSaveBlock1Ptr->trainerHill.gaugeCredits` and persist across runs.
- **Brain Appearances & Agility Symbols:**
  - **Agility Symbol:** Defeating Wally awards the **Agility Symbol** on the player's Frontier Pass (`FLAG_SYS_HILL_SILVER` and `FLAG_SYS_HILL_GOLD`), accompanied by `MUS_OBTAIN_SYMBOL` fanfare and commemorative messages.
  - **Silver Brain (`TRAINER_WALLY_HILL_SILVER`):** Appears when gauge credits reach $\ge 2.0$ (200 units).
    - If Silver Symbol is not yet earned: awards the Silver Agility Symbol + combined Battle Points.
    - If Silver Symbol was already earned previously: awards combined Battle Points only (`TRAINER_HILL_BRAIN_STREAK`).
    - Defeating Silver does **not** reset the gauge, which continues climbing towards Gold.
  - **Gold Brain (`TRAINER_WALLY_HILL_GOLD`):** Appears when gauge credits reach $\ge 6.5$ (650 units).
    - If Gold Symbol is not yet earned: awards the Gold Agility Symbol + combined Battle Points (`TRAINER_HILL_BRAIN_GOLD`).
    - If Gold Symbol was already earned previously: awards combined Battle Points only (`TRAINER_HILL_BRAIN_STREAK_LONG`).
    - Defeating Gold advances the threshold by $+4.5$ credits, triggering subsequent Gold encounters at 11.0, 15.5, 20.0 credits, etc., without resetting the gauge.
  - **Streak Loss / Broken Runs:** If the player is defeated during the challenge, the winning streak is broken, resetting `gaugeCredits` to 0 and `nextBrainThreshold` to 2.0 credits. On the next climb, Wally Silver appears at 2.0 credits awarding Battle Points only.
- **Battle Points Distribution on Brain Runs:**
  - On runs where Wally appears, the Owner does not award the standard run BP prior to battle.
  - Instead, the Owner alerts the player and coordinates the exhibition. Upon victory and Wally's farewell, the Owner approaches the center of the rooftop, triggers celebratory confetti (`DoDomeConfetti`) with crowd applause (`SE_M_ENCORE2`), and proclaims the mode champion (*"{PLAYER} is the\n{STR_VAR_1} Champion!\pCongratulations!"* via `trainerhill_buffermodename`).
  - The Owner presents **10 BP + the run BP that the Owner would have given**, presenting the combined total all at once before escorting the player to reception.
  - On runs where Wally does not appear, the Owner awards the standard completion BP as usual and the player takes the elevator.
- **Rooftop Presentation, Spectators & Wally Battle Cutscene:**
  - Upon clearing 4F and arriving at the roof, 3 coordinate triggers placed at (12, 8), (12, 9), and (12, 10) directly south of the Owner use `VAR_TEMP_2` to prevent the player from bypassing the Owner to reach the elevator.
  - When Wally is challenged, the 8 trainers defeated across all 4 floors ascend the stairs in pairs and take viewing positions flanking the arena as spectators. The first two pairs position themselves on the side flanks (Pair 1: top left and top right; Pair 2: bottom left and bottom right), and the remaining two pairs position themselves along the south barrier (Pair 3: inner left and inner right; Pair 4: outer left and outer right), ensuring trainers never overlap during entry. Their overworld sprites are dynamically populated by `TRAINER_HILL_FUNC_SET_SPECTATOR_GFX` to accurately reflect the trainers encountered in the current run.
  - The Owner directs the challenger to take position in the arena, with the player standing at (10, 8) and Wally taking his battle position at (14, 8) facing each other, giving generous spacing above the south spectator line.
  - With an elevator chime (`SE_ELEVATOR`) and door open/close animations, Wally exits the elevator doorway at (15, 5), walks down onto the roof plaza, and takes position facing the player.
  - Wally heals the player's entire party (`special HealPlayerParty`) and delivers pre-battle dialogue steeped in his canonical journey with {PLAYER} (Ralts capture on Route 102, Mauville gym loss, Victory Road promise) before starting the battle.
  - Plays `MUS_VS_FRONTIER_BRAIN` and uses the standard Battle Frontier battle transition (`sBattleTransitionTable_BattleFrontier`). In addition, all standard floor battles across Battle Hill feature the canonical Battle Frontier logo transition animation (`sBattleTransitionTable_BattleFrontier`) instead of generic trainer transitions.
  - Upon victory, all 8 spectators react with synchronized jumping/cheering emote animations (`SE_M_ENCORE2`).
  - Wally presents the Agility Symbol (if first time), shares heartfelt farewell words, and enters cleanly into the elevator cab before the doors close, accompanied by elevator chimes and proper disappearing sequence, before the Owner proclaims the champion and awards the Battle Points.
- **Reception Sequence, Challenge Save & Match Recording (Battle Frontier Parity):**
  - **Brain Victory:** Warps directly to the entrance counter with the player already oriented facing North towards the receptionist (`MAP_SCRIPT_ON_WARP_INTO_MAP_TABLE`), where the receptionist congratulates the player on defeating the Hill Prodigy Wally and conquering Battle Hill.
  - **Challenge Save:** Both upon defeating Wally and upon defeat (`ExitChallengeLost`), the receptionist states *"Your record will be saved. Please wait."*, saving progress cleanly to flash via `trainerhill_savechallenge` / `SaveGameFrontier()` with `SE_SAVE`.
  - **Frontier Pass Match Recording:** Challengers are prompted with *"Would you like to record your last match on your FRONTIER PASS?"*. Selecting Yes invokes `BattleFrontier_EventScript_SaveBattle`, saving the battle replay to the Frontier Pass with canonical confirmation.
  - **Brevity & Formatting Standards:** All dialogues strictly adhere to $\le 34$ characters per line and canonical capitalization (`TRAINER`, `FRONTIER BRAIN`, `HILL PRODIGY`, `POKéMON`, `BATTLE HILL`).
- **Teams & Battle Properties (Strictly Hoenn 386 - 6v6 Double Battle):**
  - All Wally battles are **Double Battles (6 vs 6)** triggered via `trainerbattle_no_intro_double`.
  - **Silver Team (Level 50 or Open Level, 24 IVs):**
    - **Altaria** (Adamant @ Lum Berry) – Natural Cure: *Dragon Dance, Aerial Ace, Earthquake, Protect* (252 HP / 136 Atk / 120 Spe)
    - **Kecleon** (Brave @ Sitrus Berry) – Color Change: *Fake Out, Shadow Ball, Brick Break, Protect* (252 HP / 252 Atk / 6 SpD)
    - **Magneton** (Modest @ Bright Powder) – Magnet Pull: *Thunderbolt, Thunder Wave, Tri Attack, Protect* (128 HP / 252 SpA / 128 Spe)
    - **Roselia** (Calm @ Focus Band) – Natural Cure: *Giga Drain, Sludge Bomb, Leech Seed, Protect* (252 HP / 128 Def / 128 SpA)
    - **Azumarill** (Adamant @ Mystic Water) – Huge Power: *Double-Edge, Hydro Pump, Brick Break, Protect* (252 HP / 252 Atk / 6 Spe)
    - **Gardevoir** (Modest @ Leftovers) – Trace: *Calm Mind, Psychic, Thunderbolt, Protect* (128 HP / 252 SpA / 128 Spe)
  - **Gold Team (Level 50 or Open Level, 31 IVs):**
    - **Salamence** (Adamant @ Lum Berry) – Intimidate: *Dragon Dance, Rock Slide, Aerial Ace, Protect* (6 HP / 252 Atk / 252 Spe)
    - **Flygon** (Jolly @ Soft Sand) – Levitate: *Earthquake, Rock Slide, Dragon Claw, Protect* (6 HP / 252 Atk / 252 Spe)
    - **Cacturne** (Brave @ Quick Claw) – Sand Veil: *Needle Arm, Faint Attack, Brick Break, Protect* (252 HP / 252 Atk / 6 SpA)
    - **Sceptile** (Timid @ White Herb) – Overgrow: *Leaf Blade, Dragon Claw, Crunch, Protect* (6 HP / 252 SpA / 252 Spe)
    - **Milotic** (Bold @ Leftovers) – Marvel Scale: *Surf, Ice Beam, Recover, Toxic* (252 HP / 252 Def / 6 SpA)
    - **Gardevoir** (Timid @ Chesto Berry) – Trace: *Calm Mind, Psychic, Thunderbolt, Ice Punch* (6 HP / 252 SpA / 252 Spe)
  - **Dynamic Level Scaling:** In Level 50 mode, Wally's Pokémon are Level 50. In Open Level mode, they dynamically scale to match the player party's highest level (minimum 60 via `GetHighestLevelInPlayerParty`).

### 2.12. Battle Frontier Save Constraints & Challenge Lifecycle
- **Mandatory Entry Save:** Prior to entering the challenge, players are required to save their game via the canonical Battle Frontier prompt (*"Before you begin your BATTLE HILL\nchallenge, I must save the game.\lIs that okay?"* matching Battle Dome/Factory/Tower). If declined or if saving fails, entry is aborted.
- **Corridor Entry Step:** Upon finishing reception dialogue (*"Get set! Go!"*), the player automatically steps one tile North (`walk_up`) past the counter line into the entrance hallway (X=9, Y=5).
- **In-Facility Save Prohibition:** While inside Battle Hill (`InTrainerHillChallenge()`), saving is blocked in `src/start_menu.c` via `BuildTrainerHillStartMenu()`, removing `MENU_ACTION_SAVE` from the Start Menu identically to Battle Pike and Battle Pyramid.
- **Quit / Reset Disqualification:** If the player soft-resets or powers off without completing the run, upon reloading at reception the attendant intercepts them with the canonical Battle Frontier disqualification message (*"Excuse me!\pYou didn't save before you quit\nyour challenge last time.\pBecause of that, your challenge\nso far has been disqualified.\lSorry!"*) and saves progress, clearing streak credits and ending the run.
- **Retirement Interception:** Coordinate trigger at (9, 6) on the counter line prevents the player from walking back into the lobby while a challenge is active (`VAR_TRAINER_HILL_IS_ACTIVE == 1`). The attendant prompts (*"Would you like to retire from your\nBATTLE HILL challenge?"*):
  - **Yes:** Challenge is retired via `trainerhill_retire`, resetting winning streaks/gauge credits, saving progress (anchoring the player's saved spawn coordinates to X=9, Y=7 facing South in the lobby), stepping the player down into the lobby, and clearing `VAR_TRAINER_HILL_IS_ACTIVE`.
  - **No:** The player is stepped one tile back North (`walk_up`) into the hallway towards the challenge.

---

## 3. Key Source Files

1. **`tools/trainer_hill/decompile_ereader.py`**:
   - Python pipeline decoding dotcodes in `data/raw_cards/trainer_hill/` via `nedcenc` and `nevpk`.
   - Extracts metatile maps, trainer collision, IVs, EVs, moves, and held items.
   - Enforces English trainer names, replaces Japanese nicknames with species names, and writes faithful Easy Chat phrases.
   - Generates `src/data/battle_frontier/trainer_hill_ereader.h`.

2. **`tools/trainer_hill/generate_ascii_layouts.py` & `tools/trainer_hill/export_ascii_layouts/`**:
   - Visual ASCII representation tool and exported `.txt` layouts for all 81 floors (63 raw cards, 2 JP Default floors, 16 original Western floors).
   - Validates impassable geometry, trainer coordinates, vision cones, and tag-battle intersection triggers.

3. **`src/data/battle_frontier/trainer_hill_ereader.h`**:
   - Contains candidate pools for Normal, Variety, Unique, and Expert with metatiles, collisions, coordinates, and full trainer data.

4. **`src/trainer_hill.c`**:
   - Facility gameplay engine: procedural selection of 4 floors (8 trainers), team order shuffling for double battles, and previous-floor anti-repetition guards.

5. **`src/data/battle_frontier/trainer_hill.h`**:
   - Main header including `trainer_hill_ereader.h` and managing base floor tables.

---

## 4. Build & Verification Commands

To regenerate the e-Reader data header:
```bash
python3 tools/trainer_hill/decompile_ereader.py
```

To export/verify ASCII layout representations:
```bash
python3 tools/trainer_hill/generate_ascii_layouts.py
```

To compile the ROM:
```bash
make modern -j12
```

*(Note: Requires the `devkitARM` toolchain configured under `/opt/devkitpro/devkitARM/bin`).*
