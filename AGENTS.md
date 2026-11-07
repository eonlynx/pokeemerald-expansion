# AGENTS.md — Pokémon FireRed TCG Pocket Edition Architecture

This document defines the technical architecture, data structures, runtime execution flow, and conventions of the **Pokémon FireRed TCG Pocket Edition** engine implemented on top of `pokeemerald-expansion`.

---

## 1. Project Overview & Rules Engine

The project transforms Pokémon FireRed from a traditional turn-based creature RPG into a full fidelity implementation of the official **Pokémon TCG Pocket** rules:
- **20-Card Decks**: Teams consist of a 20-card deck instead of 6 traditional Pokémon.
- **Card Collection & Storage**: Cards are stored in dedicated Bag pockets and managed through the Pokémon PC Deck Storage System.
- **TCG Pocket Combat Mechanics**:
  - **No Bench Weakness & Flat +20 Weakness**: Bench Pokémon take unmodified damage; Active Pokémon take flat +20 damage if weak to the attacker's element.
  - **Turn Energy System**: Energy cards do not exist in the deck. An Energy Zone generates 1 elemental energy per turn based on the deck's elemental types. On Turn 1, the player going first generates 0 energy and cannot attack.
  - **Interactive Energy Attachment**: During the player's turn, the player can attach the generated energy to any Pokémon in play (Active or Bench). If not attached manually before attacking or ending turn, it safely defaults to the Active Pokémon.
  - **Checkup Phase**: Poison deals flat 10 HP damage; Burn deals flat 20 HP damage with a 50% coin flip to cure; Sleep requires a 50% coin flip to wake up; Paralysis lasts exactly 1 turn; Confusion has a 50% chance of failing the attack without self-damage.
  - **Hand Limit**: Hand holds up to 10 cards. No loss by deck-out.
  - **Prize Points**: 3 Prize Points to win (Standard Pokémon give 1 Prize Point; Shiny / EX / Legendary Pokémon give 2 Prize Points).
- **Kanto Integration**: Automatic HM abilities via badges and key items, direct card acquisition in `ScriptGiveMon`, and starter decks awarded by Prof. Oak.

---

## 2. Data Structures & Memory Layout

### 2.1. Card Definitions (`include/tcg.h`, `src/data/tcg_cards.h`)
Every card is defined in `struct TcgCardInfo`:
- `cardId`: Unique canonical ID (`1` to `431`).
- `name`: Card title string in English.
- `species`: Associated Gen 3 species (`SPECIES_NONE` for Trainer items and supporters).
- `preEvoSpecies`: Direct pre-evolution required in play to evolve (`Stage 1` / `Stage 2`).
- `equivItemId`: 1-to-1 mapped vanilla item constant (`ITEM_*` aliased via `ITEM_TCG_*`).
- `cardType`: `CARD_TYPE_POKEMON_BASIC`, `STAGE1`, `STAGE2`, `TRAINER_ITEM`, `TRAINER_SUPPORTER`.
- `energyType`: Elemental energy type (`ENERGY_GRASS`, `FIRE`, `WATER`, `LIGHTNING`, `PSYCHIC`, `FIGHTING`, `DARKNESS`, `METAL`, `COLORLESS`).
- `weaknessType`: Energy type against which the card takes +20 damage.
- `retreatCost`: Retreat cost in colorless energy.
- `maxHp`: Fixed card hit points.
- `pokemonPowerId`: Associated Pokémon Power ID (0 if none).
- `powerName`, `powerDescription`: Pokémon Power metadata.
- `move1`, `move2`: Mapped Gen 1–3 moves with `struct TcgAttackCost`.
- `move1Damage`, `move2Damage`: Exact numeric card attack damages.
- `isRareShiny`: Boolean flag; yields 2 Prize Points when knocked out instead of 1.
- `description`: 2-line concise summary string (≤ 18 characters/line for Pokémon; ≤ 3 lines for Trainer cards).

### 2.2. Save Block & Deck Storage (`struct SaveBlock1`)
In `include/global.h`, `SaveBlock1` stores:
```c
struct TcgDeck customDecks[MAX_CUSTOM_DECKS];   // 14 custom player decks of 20 cards
u8 currentDeckIndex;                           // Active deck index (0-13 or 0-31)
bool8 isCurrentDeckDefault;                     // TRUE if using a preset default deck
u32 unlockedDefaultDecksMask;                  // Bitmask of 32 unlocked default decks
```
To avoid GBA `SaveBlock1` size limits, unused features were liberated in `include/config/save.h`:
- `FREE_EXTRA_SEEN_FLAGS_SAVEBLOCK1`, `FREE_POKEMON_JUMP`, `FREE_RECORD_MIXING_HALL_RECORDS`, `FREE_EXTRA_SEEN_FLAGS_SAVEBLOCK2`.

### 2.3. Bag Pockets (`include/constants/item.h`)
The Bag is organized into 8 dedicated pockets:
1. `POCKET_TCG_POKEMON`: Pokémon cards (Capacity: 100). Opens by default.
2. `POCKET_TCG_ITEMS`: Trainer Item cards (Capacity: 50).
3. `POCKET_TCG_SUPPORTERS`: Trainer Supporter cards (Capacity: 50).
4. `POCKET_POKE_BALLS`: Standard capture balls.
5. `POCKET_KEY_ITEMS`: Story progression key items.
6. `POCKET_ITEMS_LEG`: Legacy RPG items. Rendered in gray (`COLORID_GRAY_CURSOR`), context menu restricted to `{ TOSS, CANCEL }`.
7. `POCKET_TM_HM`: Rendered in gray. Pressing A plays `SE_FAILURE` with no menu opened.
8. `POCKET_BERRIES`: Rendered in gray. Context menu restricted to `{ CHECK TAG, TOSS, CANCEL }`.

---

## 3. 1-to-1 Vanilla Mappings & Icon Uniqueness

### 3.1. 1-to-1 Move Effects Mappings (`include/tcg.h`)
To eliminate custom enum pollution and keep the codebase vanilla-compliant, all TCG battle effects map 1-to-1 to existing vanilla move effects in `include/tcg.h`:
```c
#define EFFECT_TCG_COIN_DAMAGE_BONUS     EFFECT_FUSION_COMBO
#define EFFECT_TCG_SELF_DAMAGE_COIN      EFFECT_RECOIL_IF_MISS
#define EFFECT_TCG_DISCARD_USER_ENERGY   EFFECT_PUNISHMENT
#define EFFECT_TCG_DISCARD_TARGET_ENERGY EFFECT_ACROBATICS
#define EFFECT_TCG_BENCH_SNIPER          EFFECT_SNIPE_SHOT
#define EFFECT_TCG_SHIELD_NEXT_TURN      EFFECT_BODY_PRESS
#define EFFECT_TCG_HEAL_USER             EFFECT_POPULATION_BOMB
#define EFFECT_TCG_DISABLE_MOVE          EFFECT_REVELATION_DANCE
#define EFFECT_TCG_BLIND_TARGET          EFFECT_TERRAIN_PULSE
#define EFFECT_TCG_DAMAGE_MULTI_COIN     EFFECT_RETALIATE
#define EFFECT_TCG_SELF_DAMAGE_FIXED     EFFECT_LASH_OUT
#define EFFECT_TCG_DRAW_CARD             EFFECT_GRASSY_GLIDE
#define EFFECT_TCG_SCALING_ENERGY        EFFECT_ROUND
#define EFFECT_TCG_SCALING_BENCH         EFFECT_ECHOED_VOICE
#define EFFECT_TCG_SCALING_DAMAGE_SELF   EFFECT_BOLT_BEAK
#define EFFECT_TCG_SCALING_DAMAGE_TARGET EFFECT_PSYSHOCK
#define EFFECT_TCG_PLUS_20_NEXT_TURN     EFFECT_HYDRO_STEAM
#define EFFECT_TCG_COIN_OR_NOTHING       EFFECT_TRUMP_CARD
#define EFFECT_TCG_DISCARD_ALL_ENERGY    EFFECT_STORED_POWER
#define EFFECT_TCG_SWITCH_OPPONENT       EFFECT_RAGE_FIST
#define MOVE_RETREAT                     MOVE_TELEPORT
```

### 3.2. 1-to-1 Trainer Items and Supporters (`include/tcg.h`, `src/data/items.h`)
All 50 Trainer cards map 1-to-1 to distinct vanilla `ITEM_*` constants with **50 strictly unique `.iconPic` and `.iconPalette` definitions** (0 shared icons, 0 question-mark icons):
- `ITEM_TCG_PROF_OAK`: `ITEM_LINKING_CORD` (`gItemIcon_LinkingCord`)
- `ITEM_TCG_BILL`: `ITEM_EXP_SHARE` (`gItemIcon_ExpShare`)
- `ITEM_TCG_SWITCH`: `ITEM_ESCAPE_ROPE` (`gItemIcon_EscapeRope`)
- `ITEM_TCG_PLUSPOWER`: `ITEM_X_ATTACK` (`gItemIcon_BattleStatItem` / `XAttack`)
- `ITEM_TCG_DEFENDER`: `ITEM_X_DEFENSE` (`gItemIcon_BattleStatItem` / `XDefend`)
- `ITEM_TCG_CLEFAIRY_DOLL`: `ITEM_POKE_DOLL` (`gItemIcon_PokeDoll`)
- `ITEM_TCG_MYSTERIOUS_FOSSIL`: `ITEM_ROOT_FOSSIL` (`gItemIcon_RootFossil`)
- `ITEM_TCG_COMPUTER_SEARCH`: `ITEM_UPGRADE` (`gItemIcon_Upgrade`)
- And so on for all 50 Trainer items and supporters.

---

## 4. UI Architecture & Formatting Limits

### 4.1. Text Boundaries
- **Bag Descriptions (`src/data/tcg_cards.h`, `src/data/items.h`)**:
  - `WIN_DESCRIPTION` width is 14 tiles (112 px).
  - Pokémon card descriptions are strictly formatted to 2 lines of $\le 18$ characters:
    - Line 1: `Base Set No. {cardId}`
    - Line 2: `HP: {maxHp} - {stage} PKMN`
  - Trainer cards are strictly formatted to $\le 3$ lines and $\le 18$ characters per line.
- **Move Descriptions (`src/data/moves_info.h`)**:
  - Strictly $\le 2$ lines and $\le 32$ characters per line.
  - Elemental costs are strictly forbidden in descriptions; costs render independently via the `COST/` HUD.

### 4.2. Bag Species Icons (`src/item_menu.c`, `src/item_menu_icons.c`)
- Bag defaults to `POCKET_TCG_POKEMON` on opening.
- When viewing `POCKET_TCG_POKEMON`, `AddBagItemIconSprite` dynamically allocates a 32x32 sprite using `GetMonIconTiles(species)` and `gMonIconPaletteTable`, displaying real Pokémon icons instead of generic item balls.

### 4.3. PC Deck Storage System (`src/pokemon_storage_system.c`)
- Removed `MOVE ITEMS` option. Menu options are: `DEFAULT DECKS`, `CUSTOM DECKS`, `CURRENT DECK`, `SEE YA!`.
- Box 0 dynamically synchronizes to the active 20-card deck with custom wallpaper and titles.
- Trainer cards render their authentic 24x24 item icons in the storage preview window. Cards unowned in Bag render translucent.

### 4.4. Summary Screen Overhaul (`src/pokemon_summary_screen.c`)
- Trainer cards are restricted to Page 1 only (`PSS_PAGE_INFO`).
- **Page 1 (`PSS_PAGE_INFO`)**: Displays OT, `#cardId`, Ability / Pokémon Power info, Memo: Stage, HP, Retreat cost, Weakness (+20), and Prize value (`1 PT` / `2 PTS`).
- **Page 2 (`PSS_PAGE_SKILLS`)**: Displays `HP`, `MOVE 1` (damage), `MOVE 2` (damage), `RETRT` (retreat cost), `WEAK` (weakness type), `PRIZE` (prize value), `CARD ID`, and `BAG OWN` (count owned in Bag).

---

## 5. Battle Interface & Healthboxes (`src/battle_interface.c`)

- **Double-Battle-Style Healthboxes**: In singles battles, healthbox coordinates use `BATTLE_COORDS_DOUBLES`:
  - Top healthboxes: Active Pokémon (Player battler 0, Opponent battler 1).
  - Bottom healthboxes: Bench Pokémon (Player bench battler 2 at `{171, 101}`, Opponent bench battler 3 at `{32, 44}`).
- **Card ID (#123) in Place of Level**: `UpdateLvlInHealthbox` formats `CHAR_EXTRA_SYMBOL` + `CHAR_NO` (`№`) followed by the Card ID (`№123`) instead of RPG Level.
- **Bench Pokémon Display**: `UpdateTcgBenchHealthboxes()` prints the nickname and `HP/MaxHP` (e.g. `PIKACHU 60/60`) for up to 3 benched Pokémon using `FONT_SMALL_NARROW`.
- **Wild Battle Bottom Shortcuts**: In wild battles, the bottom healthbox displays `[L] BAG` and `[R] RUN`.
- **Target Blinking Support**: When targeting bench slots during field selection, `UpdateTcgBenchHealthboxes()` omits rendering the targeted slot on alternate frames, creating a smooth blinking selection effect.

---

## 6. Interactive PLAY Field Selection & Action Sub-Menu (`src/battle_controller_player.c`)

When the player selects `PLAY` from the main battle action menu (`PLAY`, `DECK`, `HAND`, `END TURN`):
1. **Field Selection (`InitFieldSelection`, `Task_HandleFieldSelection`)**:
   - D-Pad Left/Right: Toggles between Player Side (`B_SIDE_PLAYER`) and Opponent Side (`B_SIDE_OPPONENT`).
   - D-Pad Up/Down: Cycles between Active mon (slot 0) and alive Bench mons (slots 1..3).
   - Blinking: If slot 0 is targeted, the Active battler sprite blinks every 16 frames. If bench slots 1..3 are targeted, the bench Pokémon's text in the bottom healthbox blinks.
   - B Button: Cancels targeting, restores visibility, and returns to main action menu.
   - A Button: Confirms selection and opens the action sub-menu for that Pokémon.
2. **Pokémon Action Sub-Menu (`InitPokemonActionSubMenu`, `Task_HandlePokemonActionSubMenu`)**:
   - **Opponent Pokémon**: Prompts `"Foe PKMN in play."` with options `SUMMARY` and `DONE`.
   - **Player Pokémon**: Prompts `"Do what with this PKMN?"`:
     - **Active Pokémon (Slot 0)**: `FIGHT`, `ENERGY`, `SUMMARY`, `DONE`.
     - **Bench Pokémon (Slots 1..3)**: `-----`, `ENERGY`, `SUMMARY`, `DONE`.
   - **Action Behaviors**:
     - `FIGHT`: Emits `B_ACTION_USE_MOVE` to choose an attack or retreat. (Blocked on Turn 1 for the first player).
     - `ENERGY`: If energy was already attached this turn, plays `SE_FAILURE` and prints `"Energy was already attached this turn!"`. Otherwise, calls `AttachTurnEnergyToSlot`, sets `energyAttachedThisTurn = TRUE`, plays `SE_M_STAT_INCREASE`, updates bench healthboxes, and prints `"+1 {Energy} on {Mon}!"`.
     - `SUMMARY`: Smoothly fades to the Summary Screen for that specific Pokémon using `CB2_SetUpReshowBattleScreenAfterMenu2`.
     - `DONE`: Returns to main action menu.
3. **Safety Fallback**: If the player directly selects `FIGHT` or `END TURN` without manually attaching energy, the turn energy is automatically attached to the Active Pokémon (slot 0), preventing accidental energy loss.

---

## 7. Battle Literals & Messages

Canonical string IDs added to `include/constants/battle_string_ids.h` and defined in `src/battle_message.c`:
- `STRINGID_TCG_ATTACH_ENERGY_PLAYER`: `"Attached {STR_VAR_2} Energy to\n{STR_VAR_1}!\p"`
- `STRINGID_TCG_ATTACH_ENERGY_OPPONENT`: `"The opposing Trainer attached\n{STR_VAR_2} Energy to {STR_VAR_1}!\p"`
- `STRINGID_TCG_GENERATE_ENERGY_PLAYER`: `"Generated a {STR_VAR_2} Energy!\p"`
- `STRINGID_TCG_GENERATE_ENERGY_OPPONENT`: `"The opposing side generated\na {STR_VAR_2} Energy!\p"`
- `STRINGID_TCG_TRAINER_PLAYED`: `"{STR_VAR_1} played\n{STR_VAR_2}!\p"`
- `STRINGID_TCG_POWER_USED`: `"{STR_VAR_1} activated\n{STR_VAR_2}!\p"`
- `STRINGID_TCG_ENERGY_ALREADY_ATTACHED`: `"Energy was already attached\nthis turn!\p"`
- `STRINGID_TCG_COIN_HEADS`: `"Coin flip: HEADS!\p"`
- `STRINGID_TCG_COIN_TAILS`: `"Coin flip: TAILS!\p"`
- `STRINGID_TCG_RETREAT`: `"{B_ATK_NAME_WITH_PREFIX} retreated to the Bench!\p"`
- `STRINGID_TCG_FOUND_HELD_ITEM`: `"Also obtained a {STR_VAR_1}!\p"`

At the start of each player turn, the prompt dynamically informs the player of the opponent's attached energy:
- Line 1: `Foe: +1{oppE} to {oppMon}`
- Line 2: `What will {Player} do?`

---

## 8. Hand Management & Scroll Indicators (`src/party_menu.c`)

- In battle `HAND` view, up to 10 cards can be held.
- When holding > 6 cards, `AddScrollIndicatorArrowPairParameterized` renders animated red up/down scroll arrows at `{230, 8}` (top) and `{230, 148}` (bottom).
- D-Pad navigation seamlessly scrolls through the hand when navigating UP past slot 0 or DOWN past the last visible slot.
- Exiting the party menu cleanly frees the arrow task via `RemoveScrollIndicatorArrowPair`.

---

## 9. Decks & Trainer Map

- **Deduplication Threshold**: Decks sharing $\ge 15/20$ cards were deduplicated.
- **Coverage**: All 429 playable canonical cards are actively featured across **246 total decks** (**0 unused cards**).
- **Static Deterministic Mapping**: The table `gTrainerToDeckMap[TRAINERS_COUNT]` assigns a fixed thematic deck to all **624 trainers in FireRed**.
- **Formal Validation (`tools/validate_all_decks.py`)**:
  - Exactly 20 cards per deck.
  - At least 1 real Basic Pokémon.
  - Maximum 2 copies per card and per Pokémon species.
  - 0 evolution orphans (all Stage 1 and Stage 2 cards have their pre-evolutions).
  - Validation Result: **[PASS] All 246 decks validated with 0 errors**.

---

## 10. Developer Guidelines

- **NEVER run `make` or compile the ROM** in this environment; compilation is strictly handled by the user.
- **100% English Code & Data**: All C code, identifiers, comments, descriptions, and reports must be in English.
- **Preserve Clean Struct Boundaries**: Do not introduce custom enums or bloated arrays into global save blocks.
- **All Maintenance Tools in `tools/`**: Keep extraction, generation, and validation scripts inside `tools/`.
