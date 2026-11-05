# AGENTS.md - Altering Cave Lure System Expansion

This document summarizes the architecture, mechanics, technical decisions, and full implementation of the **Altering Cave Lure System** within `pokeemerald-expansion`. It serves as a comprehensive reference guide for any developer or AI agent maintaining or customizing this codebase.

---

## 1. Context & Core Objectives

In vanilla Pokémon Emerald and FireRed/LeafGreen, **Altering Cave** (`MAP_ALTERING_CAVE`) was intended to change its wild encounters via Mystery Gift / e-Reader distribution (`VAR_ALTERING_CAVE_WILD_SET`), cycling between Zubat (default) and 8 non-Hoenn species (Mareep, Pineco, Houndour, Teddiursa, Aipom, Shuckle, Stantler, Smeargle). Because the distribution events were never widely held outside Japan, the cave remained permanently filled with Zubats in normal gameplay.

This expansion repurposes and modernizes Altering Cave by introducing **6 consumable Lure items**:
- **Normal Lure**
- **Water Lure**
- **Bug Lure**
- **Rock Lure**
- **Special Lure**
- **Rare Lure**

Using a Lure shifts Altering Cave's wild encounter table to a dedicated pool with varied species and appearance ratios for **250 steps** (parity with Max Repel). When steps expire or when the player leaves the cave, encounters cleanly revert to the cave's default fauna.

---

## 2. Requirements & Implementations

### 2.1. The 6 Lure Items
- **Items defined (`include/constants/items.h`, `src/data/items.h`):**
  - `ITEM_NORMAL_LURE` (874)
  - `ITEM_WATER_LURE` (875)
  - `ITEM_BUG_LURE` (876)
  - `ITEM_ROCK_LURE` (877)
  - `ITEM_SPECIAL_LURE` (878)
  - `ITEM_RARE_LURE` (879)
- **Consumable & Bag Pocket:**
  - Located in `POCKET_ITEMS`, `.type = ITEM_USE_BAG_MENU`.
  - Players can purchase or carry multiple quantities; using one consumes exactly 1 item.
- **Duration:**
  - Configured with `.holdEffectParam = 250` (identical step duration to `ITEM_MAX_REPEL`).
- **Icons & Palettes:**
  - **Normal, Water, Bug, Rock Lure:** Use the standard Repel icon (`gItemIcon_Repel`, `gItemIconPalette_Repel`).
  - **Special Lure:** Uses the Super Repel palette (`gItemIcon_Repel`, `gItemIconPalette_SuperRepel`).
  - **Rare Lure:** Uses the Max Repel palette (`gItemIcon_Repel`, `gItemIconPalette_MaxRepel`).
- **Description Formatting:**
  - Formatted across 3 lines strictly constrained to 13–16 characters per line to guarantee no clipping with Emerald's bag menu borders.
  - All 6 lures consistently use `"in\nAltering Cave."` across lines 2 and 3.
  - Normal Lure explicitly references Normal-type Pokémon (`"Attracts Normal-\ntype Pokémon in\nAltering Cave."`).

### 2.2. Location & Usage Restrictions
- **Inside Altering Cave Only:**
  - Attempting to use any Altering Cave Lure outside of `MAP_ALTERING_CAVE` is blocked and triggers standard DAD's advice via `DisplayDadsAdviceCannotUseItemMessage`:
    > *"DAD's advice…\n{PLAYER}, there's a time and place for\leverything!"* (`gText_DadsAdvice`)
- **Active Lure Guard:**
  - If a Lure is already active in Altering Cave, attempting to use another displays:
    > *"But the effects of a Lure\nlingered from earlier."* (`gText_LureEffectsLingered`)
  - Prevents accidental overwriting of an active Lure before its steps expire.

### 2.3. Step Tracking & Expiration Flow
- **Step Counting (`UpdateAlteringCaveLureStepCounter` in `src/wild_encounter.c`):**
  - Integrated into `TryStartStepBasedScript()` in `src/field_control_avatar.c`.
  - With each valid player movement step while `FLAG_ALTERING_CAVE_LURE_ACTIVE` is set, `VAR_ALTERING_CAVE_LURE_STEPS` decrements by 1.
- **Wear-Off Script (`EventScript_AlteringCaveLureWoreOff` in `data/maps/AlteringCave/scripts.inc`):**
  - When steps reach 0, the engine launches `EventScript_AlteringCaveLureWoreOff`.
  - It buffers the active item name (`STR_VAR_1`) and checks if the player has more of that specific lure in their bag.
  - **If bag contains more:** Prompts the player:
    > *"{STR_VAR_1}'s effect wore off!\nUse another?"* (`AlteringCave_Text_LureWoreOffAskAnother`)
    - If **YES**: Plays `SE_REPEL`, consumes 1 lure from the bag, resets steps to 250, maintains the encounter table, and displays *"{PLAYER} used the {STR_VAR_2}."*
    - If **NO**: Displays *"{STR_VAR_1}'s effect wore off…"*, resets `VAR_ALTERING_CAVE_WILD_SET` to 0, and restores standard Altering Cave spawns.
  - **If bag has none left:** Displays *"{STR_VAR_1}'s effect wore off…"*, resets `VAR_ALTERING_CAVE_WILD_SET` to 0, and restores standard Altering Cave spawns.

### 2.4. Exit Interception (Safari Zone Parity)
- **Exit Trigger (`AlteringCave_EventScript_ExitTrigger` in `data/maps/AlteringCave/scripts.inc`):**
  - A coordinate trigger is placed at `(18, 22)` in `data/maps/AlteringCave/map.json` conditioned on `FLAG_ALTERING_CAVE_LURE_ACTIVE == 1`.
  - When no lure is active, the trigger is inert and the warp at `(18, 22)` operates seamlessly into Route 103.
  - When a lure is active and the player steps on `(18, 22)` to leave:
    > *"The {STR_VAR_1} is still active.\nIf you leave, its effect will fade.\pAre you sure you want to exit?"* (`AlteringCave_Text_LureStillActiveExitEarly`)
    - If **NO**: The player steps 1 tile up (`applymovement LOCALID_PLAYER, AlteringCave_Movement_StepBackUp`), keeping their active lure and staying in the cave.
    - If **YES**: Displays *"{STR_VAR_1}'s effect wore off."*, clears `FLAG_ALTERING_CAVE_LURE_ACTIVE`, zeros `VAR_ALTERING_CAVE_LURE_STEPS`, zeros `VAR_ALTERING_CAVE_WILD_SET`, and warps the player to Route 103 at `(45, 6)`.
- **Alternative Exit Cleanup (Dig, Escape Rope, Teleport, Blackout):**
  - In `Task_UseDigEscapeRopeOnField()` (`src/item_use.c`) and inside `UpdateAlteringCaveLureStepCounter()` (`src/wild_encounter.c`), if the player leaves Altering Cave by any means, `FLAG_ALTERING_CAVE_LURE_ACTIVE`, `VAR_ALTERING_CAVE_LURE_STEPS`, `VAR_ALTERING_CAVE_WILD_SET`, and `VAR_ALTERING_CAVE_LURE_ITEM` are automatically cleared.

### 2.5. Debug Menu Integration
- In `src/debug.c` (`DebugAction_PCBag_Fill_PocketItems`), the 6 Altering Cave Lures are prioritized and populated first into the Items pocket so that players and developers using the Debug Menu immediately receive them without being blocked by pocket capacity limits.

---

## 3. Encounter Tables & Architecture

### 3.1. Encounter Mapping
Altering Cave's encounter selection uses the built-in sequential header indexing in `GetCurrentMapWildMonHeaderId()` (`src/wild_encounter.c`):
$$\text{headerIndex} = \text{baseHeader} + \text{VarGet}(\text{VAR\_ALTERING\_CAVE\_WILD\_SET})$$

| Table Index | Variable Value | Lure Item | Encounter Group Label | Primary Theme & Species |
|---|---|---|---|---|
| `0` | `0` | *None (Default)* | `gAlteringCave1` | Zubat (Vanilla defaults, Lv 6–16) |
| `1` | `1` | `ITEM_NORMAL_LURE` | `gAlteringCave2` | Normal: Castform (20%), Eevee (20%), Togepi (15%), Kecleon (13%), Tauros (11%), Kangaskhan (11%), Chansey (10%) |
| `2` | `2` | `ITEM_WATER_LURE` | `gAlteringCave3` | Water: Omanyte (30%), Kabuto (30%), Lapras (18%), Relicanth (15%), Feebas (7%) |
| `3` | `3` | `ITEM_BUG_LURE` | `gAlteringCave4` | Bug: Volbeat (20%), Illumise (20%), Anorith (15%), Surskit (13%), Pinsir (12%), Heracross (10%), Scyther (10%) |
| `4` | `4` | `ITEM_ROCK_LURE` | `gAlteringCave5` | Rock: Lileep (20%), Anorith (20%), Omanyte (16%), Kabuto (16%), Aerodactyl (14%), Relicanth (14%) |
| `5` | `5` | `ITEM_SPECIAL_LURE` | `gAlteringCave6` | Special: Chimecho (20%), Wynaut (20%), Hitmonlee (16%), Hitmonchan (16%), Beldum (14%), Skarmory (14%) |
| `6` | `6` | `ITEM_RARE_LURE` | `gAlteringCave7` | Rare: Dratini (23%), Absol (20%), Feebas (20%), Chansey (20%), Kecleon (17%) |

*Note: Tables `gAlteringCave8` and `gAlteringCave9` remain reserved in the wild encounter data.*

### 3.2. Encounter Slot Distribution & Level Origins
Each of the 6 Lure encounter tables in `src/data/wild_encounters.json` contains 12 standard land encounter slots with the fixed engine odds:
- **Slots 0–1:** 20% each
- **Slots 2–5:** 10% each
- **Slots 6–7:** 5% each
- **Slots 8–9:** 4% each
- **Slots 10–11:** 1% each

#### Sourced Level Ranges (Canonical Origins)
The level assigned to each species mirrors the most common appearance in `wild_encounters.json` across Hoenn routes and FRLG areas, or standard gift/fossil resurrection levels where not naturally wild:
- **Chansey:** Lv 23 (FRLG Safari Zone Center)
- **Tauros:** Lv 28 (FRLG Safari Zone North)
- **Kangaskhan:** Lv 25 (FRLG Safari Zone East)
- **Kecleon:** Lv 25 (Hoenn Routes 118, 119, 120, 121, 123)
- **Togepi:** Lv 5 (Water Path egg hatch)
- **Castform:** Lv 25 (Weather Institute gift)
- **Eevee:** Lv 25 (Celadon Condominiums gift)
- **Feebas:** Lv 20–25 (Route 119 `gWildFeebas`)
- **Relicanth:** Lv 30–35 (Underwater Routes 124, 126)
- **Lapras:** Lv 30–45 (Icefall Cave Back)
- **Omanyte / Kabuto / Lileep / Anorith / Aerodactyl:** Lv 20 (Devon Corp fossil revival)
- **Scyther:** Lv 23 (FRLG Safari Zone Center)
- **Pinsir:** Lv 27 (Safari Zone Northwest)
- **Heracross:** Lv 15 (Pattern Bush)
- **Surskit:** Lv 3 (Route 102 land)
- **Volbeat / Illumise:** Lv 13 (Route 117)
- **Hitmonlee / Hitmonchan:** Lv 25 (Saffron Fighting Dojo)
- **Chimecho:** Lv 28 (Mt. Pyre Summit)
- **Wynaut:** Lv 10 (Mirage Island)
- **Beldum:** Lv 5 (Mossdeep Steven gift)
- **Skarmory:** Lv 16 (Route 113)
- **Absol:** Lv 25 (Route 120)
- **Dratini:** Lv 15–25 (FRLG Safari Zone fishing)

All tables are compiled into `src/data/wild_encounters.h` via `tools/wild_encounters/wild_encounters_to_header.py`.

### 3.3. Pokédex Area Screen Parity
`src/pokedex_area_screen.c` queries `VAR_ALTERING_CAVE_WILD_SET` directly. When an Altering Cave Lure is active, the Pokédex Area Screen dynamically reflects Altering Cave as the location of the active Lure's encounter pool.

---

## 4. Constants & State Storage

| Constant | Value | Purpose |
|---|---|---|
| `ITEM_NORMAL_LURE` | `874` | Normal Lure item constant |
| `ITEM_WATER_LURE` | `875` | Water Lure item constant |
| `ITEM_BUG_LURE` | `876` | Bug Lure item constant |
| `ITEM_ROCK_LURE` | `877` | Rock Lure item constant |
| `ITEM_SPECIAL_LURE` | `878` | Special Lure item constant |
| `ITEM_RARE_LURE` | `879` | Rare Lure item constant |
| `FLAG_ALTERING_CAVE_LURE_ACTIVE` | `0x20` | High-level flag tracking active lure state; powers map coord trigger |
| `VAR_ALTERING_CAVE_LURE_STEPS` | `0x40DB` | Remaining steps counter (initialized to 250) |
| `VAR_ALTERING_CAVE_LURE_ITEM` | `0x40DC` | Stores the active lure itemId for text buffering and "Use another?" prompts |
| `VAR_ALTERING_CAVE_WILD_SET` | `0x403E` | Engine variable selecting the active wild encounter table ($0..6$) |

---

## 5. Key Source Files Modified

| File | Changes Made |
|---|---|
| `include/constants/items.h` | Registered `ITEM_NORMAL_LURE` through `ITEM_RARE_LURE` (874..879). |
| `include/constants/flags.h` | Assigned `FLAG_ALTERING_CAVE_LURE_ACTIVE` to `0x20`. |
| `include/constants/vars.h` | Assigned `VAR_ALTERING_CAVE_LURE_STEPS` (`0x40DB`) and `VAR_ALTERING_CAVE_LURE_ITEM` (`0x40DC`). |
| `include/item_use.h` | Declared `ItemUseOutOfBattle_AlteringCaveLure(u8 taskId)`. |
| `src/item_use.c` | Implemented `ItemUseOutOfBattle_AlteringCaveLure` (with Dad's advice rejection), `Task_StartUseAlteringCaveLure`, `Task_UseAlteringCaveLure`, and Escape Rope/Dig cleanup. |
| `src/debug.c` | Prioritized Altering Cave Lures in `DebugAction_PCBag_Fill_PocketItems` to ensure they are added to the bag on command. |
| `src/data/items.h` | Defined item properties, prices, Max Repel steps (250), pockets, and icons for all 6 lures. |
| `include/wild_encounter.h` | Declared `enum AlteringCaveWildSet`, `UpdateAlteringCaveLureStepCounter`, and lure-to-table helpers. |
| `src/wild_encounter.c` | Implemented `UpdateAlteringCaveLureStepCounter`, `GetAlteringCaveWildSetFromLure`, and `GetAlteringCaveLureItemFromWildSet`. |
| `src/field_control_avatar.c` | Hooked `UpdateAlteringCaveLureStepCounter()` into `TryStartStepBasedScript()`. |
| `data/maps/AlteringCave/scripts.inc` | Added `EventScript_AlteringCaveLureWoreOff`, prompt logic, item renewal, and `AlteringCave_EventScript_ExitTrigger`. |
| `data/maps/AlteringCave/map.json` | Added coordinate trigger at `(18, 22)` conditioned on `FLAG_ALTERING_CAVE_LURE_ACTIVE == 1`. |
| `src/data/wild_encounters.json` | Configured tables `gAlteringCave2` through `gAlteringCave7` with 12 distinct placeholder Pokémon slots each. |
| `src/data/wild_encounters.h` | Regenerated wild encounter headers with the new Altering Cave encounter tables. |

---

## 6. Build & Verification Commands

To regenerate wild encounter headers after editing encounter tables in `src/data/wild_encounters.json`:
```bash
python tools/wild_encounters/wild_encounters_to_header.py
```

To compile and link the ROM:
```bash
make -j4
```
Outputs `pokeemerald.gba` cleanly with no warnings or errors.
